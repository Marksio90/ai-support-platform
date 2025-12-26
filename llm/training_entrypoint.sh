#!/bin/bash
# Training entrypoint - runs LoRA fine-tuning if enabled

set -e

echo "================================================"
echo "  AI Support - LoRA Training Service"
echo "================================================"
echo

# Check if training is enabled
if [ "${ENABLE_TRAINING}" != "true" ]; then
    echo "ℹ️  Training is disabled (ENABLE_TRAINING=false)"
    echo "To enable: set ENABLE_TRAINING=true in .env"
    exit 0
fi

# Check for GPU
if ! python3 -c "import torch; assert torch.cuda.is_available()" 2>/dev/null; then
    echo "⚠️  WARNING: No GPU detected!"
    echo "Training requires NVIDIA GPU with CUDA support."
    echo "CPU training is extremely slow (8-12 hours)."
    echo
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting training..."
        exit 0
    fi
fi

# Display GPU info
echo "GPU Information:"
python3 << 'EOF'
import torch
if torch.cuda.is_available():
    print(f"✓ GPU: {torch.cuda.get_device_name(0)}")
    print(f"✓ Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
else:
    print("⚠️  No GPU - training will be slow")
EOF

echo
echo "Training Configuration:"
echo "  • Epochs: ${TRAINING_EPOCHS:-3}"
echo "  • Batch size: ${TRAINING_BATCH_SIZE:-4}"
echo "  • 4-bit quantization: ${TRAINING_USE_4BIT:-true}"
echo "  • Output: /app/models/ecommerce-support-lora"
echo

# Check if model already exists
if [ -d "/app/models/ecommerce-support-lora" ]; then
    echo "ℹ️  Model already exists at /app/models/ecommerce-support-lora"
    echo "Skipping training. Remove the directory to retrain."
    exit 0
fi

echo "Starting training..."
echo

# Run training
python3 train_simple.py \
    --num_epochs ${TRAINING_EPOCHS:-3} \
    --batch_size ${TRAINING_BATCH_SIZE:-4} \
    --use_4bit ${TRAINING_USE_4BIT:-true} \
    --output_dir /app/models/ecommerce-support-lora

echo
echo "================================================"
echo "  Training Complete!"
echo "================================================"
echo
echo "Model saved to: /app/models/ecommerce-support-lora"
echo "To use in production:"
echo "  1. Model is automatically mounted as volume"
echo "  2. Update LLM service to load from /app/models/"
echo "  3. Restart services: docker-compose restart llm-service"
echo
