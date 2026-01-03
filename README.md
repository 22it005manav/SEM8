# 🎥 Real-Time Video Dehazing Using Deep Learning

Production-ready deep learning project for real-time image and video dehazing. This repository implements multiple CNN-based DeepDehazeNet architectures (4, 8, and 16 convolutional layers) with a modern web interface and backend API for seamless video processing.

---

## 📁 Project Structure

```
.
├── src/                    # Core source code
│   ├── models/            # DeepDehazeNet model architecture
│   ├── training/          # Training utilities
│   └── inference/         # Video inference engine
├── 4_layers_model/        # 4-layer model notebook and results
├── 8_layers_model/        # 8-layer model (best performing) and results
├── 16_layers_model/       # 16-layer model notebook and results
├── web-app/               # Full-stack web application (React + FastAPI)
│   ├── backend/          # FastAPI backend with video processing
│   └── frontend/         # React frontend with Tailwind CSS
├── config/                # Configuration settings
├── models/                # Model definitions and pre-trained weights
├── Dataset/               # Training and test datasets (add your data here)
├── VIDEO_PROJECT/         # Input/output directory for video processing
├── requirements.txt       # Python dependencies
├── check_requirements.py   # Setup verification script
├── QUICK_START.md         # Quick start guide
└── README.md              # This file
```

---

## ✨ Key Features

✅ **Multiple Architectures** - 4, 8, and 16-layer CNN models  
✅ **Real-time Video Processing** - Fast inference with OpenCV  
✅ **Web Interface** - Modern UI built with React & Tailwind CSS  
✅ **REST API** - FastAPI backend with Swagger documentation  
✅ **GPU Support** - Optional CUDA acceleration  
✅ **Docker Ready** - Complete Docker Compose setup  
✅ **WebSocket Updates** - Real-time progress tracking  
✅ **Side-by-side Comparison** - View before/after videos

---

## 🚀 Quick Start

### **1. Install Dependencies**

```cmd
pip install -r requirements.txt
```

### **2. Verify Setup**

```cmd
python check_requirements.py
```

### **3A. Train a Model** (Requires dataset)

```cmd
python -m src.training.train_dehazenet --device cpu --epochs 50
```

### **3B. Process Video** (Main feature)

```cmd
python -m src.inference.video_inference ^
  --input_video VIDEO_PROJECT\input_video.mp4 ^
  --output_video outputs\dehazed_output.mp4 ^
  --weights 8_layers_model\best_model_8_8.pth ^
  --device cpu
```

### **4. Run Web Application (Unified Single Port)**

```cmd
cd web-app
start-unified.bat
```

Then open: **http://localhost:8000** ✨

**What's New:**

- ✅ Single port (8000) - No more separate frontend/backend ports
- ✅ Modern UI with gradient design
- ✅ Side-by-side video comparison
- ✅ Synchronized playback controls
- ✅ Enhanced visual experience

---

## 📊 Model Comparison

| Model    | Layers | Parameters | Speed       | Quality    |
| -------- | ------ | ---------- | ----------- | ---------- |
| 4-Layer  | 4      | ~50K       | ⚡⚡⚡ Fast | Standard   |
| 8-Layer  | 8      | ~200K      | ⚡⚡ Medium | **Best** ✓ |
| 16-Layer | 16     | ~800K      | ⚡ Slow     | Excellent  |

**Recommended:** 8-layer model - Best balance of speed and quality

---

## 📦 Dataset Setup

To train models, prepare your dataset:

```
Dataset/
  ├── hazy/      # Hazy input images
  └── clear/     # Ground truth clear images
```

**Supported formats:** `.jpg`, `.jpeg`, `.png`

**Recommended datasets:**

