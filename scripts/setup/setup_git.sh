#!/bin/bash

# Git Setup Script for Tumor Detection Project
# Repository: git@github.com:hkevin01/tumor-detection-segmentation.git

set -e

echo "🔧 Setting up Git for Tumor Detection & Segmentation Project..."

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

# Navigate to project directory
cd "$(dirname "$0")"

echo "📁 Current directory: $(pwd)"

# Check if this is already a git repository
if [ -d ".git" ]; then
    echo "📋 Git repository already exists. Checking current remotes..."
    git remote -v
    
    # Check if the correct remote is already set
    if git remote get-url origin &> /dev/null; then
        current_remote=$(git remote get-url origin)
        echo "🔗 Current origin: $current_remote"
        
        if [ "$current_remote" = "git@github.com:hkevin01/tumor-detection-segmentation.git" ]; then
            echo "✅ Correct remote is already set!"
        else
            echo "🔄 Updating remote URL..."
            git remote set-url origin git@github.com:hkevin01/tumor-detection-segmentation.git
        fi
    else
        echo "➕ Adding remote origin..."
        git remote add origin git@github.com:hkevin01/tumor-detection-segmentation.git
    fi
else
    echo "🆕 Initializing new Git repository..."
    git init
    
    echo "➕ Adding remote origin..."
    git remote add origin git@github.com:hkevin01/tumor-detection-segmentation.git
fi

# Set up Git configuration (if not already set)
echo "⚙️ Checking Git configuration..."

if [ -z "$(git config user.name)" ]; then
    echo "📝 Please enter your Git username:"
    read -r git_username
    git config user.name "$git_username"
else
    echo "✅ Git username: $(git config user.name)"
fi

if [ -z "$(git config user.email)" ]; then
    echo "📧 Please enter your Git email:"
    read -r git_email
    git config user.email "$git_email"
else
    echo "✅ Git email: $(git config user.email)"
fi

# Check if SSH key is set up for GitHub
echo "🔐 Testing SSH connection to GitHub..."
if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    echo "✅ SSH key is properly configured for GitHub"
else
    echo "⚠️  SSH key may not be configured. You might need to:"
    echo "   1. Generate an SSH key: ssh-keygen -t ed25519 -C 'your_email@example.com'"
    echo "   2. Add it to ssh-agent: ssh-add ~/.ssh/id_ed25519"
    echo "   3. Copy public key to GitHub: cat ~/.ssh/id_ed25519.pub"
    echo "   4. Add the key to your GitHub account settings"
fi

# Create/update .gitignore if needed
echo "📄 Checking .gitignore..."
if [ ! -f ".gitignore" ]; then
    echo "➕ Creating .gitignore file..."
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyTorch
*.pth
*.pt

# Jupyter Notebook
.ipynb_checkpoints

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Project specific
data/
models/
*.dcm
*.dicom
temp/
logs/
reports/*.pdf
reports/*.docx

# Database
*.db
*.sqlite
*.sqlite3

# Node modules (for frontend)
gui/frontend/node_modules/
gui/frontend/build/
gui/frontend/.env

# Backend
gui/backend/venv/
gui/backend/__pycache__/
gui/backend/.env

# Temporary files
*.tmp
*.temp
*.log
EOF
else
    echo "✅ .gitignore already exists"
fi

# Check current status
echo "📊 Current Git status:"
git status

# Stage all files
echo "➕ Adding files to Git..."
git add .

# Show what will be committed
echo "📋 Files to be committed:"
git status --staged

# Prompt for initial commit
echo ""
echo "🚀 Ready to make initial commit. Continue? (y/n)"
read -r confirm

if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
    # Check if there are any commits
    if git rev-parse --verify HEAD >/dev/null 2>&1; then
        echo "📝 Making commit..."
        commit_message="Update: Enhanced tumor detection system with DICOM viewer integration

- Professional DICOM viewer with Cornerstone3D
- Complete clinical workflow interface
- AI tumor detection with visual overlays
- Enhanced study management and reporting
- Full FastAPI backend with DICOM endpoints
- React frontend with Material-UI components"
    else
        echo "📝 Making initial commit..."
        commit_message="Initial commit: Tumor Detection & Segmentation System

Features:
- MONAI-based deep learning pipeline for medical imaging
- Professional DICOM viewer with Cornerstone3D integration
- Complete clinical workflow with AI analysis
- FastAPI backend with comprehensive REST API
- React frontend with Material-UI design
- Multi-modal support and clinical reporting
- Enhanced study management and visualization tools"
    fi
    
    git commit -m "$commit_message"
    
    echo "🚀 Pushing to GitHub..."
    git branch -M main
    git push -u origin main
    
    echo ""
    echo "✅ Git setup complete!"
    echo "🔗 Repository URL: https://github.com/hkevin01/tumor-detection-segmentation"
    echo "📝 Clone command: git clone git@github.com:hkevin01/tumor-detection-segmentation.git"
else
    echo "⏸️  Commit skipped. You can commit manually later with:"
    echo "   git commit -m 'Your commit message'"
    echo "   git push -u origin main"
fi

echo ""
echo "🎉 Git setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "   • Visit: https://github.com/hkevin01/tumor-detection-segmentation"
echo "   • Configure repository settings (description, topics, etc.)"
echo "   • Set up branch protection rules if needed"
echo "   • Consider setting up GitHub Actions for CI/CD"
