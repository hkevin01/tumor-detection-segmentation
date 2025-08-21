#!/bin/bash
# Quick command reference for the overlay visualization system

echo "🎯 OVERLAY VISUALIZATION SYSTEM - QUICK COMMANDS"
echo "=================================================="
echo

echo "📊 INFERENCE WITH OVERLAYS (New Images):"
echo "python src/inference/inference.py \\"
echo "  --config config/recipes/unetr_multimodal.json \\"
echo "  --model models/unetr/best.pt \\"
echo "  --input data/new_cases/ \\"
echo "  --output-dir reports/new_inference \\"
echo "  --save-overlays --save-prob-maps --slices auto --class-index 1"
echo

echo "🏃 TRAINING WITH OVERLAYS:"
echo "python src/training/train_enhanced.py \\"
echo "  --config config/recipes/unetr_multimodal.json \\"
echo "  --dataset-config config/datasets/msd_task01_brain.json \\"
echo "  --epochs 2 --amp --save-overlays --overlays-max 5 --slices auto"
echo

echo "🧪 TESTING:"
echo "# Unit tests:"
echo "python -m pytest tests/unit/test_visualization_panels.py -v"
echo
echo "# Integration tests:"
echo "python -m pytest tests/integration/test_inference_cli_smoke.py -v"
echo

echo "📝 INTERACTIVE ANALYSIS:"
echo "jupyter notebook notebooks/qualitative_review_task01.ipynb"
echo

echo "✅ System ready for: insert new images → run detection → save labeled overlays and masks"
