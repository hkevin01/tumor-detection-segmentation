#!/bin/bash

# Project File Organization Script
echo "🗂️  Organizing AI-generated files into proper project structure"
echo "=============================================================="

# Create necessary directories if they don't exist
echo "📁 Creating/ensuring project directories exist..."

mkdir -p scripts/setup
mkdir -p scripts/utilities  
mkdir -p scripts/demo
mkdir -p tests/integration
mkdir -p tests/gui
mkdir -p docs/user-guide
mkdir -p docs/developer
mkdir -p docs/api
mkdir -p config/docker
mkdir -p tools

echo "   ✅ Created project directories"

# 1. Remove duplicate nested directory
echo ""
echo "🗑️  Removing duplicate nested directory..."
if [ -d "tumor-detection-segmentation" ]; then
    rm -rf tumor-detection-segmentation
    echo "   ✅ Removed duplicate tumor-detection-segmentation/ directory"
fi

# 2. Organize test files
echo ""
echo "🧪 Moving test files to tests/ directory..."

# Move GUI tests
if [ -f "test_gui.py" ]; then
    mv test_gui.py tests/gui/
    echo "   ✅ Moved test_gui.py → tests/gui/"
fi

# Move system tests  
if [ -f "test_system.py" ]; then
    mv test_system.py tests/integration/
    echo "   ✅ Moved test_system.py → tests/integration/"
fi

# 3. Organize demo and startup scripts
echo ""
echo "🚀 Moving demo and startup scripts..."

# Move demo files
if [ -f "demo_system.py" ]; then
    mv demo_system.py scripts/demo/
    echo "   ✅ Moved demo_system.py → scripts/demo/"
fi

# Move GUI startup scripts
if [ -f "start_gui.py" ]; then
    mv start_gui.py scripts/utilities/
    echo "   ✅ Moved start_gui.py → scripts/utilities/"
fi

if [ -f "start_complete_gui.py" ]; then
    mv start_complete_gui.py scripts/utilities/
    echo "   ✅ Moved start_complete_gui.py → scripts/utilities/"
fi

# 4. Organize setup and utility scripts
echo ""
echo "⚙️  Moving setup and utility scripts..."

setup_scripts=(
    "quick_setup.sh"
    "setup_enhanced_gui.sh" 
    "setup_git.sh"
    "install_powershell.sh"
)

for script in "${setup_scripts[@]}"; do
    if [ -f "$script" ]; then
        mv "$script" scripts/setup/
        echo "   ✅ Moved $script → scripts/setup/"
    fi
done

utility_scripts=(
    "git_status.sh"
    "system_status.sh"
    "run_gui.sh"
    "start_medical_gui.sh"
)

for script in "${utility_scripts[@]}"; do
    if [ -f "$script" ]; then
        mv "$script" scripts/utilities/
        echo "   ✅ Moved $script → scripts/utilities/"
    fi
done

# 5. Organize reorganization scripts (development tools)
echo ""
echo "🔧 Moving reorganization scripts to tools/..."

reorg_scripts=(
    "reorganize_phase1.sh"
    "reorganize_phase2.sh" 
    "reorganize_phase3.sh"
    "reorganize_phase4.sh"
    "reorganize_project.sh"
    "run_reorganization.sh"
)

for script in "${reorg_scripts[@]}"; do
    if [ -f "$script" ]; then
        mv "$script" tools/
        echo "   ✅ Moved $script → tools/"
    fi
done

# 6. Organize documentation files
echo ""
echo "📚 Moving documentation files to docs/..."

# User-facing documentation
user_docs=(
    "MEDICAL_GUI_README.md:user-guide/medical-gui.md"
    "GUI_README.md:user-guide/gui-setup.md"
    "README_GITHUB.md:user-guide/github-readme.md"
)

for doc_mapping in "${user_docs[@]}"; do
    IFS=':' read -r source target <<< "$doc_mapping"
    if [ -f "$source" ]; then
        mv "$source" "docs/$target"
        echo "   ✅ Moved $source → docs/$target"
    fi
done

# Developer documentation  
dev_docs=(
    "IMPLEMENTATION_SUMMARY.md:developer/implementation.md"
    "GIT_SETUP_GUIDE.md:developer/git-setup.md"
    "GUI_STATUS.md:developer/gui-status.md"
    "DICOM_VIEWER_COMPLETE.md:developer/dicom-viewer.md"
    "REORGANIZATION_SUMMARY.md:developer/reorganization.md"
    "REORGANIZATION_TODO.md:developer/reorganization-todo.md"
    "STEPS.md:developer/development-steps.md"
)

