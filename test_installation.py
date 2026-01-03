import sys

def test_imports():
    """Test if all critical packages are installed correctly"""
    
    print("=" * 60)
    print("Testing Package Imports...")
    print("=" * 60)
    
    tests = []
    
    # Test PyTorch
    try:
        import torch
        print(f"✅ PyTorch {torch.__version__}")
        print(f"   CUDA Available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"   CUDA Device: {torch.cuda.get_device_name(0)}")
        tests.append(("PyTorch", True))
    except Exception as e:
        print(f"❌ PyTorch: {e}")
        tests.append(("PyTorch", False))
    
    # Test TorchVision
    try:
        import torchvision
        print(f"✅ TorchVision {torchvision.__version__}")
        tests.append(("TorchVision", True))
    except Exception as e:
        print(f"❌ TorchVision: {e}")
        tests.append(("TorchVision", False))
    
    # Test FastAPI
    try:
        import fastapi
        print(f"✅ FastAPI {fastapi.__version__}")
        tests.append(("FastAPI", True))
    except Exception as e:
        print(f"❌ FastAPI: {e}")
        tests.append(("FastAPI", False))
    
    # Test OpenCV
    try:
        import cv2
        print(f"✅ OpenCV {cv2.__version__}")
        tests.append(("OpenCV", True))
    except Exception as e:
        print(f"❌ OpenCV: {e}")
        tests.append(("OpenCV", False))
    
    # Test NumPy
    try:
        import numpy as np
        print(f"✅ NumPy {np.__version__}")
        tests.append(("NumPy", True))
    except Exception as e:
        print(f"❌ NumPy: {e}")
        tests.append(("NumPy", False))
    
    # Test Pydantic
    try:
        import pydantic
        print(f"✅ Pydantic {pydantic.__version__}")
        tests.append(("Pydantic", True))
    except Exception as e:
        print(f"❌ Pydantic: {e}")
        tests.append(("Pydantic", False))
    
    print("=" * 60)
    
    failed = [name for name, status in tests if not status]
    
    if failed:
        print(f"❌ Failed imports: {', '.join(failed)}")
        return False
    else:
        print("✅ All critical packages installed successfully!")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)