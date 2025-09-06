#!/bin/bash
# Clinical Integration Deployment Script
# =====================================
#
# Single copy-paste operator prompt for clinical integration and real dataset training.
# Implements the full workflow as specified in the clinical operator prompt.
#
# Author: Tumor Detection Segmentation Team
# Phase: Clinical Production Deployment

set -e  # Exit on any error

echo "🏥 CLINICAL INTEGRATION + REAL DATASET TRAINING"
echo "==============================================="
echo "Goal: Stand up full stack for clinical workflows"
echo "Dataset: MSD Task01 (brain) as clinical MRI surrogate"
echo "Features: UNETR training, MLflow tracking, overlays, monitoring"
echo ""

# Configuration variables
export PROJECT_ROOT=$(pwd)
export MLFLOW_TRACKING_URI="http://localhost:5001"
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Hardware detection
detect_gpu_memory() {
    echo "🎮 Detecting GPU configuration..."

    if command -v nvidia-smi &> /dev/null; then
        GPU_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
        GPU_MEMORY_GB=$((GPU_MEMORY / 1024))
        echo "   Detected GPU with ${GPU_MEMORY_GB}GB VRAM"

        if [ $GPU_MEMORY_GB -ge 48 ]; then
            ROI_SIZE="160x160x160"
            BATCH_SIZE=4
            CACHE_MODE="cache"
            CONFIG_DESC="Large GPU (>=48GB): Maximum performance"
        elif [ $GPU_MEMORY_GB -ge 16 ]; then
            ROI_SIZE="128x128x128"
            BATCH_SIZE=2
            CACHE_MODE="smart"
            CONFIG_DESC="Medium GPU (16-24GB): Balanced performance"
        elif [ $GPU_MEMORY_GB -ge 8 ]; then
            ROI_SIZE="96x96x96"
            BATCH_SIZE=1
            CACHE_MODE="smart"
            CONFIG_DESC="Small GPU (8-12GB): Memory optimized"
        else
            ROI_SIZE="64x64x64"
            BATCH_SIZE=1
            CACHE_MODE="smart"
            CONFIG_DESC="CPU only: Minimal configuration"
        fi
    else
        echo "   No GPU detected, using CPU configuration"
        ROI_SIZE="64x64x64"
        BATCH_SIZE=1
        CACHE_MODE="smart"
        CONFIG_DESC="CPU only: Minimal configuration"
        GPU_MEMORY_GB=0
    fi

    echo "   Configuration: $CONFIG_DESC"
    echo "   ROI: $ROI_SIZE, Batch: $BATCH_SIZE, Cache: $CACHE_MODE"
    echo ""
}

# Execute the clinical operator workflow
main() {
    echo "🚀 Starting Clinical Operator Workflow"
    echo "======================================="
    echo "Timestamp: $(date -Iseconds)"
    echo ""

    # Detect hardware configuration
    detect_gpu_memory

    # Check if clinical operator exists
    if [ ! -f "scripts/clinical/clinical_operator.py" ]; then
        echo "❌ Clinical operator not found: scripts/clinical/clinical_operator.py"
        echo "💡 Run the clinical_operator.py script first to create the full workflow"
        exit 1
    fi

    echo "🏥 Executing comprehensive clinical operator workflow..."
    echo "   This includes all 9 steps: bootstrap → documentation/sign-off"
    echo ""

    # Activate virtual environment if available
    if [ -d ".venv" ]; then
        source .venv/bin/activate
        echo "✅ Virtual environment activated"
    elif [ -d "venv" ]; then
        source venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "⚠️ No virtual environment found, using system Python"
    fi

    # Run the clinical operator
    python scripts/clinical/clinical_operator.py \
        --gpu-memory $GPU_MEMORY_GB \
        --data-modality mri

    # Final summary
    echo ""
    echo "🎉 CLINICAL OPERATOR DEPLOYMENT COMPLETE!"
    echo "========================================"
    echo ""
    echo "🚀 NEXT STEPS:"
    echo "1. Review generated scripts in scripts/clinical/"
    echo "2. Start training: ./scripts/clinical/start_training.sh"
    echo "3. Monitor at: http://localhost:5001 (MLflow)"
    echo "4. Run inference: ./scripts/clinical/run_inference.sh"
    echo "5. Add clinical data to: data/clinical_inbox/"
    echo "6. Process clinical data: ./scripts/clinical/run_clinical_inference.sh"
    echo ""
    echo "📊 Configuration Summary:"
    echo "   Hardware: $CONFIG_DESC"
    echo "   ROI Size: $ROI_SIZE"
    echo "   Batch Size: $BATCH_SIZE"
    echo "   Cache Mode: $CACHE_MODE"
    echo "   GPU Memory: ${GPU_MEMORY_GB}GB"
    echo ""
    echo "🏥 Platform ready for clinical integration!"
}

# Execute main function
main "$@"
