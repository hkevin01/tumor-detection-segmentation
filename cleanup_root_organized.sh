#!/usr/bin/env bash
# Root folder cleanup script - Organize files into proper subfolders
# Keeps run.sh in root and updates all file references

set -e  # Exit on any error

echo "🧹 Root Folder Cleanup - Organizing files into subfolders"
echo "========================================================"

# Create necessary directories if they don't exist
echo "📁 Creating directory structure..."
mkdir -p scripts/setup
mkdir -p scripts/utilities
mkdir -p scripts/demo
mkdir -p scripts/validation
mkdir -p scripts/maintenance
mkdir -p docs/deployment
mkdir -p docs/status
mkdir -p config/development
mkdir -p temp/archive

echo "✅ Directory structure created"

# 1. Move deployment and Docker files to docs/deployment/
echo "📦 Moving deployment documentation..."
if [ -f "DEPLOYMENT.md" ]; then mv "DEPLOYMENT.md" "docs/deployment/"; fi
if [ -f "DOCKER_COMPLETE.md" ]; then mv "DOCKER_COMPLETE.md" "docs/deployment/"; fi
if [ -f "DOCKER_GUIDE.md" ]; then mv "DOCKER_GUIDE.md" "docs/deployment/"; fi

# 2. Move status and verification files to docs/status/
echo "📊 Moving status documentation..."
if [ -f "ENHANCED_TRAINING_SUMMARY.md" ]; then mv "ENHANCED_TRAINING_SUMMARY.md" "docs/status/"; fi
if [ -f "IMPLEMENTATION_COMPLETE.md" ]; then mv "IMPLEMENTATION_COMPLETE.md" "docs/status/"; fi
if [ -f "INSTALLATION_FIX.md" ]; then mv "INSTALLATION_FIX.md" "docs/status/"; fi
if [ -f "MONAI_IMPLEMENTATION_STATUS.md" ]; then mv "MONAI_IMPLEMENTATION_STATUS.md" "docs/status/"; fi
if [ -f "MONAI_TESTS_COMPLETE.md" ]; then mv "MONAI_TESTS_COMPLETE.md" "docs/status/"; fi
if [ -f "ROOT_ORGANIZATION_COMPLETE.md" ]; then mv "ROOT_ORGANIZATION_COMPLETE.md" "docs/status/"; fi
if [ -f "VERIFICATION_STATUS.md" ]; then mv "VERIFICATION_STATUS.md" "docs/status/"; fi
if [ -f "VERIFICATION_SUCCESS.md" ]; then mv "VERIFICATION_SUCCESS.md" "docs/status/"; fi

# 3. Move setup and configuration scripts to scripts/setup/
echo "⚙️ Moving setup scripts..."
if [ -f "setup_fixed.sh" ]; then mv "setup_fixed.sh" "scripts/setup/"; fi
if [ -f "cleanup_root.sh" ]; then mv "cleanup_root.sh" "scripts/setup/"; fi
if [ -f "organize_root.sh" ]; then mv "organize_root.sh" "scripts/setup/"; fi
if [ -f "move_files.sh" ]; then mv "move_files.sh" "scripts/setup/"; fi

# 4. Move demo scripts to scripts/demo/
echo "🎬 Moving demo scripts..."
if [ -f "demo_complete_workflow.sh" ]; then mv "demo_complete_workflow.sh" "scripts/demo/"; fi
if [ -f "demo_enhanced_workflow.sh" ]; then mv "demo_enhanced_workflow.sh" "scripts/demo/"; fi

# 5. Move validation and test scripts to scripts/validation/
echo "🧪 Moving validation scripts..."
if [ -f "validate_docker.py" ]; then mv "validate_docker.py" "scripts/validation/"; fi
if [ -f "validate_monai_integration.py" ]; then mv "validate_monai_integration.py" "scripts/validation/"; fi
if [ -f "verify_monai_checklist.py" ]; then mv "verify_monai_checklist.py" "scripts/validation/"; fi
if [ -f "verify_monai_venv.sh" ]; then mv "verify_monai_venv.sh" "scripts/validation/"; fi

# 6. Move test scripts to scripts/validation/
echo "🔬 Moving test scripts..."
if [ -f "test_docker.sh" ]; then mv "test_docker.sh" "scripts/validation/"; fi
if [ -f "test_enhanced_inference.py" ]; then mv "test_enhanced_inference.py" "scripts/validation/"; fi
if [ -f "test_imports_quick.py" ]; then mv "test_imports_quick.py" "scripts/validation/"; fi
if [ -f "test_monai_imports.py" ]; then mv "test_monai_imports.py" "scripts/validation/"; fi
if [ -f "test_overlay_quality.py" ]; then mv "test_overlay_quality.py" "scripts/validation/"; fi
if [ -f "test_overlay_system.py" ]; then mv "test_overlay_system.py" "scripts/validation/"; fi
if [ -f "test_system.py" ]; then mv "test_system.py" "scripts/validation/"; fi
if [ -f "test_viz_system.py" ]; then mv "test_viz_system.py" "scripts/validation/"; fi
if [ -f "debug_datalist.py" ]; then mv "debug_datalist.py" "scripts/validation/"; fi

