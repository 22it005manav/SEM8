import torch
import torch.nn as nn

class DeepDehazeNet(nn.Module):
    """
    Encoder-Decoder CNN for Real-time Video Dehazing
    Supports configurable depth (4, 8, 16 layers)
    """
    def __init__(self, num_layers=8):
        super(DeepDehazeNet, self).__init__()
        self.num_layers = num_layers
        
        def conv_block(in_c, out_c):
            return nn.Sequential(
                nn.Conv2d(in_c, out_c, 3, padding=1),
                nn.BatchNorm2d(out_c),
                nn.ReLU(inplace=True),
                nn.Dropout(0.2)
            )
        
        if num_layers == 4:
            # 4-Layer Architecture (Lightweight)
            # Encoder
            self.enc1 = conv_block(3, 64)
            self.pool1 = nn.MaxPool2d(2)
            self.enc2 = conv_block(64, 128)
            self.pool2 = nn.MaxPool2d(2)
            
            # Bottleneck
            self.bottleneck = conv_block(128, 256)
            
            # Decoder
            self.up1 = nn.ConvTranspose2d(256, 128, 2, stride=2)
            self.dec1 = conv_block(256, 128)
            self.up2 = nn.ConvTranspose2d(128, 64, 2, stride=2)
            self.dec2 = conv_block(128, 64)
            
            # Output
            self.final = nn.Conv2d(64, 3, 1)
            
        elif num_layers == 8:
            # 8-Layer Architecture (Balanced)
            # Encoder
            self.enc1 = conv_block(3, 64)
            self.pool1 = nn.MaxPool2d(2)
            self.enc2 = conv_block(64, 128)
            self.pool2 = nn.MaxPool2d(2)
            self.enc3 = conv_block(128, 256)
            self.pool3 = nn.MaxPool2d(2)
            
            # Bottleneck
            self.bottleneck = conv_block(256, 512)
            
            # Decoder
            self.up1 = nn.ConvTranspose2d(512, 256, 2, stride=2)
            self.dec1 = conv_block(512, 256)
            self.up2 = nn.ConvTranspose2d(256, 128, 2, stride=2)
            self.dec2 = conv_block(256, 128)
            self.up3 = nn.ConvTranspose2d(128, 64, 2, stride=2)
            self.dec3 = conv_block(128, 64)
            
            # Output
            self.final = nn.Conv2d(64, 3, 1)
            
        elif num_layers == 16:
            # 16-Layer Architecture (Deep)
            # Encoder
            self.enc1 = conv_block(3, 64)
            self.pool1 = nn.MaxPool2d(2)
            self.enc2 = conv_block(64, 128)
            self.pool2 = nn.MaxPool2d(2)
            self.enc3 = conv_block(128, 256)
            self.pool3 = nn.MaxPool2d(2)
            self.enc4 = conv_block(256, 512)
            self.pool4 = nn.MaxPool2d(2)
            self.enc5 = conv_block(512, 1024)
            self.pool5 = nn.MaxPool2d(2)
            
            # Bottleneck
            self.bottleneck = conv_block(1024, 2048)
            
            # Decoder
            self.up1 = nn.ConvTranspose2d(2048, 1024, 2, stride=2)
            self.dec1 = conv_block(2048, 1024)
            self.up2 = nn.ConvTranspose2d(1024, 512, 2, stride=2)
            self.dec2 = conv_block(1024, 512)
            self.up3 = nn.ConvTranspose2d(512, 256, 2, stride=2)
            self.dec3 = conv_block(512, 256)
            self.up4 = nn.ConvTranspose2d(256, 128, 2, stride=2)
            self.dec4 = conv_block(256, 128)
            self.up5 = nn.ConvTranspose2d(128, 64, 2, stride=2)
            self.dec5 = conv_block(128, 64)
            
            # Output
            self.final = nn.Conv2d(64, 3, 1)
        else:
            raise ValueError(f"Unsupported num_layers: {num_layers}. Choose 4, 8, or 16.")
    
    def forward(self, x):
        if self.num_layers == 4:
            # 4-Layer Forward Pass
            e1 = self.enc1(x)
            e2 = self.enc2(self.pool1(e1))
            b = self.bottleneck(self.pool2(e2))
            
            d1 = self.dec1(torch.cat([self.up1(b), e2], 1))
            d2 = self.dec2(torch.cat([self.up2(d1), e1], 1))
            
            output = torch.sigmoid(self.final(d2))
            
        elif self.num_layers == 8:
            # 8-Layer Forward Pass
            e1 = self.enc1(x)
            e2 = self.enc2(self.pool1(e1))
            e3 = self.enc3(self.pool2(e2))
            b = self.bottleneck(self.pool3(e3))
            
            d1 = self.dec1(torch.cat([self.up1(b), e3], 1))
            d2 = self.dec2(torch.cat([self.up2(d1), e2], 1))
            d3 = self.dec3(torch.cat([self.up3(d2), e1], 1))
            
            output = torch.sigmoid(self.final(d3))
            
        elif self.num_layers == 16:
            # 16-Layer Forward Pass
            e1 = self.enc1(x)
            e2 = self.enc2(self.pool1(e1))
            e3 = self.enc3(self.pool2(e2))
            e4 = self.enc4(self.pool3(e3))
            e5 = self.enc5(self.pool4(e4))
            b = self.bottleneck(self.pool5(e5))
            
            d1 = self.dec1(torch.cat([self.up1(b), e5], 1))
            d2 = self.dec2(torch.cat([self.up2(d1), e4], 1))
            d3 = self.dec3(torch.cat([self.up3(d2), e3], 1))
            d4 = self.dec4(torch.cat([self.up4(d3), e2], 1))
            d5 = self.dec5(torch.cat([self.up5(d4), e1], 1))
            
            output = torch.sigmoid(self.final(d5))
            
        return output