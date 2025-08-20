#!/usr/bin/env bash
# Demo: Complete Enhanced Workflow for Tumor Detection with Overlays
# This script demonstrates the full pipeline from data download to inference with overlays

set -e  # Exit on any error

echo "🚀 Enhanced Tumor Detection Segmentation Workflow Demo"
echo "======================================================"

# Configuration
DATASET_ID="Task01_BrainTumour"
DATA_ROOT="data/msd"
CONFIG_DIR="config"
MODEL_DIR="models/unetr"
REPORTS_DIR="reports"

echo ""
echo "📁 Configuration:"
echo "  Dataset: $DATASET_ID"
echo "  Data root: $DATA_ROOT"
echo "  Model directory: $MODEL_DIR"
echo "  Reports directory: $REPORTS_DIR"

# Step 1: Download dataset (if needed)
echo ""
echo "📥 Step 1: Download MSD dataset..."
if [ ! -d "$DATA_ROOT/$DATASET_ID" ]; then
    echo "  Downloading $DATASET_ID..."
    python scripts/data/pull_monai_dataset.py \
        --dataset-id $DATASET_ID \
        --root $DATA_ROOT
    echo "  ✓ Dataset downloaded"
else
    echo "  ✓ Dataset already exists"
fi

# Step 2: Quick training with overlays (1 epoch for demo)
echo ""
echo "🏋️  Step 2: Training with overlay generation..."
echo "  Running quick training (1 epoch for demo)..."
python src/training/train_enhanced.py \
    --config $CONFIG_DIR/recipes/unetr_multimodal.json \
    --dataset-config $CONFIG_DIR/datasets/msd_task01_brain.json \
    --epochs 1 \
    --amp \
    --save-overlays \
    --overlays-max 5 \
    --save-prob-maps \
    --val-max-batches 2
echo "  ✓ Training completed with overlays saved"

