"""
Video Dehazing Inference Script
Processes foggy videos frame-by-frame to produce clear output videos
"""

import os
import sys
import cv2
import torch
import numpy as np
import time
import argparse
from torchvision import transforms

# Add parent directory to path to import models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.models.dehazenet import DeepDehazeNet


def center_crop(enc_feat, target_size):
    """Helper function to center crop encoder features for skip connections"""
    _, _, h, w = enc_feat.size()
    target_h, target_w = target_size
    start_h = (h - target_h) // 2
    start_w = (w - target_w) // 2
    return enc_feat[:, :, start_h:start_h+target_h, start_w:start_w+target_w]


def dehaze_video(args):
    """Main video dehazing function"""
    
    # Setup device
    device = torch.device(args.device if torch.cuda.is_available() and args.device == "cuda" else "cpu")
    print(f"\n{'='*60}")
    print("VIDEO DEHAZING")
    print(f"{'='*60}")
    print(f"Input video: {args.input_video}")
    print(f"Output video: {args.output_video}")
    print(f"Model: {args.layers} layers")
    print(f"Device: {device}")
    print(f"Half precision: {args.half}")
    print(f"{'='*60}\n")
    
    # Check input video exists
    if not os.path.exists(args.input_video):
        print(f"❌ ERROR: Input video not found: {args.input_video}")
        return
    
    # Load model
    print("Loading model...")
    model = DeepDehazeNet(layers=args.layers).to(device)
    
    if args.half and device.type == "cuda":
        model = model.half()
        print("  Using half precision (FP16)")
    
    # Load weights
    if not os.path.exists(args.weights):
        print(f"❌ ERROR: Model weights not found: {args.weights}")
        print("   Train a model first or check the path")
        return
    
    model.load_state_dict(torch.load(args.weights, map_location=device))
    model.eval()
    print(f"✅ Loaded weights from: {args.weights}")
    
    # Warm-up (run one dummy inference)
    print("Warming up model...")
    dummy_input = torch.randn(1, 3, args.resize[0], args.resize[1])
    if args.half and device.type == "cuda":
        dummy_input = dummy_input.half()
    dummy_input = dummy_input.to(device)
    with torch.no_grad():
        _ = model(dummy_input)
    print("✅ Model ready")
    
    # Setup video I/O
    cap = cv2.VideoCapture(args.input_video)
    if not cap.isOpened():
        print(f"❌ ERROR: Cannot open video: {args.input_video}")
        return
    
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if video_fps <= 0:
        video_fps = 30.0  # Default if FPS not available
        print(f"⚠️  Warning: Could not read FPS, using default: {video_fps}")
    
    resize_dim = tuple(args.resize)
    frame_width = resize_dim[0] * 2  # Side-by-side: original | dehazed
    frame_height = resize_dim[1]
    
    # Create output directory
    output_dir = os.path.dirname(args.output_video)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Setup video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(args.output_video, fourcc, video_fps, (frame_width, frame_height))
    
    # Transform for preprocessing
    transform = transforms.Compose([transforms.ToTensor()])
    
    # Processing stats
    frame_count = 0
    total_infer_time = 0
    start_time = time.time()
    
    print(f"\nProcessing video...")
    print(f"Resolution: {resize_dim[0]}x{resize_dim[1]}")
    print(f"FPS: {video_fps:.2f}\n")
    
    # Process frames
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Resize frame
            frame_resized = cv2.resize(frame, resize_dim)
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            
            # Preprocess
            input_tensor = transform(frame_rgb).unsqueeze(0)
            if args.half and device.type == "cuda":
                input_tensor = input_tensor.half()
            input_tensor = input_tensor.to(device)
            
            # Inference
            infer_start = time.time()
            with torch.no_grad():
                output = model(input_tensor)
            infer_end = time.time()
            
            infer_time = infer_end - infer_start
            total_infer_time += infer_time
            frame_count += 1
            
            # Postprocess
            if args.half and device.type == "cuda":
                output = output.float()
            
            output_image = output.squeeze().cpu().numpy().transpose(1, 2, 0)
            output_image = np.clip(output_image * 255, 0, 255).astype(np.uint8)
            output_bgr = cv2.cvtColor(output_image, cv2.COLOR_RGB2BGR)
            
            # Combine original and dehazed side-by-side
            combined = np.hstack((frame_resized, output_bgr))
            
            # Write frame
            out.write(combined)
            
            # Show preview if enabled
            if args.show_preview:
                fps_current = 1 / infer_time if infer_time > 0 else 0
                display_frame = combined.copy()
                cv2.putText(display_frame, f"FPS: {fps_current:.1f}",
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imshow("Original | Dehazed (Press 'q' to quit)", display_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("\n⚠️  Processing interrupted by user")
                    break
            
            # Progress update
            if frame_count % 30 == 0:
                avg_fps = frame_count / (time.time() - start_time)
                print(f"  Processed {frame_count} frames... (Avg FPS: {avg_fps:.2f})")
    
    except KeyboardInterrupt:
        print("\n⚠️  Processing interrupted by user")
    finally:
        cap.release()
        out.release()
        if args.show_preview:
            cv2.destroyAllWindows()
    
    # Final stats
    end_time = time.time()
    total_time = end_time - start_time
    avg_fps = frame_count / total_time if total_time > 0 else 0
    avg_infer_time = (total_infer_time / frame_count) * 1000 if frame_count > 0 else 0
    
    print(f"\n{'='*60}")
    print("PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"Total frames processed: {frame_count}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average FPS: {avg_fps:.2f}")
    print(f"Average inference time: {avg_infer_time:.2f} ms/frame")
    print(f"Output saved to: {args.output_video}")
    print(f"{'='*60}\n")
    
    # Save stats to file
    stats_file = args.output_video.replace('.mp4', '_stats.txt')
    with open(stats_file, 'w') as f:
        f.write(f"Video Dehazing Statistics\n")
        f.write(f"{'='*60}\n")
        f.write(f"Input video: {args.input_video}\n")
        f.write(f"Output video: {args.output_video}\n")
        f.write(f"Model: {args.layers} layers\n")
        f.write(f"Device: {device}\n")
        f.write(f"Half precision: {args.half}\n")
        f.write(f"Resolution: {resize_dim[0]}x{resize_dim[1]}\n")
        f.write(f"\n")
        f.write(f"Total frames: {frame_count}\n")
        f.write(f"Total time: {total_time:.2f} seconds\n")
        f.write(f"Average FPS: {avg_fps:.2f}\n")
        f.write(f"Average inference time: {avg_infer_time:.2f} ms/frame\n")
    print(f"Statistics saved to: {stats_file}")


def main():
    parser = argparse.ArgumentParser(description='Dehaze foggy videos using DeepDehazeNet')
    
    # Required arguments
    parser.add_argument('--input_video', type=str, required=True,
                       help='Path to input foggy video')
    parser.add_argument('--output_video', type=str, required=True,
                       help='Path to save dehazed output video')
    
    # Model arguments
    parser.add_argument('--weights', type=str, default='8_layers_model/best_model_8_8.pth',
                       help='Path to model weights file')
    parser.add_argument('--layers', type=int, default=8, choices=[4, 8, 16],
                       help='Number of layers in model (must match weights)')
    
    # Processing arguments
    parser.add_argument('--resize', type=int, nargs=2, default=[512, 512],
                       help='Processing resolution (width height). Lower = faster but lower quality')
    parser.add_argument('--device', type=str, default='cuda', choices=['cuda', 'cpu'],
                       help='Device to use (cuda or cpu)')
    parser.add_argument('--half', action='store_true',
                       help='Use half precision (FP16) for faster inference on GPU')
    parser.add_argument('--no_preview', action='store_true',
                       help='Disable preview window (useful for headless systems)')
    
    args = parser.parse_args()
    args.show_preview = not args.no_preview
    
    dehaze_video(args)


if __name__ == "__main__":
    main()

