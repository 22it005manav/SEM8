"""
Model Inference Service - Wraps the existing DeepDehazeNet
"""
import sys
import os
from pathlib import Path
import torch
import numpy as np
from typing import Optional, Tuple

from app.core.config import settings

# Add project root to path to import existing model
# From web-app/backend/app/services/model_service.py, go up 4 levels to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.dehazenet import DeepDehazeNet


class ModelService:
    """
    Singleton service for model loading and inference.
    Handles lazy initialization and supports multiple model variants.
    """
    
    _instance = None
    _models = {}  # Cache loaded models by (layers, device, fp16)
    
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
    ) -> DeepDehazeNet:
        """
        Load or retrieve cached model
        
        Args:
            layers: Model depth (4, 8, or 16)
            weights_path: Path to pretrained weights
            device: Device to load model on (cuda or cpu)
            use_fp16: Use half-precision (FP16) for inference
        
        Returns:
            Loaded model ready for inference
        """
        # Check device availability
        if device == "cuda" and not torch.cuda.is_available():
            print("⚠️  CUDA requested but not available, falling back to CPU")
            device = "cpu"
            use_fp16 = False  # FP16 only works well on CUDA
        
        # Create cache key
        cache_key = (layers, device, use_fp16)
        
        # Return cached model if available
        if cache_key in self._models:
            print(f"✅ Using cached model: {layers} layers, device={device}, fp16={use_fp16}")
            return self._models[cache_key]
        
        print(f"🔄 Loading model: {layers} layers, device={device}, fp16={use_fp16}")
        
        # Initialize model
        model = DeepDehazeNet(num_layers=layers).to(device)

        # Resolve missing weights early to avoid silent random outputs
        if not weights_path or not weights_path.exists():
            available = sorted(p.name for p in settings.MODEL_DIR.glob("dehazenet_*layers_best.pth"))
            available_msg = ", ".join(available) if available else "none found"
            raise FileNotFoundError(
                f"Weights not found for {layers}-layer model at {weights_path}. "
                f"Available weights: {available_msg}."
            )

        # Load weights if provided
        try:
            state_dict = torch.load(weights_path, map_location=device)
            # Convert legacy checkpoints to new format
            state_dict = model._convert_legacy_checkpoint(state_dict)
            model.load_state_dict(state_dict)
            print(f"✅ Loaded weights from: {weights_path}")
        except RuntimeError as load_error:
            # Check if this is an architecture mismatch error
            error_msg = str(load_error)
            is_mismatch = "size mismatch" in error_msg or "Missing key" in error_msg
            
            if is_mismatch and layers > 8:
                print(f"⚠️  Architecture mismatch for {layers}-layer model weights")
                print(f"    Error: {error_msg[:100]}...")
                print(f"    Falling back to 8-layer model...")
                
                # Recursively try 8 layers
                if layers != 8:
                    return self.load_model(device=device, layers=8, use_fp16=use_fp16, weights_path=None)
                else:
                    raise RuntimeError(f"Failed to load 8-layer weights. {load_error}")
            
            # Try fallback checkpoint (final instead of best)
            fallback_path = settings.MODEL_DIR / f"dehazenet_{layers}_final.pth"
            if fallback_path.exists() and fallback_path != weights_path:
                print(f"⚠️  Failed to load {weights_path.name}, trying fallback: {fallback_path.name}")
                try:
                    state_dict = torch.load(fallback_path, map_location=device)
                    state_dict = model._convert_legacy_checkpoint(state_dict)
                    model.load_state_dict(state_dict)
                    print(f"✅ Loaded weights from fallback: {fallback_path}")
                except Exception as fallback_e:
                    # Last resort: try 8 layers
                    if layers > 8:
                        print(f"⚠️  Fallback also failed. Trying 8-layer model...")
                        return self.load_model(device=device, layers=8, use_fp16=use_fp16, weights_path=None)
                    raise RuntimeError(f"Failed to load both {weights_path.name} and {fallback_path.name}: {fallback_e}")
            else:
                raise RuntimeError(f"Failed to load weights from {weights_path}: {load_error}")
        
        # Convert to half precision if requested
        if use_fp16 and device == "cuda":
            model = model.half()
            print("✅ Converted model to FP16")
        
        # Set to evaluation mode
        model.eval()
        
        # Cache the model
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
        """
        Preprocess a single frame for inference
        
        Args:
            frame: Input frame (BGR format from OpenCV)
            target_size: Target size (width, height)
            device: Target device
            use_fp16: Use half precision
        
        Returns:
            Preprocessed tensor ready for model input
        """
        import cv2
        
        # Resize
        frame_resized = cv2.resize(frame, target_size)
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        
        # Normalize to [0, 1]
        frame_normalized = frame_rgb.astype(np.float32) / 255.0
        
        # Convert to tensor [1, 3, H, W]
        tensor = torch.from_numpy(frame_normalized).permute(2, 0, 1).unsqueeze(0)
        
        # Move to device and convert dtype if needed
        tensor = tensor.to(device)
        if use_fp16 and device == "cuda":
            tensor = tensor.half()
        
        return tensor
    
    def postprocess_output(
        self,
        output: torch.Tensor,
        use_fp16: bool = False
    ) -> np.ndarray:
        """
        Convert model output back to image format
        
        Args:
            output: Model output tensor [1, 3, H, W]
            use_fp16: Whether model used FP16
        
        Returns:
            Output image in BGR format (OpenCV compatible)
        """
        import cv2
        
        # Convert back to float32 if using FP16
        if use_fp16:
            output = output.float()
        
        # Convert to numpy [H, W, 3]
        output_image = output.squeeze().cpu().numpy().transpose(1, 2, 0)
        
        # Denormalize and clip to [0, 255]
        output_image = np.clip(output_image * 255, 0, 255).astype(np.uint8)
        
        # Convert RGB to BGR for OpenCV
        output_bgr = cv2.cvtColor(output_image, cv2.COLOR_RGB2BGR)
        
        return output_bgr
    
    @torch.no_grad()
    def infer_frame(
        self,
        model: DeepDehazeNet,
        frame: np.ndarray,
        target_size: Tuple[int, int] = (512, 512),
        device: str = "cuda",
        use_fp16: bool = False
    ) -> np.ndarray:
        """
        Complete inference pipeline for a single frame
        
        Args:
            model: Loaded model
            frame: Input frame (BGR)
            target_size: Processing size
            device: Device
            use_fp16: Half precision flag
        
        Returns:
            Dehazed frame (BGR)
        """
        # Preprocess
        input_tensor = self.preprocess_frame(frame, target_size, device, use_fp16)
        
        # Inference
        output_tensor = model(input_tensor)
        
        # Postprocess
        dehazed_frame = self.postprocess_output(output_tensor, use_fp16)
        
        return dehazed_frame
    
    def clear_cache(self):
        """Clear all cached models to free memory"""
        self._models.clear()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("✅ Model cache cleared")


# Global model service instance
model_service = ModelService()
