#!/bin/bash
# Setup training environment for LoRA fine-tuning

echo "================================================"
echo "  Setting up LoRA Training Environment"
echo "================================================"
echo

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Install training dependencies
echo
echo "Installing training dependencies..."
pip install -q torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install -q transformers==4.36.0
pip install -q peft==0.7.1
pip install -q datasets==2.16.0
pip install -q accelerate==0.25.0
pip install -q bitsandbytes==0.41.3
pip install -q sentencepiece==0.1.99
pip install -q protobuf==4.25.1

echo
echo "✓ Dependencies installed"

# Check GPU
echo
echo "Checking GPU availability..."
python3 << EOF
import torch
if torch.cuda.is_available():
    gpu_name = torch.cuda.get_device_name(0)
    gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f"✓ GPU detected: {gpu_name}")
    print(f"✓ GPU memory: {gpu_memory:.1f} GB")
else:
    print("⚠️  No GPU detected - training will be slow")
EOF

# Create models directory
echo
echo "Creating models directory..."
mkdir -p ../llm/models/ecommerce-support-lora
echo "✓ Models directory created"

echo
echo "================================================"
echo "  Setup Complete!"
echo "================================================"
echo
echo "To start training:"
echo "  cd ../llm"
echo "  python train_simple.py"
echo
echo "Training will use:"
echo "  • Base model: Mistral-7B-Instruct-v0.2"
echo "  • Method: LoRA (4-bit quantization)"
echo "  • Data: ../data/synthetic/support_dialogs.json"
echo "  • Epochs: 3"
echo "  • Batch size: 4"
echo
echo "Expected time: ~30-60 minutes on GPU"
echo "                ~8-12 hours on CPU (not recommended)"
echo
