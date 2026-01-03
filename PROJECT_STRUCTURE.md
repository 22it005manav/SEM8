# 📁 Complete Project Directory Structure

## Overview

This document shows the **complete project structure** for running on Google Colab with GPU acceleration.

---

## 🎯 Main Directory Tree

```
/content/video_dehazing/                    ← Main project folder (on Colab)
│
├── 📄 app.py                               ⭐ FastAPI Main Application
│   └── Runs on: http://localhost:8000
│       Contains all API endpoints
│
├── 📄 requirements.txt                     📦 Python Dependencies
│   └── All packages listed with versions
│
├── 📁 config/                              ⚙️ Configuration
│   ├── __init__.py
│   └── config.py                          Settings for model, training, inference
│       ├── DEVICE = "cuda"
│       ├── MODEL_DIR = "models/pretrained"
│       ├── BATCH_SIZE = 2
│       ├── IMAGE_SIZE = 256
│       └── OUTPUT_RESOLUTION = (512, 512)
│
├── 📁 src/                                 🧠 Source Code
│   ├── __init__.py
│   │
│   ├── models/                            Deep Learning Models
│   │   ├── __init__.py
│   │   └── dehazenet.py                   ⭐ DeepDehazeNet Architecture
│   │       ├── DeepDehazeNet class
│   │       │   ├── __init__(num_layers=8)
│   │       │   ├── forward(x)
│   │       │   └── Residual connections
│   │       ├── Supports 4, 8, 16 layers
│   │       └── Output: dehazed frames
│   │
│   ├── training/                         Training Code
│   │   ├── __init__.py
│   │   └── train_dehazenet.py            (For custom training)
│   │       ├── train_model()
│   │       ├── Loss calculation
│   │       └── Checkpoint saving
│   │
│   └── inference/                        Inference Code
│       ├── __init__.py
│       ├── video_inference.py            (For batch processing)
│       │   ├── process_video()
│       │   ├── Frame preprocessing
│       │   └── Video writing
│       └── image_inference.py            (For single images)
│           └── process_image()
│
├── 📁 models/                              🤖 Model Weights & Architecture
│   └── pretrained/                        Pre-trained Model Weights
│       ├── dehazenet_8layers_best.pth    8-layer model weights (~200KB)
│       │   └── Use this for balanced speed/quality
│       ├── dehazenet_16layers_best.pth   16-layer model weights (~400KB)
│       │   └── Use this for maximum quality
│       └── dehazenet_4layers_best.pth    4-layer weights (❌ NOT INCLUDED)
│           └── Falls back to 8-layer model
│
├── 📁 data/                                📊 Training Data
│   └── Dataset/                          Image Dataset for Training
│       ├── hazy/                         Degraded/Hazy Images
│       │   ├── img_001.jpg              JPEG format
│       │   ├── img_002.jpg
│       │   ├── img_003.png              PNG also supported
│       │   └── ...
│       │       └── Total: ~1000-5000 images for training
│       │
│       └── clear/                       Reference/Clear Images
│           ├── img_001.jpg              Paired with hazy images (same names!)
│           ├── img_002.jpg
│           ├── img_003.png
│           └── ...
│               └── Must have same filenames as hazy folder
│
├── 📁 uploads/                             📤 User Upload Directory
│   ├── {job_id}_video1.mp4               Video uploaded by user
│   ├── {job_id}_video2.avi               Temporary storage
│   └── {job_id}_video3.mov               Auto-cleaned after download
│
├── 📁 outputs/                             📥 Processed Output Directory
│   ├── {job_id}_dehazed.mp4              Processed video
│   ├── {job_id}_dehazed.avi              Output format same as input
│   ├── {job_id}_dehazed.json             Metadata (optional)
│   └── ...
│
├── 📁 results/                             📊 Results & Metrics
│   ├── metrics/                          Evaluation Metrics
│   │   ├── psnr_scores.csv              Peak Signal-to-Noise Ratio
│   │   ├── ssim_scores.csv              Structural Similarity Index
│   │   └── time_metrics.json            Processing time data
│   │
│   ├── dehazed_videos/                   Training/Test Results
│   │   ├── epoch_001_output.mp4
│   │   ├── epoch_050_output.mp4
│   │   └── final_result.mp4
│   │
│   └── plots/                            Visualization
│       ├── training_loss.png
│       ├── ssim_comparison.png
│       └── quality_metrics.png
│
└── 📁 notebooks/                           📓 Jupyter Notebooks
    ├── training_notebook.ipynb           Training code (optional)
    ├── inference_notebook.ipynb          Inference demo (optional)
    └── analysis_notebook.ipynb           Results analysis (optional)
```

