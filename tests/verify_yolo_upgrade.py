
import os
import sys
import torch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jarvis.core.vision.yolo_detector import YOLODetector

def verify_upgrade():
    print("Verifying YOLO Model Upgrade...")
    
    # Check if CUDA is available
    cuda_available = torch.cuda.is_available()
    print(f"CUDA Available: {cuda_available}")
    
    detector = YOLODetector()
    print(f"Target Model: {detector.model_name}")
    
    # Force load
    detector._load_model()
    
    if detector.model:
        print(f"Model loaded successfully on {next(detector.model.parameters()).device}")
        
        # Check model size/parameters count
        params = sum(p.numel() for p in detector.model.parameters())
        print(f"Total Parameters: {params:,}")
        
        # yolo11x should have much more params than yolo11m (~20m vs ~50m+)
        if params > 50_000_000:
            print("CONFIRMED: Using Extra Large (x) model.")
        else:
            print("WARNING: Model seems smaller than expected for 'x' series.")
    else:
        print("CRITICAL: Model failed to load.")

if __name__ == "__main__":
    verify_upgrade()