for doc_mapping in "${dev_docs[@]}"; do
    IFS=':' read -r source target <<< "$doc_mapping"
    if [ -f "$source" ]; then
        mv "$source" "docs/$target"
        echo "   ✅ Moved $source → docs/$target"
    fi
done

# 7. Organize configuration and deployment files
echo ""
echo "🐳 Moving configuration and deployment files..."

# Docker files
if [ -f "Dockerfile" ]; then
    mv Dockerfile config/docker/
    echo "   ✅ Moved Dockerfile → config/docker/"
fi

if [ -f "docker-compose.yml" ]; then
    mv docker-compose.yml config/docker/
    echo "   ✅ Moved docker-compose.yml → config/docker/"
fi

# Development configuration
if [ -f "code_map.json" ]; then
    mv code_map.json config/
    echo "   ✅ Moved code_map.json → config/"
fi

# 8. Create README files for new directories
echo ""
echo "📝 Creating README files for organized directories..."

# Tests directory README
cat > tests/README.md << 'EOF'
# Tests

This directory contains all test files for the medical imaging system.

## Structure

- `gui/` - GUI and frontend tests
- `integration/` - System integration tests  
- `unit/` - Unit tests (place unit test files here)
- `fixtures/` - Test data and fixtures

## Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/gui/
pytest tests/integration/
```
EOF

# Scripts directory README
cat > scripts/README.md << 'EOF'
# Scripts

Utility and automation scripts for the project.

## Structure

- `setup/` - Installation and setup scripts
- `utilities/` - Runtime utilities and GUI launchers
- `demo/` - Demo and showcase scripts

## Usage

Make scripts executable before running:
```bash
chmod +x scripts/setup/*.sh
chmod +x scripts/utilities/*.sh
```
EOF

# Tools directory README  
cat > tools/README.md << 'EOF'
# Tools

Development and maintenance tools.

Contains project reorganization scripts and other development utilities.

## Usage

```bash
chmod +x tools/*.sh
./tools/reorganize_project.sh  # For project reorganization
```
EOF

# Config directory README
cat > config/README.md << 'EOF'
# Configuration

Project configuration files.

## Structure

- `config.json` - Main application configuration
- `docker/` - Docker and containerization configs
- `code_map.json` - Project structure mapping

## Usage

Edit `config.json` to customize:
- Data paths and preprocessing parameters
- Model architecture and training hyperparameters  
- Device settings (CPU/CUDA)
- Logging and output configurations
EOF

echo "   ✅ Created README files for organized directories"

# 9. Update main README.md to reflect new structure
echo ""
echo "📖 Updating main README.md..."

# Create backup of current README
cp README.md README.md.backup

# Update the Quick Start section in README.md to reflect new script locations
sed -i 's|python src/training/train.py|python src/training/train.py|g' README.md
sed -i 's|python src/inference/inference.py|python src/inference/inference.py|g' README.md  
sed -i 's|./run_gui.sh|./scripts/utilities/run_gui.sh|g' README.md

echo "   ✅ Updated README.md with new script locations"

# 10. Make scripts executable
echo ""
echo "🔐 Making scripts executable..."

find scripts/ -name "*.sh" -exec chmod +x {} \;
find tools/ -name "*.sh" -exec chmod +x {} \;

echo "   ✅ Made all scripts executable"

echo ""
echo "✅ File organization complete!"
echo ""
echo "📋 Summary of changes:"
echo "   • Removed duplicate tumor-detection-segmentation/ directory"
echo "   • Moved test files to tests/gui/ and tests/integration/"
echo "   • Organized scripts into scripts/setup/, scripts/utilities/, scripts/demo/"
echo "   • Moved development tools to tools/"
echo "   • Organized documentation into docs/user-guide/ and docs/developer/"
echo "   • Moved Docker files to config/docker/"
echo "   • Created README files for all new directories"
echo "   • Updated main README.md with new script locations"
echo "   • Made all scripts executable"
echo ""
echo "🚀 New project structure:"
echo "   📁 src/ - Main source code (unchanged)"
echo "   📁 tests/gui/, tests/integration/ - Organized test files"  
echo "   📁 scripts/setup/, scripts/utilities/, scripts/demo/ - Organized scripts"
echo "   📁 docs/user-guide/, docs/developer/ - Organized documentation"
echo "   📁 config/docker/ - Docker configuration"
echo "   📁 tools/ - Development tools"
echo ""
echo "🎯 Next steps:"
echo "   • Run: ./scripts/utilities/run_gui.sh (instead of ./run_gui.sh)"
echo "   • Setup: Use scripts in scripts/setup/"
echo "   • Tests: pytest tests/"
echo "   • Docs: Check docs/user-guide/ for user documentation"
