# 🚀 Google Colab Quick Reference Card

## ⚡ 5-Minute Quick Start

### 1. Open & Setup

```
✅ Go to Google Colab
✅ Upload: VideoDehazing_Colab_GPU.ipynb
✅ Runtime → Change runtime type → GPU
✅ Run Cells 1-10 in order
```

### 2. Copy ngrok Token

```
🔑 https://dashboard.ngrok.com/auth
📋 Copy authentication token
📝 Paste when Cell 10 asks
```

### 3. Get Public URL

```
✅ Cell 10 will show:
   https://xxxx-xxxx-xxxx.ngrok.io

📚 API Docs:
   https://xxxx-xxxx-xxxx.ngrok.io/docs
```

---

## 🎯 Model Selection

| Use Case          | Model    | Why             |
| ----------------- | -------- | --------------- |
| **Most Videos**   | 8-layer  | ⚖️ Best balance |
| **HD Videos**     | 8-layer  | ⚡ Fast enough  |
| **High Quality**  | 16-layer | ✨ Best results |
| **Batch Process** | 8-layer  | 🚀 Faster       |

---

## 🌐 API Quick Commands

### Upload Video

```bash
POST /upload
Content-Type: multipart/form-data
Body: [video file]
```

### Process Video

```bash
POST /process/{job_id}
Content-Type: application/json
Body: {
  "model_layers": 8,
  "resolution": 512,
  "use_fp16": false
}
```

### Download Result

```bash
GET /download/{job_id}
→ Returns: dehazed video file
```

### Check Status

```bash
GET /status
→ Returns: GPU info, memory usage
```

---

## 📊 File Structure

```
/content/video_dehazing/
├── app.py              (Server)
├── config/config.py    (Settings)
├── src/models/         (Deep learning)
├── models/pretrained/  (Weights)
├── uploads/            (Input videos)
├── outputs/            (Results)
└── data/Dataset/       (Training data)
```

---

## 💡 Performance Tips

| Task    | Tip               | Benefit       |
| ------- | ----------------- | ------------- |
| Speed   | Use 8-layer       | 2x faster     |
| Quality | Use 16-layer      | Better output |
| Memory  | Reduce resolution | No crashes    |
| Batch   | Process multiple  | Efficient GPU |

---

## 🐛 Common Issues

| Issue                 | Fix                    |
| --------------------- | ---------------------- |
| ❌ No GPU             | Runtime → Change → GPU |
| ❌ Server won't start | Restart Cell 10        |
| ❌ ngrok fails        | Check token            |
| ❌ Video fails        | Verify MP4 format      |
| ❌ Out of memory      | Use 8-layer model      |

---

## 📱 Browser Access

1. Open ngrok URL in browser
2. Add `/docs` → `/docs`
3. Scroll to Upload endpoint
4. Click "Try it out"
5. Select video file
6. Click "Execute"

---

## ⏱️ Processing Time (approx)

```
Video          Model    Time
-----------    -----    ---------
1min @ 480p    8-layer  2 min
1min @ 720p    8-layer  3 min
1min @ 1080p   8-layer  5 min

1min @ 480p    16-layer 4 min
1min @ 720p    16-layer 6 min
1min @ 1080p   16-layer 10 min
```

---

## 🔋 GPU Memory

```
Metric               Used
-------------------  ------
8-layer model       ~800MB
16-layer model      ~1.2GB
Framework overhead  ~500MB
Safe margin         ~500MB
```

**Total available**: ~15GB on T4

---

## 📥 Google Drive Integration

### Mount Drive

```python
from google.colab import drive
drive.mount('/content/drive')
```

### Copy Video

```python
import shutil
shutil.copy(
    '/content/drive/My Drive/video.mp4',
    '/content/video_dehazing/uploads/'
)
```

### Save Results

```python
shutil.copy(
    '/content/video_dehazing/outputs/result.mp4',
    '/content/drive/My Drive/Results/'
)
```

---

## 🔔 Important Notes

