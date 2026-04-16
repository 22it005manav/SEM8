"""
DeepDehazeNet Model Architecture
Supports variable-depth U-Net architecture for image/video dehazing
Now supports any even number of layers (4, 8, 16, 24, 32, etc.)
"""

import torch
import torch.nn as nn


class DeepDehazeNet(nn.Module):
    """
    DeepDehazeNet: Flexible U-Net style encoder-decoder architecture for dehazing
    
    Args:
        layers (int): Number of layers (must be even, e.g., 4, 8, 16, 24, 32)
    """
    
    def __init__(self, layers=8, num_layers=None):
        """Initialize model with dynamic depth

        Args:
            layers (int): Number of layers (must be even number >= 4)
            num_layers (int, optional): Alias for layers (kept for backward compatibility)
        """
        super(DeepDehazeNet, self).__init__()

        # Backward-compatible alias so both layers and num_layers work
        if num_layers is not None:
            layers = num_layers
        
        # Validate layer count
        if layers < 4 or layers % 2 != 0:
            raise ValueError(f"Layer count must be an even number >= 4, got {layers}")
        
        self.layers = layers
        
        # Calculate depth (number of downsampling stages)
        # layers = 2 * (depth + 1), so depth = layers/2 - 1
        depth = layers // 2 - 1
        
        def conv_block(in_c, out_c):
            return nn.Sequential(
                nn.Conv2d(in_c, out_c, 3, padding=1),
                nn.BatchNorm2d(out_c),
                nn.ReLU(inplace=True),
                nn.Dropout(0.2)
            )
        
        # Calculate channel progression
        # Start at 64, double each stage, cap at 2048
        base_channels = 64
        max_channels = 2048
        
        channels = [min(base_channels * (2 ** i), max_channels) for i in range(depth + 2)]
        
        # Build encoder stages dynamically
        self.encoders = nn.ModuleList()
        self.pools = nn.ModuleList()
        
        in_channels = 3
        for i in range(depth):
            self.encoders.append(conv_block(in_channels, channels[i]))
            self.pools.append(nn.MaxPool2d(2))
            in_channels = channels[i]
        
        # Bottleneck
        self.bottleneck = conv_block(channels[depth - 1], channels[depth])
        
        # Build decoder stages dynamically
        self.upsamples = nn.ModuleList()
        self.decoders = nn.ModuleList()
        
        for i in range(depth):
            idx = depth - i - 1
            self.upsamples.append(
                nn.ConvTranspose2d(channels[depth - i], channels[idx], 2, stride=2)
            )
            # Decoder input = upsampled + skip connection (2x channels)
            self.decoders.append(conv_block(channels[idx] * 2, channels[idx]))
        
        # Final 1x1 convolution to output RGB
        self.final = nn.Conv2d(channels[0], 3, 1)
        
        self.depth = depth
        self.channels = channels
        
        print(f"✅ Built DeepDehazeNet with {layers} layers (depth={depth})")
        print(f"   Channel progression: {channels}")
    
    def forward(self, x):
        """Forward pass with dynamic U-Net architecture"""
        
        # Encoder pass - store skip connections
        skip_connections = []
        
        for encoder, pool in zip(self.encoders, self.pools):
            x = encoder(x)
            skip_connections.append(x)
            x = pool(x)
        
        # Bottleneck
        x = self.bottleneck(x)
        
        # Decoder pass - use skip connections in reverse
        for i, (upsample, decoder) in enumerate(zip(self.upsamples, self.decoders)):
            x = upsample(x)
            skip = skip_connections[-(i + 1)]  # Get skip connection in reverse order
            
            # Handle potential size mismatch due to odd dimensions
            if x.size() != skip.size():
                x = self._center_crop_or_pad(x, skip.size())
            
            x = torch.cat([x, skip], dim=1)
            x = decoder(x)
        
        # Final output
        return torch.sigmoid(self.final(x))
    
    def _center_crop_or_pad(self, tensor, target_size):
        """Center crop or pad tensor to match target size"""
        _, _, h, w = tensor.size()
        _, _, target_h, target_w = target_size
        
        if h > target_h:
            start_h = (h - target_h) // 2
            tensor = tensor[:, :, start_h:start_h + target_h, :]
        elif h < target_h:
            pad_h = target_h - h
            tensor = nn.functional.pad(tensor, (0, 0, pad_h // 2, pad_h - pad_h // 2))
        
        if w > target_w:
            start_w = (w - target_w) // 2
            tensor = tensor[:, :, :, start_w:start_w + target_w]
        elif w < target_w:
            pad_w = target_w - w
            tensor = nn.functional.pad(tensor, (pad_w // 2, pad_w - pad_w // 2, 0, 0))
        
        return tensor
    
    def _convert_legacy_checkpoint(self, state_dict):
        """Convert old hard-coded architecture checkpoint to new dynamic format"""
        old_keys = list(state_dict.keys())
        
        # Check if this is an old checkpoint (has enc1, enc2, etc.)
        if not any(k.startswith('encoders.') for k in old_keys) and any(k.startswith('enc') for k in old_keys):
            print("🔄 Converting legacy checkpoint to new format...")
            new_state_dict = {}
            
            # Mapping from old names to new ModuleList indices
            enc_mapping = {
                'enc1': 0, 'enc2': 1, 'enc3': 2, 'enc4': 3, 'enc5': 4, 'enc6': 5, 'enc7': 6
            }
            dec_mapping = {
                'dec1': 0, 'dec2': 1, 'dec3': 2, 'dec4': 3, 'dec5': 4, 'dec6': 5, 'dec7': 6
            }
            up_mapping = {
                'up1': 0, 'up2': 1, 'up3': 2, 'up4': 3, 'up5': 4, 'up6': 5, 'up7': 6
            }
            
            for key, value in state_dict.items():
                new_key = key
                
                # Convert encoder keys
                for old_enc, idx in enc_mapping.items():
                    if key.startswith(old_enc + '.'):
                        new_key = key.replace(old_enc + '.', f'encoders.{idx}.')
                        break
                
                # Convert pool keys
                if key.startswith('pool'):
                    pool_num = key[4]  # 'pool1' -> '1'
                    idx = int(pool_num) - 1
                    new_key = key.replace(f'pool{pool_num}.', f'pools.{idx}.')
                
                # Convert decoder keys
                for old_dec, idx in dec_mapping.items():
                    if key.startswith(old_dec + '.'):
                        new_key = key.replace(old_dec + '.', f'decoders.{idx}.')
                        break
                
                # Convert upsample keys
                for old_up, idx in up_mapping.items():
                    if key.startswith(old_up + '.'):
                        new_key = key.replace(old_up + '.', f'upsamples.{idx}.')
                        break
                
                new_state_dict[new_key] = value
            
            print(f"✅ Converted {len(new_state_dict)} weights from legacy format")
            return new_state_dict
        
        return state_dict

