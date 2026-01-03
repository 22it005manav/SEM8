# Quick Start Guide - Real-Time Video Dehazing

## ✅ What You Need to Run This Project

### 1. **Python Environment**
- Python 3.10 or 3.11
- Install dependencies: `pip install -r requirements.txt`

### 2. **Dataset Structure** (For Training)
Your dataset should be organized like this:
```
Dataset/
  hazy/
    img1.jpg
    img2.jpg
    ...
  clear/
    img1.jpg
    img2.jpg
    ...
```

**Important:**
- `hazy/` and `clear/` folders must exist
- Images must be paired (same filenames in both folders)
- Supported formats: `.png`, `.jpg`, `.jpeg`

### 3. **Pre-trained Model Weights** (For Video Inference)
- If you have existing weights: `8_layers_model/best_model_8_8.pth`
- OR train your own model first (see Training section)

---

## 🚀 How to Run

### **Step 1: Check Requirements**
First, verify everything is set up correctly:
```bash
python check_requirements.py
```

This will tell you:
- ✅ If all Python packages are installed
- ✅ If your dataset structure is correct
- ✅ If model weights exist

### **Step 2A: Train the Model** (If you have dataset)

**Option 1: Using the batch script (Windows)**
```bash
run_training.bat
```

**Option 2: Using Python directly**
```bash
python -m src.training.train_dehazenet --device cpu
```

**For fine-tuning from existing weights:**
```bash
python -m src.training.train_dehazenet --device cpu --resume_from 8_layers_model\best_model_8_8.pth --epochs 30 --lr 1e-5
```

**Output:**
- Model weights saved to: `weights/dehazenet_8_best.pth`
- Training plots saved to: `weights/plots/`

### **Step 2B: Dehaze a Video** (Main Feature)

**Option 1: Using the batch script (Windows)**
```bash
run_video_dehaze.bat VIDEO_PROJECT\input_video.mp4 outputs\dehazed_output.mp4
```

**Option 2: Using Python directly**
```bash
python -m src.inference.video_inference ^
  --input_video VIDEO_PROJECT\input_video.mp4 ^
  --output_video outputs\dehazed_output.mp4 ^
  --weights 8_layers_model\best_model_8_8.pth ^
  --layers 8 ^
  --device cpu
```

**Options:**
- `--device cuda` - Use GPU (faster)
- `--device cpu` - Use CPU (slower but works everywhere)
- `--half` - Use half precision (FP16) for faster GPU inference
- `--no_preview` - Disable preview window (for headless systems)
- `--resize 512 512` - Change processing resolution

**Output:**
- Dehazed video: `outputs/dehazed_output.mp4`
- Statistics file: `outputs/dehazed_output_stats.txt`

---

## 📋 Common Issues & Solutions

### **Issue: "Dataset/hazy/ NOT FOUND"**
**Solution:** 
1. Create `Dataset/hazy/` and `Dataset/clear/` folders
2. Place your paired hazy and clear images in them
3. Ensure filenames match (e.g., `img1.jpg` in both folders)

### **Issue: "Model weights not found"**
**Solution:**
1. Train a model first: `python -m src.training.train_dehazenet --device cpu`
2. OR use existing weights if available in `8_layers_model/best_model_8_8.pth`
3. OR specify custom path: `--weights path/to/your/weights.pth`

### **Issue: "ModuleNotFoundError: No module named 'src'"**
**Solution:**
- Make sure you're running commands from the **project root** directory
- The project root should contain the `src/` folder

### **Issue: Training is very slow on CPU**
**Solution:**
- This is normal! CPU training is much slower than GPU
- Consider:
  - Using fewer epochs: `--epochs 20`
  - Smaller batch size: `--batch_size 2`
  - Using a smaller dataset for testing
  - Or use GPU if available: `--device cuda`

---

## 📊 Project Structure

```
Real-time-dehazing-deep-learning/
├── src/
│   ├── models/
│   │   └── dehazenet.py          # Model architecture
│   ├── training/
│   │   └── train_dehazenet.py    # Training script
│   └── inference/
│       └── video_inference.py    # Video dehazing script
├── Dataset/                      # Your training data
│   ├── hazy/
│   └── clear/
├── weights/                      # Saved model weights (created after training)
├── outputs/                      # Dehazed videos (created after inference)
├── check_requirements.py        # Requirements checker
├── run_training.bat             # Quick training script
├── run_video_dehaze.bat         # Quick video script
└── requirements.txt             # Python dependencies
```

---

## 🎯 Quick Test

**Test if everything works:**

1. **Check requirements:**
   ```bash
   python check_requirements.py
   ```

2. **If you have a video, test video dehazing:**
   ```bash
   python -m src.inference.video_inference --input_video YOUR_VIDEO.mp4 --output_video test_output.mp4 --device cpu --no_preview
   ```

3. **If you have dataset, test training (just 1 epoch):**
   ```bash
   python -m src.training.train_dehazenet --device cpu --epochs 1
   ```

---

## 📝 Notes

- **Training on CPU is slow** - expect hours for full training. GPU is recommended.
- **Video processing speed** depends on:
  - Device (GPU much faster than CPU)
  - Resolution (lower = faster)
  - Model size (4 layers faster than 8 or 16)
- **For academic presentation**, you can:
  - Show training plots from `weights/plots/`
  - Show before/after video comparisons
  - Report FPS from statistics files

---

## 🆘 Still Having Issues?

1. Run `python check_requirements.py` and read the output
2. Make sure you're in the project root directory
3. Check that all dependencies are installed: `pip install -r requirements.txt`
4. Verify dataset structure matches the expected format