- RESIDE (http://dehazing.cs.umn.edu/reside/)
- HazeRD Dataset
- D-HAZY Dataset

---

## 🖥️ Web Application Features

### Backend (FastAPI)

- RESTful API endpoints
- Background video processing
- WebSocket progress updates
- Model inference optimization
- GPU/CPU device management

### Frontend (React)

- Modern responsive UI
- Drag-and-drop video upload
- Real-time progress tracking
- Side-by-side video comparison
- Download management

---

## 🐳 Docker Deployment

Run with Docker:

```cmd
cd web-app
docker-compose up
```

Access at: http://localhost

---

## 📋 Common Commands

```cmd
# Check all requirements
python check_requirements.py

# Train with GPU
python -m src.training.train_dehazenet --device cuda --epochs 100

# Fine-tune existing model
python -m src.training.train_dehazenet --device cuda --resume_from 8_layers_model\best_model_8_8.pth --epochs 30 --lr 1e-5

# Process video (GPU with half precision)
python -m src.inference.video_inference ^
  --input_video VIDEO_PROJECT\input_video.mp4 ^
  --output_video outputs\dehazed.mp4 ^
  --weights 8_layers_model\best_model_8_8.pth ^
  --device cuda ^
  --half
```

---

## 🔧 Configuration

Edit `config/config.py` to customize:

- Model architecture
- Training hyperparameters
- Device settings
- Batch sizes
- Learning rates

---

## 📚 Model Training

### Training from Scratch

```cmd
python -m src.training.train_dehazenet --device cpu --epochs 50 --batch_size 4 --lr 0.001
```

### Resume Training

```cmd
python -m src.training.train_dehazenet --device cuda --resume_from weights\last_checkpoint.pth --epochs 100
```

### Available Models

- **4_layers_model/** - Lightweight, fast inference
- **8_layers_model/** - **Recommended** - Best quality/speed balance
- **16_layers_model/** - High-quality but slower

---

## 🎯 Video Processing Options

### Basic Processing

```cmd
python -m src.inference.video_inference --input_video input.mp4 --output_video output.mp4
```

### Advanced Options

```cmd
python -m src.inference.video_inference ^
  --input_video input.mp4 ^
  --output_video output.mp4 ^
  --weights 8_layers_model\best_model_8_8.pth ^
  --device cuda ^
  --half ^
  --resize 512 512 ^
  --batch_size 2 ^
  --no_preview
```

**Parameters:**

- `--device` - `cpu` or `cuda` (GPU)
- `--half` - Use FP16 precision (faster on GPU)
- `--resize` - Process resolution (W H)
- `--batch_size` - Video frame batch size
- `--no_preview` - Skip preview window

---

## ⚠️ Prerequisites

**Required:**

- Python 3.10 or 3.11
- CUDA 11.8+ (optional, for GPU)
- 4GB+ RAM (8GB+ recommended)

**For Web App:**

- Node.js 16+ (frontend)
- 2GB+ disk space for Docker images

---

## 🐛 Troubleshooting

### Issue: "CUDA out of memory"

```cmd
# Use CPU instead
python -m src.inference.video_inference --input_video input.mp4 --device cpu

# Or reduce batch size
python -m src.inference.video_inference --input_video input.mp4 --device cuda --batch_size 1
```

### Issue: Slow processing

```cmd
# Use GPU with half precision
python -m src.inference.video_inference --input_video input.mp4 --device cuda --half

# Reduce resolution
python -m src.inference.video_inference --input_video input.mp4 --resize 512 512 --device cuda
```

### Issue: Missing dataset

- Download RESIDE dataset from http://dehazing.cs.umn.edu/reside/
- Extract to `Dataset/` folder with `hazy/` and `clear/` subdirectories

---

## 📊 Performance Metrics

Models are evaluated on:

- **PSNR** - Peak Signal-to-Noise Ratio (higher is better)
- **SSIM** - Structural Similarity Index (higher is better)
- **Inference Speed** - Frames per second (FPS)
- **Model Size** - Parameter count

See individual model folders for detailed results.

---

## 🌐 Web Application Details

### Running Locally

```cmd
cd web-app
start-dev.bat
```

### Docker Production Deployment

```cmd
cd web-app
docker-compose -f docker-compose.yml up -d
```

### Docker with GPU Support

```cmd
cd web-app
docker-compose -f docker-compose.gpu.yml up -d
```

Access: http://localhost:3000 (dev) or http://localhost (production)

**API Documentation:** http://localhost:8000/docs (when backend running)

---

## 📜 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Project Status

✅ Core model architecture complete  
✅ Training pipeline functional  
✅ Video inference working  
✅ Web application ready  
✅ Docker support available

**Latest Update:** December 2025

---

## 📞 Support & Issues

For questions or issues:

1. Check [QUICK_START.md](QUICK_START.md) for common problems
2. Review [PROJECT_STATUS_SUMMARY.md](PROJECT_STATUS_SUMMARY.md) for project details
3. Open an issue on GitHub

---

**Note:** This project requires sufficient computational resources. For real-time processing, GPU acceleration is recommended.
