"""
Video Dehazing API - Single-file consolidated application
Run from project root: python app.py

This application provides:
- Video upload and dehazing processing
- Real-time progress tracking via WebSockets
- Multiple model architecture support (4, 8, 16 layers)
- GPU acceleration with FP16 support
- REST API for integration
"""

import sys
import os
import uuid
import shutil
import json
import cv2
import time
import base64
import torch
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Callable, Optional, List, Tuple
from enum import Enum
from contextlib import asynccontextmanager

from fastapi import (
    FastAPI, UploadFile, File, HTTPException, BackgroundTasks, 
    WebSocket, WebSocketDisconnect, APIRouter
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import uvicorn

# ============================================================================
# CONFIGURATION
# ============================================================================

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Server
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    DEBUG: bool = Field(default=True, description="Debug mode")
    RELOAD: bool = Field(default=True, description="Auto-reload on code changes")
    
    # Paths
    UPLOAD_DIR: Path = Field(default=Path("./uploads"), description="Upload directory")
    OUTPUT_DIR: Path = Field(default=Path("./outputs"), description="Output directory")
    MODEL_DIR: Path = Field(
        default=Path(__file__).resolve().parent / "models" / "pretrained", 
        description="Model directory"
    )
    
    # Model Configuration
    DEFAULT_MODEL_LAYERS: int = Field(default=8, description="Default model layers (4, 8, or 16)")
    DEFAULT_MODEL_WEIGHTS: str = Field(default="dehazenet_8layers_best.pth", description="Default model file")
    DEVICE: str = Field(default="cpu", description="Device: cuda or cpu")
    ENABLE_FP16: bool = Field(default=False, description="Enable half-precision inference")
    
    # Processing
    MAX_UPLOAD_SIZE: int = Field(default=500, description="Max upload size in MB")
    ALLOWED_EXTENSIONS: List[str] = Field(
        default=["mp4", "avi", "mov", "mkv"], 
        description="Allowed video formats"
    )
    DEFAULT_RESOLUTION: int = Field(default=256, description="Default processing resolution")
    BATCH_SIZE: int = Field(default=8, description="Batch size for frame processing")
    
    # Cleanup
    AUTO_CLEANUP_HOURS: int = Field(default=24, description="Auto-cleanup old files after N hours")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(default=["*"], description="Allowed CORS origins")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Auto-adjust device based on availability
        try:
            if self.DEVICE == "cuda" and not torch.cuda.is_available():
                print("⚠️  CUDA not available. Falling back to CPU.")
                self.DEVICE = "cpu"
                self.ENABLE_FP16 = False
        except Exception:
            if self.DEVICE == "cuda":
                print("⚠️  Torch not installed; defaulting device to CPU.")
                self.DEVICE = "cpu"
                self.ENABLE_FP16 = False


settings = Settings()

# ============================================================================
# MODELS & SCHEMAS
# ============================================================================

class ProcessingStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ModelType(str, Enum):
    """Available model architectures"""
    LAYERS_8 = "8"
    LAYERS_16 = "16"


# Fallback mapping for unavailable models
MODEL_FALLBACK_MAP = {
    "4": "8",  # 4-layer not available, use 8-layer as fallback
}


class UploadResponse(BaseModel):
    """Response after successful upload"""
    job_id: str = Field(..., description="Unique job identifier")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    upload_time: datetime = Field(..., description="Upload timestamp")
    message: str = Field(default="Video uploaded successfully")


class ProcessRequest(BaseModel):
    """Request to start video processing"""
    model_config = {"protected_namespaces": ()}
    
    job_id: str = Field(..., description="Job ID from upload")
    model_layers: ModelType = Field(default=ModelType.LAYERS_8, description="Model architecture")
    resolution: int = Field(default=512, description="Processing resolution")
    use_fp16: bool = Field(default=False, description="Use half-precision inference")
    device: Optional[str] = Field(default=None, description="Override device (cuda/cpu)")


class ProcessResponse(BaseModel):
    """Response after starting processing"""
    job_id: str
    status: ProcessingStatus
    message: str
    estimated_time: Optional[int] = Field(None, description="Estimated completion time in seconds")


class JobStatus(BaseModel):
    """Current status of a processing job"""
    job_id: str
    status: ProcessingStatus
    progress: float = Field(..., ge=0.0, le=100.0, description="Progress percentage")
    current_frame: Optional[int] = Field(None, description="Current frame being processed")
    total_frames: Optional[int] = Field(None, description="Total frames in video")
    fps: Optional[float] = Field(None, description="Processing speed (frames per second)")
    elapsed_time: Optional[float] = Field(None, description="Time elapsed in seconds")
    estimated_remaining: Optional[float] = Field(None, description="Estimated time remaining in seconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Output info (when completed)
    output_video_path: Optional[str] = None
    output_size: Optional[int] = None
    statistics: Optional[Dict[str, Any]] = None


class DownloadInfo(BaseModel):
    """Information about downloadable output"""
    job_id: str
    filename: str
    file_size: int
    download_url: str
    created_at: datetime
    statistics: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    job_id: Optional[str] = None

# ============================================================================
# MODEL SERVICE
# ============================================================================

# Import the DeepDehazeNet model from the project
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.models.dehazenet import DeepDehazeNet
except ImportError:
    print("⚠️  Could not import DeepDehazeNet. Make sure src/models/dehazenet.py exists.")
    DeepDehazeNet = None


class ModelService:
    """Singleton service for model loading and inference."""
    
    _instance = None
    _models = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_model(
        self,
        layers: int = 8,
        weights_path: Optional[Path] = None,
        device: str = "cuda",
        use_fp16: bool = False
    ) -> 'DeepDehazeNet':
        """Load or retrieve cached model"""
        
        if DeepDehazeNet is None:
            raise RuntimeError("DeepDehazeNet model not available")
        
        # Check device availability
        if device == "cuda" and not torch.cuda.is_available():
            print("⚠️  CUDA requested but not available, falling back to CPU")
            device = "cpu"
            use_fp16 = False
        
        cache_key = (layers, device, use_fp16)
        
        if cache_key in self._models:
            print(f"✅ Using cached model: {layers} layers, device={device}, fp16={use_fp16}")
            return self._models[cache_key]
        
        print(f"🔄 Loading model: {layers} layers, device={device}, fp16={use_fp16}")
        
        model = DeepDehazeNet(num_layers=layers).to(device)

        if not weights_path or not weights_path.exists():
            available = sorted(p.name for p in settings.MODEL_DIR.glob("dehazenet_*layers_best.pth"))
            available_msg = ", ".join(available) if available else "none found"
            raise FileNotFoundError(
                f"Weights not found for {layers}-layer model at {weights_path}. "
                f"Available weights: {available_msg}."
            )

        try:
            state_dict = torch.load(weights_path, map_location=device)
            model.load_state_dict(state_dict)
            print(f"✅ Loaded weights from: {weights_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to load weights from {weights_path}: {e}")
        
        if use_fp16 and device == "cuda":
            model = model.half()
            print("✅ Converted model to FP16")
        
        model.eval()
        self._models[cache_key] = model
        
        print(f"✅ Model ready for inference")
        return model
    
    def preprocess_frame(
        self,
        frame: np.ndarray,
        target_size: Tuple[int, int] = (512, 512),
        device: str = "cuda",
        use_fp16: bool = False
    ) -> torch.Tensor:
        """Preprocess a single frame for inference"""
        
        frame_resized = cv2.resize(frame, target_size)
        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        frame_normalized = frame_rgb.astype(np.float32) / 255.0
        tensor = torch.from_numpy(frame_normalized).permute(2, 0, 1).unsqueeze(0)
        tensor = tensor.to(device)
        
        if use_fp16 and device == "cuda":
            tensor = tensor.half()
        
        return tensor
    
    def postprocess_output(
        self,
        output: torch.Tensor,
        use_fp16: bool = False
    ) -> np.ndarray:
        """Convert model output back to image format"""
        
        if use_fp16:
            output = output.float()
        
        output_image = output.squeeze().cpu().numpy().transpose(1, 2, 0)
        output_image = np.clip(output_image * 255, 0, 255).astype(np.uint8)
        output_bgr = cv2.cvtColor(output_image, cv2.COLOR_RGB2BGR)
        
        return output_bgr
    
    @torch.no_grad()
    def infer_frame(
        self,
        model: 'DeepDehazeNet',
        frame: np.ndarray,
        target_size: Tuple[int, int] = (512, 512),
        device: str = "cuda",
        use_fp16: bool = False
    ) -> np.ndarray:
        """Complete inference pipeline for a single frame"""
        
        input_tensor = self.preprocess_frame(frame, target_size, device, use_fp16)
        output_tensor = model(input_tensor)
        dehazed_frame = self.postprocess_output(output_tensor, use_fp16)
        
        return dehazed_frame
    
    def clear_cache(self):
        """Clear all cached models to free memory"""
        self._models.clear()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("✅ Model cache cleared")


model_service = ModelService()

# ============================================================================
# VIDEO PROCESSING SERVICE
# ============================================================================

class VideoProcessor:
    """Handles video processing with real-time progress updates."""
    
    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a job"""
        return self.jobs.get(job_id)
    
    def update_job_status(self, job_id: str, updates: Dict[str, Any]):
        """Update job status"""
        if job_id in self.jobs:
            self.jobs[job_id].update(updates)
    
    async def process_video(
        self,
        job_id: str,
        input_path: Path,
        output_path: Path,
        model_layers: int = 8,
        resolution: int = 512,
        device: str = "cuda",
        use_fp16: bool = False,
        progress_callback: Optional[Callable] = None
    ):
        """Process a video file with dehazing"""
        
        self.jobs[job_id] = {
            "status": ProcessingStatus.PROCESSING,
            "progress": 0.0,
            "current_frame": 0,
            "total_frames": 0,
            "fps": 0.0,
            "elapsed_time": 0.0,
            "estimated_remaining": 0.0,
            "error_message": None,
            "output_video_path": None,
            "statistics": {}
        }
        
        try:
            weights_filename = f"dehazenet_{model_layers}layers_best.pth"
            weights_path = settings.MODEL_DIR / weights_filename
            
            # Check if weights exist, fallback if necessary
            if not weights_path.exists() and str(model_layers) in MODEL_FALLBACK_MAP:
                fallback_layers = int(MODEL_FALLBACK_MAP[str(model_layers)])
                print(f"⚠️  Model weights for {model_layers} layers not found. Using {fallback_layers} layers as fallback.")
                state["error_message"] = f"Using {fallback_layers}-layer model (4-layer not available)"
                model_layers = fallback_layers
                weights_filename = f"dehazenet_{model_layers}layers_best.pth"
                weights_path = settings.MODEL_DIR / weights_filename
            
            model = model_service.load_model(
                layers=model_layers,
                weights_path=weights_path,
                device=device,
                use_fp16=use_fp16
            )

            try:
                actual_device = next(model.parameters()).device.type
                if actual_device != device:
                    print(f"⚠️  Device changed from '{device}' to '{actual_device}'.")
                    device = actual_device
                    use_fp16 = False if device != "cuda" else use_fp16
            except Exception:
                pass
            
            cap = cv2.VideoCapture(str(input_path))
            if not cap.isOpened():
                raise ValueError(f"Cannot open video: {input_path}")
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30.0
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            self.update_job_status(job_id, {
                "total_frames": total_frames,
                "statistics": {
                    "input_fps": fps,
                    "input_resolution": f"{frame_width}x{frame_height}",
                    "processing_resolution": f"{resolution}x{resolution}",
                    "model_layers": model_layers,
                    "device": device,
                    "use_fp16": use_fp16
                }
            })
            
            output_width = resolution * 2
            output_height = resolution
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(
                str(output_path),
                fourcc,
                fps,
                (output_width, output_height)
            )
            
            frame_count = 0
            total_infer_time = 0.0
            start_time = time.time()
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_resized = cv2.resize(frame, (resolution, resolution))
                
                infer_start = time.time()
                dehazed_frame = model_service.infer_frame(
                    model=model,
                    frame=frame,
                    target_size=(resolution, resolution),
                    device=device,
                    use_fp16=use_fp16
                )
                infer_time = time.time() - infer_start
                total_infer_time += infer_time
                
                combined = np.hstack((frame_resized, dehazed_frame))
                out.write(combined)
                
                frame_count += 1
                
                elapsed = time.time() - start_time
                progress = (frame_count / total_frames) * 100 if total_frames > 0 else 0
                current_fps = frame_count / elapsed if elapsed > 0 else 0
                remaining_frames = total_frames - frame_count
                eta = (remaining_frames / current_fps) if current_fps > 0 else 0
                
                status_update = {
                    "progress": progress,
                    "current_frame": frame_count,
                    "fps": current_fps,
                    "elapsed_time": elapsed,
                    "estimated_remaining": eta
                }
                self.update_job_status(job_id, status_update)
                
                if progress_callback:
                    if frame_count % 5 == 0:
                        _, orig_buffer = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, 70])
                        _, dehazed_buffer = cv2.imencode('.jpg', dehazed_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                        
                        status_update["preview"] = {
                            "original": base64.b64encode(orig_buffer).decode('utf-8'),
                            "dehazed": base64.b64encode(dehazed_buffer).decode('utf-8')
                        }
                    
                    await progress_callback(job_id, status_update)
            
            cap.release()
            out.release()
            
            total_time = time.time() - start_time
            avg_fps = frame_count / total_time if total_time > 0 else 0
            avg_infer_time = (total_infer_time / frame_count * 1000) if frame_count > 0 else 0
            
            final_stats = {
                "input_video": str(input_path.name),
                "output_video": str(output_path.name),
                "model_layers": model_layers,
                "device": device,
                "use_fp16": use_fp16,
                "input_resolution": f"{frame_width}x{frame_height}",
                "processing_resolution": f"{resolution}x{resolution}",
                "total_frames": frame_count,
                "total_time_seconds": round(total_time, 2),
                "average_fps": round(avg_fps, 2),
                "average_inference_ms": round(avg_infer_time, 2),
                "output_size_bytes": output_path.stat().st_size if output_path.exists() else 0
            }
            
            stats_path = output_path.with_suffix('.json')
            with open(stats_path, 'w') as f:
                json.dump(final_stats, f, indent=2)
            
            self.update_job_status(job_id, {
                "status": ProcessingStatus.COMPLETED,
                "progress": 100.0,
                "output_video_path": str(output_path),
                "statistics": final_stats
            })
            
            if progress_callback:
                await progress_callback(job_id, {"status": "completed", "progress": 100.0})
            
            print(f"✅ Job {job_id} completed successfully")
            
        except Exception as e:
            error_msg = f"Processing failed: {str(e)}"
            print(f"❌ Job {job_id} failed: {error_msg}")
            
            self.update_job_status(job_id, {
                "status": ProcessingStatus.FAILED,
                "error_message": error_msg
            })
            
            if progress_callback:
                await progress_callback(job_id, {"status": "failed", "error": error_msg})
            
            raise


video_processor = VideoProcessor()

# ============================================================================
# API ROUTES
# ============================================================================

router = APIRouter(prefix="/api", tags=["video-dehazing"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, job_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[job_id] = websocket
    
    def disconnect(self, job_id: str):
        if job_id in self.active_connections:
            del self.active_connections[job_id]
    
    async def send_update(self, job_id: str, data: dict):
        if job_id in self.active_connections:
            try:
                await self.active_connections[job_id].send_json(data)
            except:
                self.disconnect(job_id)


manager = ConnectionManager()


@router.post("/upload", response_model=UploadResponse)
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file for processing"""
    
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    max_size_bytes = settings.MAX_UPLOAD_SIZE * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE}MB"
        )
    
    job_id = str(uuid.uuid4())
    upload_path = settings.UPLOAD_DIR / f"{job_id}.{file_ext}"
    
    try:
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    finally:
        file.file.close()
    
    return UploadResponse(
        job_id=job_id,
        filename=file.filename,
        file_size=file_size,
        upload_time=datetime.now()
    )


