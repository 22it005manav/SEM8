"""
Training script for DeepDehazeNet
Trains or fine-tunes the model on paired hazy/clear images
"""

import os
import sys
import glob
import random
import argparse
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
from skimage.metrics import peak_signal_noise_ratio as compare_psnr
from skimage.metrics import structural_similarity as compare_ssim

# Add parent directory to path to import models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.models.dehazenet import DeepDehazeNet


class DehazingDataset(Dataset):
    """Dataset for paired hazy/clear images"""
    
    def __init__(self, pairs, img_size=256):
        self.pairs = pairs
        self.transform = transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor()
        ])
    
    def __len__(self):
        return len(self.pairs)
    
    def __getitem__(self, idx):
        hazy_path, clean_path = self.pairs[idx]
        hazy = Image.open(hazy_path).convert("RGB")
        clean = Image.open(clean_path).convert("RGB")
        return self.transform(hazy), self.transform(clean), hazy_path, clean_path


def load_dataset_pairs(hazy_dir, clear_dir):
    """Load and pair hazy/clear images by filename"""
    hazy_paths = sorted(glob.glob(os.path.join(hazy_dir, "*.*")))
    clear_paths = sorted(glob.glob(os.path.join(clear_dir, "*.*")))
    
    # Filter to only image files
    hazy_paths = [p for p in hazy_paths if p.lower().endswith(('.png', '.jpg', '.jpeg'))]
    clear_paths = [p for p in clear_paths if p.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    print(f"Found {len(hazy_paths)} hazy images")
    print(f"Found {len(clear_paths)} clear images")
    
    if len(hazy_paths) != len(clear_paths):
        print(f"⚠️  Warning: Mismatched counts. Using minimum: {min(len(hazy_paths), len(clear_paths))}")
        min_len = min(len(hazy_paths), len(clear_paths))
        hazy_paths = hazy_paths[:min_len]
        clear_paths = clear_paths[:min_len]
    
    # Pair by filename (assuming same names)
    pairs = list(zip(hazy_paths, clear_paths))
    random.shuffle(pairs)
    
    return pairs


def train_model(args):
    """Main training function"""
    
    # Setup device
    device = torch.device(args.device if torch.cuda.is_available() and args.device == "cuda" else "cpu")
    print(f"\n{'='*60}")
    print(f"Training DeepDehazeNet ({args.layers} layers)")
    print(f"Device: {device}")
    print(f"{'='*60}\n")
    
    # Load dataset
    print("Loading dataset...")
    if args.train_root == args.val_root:
        # Use same folder for both, split internally
        all_pairs = load_dataset_pairs(
            os.path.join(args.train_root, "hazy"),
            os.path.join(args.train_root, "clear")
        )
        split = int(0.8 * len(all_pairs))
        train_pairs = all_pairs[:split]
        val_pairs = all_pairs[split:]
        print(f"Split: {len(train_pairs)} train, {len(val_pairs)} validation")
    else:
        train_pairs = load_dataset_pairs(
            os.path.join(args.train_root, "hazy"),
            os.path.join(args.train_root, "clear")
        )
        val_pairs = load_dataset_pairs(
            os.path.join(args.val_root, "hazy"),
            os.path.join(args.val_root, "clear")
        )
    
    if len(train_pairs) == 0:
        print("❌ ERROR: No training pairs found!")
        print(f"   Check: {args.train_root}/hazy and {args.train_root}/clear")
        return
    
    # Create datasets
    train_dataset = DehazingDataset(train_pairs, img_size=args.img_size[0])
    val_dataset = DehazingDataset(val_pairs, img_size=args.img_size[0])
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=1, shuffle=False, num_workers=0)
    
    # Create model
    model = DeepDehazeNet(layers=args.layers).to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    
    # Load pretrained weights if resuming
    start_epoch = 0
    if args.resume_from:
        if os.path.exists(args.resume_from):
            model.load_state_dict(torch.load(args.resume_from, map_location=device))
            print(f"✅ Loaded weights from: {args.resume_from}")
        else:
            print(f"⚠️  Warning: Resume path not found: {args.resume_from}")
    
    # Create output directory
    os.makedirs(args.save_dir, exist_ok=True)
    os.makedirs(os.path.join(args.save_dir, "plots"), exist_ok=True)
    
    # Training setup
    train_losses, val_losses = [], []
    psnrs, ssims = [], []
    best_psnr = 0
    best_epoch = 0
    early_stop_counter = 0
    
    print(f"\nStarting training for {args.epochs} epochs...")
    print(f"Batch size: {args.batch_size}, Learning rate: {args.lr}")
    print(f"Image size: {args.img_size[0]}x{args.img_size[1]}\n")
    
    # Training loop
    for epoch in range(start_epoch, args.epochs):
        # Train
        model.train()
        total_train_loss = 0
        for batch_idx, (hazy, clean, _, _) in enumerate(train_loader):
            hazy, clean = hazy.to(device), clean.to(device)
            
            optimizer.zero_grad()
            output = model(hazy)
            loss = criterion(output, clean)
            loss.backward()
            optimizer.step()
            
            total_train_loss += loss.item()
            
            if (batch_idx + 1) % 10 == 0:
                print(f"  Batch {batch_idx+1}/{len(train_loader)}, Loss: {loss.item():.4f}")
        
        train_loss = total_train_loss / len(train_loader)
        train_losses.append(train_loss)
        
        # Validate
        model.eval()
        total_val_loss = 0
        total_psnr = 0
        total_ssim = 0
        
        with torch.no_grad():
            for hazy, clean, _, _ in val_loader:
                hazy, clean = hazy.to(device), clean.to(device)
                output = model(hazy)
                
                total_val_loss += criterion(output, clean).item()
                
                # Calculate PSNR
                psnr = compare_psnr(
                    clean.cpu().numpy(),
                    output.cpu().numpy(),
                    data_range=1.0
                )
                total_psnr += psnr
                
                # Calculate SSIM
                clean_np = clean.cpu().squeeze().permute(1, 2, 0).numpy()
                output_np = output.cpu().squeeze().permute(1, 2, 0).numpy()
                ssim = compare_ssim(
                    clean_np,
                    output_np,
                    channel_axis=-1,
                    data_range=1.0
                )
                total_ssim += ssim
        
        val_loss = total_val_loss / len(val_loader)
        psnr_avg = total_psnr / len(val_loader)
        ssim_avg = total_ssim / len(val_loader)
        
        val_losses.append(val_loss)
        psnrs.append(psnr_avg)
        ssims.append(ssim_avg)
        
        # Save best model
        if psnr_avg > best_psnr:
            best_psnr = psnr_avg
            best_epoch = epoch
            best_model_path = os.path.join(args.save_dir, f"dehazenet_{args.layers}_best.pth")
            torch.save(model.state_dict(), best_model_path)
            early_stop_counter = 0
        else:
            early_stop_counter += 1
        
        # Print progress
        print(f"Epoch {epoch+1}/{args.epochs}: "
              f"Train Loss={train_loss:.4f}, Val Loss={val_loss:.4f}, "
              f"PSNR={psnr_avg:.2f} dB, SSIM={ssim_avg:.4f}")
        
        # Early stopping
        if early_stop_counter >= args.patience:
            print(f"\nEarly stopping at epoch {epoch+1} (best: epoch {best_epoch+1})")
            break
    
    # Save final model
    final_model_path = os.path.join(args.save_dir, f"dehazenet_{args.layers}_final.pth")
    torch.save(model.state_dict(), final_model_path)
    print(f"\n✅ Training complete!")
    print(f"   Best model: {best_model_path} (PSNR: {best_psnr:.2f} dB)")
    print(f"   Final model: {final_model_path}")
    
    # Plot results
    plot_path = os.path.join(args.save_dir, "plots", f"training_results_{args.layers}.png")
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    
    axes[0].plot(train_losses, label='Train Loss', alpha=0.7)
    axes[0].plot(val_losses, label='Val Loss', alpha=0.7)
    axes[0].axvline(best_epoch, color='red', linestyle='--', label=f'Best @ {best_epoch+1}')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].set_title('Loss vs Epoch')
    axes[0].legend()
    axes[0].grid(True)
    
    axes[1].plot(psnrs, label='PSNR', color='green')
    axes[1].axvline(best_epoch, color='red', linestyle='--', label=f'Best @ {best_epoch+1}')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('PSNR (dB)')
    axes[1].set_title('PSNR vs Epoch')
    axes[1].legend()
    axes[1].grid(True)
    
    axes[2].plot(ssims, label='SSIM', color='purple')
    axes[2].axvline(best_epoch, color='red', linestyle='--', label=f'Best @ {best_epoch+1}')
    axes[2].set_xlabel('Epoch')
    axes[2].set_ylabel('SSIM')
    axes[2].set_title('SSIM vs Epoch')
    axes[2].legend()
    axes[2].grid(True)
    
    plt.tight_layout()
    plt.savefig(plot_path)
    print(f"   Plots saved: {plot_path}")


