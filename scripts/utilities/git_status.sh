#!/bin/bash

# Git Status Checker
echo "📊 Git Repository Status"
echo "======================="

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
    echo ""
    print_status "To initialize git repository:"
    echo "   git init"
    echo "   git add ."
    echo "   git commit -m 'Initial commit'"
    exit 1
fi

# Get basic repository info
print_status "Repository information:"
BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
REMOTE=$(git remote get-url origin 2>/dev/null || echo "no remote")
echo "   Branch: $BRANCH"
echo "   Remote: $REMOTE"

# Show current status
echo ""
print_status "Current status:"
git status --porcelain | head -20

TOTAL_CHANGES=$(git status --porcelain | wc -l)
if [ $TOTAL_CHANGES -gt 20 ]; then
    echo "... and $(( $TOTAL_CHANGES - 20 )) more files"
fi

if [ $TOTAL_CHANGES -eq 0 ]; then
    print_success "Working directory is clean! ✨"
else
    print_warning "You have $TOTAL_CHANGES changed files"
fi

# Show recent commits
echo ""
print_status "Recent commits:"
git log --oneline -5 2>/dev/null || echo "No commits yet"

# Show file statistics
echo ""
print_status "Repository statistics:"
TRACKED_FILES=$(git ls-files | wc -l)
TOTAL_FILES=$(find . -type f ! -path './.git/*' ! -path './.venv/*' ! -path './venv/*' ! -path './node_modules/*' | wc -l)
echo "   Tracked files: $TRACKED_FILES"
echo "   Total files: $TOTAL_FILES"

# Check for large files
echo ""
print_status "Checking for large files (>10MB):"
LARGE_FILES=$(find . -type f ! -path './.git/*' ! -path './.venv/*' ! -path './venv/*' ! -path './node_modules/*' -size +10M 2>/dev/null)
if [ -z "$LARGE_FILES" ]; then
    print_success "No large files found"
else
    print_warning "Large files detected:"
    echo "$LARGE_FILES" | while read file; do
        size=$(du -h "$file" | cut -f1)
        echo "   • $file ($size)"
    done
fi

# Check gitignore effectiveness
echo ""
print_status "Gitignore status:"
if [ -f ".gitignore" ]; then
    GITIGNORE_LINES=$(wc -l < .gitignore)
    print_success ".gitignore exists ($GITIGNORE_LINES lines)"
    
    # Check for common unignored files
    UNIGNORED_ISSUES=()
    
    if git ls-files | grep -q "\.pyc$"; then
        UNIGNORED_ISSUES+=("Python cache files (.pyc)")
    fi
    
    if git ls-files | grep -q "__pycache__"; then
        UNIGNORED_ISSUES+=("Python cache directories (__pycache__)")
    fi
    
    if git ls-files | grep -q "\.log$"; then
        UNIGNORED_ISSUES+=("Log files (.log)")
    fi
    
    if git ls-files | grep -q "node_modules"; then
        UNIGNORED_ISSUES+=("Node modules")
    fi
    
    if [ ${#UNIGNORED_ISSUES[@]} -eq 0 ]; then
        print_success "Gitignore appears effective"
    else
        print_warning "Potential gitignore issues:"
        for issue in "${UNIGNORED_ISSUES[@]}"; do
            echo "   • $issue"
        done
    fi
else
    print_warning ".gitignore not found"
fi

# Quick actions
echo ""
print_status "Quick actions:"
echo "   • Stage all changes: git add ."
echo "   • Commit changes: git commit -m 'Your message'"
echo "   • Push changes: git push"
echo "   • Clean untracked files: git clean -fd"
echo "   • Reset to last commit: git reset --hard HEAD"
echo ""
print_status "For detailed cleanup: ./scripts/utilities/git_cleanup.sh"
