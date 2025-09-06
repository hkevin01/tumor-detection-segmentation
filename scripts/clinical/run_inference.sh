#!/bin/bash
# Clinical Inference Script - Generated 2025-09-06T00:13:53.024723

echo "🔬 Starting clinical inference with overlay generation..."

# Activate virtual environment if available
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
fi

# Run inference
python src/inference/inference.py --config config/recipes/unetr_multimodal.json --dataset-config config/datasets/msd_task01_brain.json --model models/unetr/best.pt --output-dir reports/inference_exports --save-overlays --save-prob-maps --class-index 1 --slices auto --tta --amp

echo "✅ Inference completed!"
echo "📁 Check outputs in: reports/inference_exports/"
