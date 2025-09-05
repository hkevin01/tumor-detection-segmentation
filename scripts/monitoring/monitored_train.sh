#!/bin/bash
# Memory-monitored training wrapper

echo "🧠 Starting memory-monitored training..."

# Start monitoring in background
python scripts/monitoring/vscode_crash_monitor.py --action start &
MONITOR_PID=$!

# Cleanup function
cleanup() {
    echo "🛑 Stopping monitoring..."
    kill $MONITOR_PID 2>/dev/null
    # Force garbage collection
    python -c "import gc; gc.collect()"
    # Clear CUDA cache if available
    python -c "try: import torch; torch.cuda.empty_cache(); except: pass"
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Set memory limits
ulimit -v 8388608  # 8GB virtual memory limit

# Set environment variables for memory optimization
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
export CUDA_VISIBLE_DEVICES=0
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

# Run training with memory monitoring
echo "🚀 Starting training..."
python "$@"

# Cleanup
cleanup