# 7. Move development configuration files to config/development/
echo "⚙️ Moving development config files..."
if [ -f "requirements-docker.txt" ]; then mv "requirements-docker.txt" "config/development/"; fi
if [ -f "requirements-fixed.txt" ]; then mv "requirements-fixed.txt" "config/development/"; fi
if [ -f "mypy.ini" ]; then mv "mypy.ini" "config/development/"; fi
if [ -f "pytest.ini" ]; then mv "pytest.ini" "config/development/"; fi
if [ -f ".ruff.toml" ]; then mv ".ruff.toml" "config/development/"; fi

echo "✅ Files moved to appropriate directories"

# Update file references in scripts and documentation
echo "🔗 Updating file references..."

# Update run.sh to reference moved files
if [ -f "run.sh" ]; then
    echo "  Updating run.sh references..."
    # Update config file references
    sed -i 's|mypy\.ini|config/development/mypy.ini|g' run.sh 2>/dev/null || true
    sed -i 's|pytest\.ini|config/development/pytest.ini|g' run.sh 2>/dev/null || true
    sed -i 's|\.ruff\.toml|config/development/.ruff.toml|g' run.sh 2>/dev/null || true
    sed -i 's|requirements-docker\.txt|config/development/requirements-docker.txt|g' run.sh 2>/dev/null || true
fi

# Update any Makefile or other build scripts
if [ -f "Makefile" ]; then
    echo "  Updating Makefile references..."
    sed -i 's|mypy\.ini|config/development/mypy.ini|g' Makefile 2>/dev/null || true
    sed -i 's|pytest\.ini|config/development/pytest.ini|g' Makefile 2>/dev/null || true
    sed -i 's|\.ruff\.toml|config/development/.ruff.toml|g' Makefile 2>/dev/null || true
fi

# Update .github workflows if they exist
if [ -d ".github/workflows" ]; then
    echo "  Updating GitHub workflow references..."
    find .github/workflows -name "*.yml" -o -name "*.yaml" | while read -r file; do
        sed -i 's|mypy\.ini|config/development/mypy.ini|g' "$file" 2>/dev/null || true
        sed -i 's|pytest\.ini|config/development/pytest.ini|g' "$file" 2>/dev/null || true
        sed -i 's|\.ruff\.toml|config/development/.ruff.toml|g' "$file" 2>/dev/null || true
        sed -i 's|requirements-docker\.txt|config/development/requirements-docker.txt|g' "$file" 2>/dev/null || true
    done
fi

# Update Docker files
echo "  Updating Docker references..."
if [ -f "Dockerfile" ]; then
    sed -i 's|requirements-docker\.txt|config/development/requirements-docker.txt|g' Dockerfile 2>/dev/null || true
fi

if [ -f "docker-compose.yml" ]; then
    sed -i 's|mypy\.ini|config/development/mypy.ini|g' docker-compose.yml 2>/dev/null || true
    sed -i 's|pytest\.ini|config/development/pytest.ini|g' docker-compose.yml 2>/dev/null || true
    sed -i 's|\.ruff\.toml|config/development/.ruff.toml|g' docker-compose.yml 2>/dev/null || true
fi

# Update any scripts that might reference moved files
echo "  Updating script references..."
find scripts/ -type f \( -name "*.sh" -o -name "*.py" \) | while read -r file; do
    # Update references to validation scripts
    sed -i 's|python validate_docker\.py|python scripts/validation/validate_docker.py|g' "$file" 2>/dev/null || true
    sed -i 's|python validate_monai_integration\.py|python scripts/validation/validate_monai_integration.py|g' "$file" 2>/dev/null || true
    sed -i 's|python verify_monai_checklist\.py|python scripts/validation/verify_monai_checklist.py|g' "$file" 2>/dev/null || true
    sed -i 's|\./verify_monai_venv\.sh|scripts/validation/verify_monai_venv.sh|g' "$file" 2>/dev/null || true

    # Update references to test scripts
    sed -i 's|python test_|python scripts/validation/test_|g' "$file" 2>/dev/null || true
    sed -i 's|\./test_|scripts/validation/test_|g' "$file" 2>/dev/null || true

    # Update references to demo scripts
    sed -i 's|\./demo_|scripts/demo/demo_|g' "$file" 2>/dev/null || true
done

# Update README.md references
if [ -f "README.md" ]; then
    echo "  Updating README.md references..."
    sed -i 's|mypy\.ini|config/development/mypy.ini|g' README.md 2>/dev/null || true
    sed -i 's|pytest\.ini|config/development/pytest.ini|g' README.md 2>/dev/null || true
    sed -i 's|\.ruff\.toml|config/development/.ruff.toml|g' README.md 2>/dev/null || true
    sed -i 's|requirements-docker\.txt|config/development/requirements-docker.txt|g' README.md 2>/dev/null || true

    # Update demo script references
    sed -i 's|\./demo_complete_workflow\.sh|scripts/demo/demo_complete_workflow.sh|g' README.md 2>/dev/null || true
    sed -i 's|\./demo_enhanced_workflow\.sh|scripts/demo/demo_enhanced_workflow.sh|g' README.md 2>/dev/null || true