⚠️ **Session Duration**: 12 hours max
⚠️ **Storage**: Files deleted after disconnect
⚠️ **Save to Drive**: For persistent storage
⚠️ **Restart**: Continue from Cell 1 if needed

---

## 📚 Document Guide

| File                              | Purpose            |
| --------------------------------- | ------------------ |
| **VideoDehazing_Colab_GPU.ipynb** | Main notebook      |
| **COLAB_COMPLETE_GUIDE.md**       | Full documentation |
| **COLAB_QUICK_REFERENCE.md**      | This file          |
| **COLAB_SETUP.md**                | Detailed setup     |

---

## ✅ Verification Checklist

After each major step:

```
Cell 1:  ✓ Environment configured
Cell 2:  ✓ Packages installed
Cell 3:  ✓ System deps installed
Cell 4:  ✓ GPU verified
Cell 5:  ✓ Directories created
Cell 6:  ✓ Model loaded
Cell 7:  ✓ Config created
Cell 8:  ✓ FastAPI app created
Cell 9:  ✓ Requirements file ready
Cell 10: ✓ Server running + Public URL
```

---

## 🎬 End-to-End Workflow

```
1. [5 min] Setup Colab + GPU
   ↓
2. [2 min] Run Cells 1-10
   ↓
3. [1 min] Upload video
   ↓
4. [varies] Process video
   ↓
5. [1 min] Download result
   ↓
6. [1 min] Save to Drive
```

**Total time**: ~10-20 minutes per video

---

## 🌍 Remote Access

✅ **Works from anywhere**: Colab + ngrok
✅ **No local server needed**: Everything in cloud
✅ **Mobile friendly**: API works on phones
✅ **Real-time updates**: WebSocket support

Access from:

- 🖥️ Desktop
- 💻 Laptop
- 📱 Phone
- 📲 Tablet
- ☁️ Any device with browser

---

## 🆘 Quick Troubleshoot

**Problem**: No GPU available

- **Fix**: Check runtime type is GPU

**Problem**: Server won't start

- **Fix**: Run all cells 1-9 first

**Problem**: ngrok tunnel fails

- **Fix**: Verify auth token is correct

**Problem**: Video upload fails

- **Fix**: Check format (MP4) and size (<500MB)

**Problem**: Out of memory

- **Fix**: Use 8-layer model or reduce resolution

---

## 📞 Support Resources

🔗 **Official Docs**:

- FastAPI: https://fastapi.tiangolo.com/
- PyTorch: https://pytorch.org/
- OpenCV: https://opencv.org/

🔗 **Colab Help**:

- Google Colab: https://colab.research.google.com/
- Runtime Tips: https://colab.research.google.com/notebooks/

🔗 **ngrok**:

- Setup: https://ngrok.com/
- Dashboard: https://dashboard.ngrok.com/

---

## 💾 Backup Strategy

```
Google Drive Setup:
├── Models/
│   ├── dehazenet_8layers_best.pth
│   └── dehazenet_16layers_best.pth
├── Videos/
│   ├── input_videos/
│   └── processed_videos/
└── Code/
    └── backup_weights.pth
```

---

## 🎓 Learning Path

1. **Basic**: Run Cell 10 → Upload video
2. **Intermediate**: Modify model_layers
3. **Advanced**: Train custom model
4. **Expert**: Deploy own server

---

## 📈 Optimization Tips

| Goal        | Action            |
| ----------- | ----------------- |
| Faster      | Reduce resolution |
| Better      | Use 16-layer      |
| More stable | Batch size = 1    |
| More frames | Lower FPS         |

---

## 🏁 Success Indicators

✅ Cell 10 shows public URL
✅ `/docs` opens in browser
✅ Status endpoint responds
✅ Video uploads without error
✅ Processing starts
✅ Output downloads successfully

**Congratulations!** 🎉 Your system is ready!

---

**Version**: 1.0
**Last Updated**: January 3, 2026
**Status**: Ready to Use ✅
