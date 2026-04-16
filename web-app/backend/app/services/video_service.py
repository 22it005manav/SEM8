"""
Video Processing Service - Handles video dehazing with progress tracking
"""
import cv2
import time
import json
import base64
from pathlib import Path
from typing import Dict, Any, Callable, Optional
from datetime import datetime
import numpy as np

from app.services.model_service import model_service
from app.models.schemas import ProcessingStatus
from app.core.config import settings


class VideoProcessor:
    """
    Handles video processing with real-time progress updates.
    Processes videos frame-by-frame using the dehazing model.
    """
    
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
        """
        Process a video file with dehazing
        
        Args:
            job_id: Unique job identifier
            input_path: Path to input video
            output_path: Path to save output video
            model_layers: Model depth (4, 8, or 16)
            resolution: Processing resolution
            device: Device for inference
            use_fp16: Use half-precision
            progress_callback: Optional callback for progress updates
        """
        
        # Initialize job status
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
            # Load model
            weights_filename = f"dehazenet_{model_layers}layers_best.pth"
            weights_path = settings.MODEL_DIR / weights_filename
            
            model = model_service.load_model(
                layers=model_layers,
                weights_path=weights_path,
                device=device,
                use_fp16=use_fp16
            )

            # Reconcile actual device after loading (may fallback to CPU)
            try:
                actual_device = next(model.parameters()).device.type
                if actual_device != device:
                    print(f"⚠️  Device changed from '{device}' to '{actual_device}'. Updating pipeline.")
                    device = actual_device
                    use_fp16 = False if device != "cuda" else use_fp16
            except Exception:
                pass
            
            # Open input video
            cap = cv2.VideoCapture(str(input_path))
            if not cap.isOpened():
                raise ValueError(f"Cannot open video: {input_path}")
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30.0
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Update job with video info
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
            
            # Setup output video writer
            # Output is side-by-side: original | dehazed
            output_width = resolution * 2
            output_height = resolution
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(
                str(output_path),
                fourcc,
                fps,
                (output_width, output_height)
            )
            
            # Processing loop
            frame_count = 0
            total_infer_time = 0.0
            start_time = time.time()
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Resize original for side-by-side
                frame_resized = cv2.resize(frame, (resolution, resolution))
                
                # Inference
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
                
                # Combine original and dehazed side-by-side
                combined = np.hstack((frame_resized, dehazed_frame))
                out.write(combined)
                
                frame_count += 1
                
                # Calculate statistics
                elapsed = time.time() - start_time
                if total_frames > 0:
                    progress = (frame_count / total_frames) * 100
                else:
                    progress = 0.0
                current_fps = frame_count / elapsed if elapsed > 0 else 0
                remaining_frames = total_frames - frame_count
                eta = (remaining_frames / current_fps) if current_fps > 0 else 0
                
                # Update status
                status_update = {
                    "progress": progress,
                    "current_frame": frame_count,
                    "fps": current_fps,
                    "elapsed_time": elapsed,
                    "estimated_remaining": eta
                }
                self.update_job_status(job_id, status_update)
                
                # Send progress update via callback (WebSocket)
                if progress_callback:
                    # Every 5th frame, send preview images
                    if frame_count % 5 == 0:
                        # Encode frames as JPEG for preview
                        _, orig_buffer = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, 70])
                        _, dehazed_buffer = cv2.imencode('.jpg', dehazed_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                        
                        status_update["preview"] = {
                            "original": base64.b64encode(orig_buffer).decode('utf-8'),
                            "dehazed": base64.b64encode(dehazed_buffer).decode('utf-8')
                        }
                    
                    await progress_callback(job_id, status_update)
            
            # Cleanup
            cap.release()
            out.release()
            
            # Calculate final statistics
            total_time = time.time() - start_time
            avg_fps = frame_count / total_time if total_time > 0 else 0
            avg_infer_time = (total_infer_time / frame_count * 1000) if frame_count > 0 else 0
            
            # Final statistics
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
            
            # Save statistics to file
            stats_path = output_path.with_suffix('.json')
            with open(stats_path, 'w') as f:
                json.dump(final_stats, f, indent=2)
            
            # Mark as completed
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


# Global video processor instance
video_processor = VideoProcessor()
