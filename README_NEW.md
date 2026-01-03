# 🎥 Real-Time Video Dehazing Using Deep Learning

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2.2-red.svg)](https://pytorch.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Production-ready deep learning system for real-time image and video dehazing. This repository implements CNN-based DeepDehazeNet architectures with a modern web interface, REST API, and **Google Colab GPU support** for seamless video processing.

![Demo](https://img.shields.io/badge/Demo-Live-brightgreen) _Upload your hazy videos and get crystal-clear results in real-time!_

---

## ✨ Key Features

✅ **Multiple CNN Architectures** - 8-layer (balanced) and 16-layer (premium) models  
✅ **Real-time Video Processing** - Fast inference with OpenCV optimization  
✅ **Modern Web Interface** - React + Tailwind CSS with drag-and-drop upload  
✅ **REST API** - FastAPI backend with Swagger/OpenAPI documentation  
✅ **GPU Acceleration** - CUDA support + **Google Colab GPU setup included**  
✅ **Side-by-side Comparison** - View original vs. dehazed videos  
✅ **WebSocket Progress** - Real-time processing status updates  
✅ **Docker Ready** - Complete containerization setup  
✅ **One-Click Colab** - Run with free GPU on Google Colab (no setup needed!)

---

## 🚀 Quick Start Options

### Option 1: Run Locally (CPU/GPU)

**1. Clone Repository**

```bash
git clone https://github.com/YOUR_USERNAME/Real-time-dehazing-deep-learning.git
cd Real-time-dehazing-deep-learning
```

**2. Install Dependencies**

```bash
pip install -r requirements.txt
```

**3. Download Pre-trained Models**
Download the model weights and place them in `models/pretrained/`:

- `dehazenet_8layers_best.pth` - 8-layer model (recommended)
- `dehazenet_16layers_best.pth` - 16-layer model (premium quality)

[📥 Download Models](https://drive.google.com/drive/folders/YOUR_DRIVE_LINK) _(Add your Google Drive link)_

**4. Run Web Application**

```bash
python app.py
```

Open http://localhost:8000 in your browser! 🎉

### Option 2: Run on Google Colab (Free GPU!) ⚡

Perfect for users without GPU or who want cloud processing:

1. **Open Colab Notebook:** [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/YOUR_USERNAME/Real-time-dehazing-deep-learning/blob/main/VideoDehazing_Colab_GPU.ipynb)

2. **Run All Cells** - Full setup in 3 minutes

3. **Get Public URL** - ngrok tunnel for web access

4. **Upload Videos** - Process with free T4 GPU

📖 **Detailed Guide:** [COLAB_COMPLETE_GUIDE.md](COLAB_COMPLETE_GUIDE.md) | [Quick Reference](COLAB_QUICK_REFERENCE.md)

### Option 3: Docker Deployment

```bash
cd web-app
docker-compose up
```

Access at: http://localhost

---

## 📁 Project Structure

```
Real-time-dehazing-deep-learning/
├── app.py                          # 🎯 Main FastAPI application (single-file deployment)
├── VideoDehazing_Colab_GPU.ipynb   # 🌐 Google Colab notebook with GPU setup
├── requirements.txt                # Python dependencies
├── config/
│   └── config.py                  # Configuration settings
├── models/
│   ├── dehazenet.py               # DeepDehazeNet architecture
│   └── pretrained/                # Pre-trained model weights (*.pth)
├── data/
│   └── Dataset/                   # Training data (hazy/clear pairs)
├── src/
│   ├── models/                    # Model definitions
│   ├── training/                  # Training scripts
│   └── inference/                 # Video inference engine
├── web-app/
│   ├── backend/                   # FastAPI microservice (advanced setup)
│   └── frontend/                  # React UI with Tailwind CSS
├── uploads/                       # User-uploaded videos
├── outputs/                       # Processed results
└── docs/                          # Comprehensive documentation
    ├── COLAB_COMPLETE_GUIDE.md    # 50+ page Colab reference
    ├── COLAB_QUICK_REFERENCE.md   # 5-minute quick start
    ├── INDEX.md                   # Documentation index
    └── START_HERE.md              # New user guide
```

---

## 📊 Model Comparison

| Model    | Layers | Parameters | Speed     | Quality   | Use Case                    |
| -------- | ------ | ---------- | --------- | --------- | --------------------------- |
| 8-Layer  | 8      | ~200K      | ⚡⚡ Fast | Excellent | **Recommended** - Balanced  |
| 16-Layer | 16     | ~800K      | ⚡ Medium | Premium   | High-quality video projects |

**Default:** 8-layer model provides the best speed/quality tradeoff for most use cases.

---

## 🖥️ Web Interface Features

### Upload & Process

- Drag-and-drop video upload
- Model selection (8-layer or 16-layer)
- Real-time progress bar with WebSocket
- Automatic processing queue

### Results Viewer

- **Side-by-side comparison** - Original vs. Dehazed
- **Synchronized playback** - Compare frame-by-frame
- **Download button** - Save processed videos
- **Responsive design** - Works on desktop and mobile

### API Endpoints

- `POST /process` - Upload and process video
- `GET /status/{job_id}` - Check processing status
- `GET /download/{job_id}` - Download results
- `GET /docs` - Interactive API documentation

---

## 🧠 Model Architecture

**DeepDehazeNet** - End-to-end CNN for single image dehazing

- **Input:** RGB hazy image (3 channels)
- **Architecture:**
  - Convolutional layers with ReLU activation
  - Residual skip connection (input to output)
  - MaxPooling for feature extraction
- **Output:** RGB dehazed image (3 channels)
- **Loss:** MSE between dehazed and ground truth

```python
class DeepDehazeNet(nn.Module):
    def __init__(self, num_layers=8):
        # num_layers: 4, 8, or 16 convolutional layers
        # Deeper models capture more complex atmospheric effects
```

---

## 🎓 Training Your Own Model

### Prepare Dataset

```
data/Dataset/
  ├── hazy/      # Hazy input images (PNG/JPG)
  └── clear/     # Ground truth clear images
```

**Recommended datasets:**

- [RESIDE](https://sites.google.com/view/reside-dehaze-datasets) - Large-scale benchmark
- [D-HAZY](https://www.meo.etc.upt.ro/AncutiProjectPages/D_Hazy_ICIP2016/) - Depth-based
- [O-HAZE/I-HAZE](https://data.vision.ee.ethz.ch/cvl/ntire18/) - Outdoor/Indoor

### Train Command

```bash
# CPU Training
python -m src.training.train_dehazenet --device cpu --epochs 50 --batch_size 4

# GPU Training (faster)
python -m src.training.train_dehazenet --device cuda --epochs 100 --batch_size 16
```

### Fine-tune Existing Model

```bash
python -m src.training.train_dehazenet \
  --device cuda \
  --resume_from models/pretrained/dehazenet_8layers_best.pth \
  --epochs 30 \
  --lr 1e-5
```

---

## 🔧 Configuration

Edit [config/config.py](config/config.py) to customize:

```python
# Model
NUM_LAYERS = 8  # or 16
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

# Training
LEARNING_RATE = 0.001
BATCH_SIZE = 16
NUM_EPOCHS = 100

# Inference
INPUT_SIZE = (640, 480)  # Resize input videos
FPS_LIMIT = 30  # Max output FPS
```

---

## 🐳 Docker Deployment

### CPU Version

```bash
cd web-app
docker-compose up
```

### GPU Version (NVIDIA Docker required)

```bash
docker-compose -f docker-compose.gpu.yml up
```

Access at: http://localhost

---

## 📖 Documentation

| Guide                                                | Description                         |
| ---------------------------------------------------- | ----------------------------------- |
| [START_HERE.md](START_HERE.md)                       | First-time user guide               |
| [QUICK_START.md](QUICK_START.md)                     | Fast setup for local deployment     |
| [COLAB_COMPLETE_GUIDE.md](COLAB_COMPLETE_GUIDE.md)   | 50+ page Google Colab reference     |
| [COLAB_QUICK_REFERENCE.md](COLAB_QUICK_REFERENCE.md) | 5-minute Colab quick start          |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)         | Detailed architecture documentation |
| [INDEX.md](INDEX.md)                                 | Complete documentation index        |

---

## 🎯 Use Cases

✅ **Outdoor Photography** - Remove haze from landscape photos  
✅ **Surveillance Videos** - Enhance foggy security footage  
✅ **Drone Footage** - Clear aerial videos in poor weather  
✅ **Underwater Imaging** - Improve visibility in marine videos  
✅ **Medical Imaging** - Enhance contrast in certain scans  
✅ **Autonomous Driving** - Pre-process camera input in fog

---

## 🛠️ Technical Stack

| Component        | Technology                 |
| ---------------- | -------------------------- |
| Deep Learning    | PyTorch 2.2.2              |
| Backend API      | FastAPI 0.115.6 + Uvicorn  |
| Frontend         | React 18 + Tailwind CSS 3  |
| Video Processing | OpenCV 4.10                |
| GPU Acceleration | CUDA 11.8                  |
| Cloud Platform   | Google Colab (free T4 GPU) |
| Tunneling        | ngrok 7.0.0                |
| Containerization | Docker + Docker Compose    |

---

## 📝 API Usage Examples

### Python

```python
import requests

# Upload video
files = {'file': open('foggy_video.mp4', 'rb')}
data = {'model_type': '8'}
response = requests.post('http://localhost:8000/process', files=files, data=data)
job_id = response.json()['job_id']

# Check status
status = requests.get(f'http://localhost:8000/status/{job_id}').json()
print(status['progress'])  # 0-100

# Download result
if status['status'] == 'completed':
    result = requests.get(f'http://localhost:8000/download/{job_id}')
    with open('dehazed.mp4', 'wb') as f:
        f.write(result.content)
```

### cURL

```bash
# Upload and process
curl -X POST http://localhost:8000/process \
  -F "file=@input.mp4" \
  -F "model_type=8"

# Check status
curl http://localhost:8000/status/JOB_ID

# Download
curl http://localhost:8000/download/JOB_ID -o dehazed.mp4
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- DeepDehazeNet architecture based on CNN dehazing research
- RESIDE dataset creators
- PyTorch and FastAPI communities
- Google Colab for free GPU access

---

## 📧 Contact

**Project Maintainer:** [Your Name](mailto:your.email@example.com)  
**GitHub Issues:** [Report bugs or request features](https://github.com/YOUR_USERNAME/Real-time-dehazing-deep-learning/issues)

---

## 🌟 Star History

If you find this project helpful, please consider giving it a ⭐ on GitHub!

[![Star History Chart](https://api.star-history.com/svg?repos=YOUR_USERNAME/Real-time-dehazing-deep-learning&type=Date)](https://star-history.com/#YOUR_USERNAME/Real-time-dehazing-deep-learning&Date)

---

**Made with ❤️ for the Computer Vision Community**
