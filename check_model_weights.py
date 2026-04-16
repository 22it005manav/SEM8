"""
Quick script to check what architecture the weight files actually contain
"""
import torch
from pathlib import Path

MODEL_DIR = Path("models/pretrained")

for weights_file in MODEL_DIR.glob("dehazenet_*.pth"):
    print(f"\n{'='*60}")
    print(f"File: {weights_file.name}")
    print(f"{'='*60}")
    
    try:
        state_dict = torch.load(weights_file, map_location="cpu")
        
        # Count encoder stages
        encoder_keys = [k for k in state_dict.keys() if k.startswith('encoders.') or k.startswith('enc')]
        decoder_keys = [k for k in state_dict.keys() if k.startswith('decoders.') or k.startswith('dec')]
        
        # Get max index
        if encoder_keys:
            if any('encoders.' in k for k in encoder_keys):
                # New format
                max_enc_idx = max(int(k.split('.')[1]) for k in encoder_keys if k.startswith('encoders.'))
                num_encoders = max_enc_idx + 1
            else:
                # Legacy format (enc1, enc2, etc.)
                enc_nums = [int(k[3]) for k in encoder_keys if k.startswith('enc') and k[3].isdigit()]
                num_encoders = max(enc_nums) if enc_nums else 0
            
            # Calculate layers: layers = 2 * (depth + 1), depth = num_encoders
            layers = 2 * (num_encoders + 1)
            
            print(f"Number of encoder stages: {num_encoders}")
            print(f"Implied architecture: {layers} layers")
        
        # Check bottleneck shape to verify
        bottleneck_keys = [k for k in state_dict.keys() if 'bottleneck' in k and 'weight' in k]
        if bottleneck_keys:
            shape = state_dict[bottleneck_keys[0]].shape
            print(f"Bottleneck shape: {shape}")
        
        print(f"Total parameters: {len(state_dict)}")
        
    except Exception as e:
        print(f"Error loading: {e}")