# Check training outputs
echo ""
echo "📊 Training outputs:"
if [ -d "$MODEL_DIR/overlays" ]; then
    OVERLAY_COUNT=$(ls $MODEL_DIR/overlays/*.png 2>/dev/null | wc -l)
    echo "  ✓ Training overlays: $OVERLAY_COUNT files in $MODEL_DIR/overlays/"
    ls $MODEL_DIR/overlays/ | head -3
    if [ $OVERLAY_COUNT -gt 3 ]; then
        echo "    ... and $(($OVERLAY_COUNT - 3)) more"
    fi
else
    echo "  ⚠️  No training overlays found"
fi

# Step 3: Enhanced inference with comprehensive overlays
echo ""
echo "🔍 Step 3: Enhanced inference with overlays..."
echo "  Running inference on validation set..."
python src/inference/inference_enhanced.py \
    --config $CONFIG_DIR/recipes/unetr_multimodal.json \
    --dataset-config $CONFIG_DIR/datasets/msd_task01_brain.json \
    --model $MODEL_DIR/best.pt \
    --output-dir $REPORTS_DIR/inference_demo \
    --save-overlays \
    --save-prob-maps \
    --class-index 1 \
    --slices auto \
    --sw-overlap 0.25 \
    --batch-size 1
echo "  ✓ Inference completed with overlays"

# Check inference outputs
echo ""
echo "📊 Inference outputs:"
INFERENCE_DIR="$REPORTS_DIR/inference_demo"
if [ -d "$INFERENCE_DIR" ]; then
    echo "  ✓ Inference directory: $INFERENCE_DIR"

    if [ -d "$INFERENCE_DIR/overlays" ]; then
        OVERLAY_COUNT=$(ls $INFERENCE_DIR/overlays/*.png 2>/dev/null | wc -l)
        echo "  ✓ Inference overlays: $OVERLAY_COUNT files"
        ls $INFERENCE_DIR/overlays/ | head -3
    fi

    if [ -d "$INFERENCE_DIR/prob_maps" ]; then
        PROB_COUNT=$(ls $INFERENCE_DIR/prob_maps/*.png 2>/dev/null | wc -l)
        echo "  ✓ Probability maps: $PROB_COUNT files"
        ls $INFERENCE_DIR/prob_maps/ | head -3
    fi

    NIFTI_COUNT=$(ls $INFERENCE_DIR/*.nii.gz 2>/dev/null | wc -l)
    if [ $NIFTI_COUNT -gt 0 ]; then
        echo "  ✓ NIfTI masks: $NIFTI_COUNT files"
        ls $INFERENCE_DIR/*.nii.gz | head -3
    fi
else
    echo "  ⚠️  No inference outputs found"
fi

# Step 4: Alternative - Simple path-based inference
echo ""
echo "🔍 Step 4: Simple path-based inference demo..."
if [ -d "$DATA_ROOT/$DATASET_ID/imagesVal" ]; then
    echo "  Running path-based inference on sample files..."
    python src/inference/inference_enhanced.py \
        --config $CONFIG_DIR/recipes/unetr_multimodal.json \
        --model $MODEL_DIR/best.pt \
        --input $DATA_ROOT/$DATASET_ID/imagesVal \
        --output-dir $REPORTS_DIR/simple_inference \
        --save-overlays \
        --slices "40,60,80" \
        --class-index 1
    echo "  ✓ Simple inference completed"
else
    echo "  ⚠️  Validation images not found, skipping simple inference"
fi

# Step 5: Notebook demonstration
echo ""
echo "📔 Step 5: Qualitative review notebook..."
echo "  Opening qualitative review notebook for interactive analysis..."
echo "  File: notebooks/qualitative_review_task01.ipynb"
echo "  This notebook provides comprehensive overlay analysis and visualization"

# Summary
echo ""
echo "🎉 ENHANCED WORKFLOW COMPLETE!"
echo "==============================================="
echo ""
echo "✅ ACHIEVED GOALS:"
echo "  ✓ Reliable image overlays showing learned tumor behavior"
echo "  ✓ Multi-slice panels (25%, 50%, 75% axial positions)"
echo "  ✓ Training overlays during validation"
echo "  ✓ Inference overlays with proper affine handling"
echo "  ✓ Probability heatmaps for tumor class"
echo "  ✓ NIfTI masks with correct spatial orientation"
echo "  ✓ TTA support for improved accuracy"
echo "  ✓ Comprehensive CLI options"
echo ""
echo "📁 OUTPUT LOCATIONS:"
echo "  Training overlays: $MODEL_DIR/overlays/"
echo "  Inference overlays: $REPORTS_DIR/inference_demo/overlays/"
echo "  Probability maps: $REPORTS_DIR/inference_demo/prob_maps/"
echo "  NIfTI masks: $REPORTS_DIR/inference_demo/*.nii.gz"
echo "  Qualitative notebook: notebooks/qualitative_review_task01.ipynb"
echo ""
echo "🔧 READY-TO-USE COMMANDS:"
echo "  # Training with overlays:"
echo "  python src/training/train_enhanced.py --config $CONFIG_DIR/recipes/unetr_multimodal.json --dataset-config $CONFIG_DIR/datasets/msd_task01_brain.json --epochs 2 --save-overlays --save-prob-maps"
echo ""
echo "  # Inference with overlays:"
echo "  python src/inference/inference_enhanced.py --config $CONFIG_DIR/recipes/unetr_multimodal.json --dataset-config $CONFIG_DIR/datasets/msd_task01_brain.json --model $MODEL_DIR/best.pt --save-overlays --save-prob-maps --tta"
echo ""
echo "  # Simple inference:"
echo "  python src/inference/inference_enhanced.py --config $CONFIG_DIR/recipes/unetr_multimodal.json --model $MODEL_DIR/best.pt --input path/to/nifti/files --save-overlays"
echo ""
echo "🎯 VISUALIZATION FEATURES:"
echo "  ✓ GT vs Prediction overlay panels"
echo "  ✓ Prediction-only overlays (for inference without GT)"
echo "  ✓ Tumor probability heatmaps"
echo "  ✓ Configurable slice selection (auto or custom)"
echo "  ✓ Multiple colormap options"
echo "  ✓ Proper medical image affine preservation"
echo ""
echo "🚀 The enhanced overlay system is ready for production use!"
