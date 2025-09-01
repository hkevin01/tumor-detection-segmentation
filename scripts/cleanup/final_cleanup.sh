#!/bin/bash
# Final cleanup script for root directory organization
# This script moves all remaining files from root to appropriate subdirectories

set -e

echo "Starting final cleanup of root directory..."

# Create necessary directories
mkdir -p scripts/cleanup
mkdir -p scripts/utilities
mkdir -p scripts/demo
mkdir -p scripts/docker
mkdir -p scripts/setup
mkdir -p docs/setup
mkdir -p docs/status
mkdir -p docs/project
mkdir -p tests/utilities
mkdir -p tests/validation
mkdir -p tests/docker
mkdir -p tests/frameworks
mkdir -p tests/inference
mkdir -p tests/visualization
mkdir -p tests/integration
mkdir -p tests/unit

echo "Moving script files..."

# Move cleanup scripts
mv cleanup_root.sh scripts/cleanup/ 2>/dev/null || true
mv cleanup_root_organized.sh scripts/cleanup/ 2>/dev/null || true

# Move utility scripts
mv commands.sh scripts/utilities/ 2>/dev/null || true
mv move_files.sh scripts/setup/ 2>/dev/null || true
mv organize_root.sh scripts/setup/ 2>/dev/null || true
mv scripts.sh scripts/setup/ 2>/dev/null || true
mv setup_fixed.sh scripts/setup/ 2>/dev/null || true
mv verify_monai_venv.sh scripts/setup/ 2>/dev/null || true

# Move demo scripts
mv demo_complete_workflow.sh scripts/demo/ 2>/dev/null || true
mv demo_enhanced_workflow.sh scripts/demo/ 2>/dev/null || true

# Move docker scripts
mv docker-entrypoint.sh scripts/docker/ 2>/dev/null || true
mv docker-manager.sh scripts/docker/ 2>/dev/null || true

echo "Moving documentation files..."

# Move setup documentation
mv DOCKER_SETUP.md docs/setup/ 2>/dev/null || true
mv INSTALLATION_FIX.md docs/setup/ 2>/dev/null || true

# Move status documentation
mv DOCKER_COMPLETE.md docs/status/ 2>/dev/null || true
mv DOCKER_GUIDE.md docs/status/ 2>/dev/null || true
mv TRANSITION_COMPLETE.md docs/status/ 2>/dev/null || true
mv MONAI_IMPLEMENTATION_STATUS.md docs/status/ 2>/dev/null || true
mv VERIFICATION_STATUS.md docs/status/ 2>/dev/null || true
mv VERIFICATION_SUCCESS.md docs/status/ 2>/dev/null || true
mv SWIG_WARNING_SUPPRESSION.md docs/status/ 2>/dev/null || true
mv ENHANCED_TRAINING_SUMMARY.md docs/status/ 2>/dev/null || true
mv IMPLEMENTATION_COMPLETE.md docs/status/ 2>/dev/null || true
mv MONAI_TESTS_COMPLETE.md docs/status/ 2>/dev/null || true
mv PHASE_3_SUMMARY.md docs/status/ 2>/dev/null || true
mv ROOT_ORGANIZATION_COMPLETE.md docs/status/ 2>/dev/null || true

# Move project documentation
mv DEPLOYMENT.md docs/project/ 2>/dev/null || true

echo "Moving test files..."

# Move utility test files
mv debug_datalist.py tests/utilities/ 2>/dev/null || true
mv diagnose_tests.py tests/utilities/ 2>/dev/null || true
mv run_tests.py tests/utilities/ 2>/dev/null || true

# Move validation test files
mv validate_docker.py tests/validation/ 2>/dev/null || true
mv validate_monai_integration.py tests/validation/ 2>/dev/null || true
mv validate_prompt_pack.py tests/validation/ 2>/dev/null || true
mv verify_monai_checklist.py tests/validation/ 2>/dev/null || true

# Move docker test files
mv test_docker.sh tests/docker/ 2>/dev/null || true

# Move framework test files
mv test_detectron2_enhanced.py tests/frameworks/ 2>/dev/null || true
mv test_detectron2_structure.py tests/frameworks/ 2>/dev/null || true
mv test_monai_imports.py tests/frameworks/ 2>/dev/null || true
mv test_hybrid_framework.py tests/frameworks/ 2>/dev/null || true

# Move inference test files
mv test_enhanced_inference.py tests/inference/ 2>/dev/null || true
mv test_overlay_quality.py tests/inference/ 2>/dev/null || true

# Move integration test files
mv test_overlay_system.py tests/integration/ 2>/dev/null || true
mv test_system.py tests/integration/ 2>/dev/null || true

# Move unit test files
mv test_imports.py tests/unit/ 2>/dev/null || true
mv test_imports_quick.py tests/unit/ 2>/dev/null || true
mv test_warnings.py tests/unit/ 2>/dev/null || true

# Move visualization test files
mv test_viz_system.py tests/visualization/ 2>/dev/null || true

echo "Final cleanup complete!"
echo "All files have been moved to appropriate subdirectories."
echo ""
echo "Summary of organization:"
echo "- Scripts: scripts/ with subdirectories (cleanup, utilities, demo, docker, setup)"
echo "- Documentation: docs/ with subdirectories (setup, status, project)"
echo "- Tests: tests/ with subdirectories (utilities, validation, docker, frameworks, inference, integration, unit, visualization)"
echo ""
echo "Root directory is now clean and organized!"