@router.post("/process", response_model=ProcessResponse)
async def start_processing(
    request: ProcessRequest,
    background_tasks: BackgroundTasks
):
    """Start video dehazing processing"""
    
    upload_files = list(settings.UPLOAD_DIR.glob(f"{request.job_id}.*"))
    if not upload_files:
        raise HTTPException(status_code=404, detail="Job not found. Please upload video first.")
    
    input_path = upload_files[0]
    output_path = settings.OUTPUT_DIR / f"{request.job_id}_dehazed.mp4"
    
    device = request.device if request.device else settings.DEVICE
    
    async def progress_callback(job_id: str, update: dict):
        await manager.send_update(job_id, update)
    
    background_tasks.add_task(
        video_processor.process_video,
        job_id=request.job_id,
        input_path=input_path,
        output_path=output_path,
        model_layers=int(request.model_layers),
        resolution=request.resolution,
        device=device,
        use_fp16=request.use_fp16 and device == "cuda",
        progress_callback=progress_callback
    )
    
    return ProcessResponse(
        job_id=request.job_id,
        status=ProcessingStatus.PROCESSING,
        message="Processing started successfully",
        estimated_time=None
    )


@router.get("/status/{job_id}", response_model=JobStatus)
async def get_status(job_id: str):
    """Get current processing status"""
    
    status = video_processor.get_job_status(job_id)
    
    if not status:
        upload_files = list(settings.UPLOAD_DIR.glob(f"{job_id}.*"))
        if upload_files:
            return JobStatus(
                job_id=job_id,
                status=ProcessingStatus.PENDING,
                progress=0.0,
                current_frame=None,
                total_frames=None,
                fps=None,
                elapsed_time=None,
                estimated_remaining=None,
                error_message=None
            )
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatus(
        job_id=job_id,
        status=status["status"],
        progress=status.get("progress", 0.0),
        current_frame=status.get("current_frame"),
        total_frames=status.get("total_frames"),
        fps=status.get("fps"),
        elapsed_time=status.get("elapsed_time"),
        estimated_remaining=status.get("estimated_remaining"),
        error_message=status.get("error_message"),
        output_video_path=status.get("output_video_path"),
        statistics=status.get("statistics")
    )


