#!/bin/bash
# Clinical Data Inference Script - Generated 2025-09-06T00:13:54.227477

echo "🏥 Running inference on clinical data..."

# Check for clinical data
if [ ! -d "data/clinical_inbox" ] || [ -z "$(ls -A data/clinical_inbox)" ]; then
    echo "⚠️  No clinical data found in data/clinical_inbox/"
    echo "💡 Place clinical MRI/CT data there first"
    exit 1
fi

# Activate virtual environment if available
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
fi

# Run clinical inference
python src/inference/inference.py --config config/recipes/unetr_multimodal.json --model models/unetr/best.pt --input data/clinical_inbox/ --output-dir reports/clinical_exports --save-overlays --slices 40,60,80 --class-index 1

echo "✅ Clinical inference completed!"
echo "📁 Check outputs in: reports/clinical_exports/"
