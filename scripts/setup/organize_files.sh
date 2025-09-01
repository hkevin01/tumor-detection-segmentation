#!/bin/bash
# Organize files script
# This script organizes project files

# Create directories if they don't exist
mkdir -p scripts
mkdir -p docs
mkdir -p tests

# Move shell scripts to scripts/
mv cleanup_root.sh scripts/ 2>/dev/null || true
mv cleanup_root_organized.sh scripts/ 2>/dev/null || true
mv commands.sh scripts/ 2>/dev/null || true
mv demo_complete_workflow.sh scripts/ 2>/dev/null || true
mv demo_enhanced_workflow.sh scripts/ 2>/dev/null || true
mv docker-entrypoint.sh scripts/ 2>/dev/null || true
mv docker-manager.sh scripts/ 2>/dev/null || true
mv move_files.sh scripts/ 2>/dev/null || true
mv organize_root.sh scripts/ 2>/dev/null || true
mv run.sh scripts/ 2>/dev/null || true
mv scripts.sh scripts/ 2>/dev/null || true
mv setup_fixed.sh scripts/ 2>/dev/null || true
mv test_docker.sh scripts/ 2>/dev/null || true
mv verify_monai_venv.sh scripts/ 2>/dev/null || true

# Move markdown files to docs/
mv DEPLOYMENT.md docs/ 2>/dev/null || true
mv DOCKER_COMPLETE.md docs/ 2>/dev/null || true
mv DOCKER_GUIDE.md docs/ 2>/dev/null || true
mv DOCKER_SETUP.md docs/ 2>/dev/null || true
mv ENHANCED_TRAINING_SUMMARY.md docs/ 2>/dev/null || true
mv IMPLEMENTATION_COMPLETE.md docs/ 2>/dev/null || true
mv INSTALLATION_FIX.md docs/ 2>/dev/null || true
mv MONAI_IMPLEMENTATION_STATUS.md docs/ 2>/dev/null || true
mv MONAI_TESTS_COMPLETE.md docs/ 2>/dev/null || true
mv PHASE_3_SUMMARY.md docs/ 2>/dev/null || true
mv ROOT_ORGANIZATION_COMPLETE.md docs/ 2>/dev/null || true
mv SWIG_WARNING_SUPPRESSION.md docs/ 2>/dev/null || true
mv TRANSITION_COMPLETE.md docs/ 2>/dev/null || true
mv VERIFICATION_STATUS.md docs/ 2>/dev/null || true
mv VERIFICATION_SUCCESS.md docs/ 2>/dev/null || true

# Move test files to tests/
mv debug_datalist.py tests/ 2>/dev/null || true
mv diagnose_tests.py tests/ 2>/dev/null || true
mv run_tests.py tests/ 2>/dev/null || true
mv test_detectron2_enhanced.py tests/ 2>/dev/null || true
mv test_detectron2_structure.py tests/ 2>/dev/null || true
mv test_enhanced_inference.py tests/ 2>/dev/null || true
mv test_hybrid_framework.py tests/ 2>/dev/null || true
mv test_imports.py tests/ 2>/dev/null || true
mv test_imports_quick.py tests/ 2>/dev/null || true
mv test_monai_imports.py tests/ 2>/dev/null || true
mv test_overlay_quality.py tests/ 2>/dev/null || true
mv test_overlay_system.py tests/ 2>/dev/null || true
mv test_system.py tests/ 2>/dev/null || true
mv test_viz_system.py tests/ 2>/dev/null || true
mv test_warnings.py tests/ 2>/dev/null || true
mv validate_docker.py tests/ 2>/dev/null || true
mv validate_monai_integration.py tests/ 2>/dev/null || true
mv validate_prompt_pack.py tests/ 2>/dev/null || true
mv verify_monai_checklist.py tests/ 2>/dev/null || true

echo "File organization complete!"
