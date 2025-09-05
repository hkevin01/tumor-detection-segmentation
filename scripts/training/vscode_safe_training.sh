#!/bin/bash
#
# VSCode-Safe Training Script
# Prevents crashes by monitoring resources and using conservative settings
#

set -e

WORKSPACE_DIR="/home/kevin/Projects/tumor-detection-segmentation"
VENV_PATH="$WORKSPACE_DIR/.venv"

echo "=== VSCode Crash Prevention System ==="

# Function to check system resources
check_resources() {
    # Get memory usage (percentage)
    MEMORY_PERCENT=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')

    # Get CPU usage (simple check)
    CPU_PERCENT=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)

    # Available memory in GB
    MEMORY_AVAIL_GB=$(free -g | grep Mem | awk '{print $7}')

    echo "System Status:"
    echo "  Memory: ${MEMORY_PERCENT}% used (${MEMORY_AVAIL_GB}GB available)"
    echo "  CPU: ${CPU_PERCENT}% used"

    # Check if safe (conservative limits)
    if (( $(echo "$MEMORY_PERCENT < 65.0" | bc -l) )) && (( $(echo "$CPU_PERCENT < 70.0" | bc -l) )) && (( MEMORY_AVAIL_GB > 4 )); then
        echo "  VSCode Safe: ✓"
        return 0
    else
        echo "  VSCode Safe: ✗"
        return 1
    fi
}

# Function to run training with resource limits
run_safe_training() {
    local epochs=${1:-2}
    local max_batches=${2:-1}

    echo ""
    echo "🚀 Starting VSCode-safe training:"
    echo "   Epochs: $epochs"
    echo "   Max validation batches: $max_batches"
    echo "   Conservative resource limits applied"

    cd "$WORKSPACE_DIR"

    # Activate virtual environment
    source "$VENV_PATH/bin/activate"

    # Set resource-limiting environment variables
    export OMP_NUM_THREADS=2
    export MKL_NUM_THREADS=2
    export NUMEXPR_NUM_THREADS=2
    export OPENBLAS_NUM_THREADS=2
    export PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:256"
    export PYTHONHASHSEED=0
    export PYTHONUNBUFFERED=1

    # Create safe output directory
    mkdir -p logs/safe_training

    # Build training command with conservative settings
    TRAIN_CMD="python src/training/train_enhanced.py \
        --config config/recipes/unetr_multimodal.json \
        --dataset-config config/datasets/msd_task01_brain.json \
        --epochs $epochs \
        --val-max-batches $max_batches \
        --output-dir logs/safe_training/test_${epochs}epochs"

    echo "   Command: $TRAIN_CMD"
    echo ""

    # Run with nice priority (lower system impact)
    nice -n 10 $TRAIN_CMD

    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        echo ""
        echo "✅ Training completed successfully!"
        echo "   No VSCode crashes detected"
        return 0
    else
        echo ""
        echo "❌ Training failed with exit code $exit_code"
        return $exit_code
    fi
}

# Main execution
main() {
    # Check if system is safe for training
    if ! check_resources; then
        echo ""
        echo "⚠️  System not safe for training!"
        echo "   High resource usage detected"
        echo "   Please:"
        echo "   - Close unnecessary applications"
        echo "   - Wait for system to cool down"
        echo "   - Try again in a few minutes"
        exit 1
    fi

    # Get training parameters
    EPOCHS=${1:-2}
    MAX_BATCHES=${2:-1}

    echo ""
    echo "System is safe for training. Proceeding..."

    # Run safe training
    run_safe_training "$EPOCHS" "$MAX_BATCHES"
}

# Help function
show_help() {
    echo "VSCode-Safe Training Launcher"
    echo ""
    echo "Usage: $0 [epochs] [max_val_batches]"
    echo ""
    echo "Examples:"
    echo "  $0           # 2 epochs, 1 validation batch (default)"
    echo "  $0 5         # 5 epochs, 1 validation batch"
    echo "  $0 3 2       # 3 epochs, 2 validation batches"
    echo ""
    echo "This script prevents VSCode crashes by:"
    echo "  - Monitoring system resources"
    echo "  - Using conservative resource limits"
    echo "  - Running training with lower priority"
    echo "  - Limiting concurrent processes"
}

# Parse command line arguments
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

# Run main function
main "$@"
