"""
Pydantic models for API requests and responses
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ProcessingStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadResponse(BaseModel):
    """Response after successful upload"""
    job_id: str = Field(..., description="Unique job identifier")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    upload_time: datetime = Field(..., description="Upload timestamp")
    message: str = Field(default="Video uploaded successfully")


class ProcessRequest(BaseModel):
    """Request to start video processing"""
    model_config = {"protected_namespaces": ()}  # Allow model_ prefix
    
    job_id: str = Field(..., description="Job ID from upload")
    model_layers: int = Field(default=8, description="Model architecture (even numbers >= 4, e.g., 4, 8, 16, 24, 32)")
    resolution: int = Field(default=512, description="Processing resolution (e.g., 512 for 512x512)")
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
