#!/bin/bash

# Final Project Organization - Clean up remaining root files
echo "🗂️  Final Project File Organization"
echo "==================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo ""
print_status "Analyzing remaining files in root directory..."

# Create any missing directories
mkdir -p scripts/utilities
mkdir -p scripts/setup  
mkdir -p scripts/demo
mkdir -p tests/integration
mkdir -p tests/gui
mkdir -p docs/user-guide
mkdir -p docs/developer
mkdir -p config/docker
mkdir -p tools

echo ""
print_status "Moving remaining AI-generated files to proper locations..."

# 1. Move remaining test files
if [ -f "test_gui.py" ]; then
    mv test_gui.py tests/gui/
    print_success "Moved test_gui.py → tests/gui/"
fi

if [ -f "test_system.py" ]; then
    mv test_system.py tests/integration/
    print_success "Moved test_system.py → tests/integration/"
fi

# 2. Move remaining startup/demo scripts
if [ -f "demo_system.py" ]; then
    mv demo_system.py scripts/demo/
    print_success "Moved demo_system.py → scripts/demo/"
fi

if [ -f "start_gui.py" ]; then
    mv start_gui.py scripts/utilities/
    print_success "Moved start_gui.py → scripts/utilities/"
fi

if [ -f "start_complete_gui.py" ]; then
    mv start_complete_gui.py scripts/utilities/
    print_success "Moved start_complete_gui.py → scripts/utilities/"
fi

if [ -f "start_medical_gui.sh" ]; then
    mv start_medical_gui.sh scripts/utilities/
    print_success "Moved start_medical_gui.sh → scripts/utilities/"
fi

# 3. Move remaining setup scripts
setup_scripts=(
    "quick_setup.sh"
    "setup_enhanced_gui.sh"
    "setup_git.sh"
    "setup_fixed.sh"
)

for script in "${setup_scripts[@]}"; do
    if [ -f "$script" ]; then
        mv "$script" scripts/setup/
        print_success "Moved $script → scripts/setup/"
    fi
done

# 4. Move utility scripts
utility_scripts=(
    "git_status.sh"
    "system_status.sh"
    "run_gui.sh"
)

for script in "${utility_scripts[@]}"; do
    if [ -f "$script" ]; then
        mv "$script" scripts/utilities/
        print_success "Moved $script → scripts/utilities/"
    fi
done

# 5. Move reorganization and development tools
tool_scripts=(
    "organize_project.sh"
    "reorganize_phase1.sh"
    "reorganize_phase2.sh"
    "reorganize_phase3.sh"
    "reorganize_phase4.sh"
    "reorganize_project.sh"
    "run_reorganization.sh"
)

for script in "${tool_scripts[@]}"; do
    if [ -f "$script" ]; then
        mv "$script" tools/
        print_success "Moved $script → tools/"
    fi
done

# 6. Move documentation files to proper locations
print_status "Organizing documentation files..."

# User-facing documentation
user_docs=(
    "MEDICAL_GUI_README.md:user-guide/medical-gui.md"
    "GUI_README.md:user-guide/gui-setup.md"
    "README_GITHUB.md:user-guide/github-readme.md"
    "INSTALLATION_FIX.md:user-guide/installation-fix.md"
)

for doc_mapping in "${user_docs[@]}"; do
    IFS=':' read -r source target <<< "$doc_mapping"
    if [ -f "$source" ]; then
        mv "$source" "docs/$target"
        print_success "Moved $source → docs/$target"
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
    "PROJECT_ORGANIZATION_SUMMARY.md:developer/organization-summary.md"
)

for doc_mapping in "${dev_docs[@]}"; do
    IFS=':' read -r source target <<< "$doc_mapping"
    if [ -f "$source" ]; then
        mv "$source" "docs/$target"
        print_success "Moved $source → docs/$target"
    fi
done

# 7. Move Docker and configuration files
print_status "Organizing configuration files..."

if [ -f "Dockerfile" ]; then
    mv Dockerfile config/docker/
    print_success "Moved Dockerfile → config/docker/"
fi

if [ -f "docker-compose.yml" ]; then
    mv docker-compose.yml config/docker/
    print_success "Moved docker-compose.yml → config/docker/"
fi

# Move additional requirements files to config
if [ -f "requirements-fixed.txt" ]; then
    mv requirements-fixed.txt config/
    print_success "Moved requirements-fixed.txt → config/"
fi

# 8. Clean up backup files
print_status "Cleaning up backup files..."
if [ -f "README.md.backup" ]; then
    rm README.md.backup
    print_success "Removed README.md.backup"
fi

# 9. Make all scripts executable
print_status "Making scripts executable..."
find scripts/ -name "*.sh" -exec chmod +x {} \;
find tools/ -name "*.sh" -exec chmod +x {} \;
print_success "Made all scripts executable"

# 10. Update README paths
print_status "Updating README.md references..."
if [ -f "README.md" ]; then
    # Update script paths in README
    sed -i 's|./run_gui.sh|./scripts/utilities/run_gui.sh|g' README.md
    sed -i 's|./git_status.sh|./scripts/utilities/git_status.sh|g' README.md
    sed -i 's|./quick_setup.sh|./scripts/setup/quick_setup.sh|g' README.md
    print_success "Updated README.md with new script paths"
fi

echo ""
print_status "Final project structure:"
echo ""
echo "📁 Project Root:"
echo "   ├── 📂 src/                    # Main source code"
echo "   ├── 📂 tests/                  # Test suites"
echo "   │   ├── gui/                   # GUI tests"
echo "   │   └── integration/           # Integration tests"
echo "   ├── 📂 scripts/                # Organized scripts"
echo "   │   ├── setup/                 # Setup and installation"
echo "   │   ├── utilities/             # Runtime utilities"
echo "   │   └── demo/                  # Demo scripts"
echo "   ├── 📂 docs/                   # Documentation"
echo "   │   ├── user-guide/            # User documentation"
echo "   │   └── developer/             # Developer docs"
echo "   ├── 📂 config/                 # Configuration"
echo "   │   └── docker/                # Docker configs"
echo "   ├── 📂 tools/                  # Development tools"
echo "   ├── 📂 data/                   # Data storage"
echo "   ├── 📂 models/                 # ML models"
echo "   ├── 📂 frontend/, gui/         # Frontend code"
echo "   └── 📄 Core files (README, requirements, setup.py)"

echo ""
print_success "✅ Project organization complete!"
echo ""
print_status "Summary of changes:"
echo "   • Moved all test files to tests/ directory"
echo "   • Organized scripts by function (setup/, utilities/, demo/)"
echo "   • Structured documentation (user-guide/, developer/)"
echo "   • Centralized configuration files"
echo "   • Moved development tools to tools/"
echo "   • Updated README.md with new paths"
echo "   • Made all scripts executable"
echo ""
print_status "🚀 Your project now follows Python project best practices!"
echo ""
echo "🎯 Quick actions:"
echo "   • Setup: ./scripts/setup/quick_setup.sh"
echo "   • Run GUI: ./scripts/utilities/run_gui.sh"
echo "   • Run tests: pytest tests/"
echo "   • Clean git: ./scripts/utilities/git_cleanup.sh"
