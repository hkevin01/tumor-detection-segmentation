#!/bin/bash
# Clinical Training Script - Generated 2025-09-06T00:13:50.518290
# Hardware: CPU only: Minimal configuration

echo "🚀 Starting clinical training with MLflow tracking..."
echo "Hardware config: CPU only: Minimal configuration"

# Activate virtual environment if available
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
fi

# Set MLflow tracking URI
export MLFLOW_TRACKING_URI=http://localhost:5001

# Run training
python src/training/train_enhanced.py --config config/recipes/unetr_multimodal.json --dataset-config config/datasets/msd_task01_brain.json --epochs 50 --sw-overlap 0.25 --save-overlays --overlays-max 5 --tags dataset=Task01_BrainTumour,model=UNETR,roi=64x64x64,cache=smart,tta=false --experiment-name msd-task01-unetr-mm --run-name baseline-v1

echo "✅ Training completed!"
echo "📊 View results at: http://localhost:5001"
