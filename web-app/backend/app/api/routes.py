"""
API Routes for Video Dehazing Backend
"""
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from app.models.schemas import (
    UploadResponse, ProcessRequest, ProcessResponse, JobStatus,
    DownloadInfo, ErrorResponse, ProcessingStatus
)
from app.core.config import settings
from app.services.video_service import video_processor
from app.services.model_service import model_service


router = APIRouter(prefix="/api", tags=["video-dehazing"])

# WebSocket connection manager
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
    """
    Upload a video file for processing
    
    - **file**: Video file (MP4, AVI, MOV, MKV)
    
    Returns a unique job_id for tracking
    """
    # Validate file extension
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset
    
    max_size_bytes = settings.MAX_UPLOAD_SIZE * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE}MB"
        )
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Save file
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
    """
    Start video dehazing processing
    
    - **job_id**: Job ID from upload
    - **model_layers**: Model architecture (4, 8, or 16 layers)
    - **resolution**: Processing resolution (default: 512)
    - **use_fp16**: Enable half-precision inference (GPU only)
    - **device**: Override device (cuda/cpu)
    """
    # Find uploaded file
    upload_files = list(settings.UPLOAD_DIR.glob(f"{request.job_id}.*"))
    if not upload_files:
        raise HTTPException(status_code=404, detail="Job not found. Please upload video first.")
    
    input_path = upload_files[0]
    output_path = settings.OUTPUT_DIR / f"{request.job_id}_dehazed.mp4"
    
    # Determine device
    device = request.device if request.device else settings.DEVICE
    
    # Progress callback for WebSocket updates
    async def progress_callback(job_id: str, update: dict):
        await manager.send_update(job_id, update)
    
    # Start processing in background
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
    """
    Get current processing status
    
    - **job_id**: Job identifier
    """
    status = video_processor.get_job_status(job_id)
    
    if not status:
        # Check if upload exists
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
    """
    Download processed video
    
    - **job_id**: Job identifier
    """
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
    """
    Get information about downloadable video
    
    - **job_id**: Job identifier
    """
    output_path = settings.OUTPUT_DIR / f"{job_id}_dehazed.mp4"
    stats_path = settings.OUTPUT_DIR / f"{job_id}_dehazed.json"
    
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Processed video not found")
    
    # Load statistics if available
    statistics = None
    if stats_path.exists():
        import json
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
    """
    WebSocket endpoint for real-time progress updates
    
    - **job_id**: Job identifier
    """
    await manager.connect(job_id, websocket)
    try:
        while True:
            # Keep connection alive and send updates
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await websocket.send_json({"type": "heartbeat", "timestamp": datetime.now().isoformat()})
    except WebSocketDisconnect:
        manager.disconnect(job_id)


@router.delete("/job/{job_id}")
async def delete_job(job_id: str):
    """
    Delete job and associated files
    
    - **job_id**: Job identifier
    """
    deleted = []
    
    # Delete uploaded file
    for upload_file in settings.UPLOAD_DIR.glob(f"{job_id}.*"):
        upload_file.unlink()
        deleted.append(str(upload_file))
    
    # Delete output files
    for output_file in settings.OUTPUT_DIR.glob(f"{job_id}*"):
        output_file.unlink()
        deleted.append(str(output_file))
    
    # Remove from job tracker
    if job_id in video_processor.jobs:
        del video_processor.jobs[job_id]
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"message": f"Deleted {len(deleted)} files", "files": deleted}


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    import torch
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cuda_available": torch.cuda.is_available(),
        "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "upload_dir": str(settings.UPLOAD_DIR),
        "output_dir": str(settings.OUTPUT_DIR),
        "model_dir": str(settings.MODEL_DIR)
    }