def main():
    parser = argparse.ArgumentParser(description='Train DeepDehazeNet for video dehazing')
    
    # Dataset arguments
    parser.add_argument('--train_root', type=str, default='Dataset',
                       help='Root directory for training data (should contain hazy/ and clear/ subfolders)')
    parser.add_argument('--val_root', type=str, default='Dataset',
                       help='Root directory for validation data (if same as train_root, will split 80/20)')
    
    # Model arguments
    parser.add_argument('--layers', type=int, default=8,
                       help='Number of layers (even numbers >= 4, e.g., 4, 8, 16, 24, 32)')
    parser.add_argument('--resume_from', type=str, default=None,
                       help='Path to pretrained weights to fine-tune from')
    
    # Training arguments
    parser.add_argument('--epochs', type=int, default=50,
                       help='Number of training epochs')
    parser.add_argument('--batch_size', type=int, default=4,
                       help='Batch size for training')
    parser.add_argument('--lr', type=float, default=1e-4,
                       help='Learning rate')
    parser.add_argument('--patience', type=int, default=20,
                       help='Early stopping patience')
    parser.add_argument('--img_size', type=int, nargs=2, default=[256, 256],
                       help='Image size (width height)')
    
    # Other arguments
    parser.add_argument('--device', type=str, default='cuda', choices=['cuda', 'cpu'],
                       help='Device to use (cuda or cpu)')
    parser.add_argument('--save_dir', type=str, default='weights',
                       help='Directory to save model weights and plots')
    
    args = parser.parse_args()
    
    train_model(args)


if __name__ == "__main__":
    main()

