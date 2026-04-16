#!/usr/bin/env python
"""
GPU Setup and Installation Script
This script helps set up GPU acceleration for the Video Dehazing application.
"""
import subprocess
import sys
import os

print("\n" + "=" * 70)
print("GPU Setup for Video Dehazing Application")
print("=" * 70 + "\n")

# Check if CUDA Toolkit is installed
print("Checking CUDA Toolkit installation...")
try:
    result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ CUDA Toolkit detected")
        print(result.stdout)
    else:
        raise Exception("CUDA not found")
except Exception as e:
    print("\n❌ CUDA Toolkit NOT found on system")
    print("\nTo enable GPU acceleration, you need to install CUDA Toolkit 11.8:")
    print("=" * 70)
    print("STEP 1: Download CUDA Toolkit 11.8")
    print("  → https://developer.nvidia.com/cuda-11-8-0-download-archive")
    print("\nSTEP 2: Install CUDA Toolkit")
    print("  Windows: Run the .exe installer and select full installation")
    print("  Linux: Follow the official NVIDIA installation instructions")
    print("\nSTEP 3: Install cuDNN 8.x for CUDA 11.8")
    print("  → https://developer.nvidia.com/cudnn")
    print("\nSTEP 4: Verify Installation")
    print("  Run: nvcc --version")
    print("=" * 70 + "\n")
    
    response = input("Continue with PyTorch GPU installation anyway? (y/n): ")
    if response.lower() != 'y':
        print("Exiting setup.")
        sys.exit(0)

print("\nInstalling GPU-enabled PyTorch and dependencies...")
print("=" * 70 + "\n")

# Install PyTorch with CUDA 11.8
pytorch_cmd = [
    sys.executable, "-m", "pip", "install", "--upgrade",
    "torch==2.2.2", "torchvision==0.17.2", "torchaudio==2.2.2",
    "--index-url", "https://download.pytorch.org/whl/cu118"
]

print("Step 1: Installing PyTorch 2.2.2 with CUDA 11.8...\n")
result = subprocess.run(pytorch_cmd, capture_output=False)
if result.returncode != 0:
    print("\n❌ ERROR: PyTorch installation failed!")
    sys.exit(1)

# Install other dependencies
deps_cmd = [
    sys.executable, "-m", "pip", "install",
    "fastapi==0.115.6", "uvicorn[standard]==0.34.0", "python-multipart==0.0.20",
    "aiofiles==24.1.0", "websockets==14.1", "pydantic==2.10.5",
    "pydantic-settings==2.7.1",
    "opencv-python==4.10.0.84", "Pillow==11.3.0", "numpy<2.0",
    "scipy==1.13.1", "pandas==2.2.3", "tqdm==4.67.1",
    "matplotlib==3.9.4", "scikit-image==0.24.0", "python-dotenv==1.0.1"
]

print("\nStep 2: Installing other dependencies...\n")
result = subprocess.run(deps_cmd, capture_output=False)
if result.returncode != 0:
    print("\n❌ ERROR: Dependency installation failed!")
    sys.exit(1)

print("\n" + "=" * 70)
print("Step 3: Verifying installation...")
print("=" * 70 + "\n")

# Verify installation
verify_code = """
import torch
print(f'✓ PyTorch version: {torch.__version__}')
print(f'✓ CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'✓ CUDA version: {torch.version.cuda}')
    print(f'✓ GPU Device: {torch.cuda.get_device_name(0)}')
    try:
        props = torch.cuda.get_device_properties(0)
        memory = props.total_memory / 1e9
        print(f'✓ GPU Memory: {memory:.2f} GB')
    except:
        pass
    print('\\n✅ GPU is ready for use!')
else:
    print('\\n⚠️  CUDA is not available. Make sure:')
    print('   1. CUDA Toolkit 11.8 is installed')
    print('   2. cuDNN 8.x is installed')
    print('   3. System is restarted after installation')
"""

result = subprocess.run([sys.executable, "-c", verify_code], capture_output=False)

print("\n" + "=" * 70)
if result.returncode == 0:
    print("✅ Installation completed successfully!")
else:
    print("⚠️  Installation completed with warnings. Check output above.")
print("=" * 70 + "\n")

print("Next steps:")
print("1. Restart your terminal/application")
print("2. Run the application: python app.py")
print("3. Check the web interface at http://localhost:8000")
print("   GPU option should now be available if CUDA Toolkit is installed\n")