@router.get("/download/{job_id}")
async def download_video(job_id: str):
    """Download processed video"""
    
    output_path = settings.OUTPUT_DIR / f"{job_id}_dehazed.mp4"
    
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Processed video not found. Check job status.")
    
    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"dehazed_{job_id}.mp4"
    )


@router.get("/download/{job_id}/info", response_model=DownloadInfo)
async def get_download_info(job_id: str):
    """Get information about downloadable video"""
    
    output_path = settings.OUTPUT_DIR / f"{job_id}_dehazed.mp4"
    stats_path = settings.OUTPUT_DIR / f"{job_id}_dehazed.json"
    
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Processed video not found")
    
    statistics = None
    if stats_path.exists():
        with open(stats_path, 'r') as f:
            statistics = json.load(f)
    
    return DownloadInfo(
        job_id=job_id,
        filename=f"dehazed_{job_id}.mp4",
        file_size=output_path.stat().st_size,
        download_url=f"/api/download/{job_id}",
        created_at=datetime.fromtimestamp(output_path.stat().st_mtime),
        statistics=statistics
    )


@router.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time progress updates"""
    
    await manager.connect(job_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"type": "heartbeat", "timestamp": datetime.now().isoformat()})
    except WebSocketDisconnect:
        manager.disconnect(job_id)


@router.delete("/job/{job_id}")
async def delete_job(job_id: str):
    """Delete job and associated files"""
    
    deleted = []
    
    for upload_file in settings.UPLOAD_DIR.glob(f"{job_id}.*"):
        upload_file.unlink()
        deleted.append(str(upload_file))
    
    for output_file in settings.OUTPUT_DIR.glob(f"{job_id}*"):
        output_file.unlink()
        deleted.append(str(output_file))
    
    if job_id in video_processor.jobs:
        del video_processor.jobs[job_id]
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"message": f"Deleted {len(deleted)} files", "files": deleted}


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cuda_available": torch.cuda.is_available(),
        "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "upload_dir": str(settings.UPLOAD_DIR),
        "output_dir": str(settings.OUTPUT_DIR),
        "model_dir": str(settings.MODEL_DIR)
    }


# ============================================================================
# FASTAPI APPLICATION SETUP
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("=" * 60)
    print("🚀 Video Dehazing Backend Starting...")
    print("=" * 60)
    print(f"📁 Upload Directory: {settings.UPLOAD_DIR}")
    print(f"📁 Output Directory: {settings.OUTPUT_DIR}")
    print(f"📁 Model Directory: {settings.MODEL_DIR}")
    print(f"🔧 Device: {settings.DEVICE}")
    print(f"🎯 Default Model: {settings.DEFAULT_MODEL_LAYERS} layers")
    print(f"🌐 Access at: http://localhost:{settings.PORT}")
    print(f"📚 API Docs: http://localhost:{settings.PORT}/docs")
    print("=" * 60)
    
    yield
    
    # Shutdown
    print("\n🛑 Shutting down...")


app = FastAPI(
    title="Video Dehazing API",
    description="Real-time video dehazing using deep learning",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)

# Serve static files (for downloads)
app.mount("/outputs", StaticFiles(directory=str(settings.OUTPUT_DIR)), name="outputs")

# Serve frontend if available
frontend_dist = PROJECT_ROOT / "web-app" / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dist / "assets")), name="static")


@app.get("/")
async def root():
    """Serve frontend index.html or API info"""
    index_file = frontend_dist / "index.html" if frontend_dist.exists() else None
    if index_file and index_file.exists():
        return FileResponse(index_file)
    
    return {
        "message": "Video Dehazing API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
        "upload": "/api/upload",
        "process": "/api/process",
        "status": "/api/status/{job_id}",
        "download": "/api/download/{job_id}"
    }


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Catch-all to serve frontend files"""
    
    if not frontend_dist.exists():
        return {"error": "Frontend not available"}, 404
    
    file_path = frontend_dist / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    
    index_file = frontend_dist / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    
    return {"error": "File not found"}, 404


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Starting Video Dehazing Application...")
    print("=" * 60 + "\n")
    
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
    )
