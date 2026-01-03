import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage.metrics import structural_similarity as ssim
import matplotlib.pyplot as plt
from models.dehazenet import DeepDehazeNet
from sklearn.model_selection import train_test_split
import random

class DehazingDataset(Dataset):
    def __init__(self, hazy_paths=None, clear_paths=None, hazy_dir=None, clear_dir=None, img_size=256):
        """Initialize dataset with either file paths or directory paths
        
        Args:
            hazy_paths: List of hazy image file paths (optional)
            clear_paths: List of clear image file paths (optional)
            hazy_dir: Directory containing hazy images (optional)
            clear_dir: Directory containing clear images (optional)
            img_size: Size to resize images to
        """
        if hazy_paths is not None and clear_paths is not None:
            self.hazy_paths = hazy_paths
            self.clear_paths = clear_paths
        elif hazy_dir is not None and clear_dir is not None:
            self.hazy_paths = sorted([os.path.join(hazy_dir, f) 
                                      for f in os.listdir(hazy_dir)])
            self.clear_paths = sorted([os.path.join(clear_dir, f) 
                                       for f in os.listdir(clear_dir)])
        else:
            raise ValueError("Must provide either (hazy_paths, clear_paths) or (hazy_dir, clear_dir)")
        
        self.transform = transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor()
        ])
    
    def __len__(self):
        return len(self.hazy_paths)
    
    def __getitem__(self, idx):
        hazy = Image.open(self.hazy_paths[idx]).convert("RGB")
        clear = Image.open(self.clear_paths[idx]).convert("RGB")
        return self.transform(hazy), self.transform(clear)


