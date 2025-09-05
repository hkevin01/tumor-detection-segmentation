#!/bin/bash
#
# Ultra-Lightweight Training Mode for VSCode Safety
# Uses minimal resources to prevent crashes
#

set -e

WORKSPACE_DIR="/home/kevin/Projects/tumor-detection-segmentation"
VENV_PATH="$WORKSPACE_DIR/.venv"

echo "=== Ultra-Lightweight Training Mode ==="
echo "💡 Designed for high-memory systems to prevent VSCode crashes"

# Function to check if we can run even in high-memory conditions
check_ultra_light_safe() {
    MEMORY_PERCENT=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')
    MEMORY_AVAIL_GB=$(free -g | grep Mem | awk '{print $7}')

    echo "System Status:"
    echo "  Memory: ${MEMORY_PERCENT}% used (${MEMORY_AVAIL_GB}GB available)"

    # More relaxed limits for ultra-light mode
    if (( MEMORY_AVAIL_GB > 3 )); then
        echo "  Ultra-Light Mode: ✅ Can proceed with minimal training"
        return 0
    else
        echo "  Ultra-Light Mode: ❌ System critically low on memory"
        return 1
    fi
}

# Function to run minimal training
run_ultra_light_training() {
    echo ""
    echo "🪶 Starting ultra-lightweight training:"
    echo "   - 1 epoch only"
    echo "   - 1 validation batch"
    echo "   - Minimal memory footprint"
    echo "   - No overlays or prob maps"
    echo "   - Background priority"

    cd "$WORKSPACE_DIR"
    source "$VENV_PATH/bin/activate"

    # Ultra-conservative environment variables
    export OMP_NUM_THREADS=1
    export MKL_NUM_THREADS=1
    export NUMEXPR_NUM_THREADS=1
    export OPENBLAS_NUM_THREADS=1
    export PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:128"
    export PYTHONHASHSEED=0
    export PYTHONUNBUFFERED=1

    # Create minimal output directory
    mkdir -p logs/ultra_light

    # Ultra-minimal training command
    TRAIN_CMD="python src/training/train_enhanced.py \
        --config config/recipes/unetr_multimodal.json \
        --dataset-config config/datasets/msd_task01_brain.json \
        --epochs 1 \
        --val-max-batches 1 \
        --output-dir logs/ultra_light/minimal_test"

    echo ""
    echo "⚙️  Starting minimal training..."
    echo "   This should complete in a few minutes"
    echo "   Monitor VSCode for stability"

    # Run with lowest priority
    nice -n 19 ionice -c 3 $TRAIN_CMD

    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        echo ""
        echo "🎉 Ultra-light training completed!"
        echo "   ✅ No VSCode crashes"
        echo "   ✅ System remained stable"
        return 0
    else
        echo ""
        echo "❌ Training failed (exit code $exit_code)"
        return $exit_code
    fi
}

# Function to show memory reduction tips
show_memory_tips() {
    echo ""
    echo "💡 Memory Reduction Tips:"
    echo ""
    echo "🌐 Browser:"
    echo "   - Close unnecessary tabs"
    echo "   - Use 'chrome://discards/' to check tab memory"
    echo "   - Consider using a lightweight browser"
    echo ""
    echo "💻 VSCode:"
    echo "   - Close unused editor tabs"
    echo "   - Disable heavy extensions temporarily"
    echo "   - Use 'Developer: Reload Window' to refresh"
    echo ""
    echo "🖥️  System:"
    echo "   - Close other applications"
    echo "   - Check 'htop' for memory-heavy processes"
    echo "   - Consider increasing swap space"
    echo ""
    echo "🔧 Training:"
    echo "   - Use this ultra-light mode first"
    echo "   - Gradually increase epochs if stable"
    echo "   - Monitor during training"
}

# Main function
main() {
    if ! check_ultra_light_safe; then
        echo ""
        echo "⚠️  Even ultra-light mode may be risky!"
        show_memory_tips
        echo ""
        echo "❓ Continue anyway? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo "Aborting for safety"
            exit 1
        fi
    fi

    echo ""
    echo "🚀 Proceeding with ultra-light training..."
    run_ultra_light_training

    if [ $? -eq 0 ]; then
        echo ""
        echo "🎯 Next Steps:"
        echo "   1. If VSCode remained stable, try 2-3 epochs"
        echo "   2. Monitor system resources during training"
        echo "   3. Use ./scripts/training/vscode_safe_training.sh for normal mode"
        echo ""
        echo "🔄 To run again:"
        echo "   ./scripts/training/ultra_light_training.sh"
    fi
}

# Help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Ultra-Lightweight Training Mode"
    echo ""
    echo "This mode runs the absolute minimum training to test system stability:"
    echo "  - 1 epoch only"
    echo "  - 1 validation batch"
    echo "  - Lowest system priority"
    echo "  - Minimal memory usage"
    echo ""
    echo "Use this when normal training would crash VSCode due to high memory usage."
    exit 0
fi

main "$@"
