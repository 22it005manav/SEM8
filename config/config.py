import os

# ===== DATASET CONFIG =====
DATASET_ROOT = "data/dataset"
TRAIN_HAZY = os.path.join(DATASET_ROOT, "train/hazy")
TRAIN_CLEAR = os.path.join(DATASET_ROOT, "train/clear")
TEST_HAZY = os.path.join(DATASET_ROOT, "test/hazy")
TEST_CLEAR = os.path.join(DATASET_ROOT, "test/clear")

# ===== MODEL CONFIG =====
MODEL_ARCHITECTURE = "DeepDehazeNet"
NUM_LAYERS = 8  # Options: any even number >= 4 (e.g., 4, 8, 16, 24, 32)
                # Note: Deeper models require more VRAM and training data
PRETRAINED_MODEL = "models/pretrained/best_model.pth"

# ===== TRAINING CONFIG =====
BATCH_SIZE = 4
LEARNING_RATE = 1e-4
EPOCHS = 200
EARLY_STOPPING_PATIENCE = 20
IMAGE_SIZE = 256
DEVICE = "cuda"  # or "cpu"

# ===== INFERENCE CONFIG =====
OUTPUT_VIDEO_SIZE = (512, 512)  # (height, width)
FP16_INFERENCE = True  # Enable FP16 for faster inference on GPU
INPUT_VIDEO = "input_video.mp4"
OUTPUT_VIDEO = "results/dehazed_videos/output.mp4"

# ===== METRICS CONFIG =====
PSNR_RANGE = 1.0  # For data_range in PSNR calculation
SSIM_RANGE = 1.0

# ===== PATHS =====
RESULTS_DIR = "results"
MODELS_DIR = "models/pretrained"
METRICS_DIR = os.path.join(RESULTS_DIR, "metrics")
VIDEO_OUTPUT_DIR = os.path.join(RESULTS_DIR, "dehazed_videos")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(METRICS_DIR, exist_ok=True)
os.makedirs(VIDEO_OUTPUT_DIR, exist_ok=True)