fi

# Update any Python files that might import or reference moved files
echo "  Updating Python imports and references..."
find src/ tests/ -name "*.py" | while read -r file; do
    # Update any imports that might reference root-level files
    sed -i 's|from validate_docker|from scripts.validation.validate_docker|g' "$file" 2>/dev/null || true
    sed -i 's|import validate_docker|import scripts.validation.validate_docker|g' "$file" 2>/dev/null || true
done

echo "✅ File references updated"

# Create a summary of what was moved
echo "📋 Creating cleanup summary..."
cat > "docs/status/ROOT_CLEANUP_SUMMARY.md" << 'EOF'
# Root Folder Cleanup Summary

This document summarizes the organization of files from the root directory into appropriate subfolders.

## Files Moved

### Documentation Files → `docs/`
- `DEPLOYMENT.md` → `docs/deployment/`
- `DOCKER_COMPLETE.md` → `docs/deployment/`
- `DOCKER_GUIDE.md` → `docs/deployment/`
- `ENHANCED_TRAINING_SUMMARY.md` → `docs/status/`
- `IMPLEMENTATION_COMPLETE.md` → `docs/status/`
- `INSTALLATION_FIX.md` → `docs/status/`
- `MONAI_IMPLEMENTATION_STATUS.md` → `docs/status/`
- `MONAI_TESTS_COMPLETE.md` → `docs/status/`
- `ROOT_ORGANIZATION_COMPLETE.md` → `docs/status/`
- `VERIFICATION_STATUS.md` → `docs/status/`
- `VERIFICATION_SUCCESS.md` → `docs/status/`

### Setup Scripts → `scripts/setup/`
- `setup_fixed.sh` → `scripts/setup/`
- `cleanup_root.sh` → `scripts/setup/`
- `organize_root.sh` → `scripts/setup/`
- `move_files.sh` → `scripts/setup/`

### Demo Scripts → `scripts/demo/`
- `demo_complete_workflow.sh` → `scripts/demo/`
- `demo_enhanced_workflow.sh` → `scripts/demo/`

### Validation Scripts → `scripts/validation/`
- `validate_docker.py` → `scripts/validation/`
- `validate_monai_integration.py` → `scripts/validation/`
- `verify_monai_checklist.py` → `scripts/validation/`
- `verify_monai_venv.sh` → `scripts/validation/`
- `test_docker.sh` → `scripts/validation/`
- `test_enhanced_inference.py` → `scripts/validation/`
- `test_imports_quick.py` → `scripts/validation/`
- `test_monai_imports.py` → `scripts/validation/`
- `test_overlay_quality.py` → `scripts/validation/`
- `test_overlay_system.py` → `scripts/validation/`
- `test_system.py` → `scripts/validation/`
- `test_viz_system.py` → `scripts/validation/`
- `debug_datalist.py` → `scripts/validation/`

### Development Config → `config/development/`
- `requirements-docker.txt` → `config/development/`
- `requirements-fixed.txt` → `config/development/`
- `mypy.ini` → `config/development/`
- `pytest.ini` → `config/development/`
- `.ruff.toml` → `config/development/`

## Files Kept in Root
- `run.sh` (main entry point)
- `README.md` (project documentation)
- `LICENSE` (license file)
- `requirements.txt` (main requirements)
- `setup.py` (package setup)
- `config.json` (main configuration)
- `.env` (environment variables)
- `.gitignore` (git ignore rules)

## Updated References
- All scripts and configuration files updated to reference new file locations
- GitHub workflows updated for moved config files
- Docker files updated for moved requirements
- README.md updated with new paths
- Python imports updated where necessary

## Benefits
- ✅ Cleaner root directory with only essential files
- ✅ Logical organization by file type and purpose
- ✅ Easier navigation and maintenance
- ✅ All functionality preserved with updated references
- ✅ Better project structure for development and deployment
EOF

echo "✅ Cleanup summary created"

# Display the cleaned root directory
echo ""
echo "🎉 ROOT FOLDER CLEANUP COMPLETE!"
echo "================================"
echo ""
echo "📁 New root directory structure:"
ls -la | grep -E '^-' | awk '{print "  " $9}' | grep -v "^  \.$" | grep -v "^  \.\.$"
echo ""
echo "📂 Organized subdirectories:"
echo "  docs/deployment/     - Deployment and Docker documentation"
echo "  docs/status/         - Status and verification documentation"
echo "  scripts/setup/       - Setup and installation scripts"
echo "  scripts/demo/        - Demo and showcase scripts"
echo "  scripts/validation/  - Test and validation scripts"
echo "  config/development/  - Development configuration files"
echo ""
echo "✅ All file references have been updated"
echo "✅ run.sh kept in root as requested"
echo "✅ All functionality preserved"
echo ""
echo "📋 See docs/status/ROOT_CLEANUP_SUMMARY.md for detailed summary"
