import os
import cv2
import torch
import numpy as np
import time
from torchvision import transforms
from models.dehazenet import DeepDehazeNet

class VideoDehazer:
    def __init__(self, model_path, device="cuda", fp16=True):
        """
        Initialize video dehazer
        Args:
            model_path: Path to trained model weights
            device: 'cuda' or 'cpu'
            fp16: Use half precision for faster inference
        """
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.model = DeepDehazeNet(num_layers=8).to(self.device)
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        
        if fp16:
            self.model = self.model.half()
        
        self.model.eval()
        self.transform = transforms.ToTensor()
        self.fp16 = fp16
    
    def dehaze_video(self, input_path, output_path, output_size=(512, 512)):
        """
        Dehaze video file
        Args:
            input_path: Path to input foggy video
            output_path: Path to save dehazed video
            output_size: Output resolution (height, width)
        """
        
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise IOError(f"Cannot open video: {input_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_width, frame_height = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), \
                                     int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, 
                            (output_size[1] * 2, output_size[0]))  # side-by-side
        
        frame_count = 0
        total_time = 0
        
        print(f"Processing: {input_path}")
        print(f"Input: {frame_width}x{frame_height} @ {fps:.1f} FPS")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Resize
            frame_resized = cv2.resize(frame, (output_size[1], output_size[0]))
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            
            # Prepare input
            input_tensor = self.transform(frame_rgb).unsqueeze(0).to(self.device)
            if self.fp16:
                input_tensor = input_tensor.half()
            
            # Inference
            start_time = time.time()
            with torch.no_grad():
                output = self.model(input_tensor)
            infer_time = time.time() - start_time
            
            # Convert output
            output_image = output.squeeze().float().cpu().numpy().transpose(1, 2, 0)
            output_image = np.clip(output_image * 255, 0, 255).astype(np.uint8)
            output_bgr = cv2.cvtColor(output_image, cv2.COLOR_RGB2BGR)
            
            # Stack side-by-side
            combined = np.hstack((frame_resized, output_bgr))
            
            # Write
            out.write(combined)
            
            frame_count += 1
            total_time += infer_time
            
            # Progress
            if frame_count % 30 == 0:
                avg_fps = frame_count / total_time
                print(f"Processed {frame_count} frames | "
                      f"FPS: {avg_fps:.2f} | Infer time: {infer_time*1000:.2f}ms")
        
        cap.release()
        out.release()
        
        # Summary
        avg_fps = frame_count / total_time
        avg_infer_ms = (total_time / frame_count) * 1000
        
        print(f"\n✅ Video dehazing complete!")
        print(f"Total frames: {frame_count}")
        print(f"Average FPS: {avg_fps:.2f}")
        print(f"Average inference time: {avg_infer_ms:.2f} ms/frame")
        print(f"Output saved to: {output_path}")
        
        return {
            "frames": frame_count,
            "fps": avg_fps,
            "avg_infer_ms": avg_infer_ms
        }


if __name__ == "__main__":
    # Example usage
    dehazer = VideoDehazer(model_path="models/pretrained/best_model.pth")
    
    # Process video
    stats = dehazer.dehaze_video(
        input_path="input_video.mp4",
        output_path="results/dehazed_videos/output.mp4",
        output_size=(480, 640)  # (height, width)
    )