#!/bin/bash

# Git Repository Cleanup Script
echo "🧹 Git Repository Cleanup for Medical Imaging AI"
echo "================================================"

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

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    print_error "Not in a git repository!"
    exit 1
fi

print_status "Analyzing repository status..."

# Show current repository status
echo ""
print_status "Current git status:"
git status --porcelain | head -20
if [ $(git status --porcelain | wc -l) -gt 20 ]; then
    echo "... and $(( $(git status --porcelain | wc -l) - 20 )) more files"
fi

echo ""
print_status "Files that should probably be ignored:"

# Check for common files that shouldn't be tracked
echo ""
echo "🔍 Python cache files:"
find . -name "__pycache__" -type d | head -10

echo ""
echo "🔍 Virtual environment files:"
find . -name "venv" -o -name ".venv" -o -name "env" | head -5

echo ""
echo "🔍 Log files:"
find . -name "*.log" | head -10

echo ""
echo "🔍 Temporary files:"
find . -name "*.tmp" -o -name "*.temp" -o -name "*.bak" | head -10

echo ""
echo "🔍 OS specific files:"
find . -name ".DS_Store" -o -name "Thumbs.db" | head -5

echo ""
echo "🔍 IDE files:"
find . -name ".vscode" -o -name ".idea" | head -5

echo ""
echo "🔍 Node modules:"
find . -name "node_modules" -type d | head -5

echo ""
print_status "Recommended cleanup actions:"

echo ""
echo "1. 🗑️  Remove files from git tracking (but keep locally):"
echo "   git rm --cached -r __pycache__/"
echo "   git rm --cached -r venv/"
echo "   git rm --cached -r .venv/"
echo "   git rm --cached -r node_modules/"
echo "   git rm --cached *.log"
echo "   git rm --cached .DS_Store"
echo "   git rm --cached Thumbs.db"

echo ""
echo "2. 📁 Remove large data directories from tracking:"
echo "   git rm --cached -r data/ (if contains data files)"
echo "   git rm --cached -r models/ (if contains model files)"
echo "   git rm --cached -r logs/"

echo ""
echo "3. 🔒 Remove environment and config files:"
echo "   git rm --cached .env"
echo "   git rm --cached config.json (if contains secrets)"

echo ""
print_warning "IMPORTANT: The --cached flag removes files from git tracking"
print_warning "but keeps them in your local filesystem."

echo ""
read -p "Would you like me to run automatic cleanup? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Running automatic cleanup..."
    
    # Remove common files that shouldn't be tracked
    git rm --cached -r __pycache__ 2>/dev/null || true
    git rm --cached -r venv/ 2>/dev/null || true
    git rm --cached -r .venv/ 2>/dev/null || true
    git rm --cached -r node_modules/ 2>/dev/null || true
    git rm --cached -r frontend/node_modules/ 2>/dev/null || true
    git rm --cached -r gui/frontend/node_modules/ 2>/dev/null || true
    git rm --cached *.log 2>/dev/null || true
    git rm --cached .DS_Store 2>/dev/null || true
    git rm --cached Thumbs.db 2>/dev/null || true
    git rm --cached .env 2>/dev/null || true
    git rm --cached -r logs/ 2>/dev/null || true
    git rm --cached -r temp/ 2>/dev/null || true
    git rm --cached -r tmp/ 2>/dev/null || true
    
    # Remove backup files created during reorganization
    git rm --cached *.backup 2>/dev/null || true
    git rm --cached PROJECT_ORGANIZATION_SUMMARY.md.backup 2>/dev/null || true
    git rm --cached README.md.backup 2>/dev/null || true
    
    print_success "Automatic cleanup completed!"
    
    echo ""
    print_status "Files removed from git tracking:"
    git status --porcelain | grep "^D"
    
    echo ""
    print_status "To commit these changes:"
    echo "   git add .gitignore"
    echo "   git commit -m 'Update .gitignore and clean up repository'"
    
else
    print_status "Skipping automatic cleanup."
fi

echo ""
print_status "Updated .gitignore now includes:"
echo "   ✅ Python cache and virtual environments"
echo "   ✅ Node.js modules and build files"
echo "   ✅ Medical data and DICOM files"
echo "   ✅ ML models and checkpoints"
echo "   ✅ Logs and temporary files"
echo "   ✅ IDE and OS specific files"
echo "   ✅ Environment and secret files"
echo ""
print_success "Repository cleanup analysis complete!"
