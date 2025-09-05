#!/bin/bash
#
# VSCode Crash Prevention - Complete Solution
#

echo "=== VSCode Crash Prevention System ==="
echo "🛡️  Complete solution for stable medical imaging training"
echo ""

SCRIPT_DIR="/home/kevin/Projects/tumor-detection-segmentation/scripts/training"

# Function to show current system status
show_status() {
    echo "📊 Current System Status:"

    MEMORY_PERCENT=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')
    MEMORY_AVAIL_GB=$(free -g | grep Mem | awk '{print $7}')
    CPU_PERCENT=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)

    echo "   Memory: ${MEMORY_PERCENT}% used (${MEMORY_AVAIL_GB}GB available)"
    echo "   CPU: ${CPU_PERCENT}% used"

    # Determine safety level
    if (( $(echo "$MEMORY_PERCENT < 60.0" | bc -l) )) && (( $(echo "$CPU_PERCENT < 60.0" | bc -l) )); then
        echo "   Status: 🟢 Excellent - Safe for full training"
        return 0
    elif (( $(echo "$MEMORY_PERCENT < 70.0" | bc -l) )) && (( $(echo "$CPU_PERCENT < 75.0" | bc -l) )); then
        echo "   Status: 🟡 Good - Safe for conservative training"
        return 1
    elif (( MEMORY_AVAIL_GB > 3 )); then
        echo "   Status: 🟠 Caution - Only ultra-light training recommended"
        return 2
    else
        echo "   Status: 🔴 Critical - Training not recommended"
        return 3
    fi
}

# Function to show menu
show_menu() {
    echo ""
    echo "🔧 Available Actions:"
    echo ""
    echo "1. 🧹 Clean up resources (free memory)"
    echo "2. 🪶 Run ultra-light training (1 epoch, minimal resources)"
    echo "3. ⚖️  Run conservative training (2-3 epochs, safe limits)"
    echo "4. 🚀 Run normal training (5+ epochs, monitor required)"
    echo "5. 📊 Check system resources only"
    echo "6. ❓ Show help and tips"
    echo "7. 🚪 Exit"
    echo ""
}

# Function to run cleanup
run_cleanup() {
    echo "🧹 Running resource cleanup..."
    "$SCRIPT_DIR/cleanup_resources.sh"
    echo ""
    echo "Press Enter to continue..."
    read -r
}

# Function to run ultra-light training
run_ultra_light() {
    echo "🪶 Running ultra-light training..."
    "$SCRIPT_DIR/ultra_light_training.sh"
    echo ""
    echo "Press Enter to continue..."
    read -r
}

# Function to run conservative training
run_conservative() {
    echo "⚖️  Running conservative training..."
    echo "💡 This will use 2 epochs with safe resource limits"
    echo ""
    "$SCRIPT_DIR/vscode_safe_training.sh" 2 1
    echo ""
    echo "Press Enter to continue..."
    read -r
}

# Function to run normal training
run_normal() {
    echo "🚀 Running normal training..."
    echo "⚠️  This requires active monitoring to prevent VSCode crashes"
    echo ""
    echo "Epochs (default 5): "
    read -r epochs
    epochs=${epochs:-5}

    "$SCRIPT_DIR/vscode_safe_training.sh" "$epochs" 2
    echo ""
    echo "Press Enter to continue..."
    read -r
}

# Function to show help
show_help() {
    echo ""
    echo "📖 VSCode Crash Prevention Help"
    echo ""
    echo "🎯 Goal: Train medical imaging models without crashing VSCode"
    echo ""
    echo "📁 Scripts Created:"
    echo "   • cleanup_resources.sh - Frees memory and optimizes system"
    echo "   • ultra_light_training.sh - Minimal training (1 epoch)"
    echo "   • vscode_safe_training.sh - Conservative training with limits"
    echo ""
    echo "🛡️  Protection Methods:"
    echo "   • Resource monitoring and limits"
    echo "   • Lower process priority (nice/ionice)"
    echo "   • Conservative memory management"
    echo "   • Thread limiting to prevent CPU overload"
    echo ""
    echo "🚨 Warning Signs:"
    echo "   • VSCode becomes slow or unresponsive"
    echo "   • System memory > 80%"
    echo "   • High CPU usage (> 90%)"
    echo "   • Swap usage increasing rapidly"
    echo ""
    echo "💡 Best Practices:"
    echo "   1. Always run cleanup first"
    echo "   2. Start with ultra-light mode"
    echo "   3. Monitor system during training"
    echo "   4. Close unnecessary applications"
    echo "   5. Use incremental training (1→2→5 epochs)"
    echo ""
    echo "🔧 Manual Commands:"
    echo "   ./scripts/training/cleanup_resources.sh"
    echo "   ./scripts/training/ultra_light_training.sh"
    echo "   ./scripts/training/vscode_safe_training.sh [epochs] [val_batches]"
    echo ""
    echo "Press Enter to continue..."
    read -r
}

# Main menu loop
main() {
    while true; do
        clear
        echo "=== VSCode Crash Prevention System ==="
        echo "🛡️  Complete solution for stable medical imaging training"

        # Show system status
        show_status
        status_code=$?

        # Recommendation based on status
        case $status_code in
            0)
                echo "💡 Recommendation: Any training mode is safe"
                ;;
            1)
                echo "💡 Recommendation: Use conservative training (option 3)"
                ;;
            2)
                echo "💡 Recommendation: Use ultra-light training only (option 2)"
                ;;
            3)
                echo "💡 Recommendation: Clean up resources first (option 1)"
                ;;
        esac

        show_menu
        echo -n "Choose action (1-7): "
        read -r choice

        case $choice in
            1)
                run_cleanup
                ;;
            2)
                run_ultra_light
                ;;
            3)
                run_conservative
                ;;
            4)
                run_normal
                ;;
            5)
                echo ""
                echo "📊 System resource check only..."
                show_status
                echo ""
                echo "Press Enter to continue..."
                read -r
                ;;
            6)
                show_help
                ;;
            7)
                echo ""
                echo "👋 Goodbye! Your VSCode should remain stable."
                exit 0
                ;;
            *)
                echo ""
                echo "❌ Invalid choice. Please select 1-7."
                echo "Press Enter to continue..."
                read -r
                ;;
        esac
    done
}

# Show help if requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

# Run main menu
main