def train_dehaze_model(
    pretrained_path=None,     # ← Load pretrained weights
    freeze_encoder=False,     # ← Freeze early layers
    epochs=50,                # ← Fewer epochs for fine-tuning
    lr=1e-5,                  # ← Lower learning rate
    batch_size=4,
    patience=20,
    device="cuda",
    model_name="dehazenet_best.pth",  # ← Model save name
    num_layers=8              # ← Number of layers in model
):
    """Train DeepDehazeNet for video dehazing"""
    
    # Setup
    device = torch.device(device if torch.cuda.is_available() else "cpu")
    print(f"🔧 Using device: {device}")
    
    model = DeepDehazeNet(num_layers=num_layers).to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    
    if pretrained_path:
        if os.path.exists(pretrained_path):
            model.load_state_dict(torch.load(pretrained_path, map_location=device))
            print("✅ Loaded pretrained weights")
        else:
            print(f"⚠️ Pretrained path {pretrained_path} not found, training from scratch")
        
        if freeze_encoder:
            # Freeze early layers
            for param in model.enc1.parameters():
                param.requires_grad = False
            for param in model.enc2.parameters():
                param.requires_grad = False
            print("🔒 Encoder layers frozen")
    
    # Data - Load and split properly
    data_dir = "data/Dataset/train"  # Fixed path
    all_pairs = list(zip(
        sorted([os.path.join(data_dir, "hazy", f) 
                for f in os.listdir(os.path.join(data_dir, "hazy"))]),
        sorted([os.path.join(data_dir, "clear", f) 
                for f in os.listdir(os.path.join(data_dir, "clear"))])
    ))
    random.shuffle(all_pairs)
    print(f"📊 Total dataset: {len(all_pairs)} image pairs")

    # 70% train, 15% val, 15% test
    train_pairs, temp_pairs = train_test_split(all_pairs, train_size=0.7, random_state=42)
    val_pairs, test_pairs = train_test_split(temp_pairs, train_size=0.5, random_state=42)
    
    print(f"📊 Split: Train={len(train_pairs)}, Val={len(val_pairs)}, Test={len(test_pairs)}")

    # Create datasets using the split pairs
    train_hazy, train_clear = zip(*train_pairs)
    val_hazy, val_clear = zip(*val_pairs)
    test_hazy, test_clear = zip(*test_pairs)
    
    train_dataset = DehazingDataset(hazy_paths=list(train_hazy), clear_paths=list(train_clear))
    val_dataset = DehazingDataset(hazy_paths=list(val_hazy), clear_paths=list(val_clear))
    test_dataset = DehazingDataset(hazy_paths=list(test_hazy), clear_paths=list(test_clear))
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=1, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=1, shuffle=False)
    
    # Create save directory
    os.makedirs("models/pretrained", exist_ok=True)
    
    # Training loop
    train_losses, val_losses = [], []
    psnr_scores, ssim_scores = [], []
    best_psnr, early_stop_count = 0, 0
    
    print(f"\n🚀 Starting training for {epochs} epochs...\n")
    
    for epoch in range(epochs):
        # Training
        model.train()
        train_loss = 0
        for hazy, clear in train_loader:
            hazy, clear = hazy.to(device), clear.to(device)
            optimizer.zero_grad()
            output = model(hazy)
            loss = criterion(output, clear)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        
        train_loss /= len(train_loader)
        train_losses.append(train_loss)
        
        # Validation
        model.eval()
        val_loss, avg_psnr, avg_ssim = 0, 0, 0
        with torch.no_grad():
            for hazy, clear in val_loader:
                hazy, clear = hazy.to(device), clear.to(device)
                output = model(hazy)
                val_loss += criterion(output, clear).item()
                
                # Metrics - process each image in batch
                for i in range(clear.size(0)):
                    clean_np = clear[i].cpu().numpy()
                    output_np = output[i].cpu().numpy()
                    avg_psnr += psnr(clean_np, output_np, data_range=1.0)
                    ssim_val = ssim(clean_np.transpose(1,2,0), 
                                   output_np.transpose(1,2,0), 
                                   channel_axis=-1, data_range=1.0)
                    avg_ssim += float(ssim_val)
        
        val_loss /= len(val_loader)
        avg_psnr /= len(val_dataset)
        avg_ssim /= len(val_dataset)
        
        val_losses.append(val_loss)
        psnr_scores.append(avg_psnr)
        ssim_scores.append(avg_ssim)
        
        # Save best model
        if avg_psnr > best_psnr:
            best_psnr = avg_psnr
            save_path = os.path.join("models", "pretrained", model_name)
            torch.save(model.state_dict(), save_path)
            early_stop_count = 0
            print(f"Epoch {epoch+1}/{epochs}: Train Loss={train_loss:.4f}, "
                  f"Val Loss={val_loss:.4f}, PSNR={avg_psnr:.2f}dB, SSIM={avg_ssim:.4f} ⭐ BEST")
        else:
            early_stop_count += 1
            print(f"Epoch {epoch+1}/{epochs}: Train Loss={train_loss:.4f}, "
                  f"Val Loss={val_loss:.4f}, PSNR={avg_psnr:.2f}dB, SSIM={avg_ssim:.4f}")
        
        if early_stop_count >= patience:
            print(f"\n⚠️ Early stopping at epoch {epoch+1} (no improvement for {patience} epochs)")
            break
    
    # Final evaluation on test set
    print(f"\n📈 Evaluating on test set...")
    model.eval()
    test_loss, test_psnr, test_ssim = 0, 0, 0
    with torch.no_grad():
        for hazy, clear in test_loader:
            hazy, clear = hazy.to(device), clear.to(device)
            output = model(hazy)
            test_loss += criterion(output, clear).item()
            
            for i in range(clear.size(0)):
                clean_np = clear[i].cpu().numpy()
                output_np = output[i].cpu().numpy()
                test_psnr += psnr(clean_np, output_np, data_range=1.0)
                ssim_val = ssim(clean_np.transpose(1,2,0), 
                               output_np.transpose(1,2,0), 
                               channel_axis=-1, data_range=1.0)
                test_ssim += float(ssim_val)
    
    test_loss /= len(test_loader)
    test_psnr /= len(test_dataset)
    test_ssim /= len(test_dataset)
    
    print(f"\n🎯 Test Results: Loss={test_loss:.4f}, PSNR={test_psnr:.2f}dB, SSIM={test_ssim:.4f}")
    
    # Save plots
    os.makedirs("results/metrics", exist_ok=True)
    
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 3, 1)
    plt.plot(train_losses, label='Train Loss')
    plt.plot(val_losses, label='Validation Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(1, 3, 2)
    plt.plot(psnr_scores, label='PSNR', color='green')
    plt.xlabel('Epoch')
    plt.ylabel('PSNR (dB)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(1, 3, 3)
    plt.plot(ssim_scores, label='SSIM', color='orange')
    plt.xlabel('Epoch')
    plt.ylabel('SSIM')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("results/metrics/training_curves.png", dpi=150)
    
    print(f"\n✅ Best model saved to: models/pretrained/{model_name}")
    print(f"✅ Training plots saved to: results/metrics/training_curves.png")
    print(f"✅ Best validation PSNR: {best_psnr:.2f}dB")
    
    return {
        'best_psnr': best_psnr,
        'test_psnr': test_psnr,
        'test_ssim': test_ssim,
        'test_loss': test_loss
    }


if __name__ == "__main__":
    # Simple usage
    train_dehaze_model()

    # With custom parameters
    train_dehaze_model(
        epochs=100,
        batch_size=8,
        lr=1e-4,
        model_name="my_model.pth",
        num_layers=8
    )

    # With pretrained weights
    train_dehaze_model(
        pretrained_path="models/pretrained/old_model.pth",
        freeze_encoder=True,
        epochs=20,
        lr=1e-5
    )