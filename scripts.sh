#!/usr/bin/env bash
# Convenience script for accessing organized scripts after root cleanup

print_usage() {
    echo "🧹 Root Cleanup - Quick Access Script"
    echo "====================================="
    echo ""
    echo "Usage: $0 [category] [script]"
    echo ""
    echo "📂 Available categories and scripts:"
    echo ""
    echo "📦 Demo Scripts (scripts/demo/):"
    echo "  $0 demo workflow      - Run complete workflow demo"
    echo "  $0 demo enhanced      - Run enhanced workflow demo"
    echo ""
    echo "🧪 Validation Scripts (scripts/validation/):"
    echo "  $0 validate docker    - Validate Docker setup"
    echo "  $0 validate monai     - Validate MONAI integration"
    echo "  $0 test overlay       - Test overlay quality"
    echo "  $0 test inference     - Test enhanced inference"
    echo "  $0 test system        - Test complete system"
    echo ""
    echo "⚙️ Setup Scripts (scripts/setup/):"
    echo "  $0 setup fixed        - Run fixed setup script"
    echo "  $0 setup cleanup      - Run cleanup script"
    echo ""
    echo "📋 View Documentation:"
    echo "  $0 docs deployment    - View deployment docs"
    echo "  $0 docs status        - View status docs"
    echo "  $0 docs summary       - View cleanup summary"
    echo ""
    echo "🔍 List Scripts:"
    echo "  $0 list demo          - List demo scripts"
    echo "  $0 list validation    - List validation scripts"
    echo "  $0 list setup         - List setup scripts"
    echo "  $0 list all           - List all organized scripts"
}

run_demo() {
    case "$2" in
        "workflow")
            echo "🎬 Running complete workflow demo..."
            bash scripts/demo/demo_complete_workflow.sh
            ;;
        "enhanced")
            echo "🎬 Running enhanced workflow demo..."
            bash scripts/demo/demo_enhanced_workflow.sh
            ;;
        *)
            echo "Available demo scripts:"
            ls -1 scripts/demo/*.sh 2>/dev/null | sed 's|scripts/demo/||' | sed 's|\.sh$||'
            ;;
    esac
}

run_validation() {
    case "$2" in
        "docker")
            echo "🧪 Validating Docker setup..."
            python scripts/validation/validate_docker.py
            ;;
        "monai")
            echo "🧪 Validating MONAI integration..."
            python scripts/validation/validate_monai_integration.py
            ;;
        "overlay")
            echo "🧪 Testing overlay quality..."
            python scripts/validation/test_overlay_quality.py
            ;;
        "inference")
            echo "🧪 Testing enhanced inference..."
            python scripts/validation/test_enhanced_inference.py
            ;;
        "system")
            echo "🧪 Testing complete system..."
            python scripts/validation/test_system.py
            ;;
        *)
            echo "Available validation scripts:"
            ls -1 scripts/validation/ 2>/dev/null | grep -E '\.(py|sh)$'
            ;;
    esac
}

run_setup() {
    case "$2" in
        "fixed")
            echo "⚙️ Running fixed setup..."
            bash scripts/setup/setup_fixed.sh
            ;;
        "cleanup")
            echo "⚙️ Running cleanup..."
            bash scripts/setup/cleanup_root.sh
            ;;
        *)
            echo "Available setup scripts:"
            ls -1 scripts/setup/ 2>/dev/null | grep -E '\.(py|sh)$'
            ;;
    esac
}

view_docs() {
    case "$2" in
        "deployment")
            echo "📦 Deployment documentation:"
            ls -1 docs/deployment/ 2>/dev/null | head -10
            ;;
        "status")
            echo "📊 Status documentation:"
            ls -1 docs/status/ 2>/dev/null | head -10
            ;;
        "summary")
            echo "📋 Viewing cleanup summary..."
            cat docs/status/ROOT_CLEANUP_SUMMARY.md 2>/dev/null || echo "Summary not found"
            ;;
        *)
            echo "Available documentation categories:"
            echo "  deployment - Deployment and Docker docs"
            echo "  status     - Status and verification docs"
            echo "  summary    - Root cleanup summary"
            ;;
    esac
}

list_scripts() {
    case "$2" in
        "demo")
            echo "📦 Demo scripts (scripts/demo/):"
            ls -la scripts/demo/ 2>/dev/null || echo "No demo scripts found"
            ;;
        "validation")
            echo "🧪 Validation scripts (scripts/validation/):"
            ls -la scripts/validation/ 2>/dev/null || echo "No validation scripts found"
            ;;
        "setup")
            echo "⚙️ Setup scripts (scripts/setup/):"
            ls -la scripts/setup/ 2>/dev/null || echo "No setup scripts found"
            ;;
        "all")
            echo "📂 All organized scripts:"
            echo ""
            echo "Demo scripts:"
            ls -1 scripts/demo/ 2>/dev/null | sed 's/^/  /'
            echo ""
            echo "Validation scripts:"
            ls -1 scripts/validation/ 2>/dev/null | sed 's/^/  /'
            echo ""
            echo "Setup scripts:"
            ls -1 scripts/setup/ 2>/dev/null | sed 's/^/  /'
            ;;
        *)
            echo "Specify: demo, validation, setup, or all"
            ;;
    esac
}

# Main script logic
case "$1" in
    "demo")
        run_demo "$@"
        ;;
    "validate")
        run_validation "$@"
        ;;
    "setup")
        run_setup "$@"
        ;;
    "docs")
        view_docs "$@"
        ;;
    "list")
        list_scripts "$@"
        ;;
    "help"|"-h"|"--help"|"")
        print_usage
        ;;
    *)
        echo "Unknown category: $1"
        echo ""
        print_usage
        ;;
esac
