# 🎥 Video Dehazing Web Application

Production-ready full-stack web application for real-time video dehazing using deep learning.

## 🌟 Features

- ✅ **Modern Web Interface** - Upload, process, and download dehazed videos
- ✅ **Real-time Progress** - WebSocket-based live updates
- ✅ **Side-by-side Comparison** - View original and dehazed videos together
- ✅ **Multiple Models** - Choose between 4, 8, or 16-layer architectures
- ✅ **GPU Acceleration** - Optional CUDA support with FP16
- ✅ **Dockerized** - Easy deployment with Docker Compose
- ✅ **RESTful API** - Complete FastAPI backend with Swagger docs
- ✅ **Responsive UI** - Beautiful Tailwind CSS interface

---

## 📋 Table of Contents

1. [Architecture](#architecture)
2. [Quick Start](#quick-start)
3. [Development Setup](#development-setup)
4. [Docker Deployment](#docker-deployment)
5. [API Documentation](#api-documentation)
6. [Frontend Guide](#frontend-guide)
7. [Configuration](#configuration)
8. [Optimization](#optimization)
9. [Troubleshooting](#troubleshooting)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│           React Frontend (Port 3000/80)      │
│  • Video upload UI                          │
│  • Real-time progress tracking              │
│  • Side-by-side video preview               │
│  • Download management                      │
└─────────────────┬───────────────────────────┘
                  │ HTTP + WebSocket
┌─────────────────┴───────────────────────────┐
│        FastAPI Backend (Port 8000)          │
│  • REST API endpoints                       │
│  • Background task processing               │
│  • WebSocket progress updates               │
│  • Model inference engine                   │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────┴───────────────────────────┐
│         DeepDehazeNet (PyTorch)             │
│  • 8-layer U-Net architecture               │
│  • ~9.2M parameters                         │
│  • Frame-by-frame processing                │
└─────────────────────────────────────────────┘
```

**Technology Stack:**

- **Backend:** FastAPI, PyTorch, OpenCV, Uvicorn
- **Frontend:** React 18, Vite, Tailwind CSS, Axios
- **Deployment:** Docker, Docker Compose, Nginx

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (for containerized deployment)
- CUDA 11.8+ (optional, for GPU)

### 1. Clone and Navigate

```bash
cd "D:\8 SEM VIDEO PROJECT\Real-time-dehazing-deep-learning\web-app"
```

### 2. Option A: Docker Deployment (Recommended)

**CPU Version:**

```bash
docker-compose up -d
```

**GPU Version:**

```bash
docker-compose -f docker-compose.gpu.yml up -d
```

Access the app at: **http://localhost**

### 2. Option B: Local Development

**Backend:**

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env

# Run backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Access:

- Frontend: **http://localhost:3000**
- Backend API: **http://localhost:8000**
- API Docs: **http://localhost:8000/docs**

---

## 💻 Development Setup

### Backend Setup

1. **Install Dependencies:**

```bash
cd backend
pip install -r requirements.txt
```

2. **Configure Environment:**

Create `.env` file:

```env
HOST=0.0.0.0
PORT=8000
DEBUG=True

UPLOAD_DIR=./uploads
OUTPUT_DIR=./outputs
MODEL_DIR=../../models/pretrained

DEFAULT_MODEL_LAYERS=8
DEFAULT_MODEL_WEIGHTS=dehazenet_8layers_best.pth
DEVICE=cuda  # or cpu

MAX_UPLOAD_SIZE=500
ALLOWED_EXTENSIONS=mp4,avi,mov,mkv
DEFAULT_RESOLUTION=512
```

3. **Run Development Server:**

```bash
uvicorn app.main:app --reload
```

### Frontend Setup

1. **Install Dependencies:**

```bash
cd frontend
npm install
```

2. **Environment Variables:**

Create `.env` (optional):

```env
VITE_API_URL=http://localhost:8000/api
```

3. **Run Development Server:**

```bash
npm run dev
```

4. **Build for Production:**

```bash
npm run build
```

---

## 🐳 Docker Deployment

### CPU Deployment

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### GPU Deployment

**Prerequisites:**

- NVIDIA Docker runtime installed
- CUDA-compatible GPU

```bash
# Build and run with GPU
docker-compose -f docker-compose.gpu.yml up -d

# Verify GPU access
docker exec dehazing-backend-gpu nvidia-smi
```

### Custom Configuration

Edit `docker-compose.yml` environment variables:

```yaml
environment:
  - DEVICE=cuda # cpu or cuda
  - ENABLE_FP16=True # GPU only
  - DEFAULT_MODEL_LAYERS=8 # 4, 8, or 16
  - MAX_UPLOAD_SIZE=500 # MB
```

---

## 📚 API Documentation

### Interactive API Docs

Access Swagger UI: **http://localhost:8000/docs**

### Key Endpoints

#### 1. Upload Video

```http
POST /api/upload
Content-Type: multipart/form-data

Body:
- file: video file (MP4, AVI, MOV, MKV)

Response:
{
  "job_id": "uuid",
  "filename": "video.mp4",
  "file_size": 12345678,
  "upload_time": "2025-12-28T10:00:00",
  "message": "Video uploaded successfully"
}
```

#### 2. Start Processing

```http
POST /api/process
Content-Type: application/json

Body:
{
  "job_id": "uuid",
  "model_layers": "8",  // "4", "8", or "16"
  "resolution": 512,
  "use_fp16": false,
  "device": null  // null, "cuda", or "cpu"
}

Response:
{
  "job_id": "uuid",
  "status": "processing",
  "message": "Processing started successfully"
}
```

#### 3. Check Status

```http
GET /api/status/{job_id}

Response:
{
  "job_id": "uuid",
  "status": "processing",  // "pending", "processing", "completed", "failed"
  "progress": 45.5,
  "current_frame": 273,
  "total_frames": 600,
  "fps": 1.2,
  "elapsed_time": 227.5,
  "estimated_remaining": 272.5,
  "statistics": {...}
}
```

#### 4. Download Result

```http
GET /api/download/{job_id}

Response: video/mp4 file
```

#### 5. WebSocket Connection

```javascript
const ws = new WebSocket("ws://localhost:8000/api/ws/{job_id}");

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log("Progress:", update.progress);
};
```

#### 6. Delete Job

```http
DELETE /api/job/{job_id}

Response:
{
  "message": "Deleted 3 files",
  "files": ["...", "...", "..."]
}
```

---

## 🎨 Frontend Guide

### Component Structure

```
frontend/
├── src/
│   ├── App.jsx              # Main application component
│   ├── services/
│   │   └── api.js           # API client & WebSocket service
│   ├── index.css            # Tailwind styles
│   └── main.jsx             # React entry point
├── index.html
├── package.json
├── vite.config.js
└── tailwind.config.js
```

### Key Features

**1. Video Upload**

- Drag & drop support
- File type validation
- Size limit enforcement (500MB)
- Upload progress tracking

**2. Processing Controls**

- Model selection (4/8/16 layers)
- Resolution slider (256-1024)
- FP16 toggle (GPU only)
- Real-time progress bar

**3. Video Comparison**

- Side-by-side player
- Original vs dehazed
- Synchronized playback
- Download button

**4. Real-time Updates**

- WebSocket connection
- Progress percentage
- FPS monitoring
- ETA calculation

### Customization

**Change Theme:**

Edit `src/index.css`:

```css
body {
  background-color: #your-color;
  color: #your-text-color;
}
```

**Modify API URL:**

Create `frontend/.env`:

```env
VITE_API_URL=http://your-backend-url:8000/api
```

---

## ⚙️ Configuration

### Backend Configuration

**File:** `backend/.env`

| Variable               | Default   | Description                    |
| ---------------------- | --------- | ------------------------------ |
| `HOST`                 | `0.0.0.0` | Server host                    |
| `PORT`                 | `8000`    | Server port                    |
| `DEVICE`               | `cuda`    | Device: `cuda` or `cpu`        |
| `DEFAULT_MODEL_LAYERS` | `8`       | Model depth: `4`, `8`, or `16` |
| `DEFAULT_RESOLUTION`   | `512`     | Processing resolution          |
| `ENABLE_FP16`          | `False`   | Half-precision inference       |
| `MAX_UPLOAD_SIZE`      | `500`     | Max upload size (MB)           |
| `AUTO_CLEANUP_HOURS`   | `24`      | Auto-delete old files          |

### Model Selection

Place pretrained weights in `models/pretrained/`:

```
models/pretrained/
├── dehazenet_4layers_best.pth
├── dehazenet_8layers_best.pth
└── dehazenet_16layers_best.pth
```

Update `DEFAULT_MODEL_WEIGHTS` in `.env` to change default model.

---

## 🚄 Optimization

### Performance Tuning

**1. GPU Acceleration (30-50x faster)**

```env
DEVICE=cuda
ENABLE_FP16=True  # 2x faster on GPU
```

**2. Batch Processing**

Edit `backend/app/core/config.py`:

```python
BATCH_SIZE = 8  # Process multiple frames at once
```

**3. Resolution vs Speed**

| Resolution | Speed     | Quality   |
| ---------- | --------- | --------- |
| 256×256    | 4x faster | Good      |
| 512×512    | Baseline  | Excellent |
| 1024×1024  | 4x slower | Maximum   |

**4. Model Selection**

| Model    | Parameters | Speed    | Quality   |
| -------- | ---------- | -------- | --------- |
| 4-layer  | ~2.3M      | Fastest  | Good      |
| 8-layer  | ~9.2M      | Balanced | Excellent |
| 16-layer | ~36.8M     | Slowest  | Maximum   |

### Scaling for Production

**1. Load Balancing:**

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3 # Run 3 backend instances
```

**2. Use Redis for Job Queue:**

- Implement Celery workers
- Distribute processing across multiple GPUs

**3. CDN for Output:**

- Store processed videos in S3/CloudFront
- Return CDN URLs instead of direct downloads

---

## 🐛 Troubleshooting

### Common Issues

**1. "CUDA not available" error**

```bash
# Check CUDA installation
docker exec -it dehazing-backend-gpu nvidia-smi

# Fallback to CPU
docker-compose down
docker-compose up -d  # Uses CPU version
```

**2. "Model weights not found"**

```bash
# Verify model files exist
ls models/pretrained/

# Copy trained weights
cp models/pretrained/dehazenet_8layers_best.pth web-app/backend/
```

**3. "Upload failed: File too large"**

```env
# Increase max upload size in .env
MAX_UPLOAD_SIZE=1000  # 1GB
```

**4. WebSocket connection fails**

```javascript
// Check WebSocket URL in frontend/src/services/api.js
const wsUrl = `ws://localhost:8000/api/ws/${jobId}`;
// Change to your backend URL
```

**5. Out of memory during processing**

```env
# Reduce batch size and resolution
BATCH_SIZE=4
DEFAULT_RESOLUTION=256
```

**6. Slow processing on CPU**

```
Expected: 0.5-2 FPS on CPU
Solution: Use GPU or reduce resolution/model size
```

### Debugging

**Backend Logs:**

```bash
# Docker
docker-compose logs -f backend

# Local
# Check console output
```

**Check API Health:**

```bash
curl http://localhost:8000/api/health
```

**Test Frontend Connection:**

```bash
# Check if backend is accessible
curl http://localhost:8000/docs
```

---

## 📦 Project Structure

```
web-app/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py          # API endpoints
│   │   ├── core/
│   │   │   └── config.py          # Configuration
│   │   ├── models/
│   │   │   └── schemas.py         # Pydantic models
│   │   ├── services/
│   │   │   ├── model_service.py   # ML model wrapper
│   │   │   └── video_service.py   # Video processing
│   │   └── main.py                # FastAPI app
│   ├── uploads/                   # Uploaded videos
│   ├── outputs/                   # Processed outputs
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── Dockerfile.gpu
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── services/
│   │   │   └── api.js             # API client
│   │   ├── App.jsx                # Main component
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── Dockerfile
│   └── nginx.conf
│
├── docker-compose.yml              # CPU deployment
├── docker-compose.gpu.yml          # GPU deployment
└── README.md
```

---

## 🎯 Usage Example

### Complete Workflow

1. **Open App:** http://localhost (or http://localhost:3000 in dev)

2. **Upload Video:**

   - Click upload area
   - Select MP4/AVI/MOV/MKV file (max 500MB)
   - Wait for upload to complete

3. **Configure Processing:**

   - Click Settings icon
   - Choose model (4/8/16 layers)
   - Adjust resolution (256-1024)
   - Enable FP16 if using GPU

4. **Start Processing:**

   - Click "Start Dehazing"
   - Monitor real-time progress
   - View FPS, ETA, frames processed

5. **View Results:**

   - Compare original vs dehazed videos
   - Check processing statistics
   - Download dehazed video

6. **Process Another:**
   - Click "New Video"
   - Repeat workflow

---

## 📊 API Rate Limits

No rate limits by default. For production, implement with middleware:

```python
# backend/app/main.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/upload")
@limiter.limit("10/minute")
async def upload_video(...):
    ...
```

---

## 🔒 Security Considerations

**Production Checklist:**

- [ ] Enable HTTPS (SSL/TLS)
- [ ] Add authentication (JWT/OAuth)
- [ ] Implement file scanning (ClamAV)
- [ ] Rate limiting on uploads
- [ ] Input validation & sanitization
- [ ] CORS configuration
- [ ] Secure secret keys
- [ ] Regular dependency updates

---

## 📝 License

This project is part of the Real-Time Video Dehazing research project.  
Licensed under MIT License.

---

## 👥 Authors

**Sukhmandeep Singh**  
Email: sukhmandeep2125@gmail.com

---

## 🙏 Acknowledgments

- DeepDehazeNet architecture
- FastAPI framework
- React & Vite
- PyTorch & OpenCV communities

---

## 📞 Support

- **Issues:** Report bugs via GitHub Issues
- **Documentation:** Full API docs at `/docs`
- **Email:** sukhmandeep2125@gmail.com

---

**🎉 Your production-ready video dehazing web app is ready to deploy!**
