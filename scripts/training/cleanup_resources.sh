#!/bin/bash
#
# VSCode Resource Cleanup and Memory Optimization
#

echo "=== VSCode Resource Cleanup ==="

# Function to clean Python caches
clean_python_caches() {
    echo "🧹 Cleaning Python caches..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "*.pyo" -delete 2>/dev/null || true
    echo "   Python caches cleaned"
}

# Function to clean temporary files
clean_temp_files() {
    echo "🧹 Cleaning temporary files..."

    # Clean logs older than 1 day
    find logs/ -name "*.log" -mtime +1 -delete 2>/dev/null || true

    # Clean temporary outputs
    rm -rf temp/training_* 2>/dev/null || true
    rm -rf /tmp/pytorch_* 2>/dev/null || true

    echo "   Temporary files cleaned"
}

# Function to optimize memory
optimize_memory() {
    echo "🧹 Optimizing system memory..."

    # Drop caches (requires sudo)
    if command -v sync >/dev/null 2>&1; then
        sync
        echo "   File system synced"
    fi

    # Clear swap if possible
    if [ -w /proc/sys/vm/drop_caches ]; then
        echo 1 > /proc/sys/vm/drop_caches 2>/dev/null || true
        echo "   Memory caches dropped"
    fi

    echo "   Memory optimization complete"
}

# Function to show current resources
show_resources() {
    echo ""
    echo "📊 Current System Resources:"

    # Memory
    MEMORY_PERCENT=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')
    MEMORY_AVAIL_GB=$(free -g | grep Mem | awk '{print $7}')
    echo "   Memory: ${MEMORY_PERCENT}% used (${MEMORY_AVAIL_GB}GB available)"

    # CPU (simple check)
    CPU_PERCENT=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    echo "   CPU: ${CPU_PERCENT}% used"

    # Check if now safe
    if (( $(echo "$MEMORY_PERCENT < 65.0" | bc -l) )) && (( $(echo "$CPU_PERCENT < 70.0" | bc -l) )) && (( MEMORY_AVAIL_GB > 4 )); then
        echo "   Status: ✅ Safe for training"
        return 0
    else
        echo "   Status: ⚠️  Still high usage"
        return 1
    fi
}

# Main cleanup
main() {
    cd "/home/kevin/Projects/tumor-detection-segmentation"

    clean_python_caches
    clean_temp_files
    optimize_memory

    echo ""
    echo "🎉 Cleanup complete!"

    show_resources

    if [ $? -eq 0 ]; then
        echo ""
        echo "💡 System is now ready for safe training"
        echo "   Run: ./scripts/training/vscode_safe_training.sh"
    else
        echo ""
        echo "💡 If still showing high usage:"
        echo "   - Close browser tabs"
        echo "   - Close other applications"
        echo "   - Wait a few minutes and try again"
    fi
}

main "$@"
