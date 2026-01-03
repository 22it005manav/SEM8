"""
Configuration Management for Video Dehazing Backend
"""
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


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
    # Resolve model directory relative to project root
    MODEL_DIR: Path = Field(default=Path(__file__).resolve().parents[4] / "models" / "pretrained", description="Model directory")
    
    # Model Configuration
    DEFAULT_MODEL_LAYERS: int = Field(default=8, description="Default model layers (4, 8, or 16)")
    DEFAULT_MODEL_WEIGHTS: str = Field(default="dehazenet_8layers_best.pth", description="Default model file")
    DEVICE: str = Field(default="cpu", description="Device: cuda or cpu")
    ENABLE_FP16: bool = Field(default=False, description="Enable half-precision inference")
    
    # Processing
    MAX_UPLOAD_SIZE: int = Field(default=500, description="Max upload size in MB")
    ALLOWED_EXTENSIONS: List[str] = Field(default=["mp4", "avi", "mov", "mkv"], description="Allowed video formats")
    DEFAULT_RESOLUTION: int = Field(default=256, description="Default processing resolution")
    BATCH_SIZE: int = Field(default=8, description="Batch size for frame processing")
    
    @field_validator('ALLOWED_EXTENSIONS', mode='before')
    @classmethod
    def parse_allowed_extensions(cls, v):
        """Parse comma-separated string from .env file"""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(',')]
        return v
    # Cleanup
    AUTO_CLEANUP_HOURS: int = Field(default=24, description="Auto-cleanup old files after N hours")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse comma-separated string from .env file"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
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
            import torch  # Lazy import to avoid hard dependency at parse time
            if self.DEVICE == "cuda" and not torch.cuda.is_available():
                print("⚠️  CUDA not available. Falling back to CPU.")
                self.DEVICE = "cpu"
                self.ENABLE_FP16 = False
        except Exception:
            # If torch not installed yet, default to CPU to avoid runtime errors
            if self.DEVICE == "cuda":
                print("⚠️  Torch not installed; defaulting device to CPU.")
                self.DEVICE = "cpu"
                self.ENABLE_FP16 = False


# Global settings instance
settings = Settings()