---

## 📋 File Details

### Core Application Files

#### `app.py` (Main Server)

```python
# Contains:
- FastAPI app initialization
- CORS middleware setup
- Model loading and caching
- All API endpoints:
  * GET /              (Welcome)
  * GET /status        (GPU status)
  * POST /upload       (Video upload)
  * POST /process      (Processing)
  * GET /download      (Download results)
- Video processing loop
- Error handling
```

---

#### `config/config.py` (Settings)

```python
# Contains:
DEVICE = "cuda" / "cpu"
MODEL_LAYERS = 8              # 8 or 16
MODEL_DIR = "models/pretrained"
BATCH_SIZE = 2
IMAGE_SIZE = 256
OUTPUT_RESOLUTION = (512, 512)
MAX_VIDEO_SIZE = 500MB
OUTPUT_FPS = 30
LEARNING_RATE = 1e-4
EPOCHS = 100
```

---

#### `src/models/dehazenet.py` (Neural Network)

```python
class DeepDehazeNet(nn.Module):
    def __init__(self, num_layers=8):
        # Layer 1:  Input(3) -> 16 channels
        # Layer 2-N: 16 -> 16 channels
        # Layer N+1: 16 -> Output(3)

    def forward(self, x):
        # Conv layers with ReLU
        # Residual connection (skip)
        # Output clamp [0, 1]
        return output
```

---

## 📊 Model Architecture Breakdown

### 8-Layer Model (Recommended)

```
Input Image (3×H×W)
    ↓
Conv2d(3→16) + ReLU
    ↓
Conv2d(16→16) + ReLU  ×6 layers
    ↓
Conv2d(16→3)
    ↓
Skip Connection (+ Input)
    ↓
Clamp [0, 1]
    ↓
Output Image (3×H×W)
```

**Parameters**: ~200K
**Memory**: ~800MB (batch=1)
**Speed**: 20 fps @ 1080p
**Quality**: Excellent

---

### 16-Layer Model (Premium)

```
Input Image (3×H×W)
    ↓
Conv2d(3→16) + ReLU
    ↓
Conv2d(16→16) + ReLU  ×14 layers
    ↓
Conv2d(16→3)
    ↓
Skip Connection (+ Input)
    ↓
Clamp [0, 1]
    ↓
Output Image (3×H×W)
```

**Parameters**: ~400K
**Memory**: ~1.2GB (batch=1)
**Speed**: 10 fps @ 1080p
**Quality**: Maximum

---

## 🎯 Data Format Specifications

### Input Video Requirements

```
Format:      MP4, AVI, MOV, MKV
Codec:       H.264, H.265, MPEG
Frame Rate:  20-60 fps (any)
Resolution:  Any (auto-resized)
Max Size:    500 MB
Channels:    3 (RGB/BGR)
```

### Output Video Format

```
Format:      MP4
Codec:       H.264
Frame Rate:  Same as input
Resolution:  Configurable (256-1024)
Quality:     High (CRF 23)
Channels:    3 (RGB)
```

---

## 🔄 API Flow Diagram

```
User Browser
    ↓
[Upload Video] → POST /upload
    ↓ Returns job_id
Colab Server
    ↓
[Process Video] → POST /process/{job_id}
    ↓
┌─────────────────┐
│ Load Model      │
│ (GPU Memory)    │
└─────────────────┘
    ↓
┌─────────────────┐
│ Read Frames     │
│ (OpenCV)        │
└─────────────────┘
    ↓
┌─────────────────┐
│ Preprocess      │
│ (Resize, Norm)  │
└─────────────────┘
    ↓
┌─────────────────┐
│ Model Forward   │
│ (GPU Inference) │
└─────────────────┘
    ↓
┌─────────────────┐
│ Postprocess     │
│ (Denorm, Save)  │
└─────────────────┘
    ↓
[Download Result] → GET /download/{job_id}
    ↓
User Browser
```

---

## 💾 Storage Breakdown

```
Component                   Size
─────────────────────────   ──────────
PyTorch                     ~500 MB
OpenCV + deps              ~200 MB
FastAPI + deps             ~100 MB
8-layer Model              200 KB
16-layer Model             400 KB
Configuration files        < 1 MB
─────────────────────────   ──────────
Total Base Install         ~800 MB

Plus per job:
─────────────────────────   ──────────
Input video (1 min)        30-200 MB (depends on resolution)
Output video (1 min)       30-200 MB
Temporary files            Cleaned after download
─────────────────────────   ──────────
```

---

## 🔐 Directory Permissions

```
Directory          Mode    Purpose
─────────────────  ────    ──────────────────
src/               r+x     Read + Execute
models/            r+x     Read model weights
config/            r+x     Read config
uploads/           rwx     Write uploaded files
outputs/           rwx     Write results
data/              r+x     Read training data
results/           rwx     Write metrics
```

---

## 📝 File Organization Best Practices

### For Organization:

```
models/pretrained/
  └── README.md              # Weight documentation
      └── Model sources, training configs

results/
  └── metrics/
      └── EVALUATION.md      # Performance metrics
  └── plots/
      └── INDEX.md           # Visualization guide
```

### For Version Control (git):

```
.gitignore should include:
- *.pth                  (Model weights - large)
- uploads/               (User uploads)
- outputs/               (Results)
- venv/                  (Virtual environment)
- __pycache__/
- *.pyc
```

---

## 🚀 Initialization Sequence on Colab

```
1. Colab Cell 1: Create directories
   ✓ All folders created

2. Colab Cell 2-3: Install packages
   ✓ Dependencies ready

3. Colab Cell 4: Load model
   ✓ Model architecture: src/models/dehazenet.py
   ✓ Load weights: models/pretrained/*.pth
   ✓ Device: GPU (cuda) or CPU

4. Colab Cell 10: Start server
   ✓ Uvicorn listening on :8000
   ✓ ngrok tunnel created
   ✓ Ready for requests

5. User: Upload video
   ✓ Saved to: uploads/{job_id}_*

6. User: Process request
   ✓ Reads from: uploads/
   ✓ Model inference
   ✓ Writes to: outputs/

7. User: Download result
   ✓ Served from: outputs/{job_id}_*
```

---

## 🎓 Key Concepts

### Job ID

- Unique identifier for each processing request
- Format: UUID (36 characters)
- Used to track files: `{job_id}_filename.ext`

### Device Selection

- CUDA (GPU): Fast processing
- CPU: Fallback, slower
- Auto-detected in code

### Model Caching

- Model loaded once
- Stays in GPU memory
- Reused for multiple jobs
- Reduces processing time

### Residual Learning

- Skip connection: output = model(input) + input
- Improves training and quality
- Stabilizes gradient flow

---

## ✅ Verification Checklist

After setup, verify each directory exists:

```
□ /content/video_dehazing/              (Main)
□ /content/video_dehazing/src/          (Source)
□ /content/video_dehazing/src/models/   (Model architecture)
□ /content/video_dehazing/config/       (Configuration)
□ /content/video_dehazing/models/       (Model folder)
□ /content/video_dehazing/models/pretrained/  (Weights)
□ /content/video_dehazing/data/Dataset/ (Training data)
□ /content/video_dehazing/uploads/      (Upload dir)
□ /content/video_dehazing/outputs/      (Output dir)
□ /content/video_dehazing/results/      (Results)

Files created:
□ app.py                                (FastAPI)
□ requirements.txt                      (Dependencies)
□ src/models/dehazenet.py              (Model code)
□ config/config.py                     (Settings)
```

---

## 🔗 File Dependencies

```
app.py
  ├─→ config/config.py          (Settings)
  ├─→ src/models/dehazenet.py   (Model class)
  ├─→ torch                     (PyTorch)
  ├─→ fastapi                   (Web framework)
  ├─→ opencv-python             (Video processing)
  └─→ numpy                     (Array operations)

Video Upload → Process → Download
  uploads/  →  inference  →  outputs/
```

---

## 📈 Scalability Notes

Current setup supports:

- ✅ **Sequential processing**: 1 video at a time
- ✅ **Batch sizing**: Configurable batch size
- ✅ **Model selection**: 8 or 16 layer
- ✅ **Resolution**: 256-1024 pixels

For production:

- Multiple workers
- Job queue (Redis)
- Load balancing
- Distributed GPU

---

## 📚 Documentation Files Included

| File                       | Purpose                     |
| -------------------------- | --------------------------- |
| `COLAB_SETUP.md`           | Detailed setup instructions |
| `COLAB_COMPLETE_GUIDE.md`  | Full documentation          |
| `COLAB_QUICK_REFERENCE.md` | Quick lookup                |
| `PROJECT_STRUCTURE.md`     | This file                   |
| `README.md`                | General project info        |

---

## 🎯 Next Steps

1. Review this structure
2. Follow `COLAB_SETUP.md`
3. Upload notebook to Colab
4. Run cells in order
5. Access API at public URL
6. Start dehazing videos!

---

**Project Status**: ✅ Ready to Deploy

**Last Updated**: January 3, 2026

**Version**: 1.0 - Complete Structure
