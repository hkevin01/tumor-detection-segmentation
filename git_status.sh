#!/bin/bash

# Git Quick Reference for Tumor Detection Project
echo "🚀 Tumor Detection Project - Git Commands"
echo "==========================================="
echo ""

# Check current status
echo "📊 Current Git Status:"
git status --short
echo ""

echo "🔄 Common Git Commands:"
echo ""
echo "📥 Pull latest changes:"
echo "  git pull origin main"
echo ""
echo "📤 Push your changes:"
echo "  git add ."
echo "  git commit -m 'Your descriptive message'"
echo "  git push origin main"
echo ""
echo "🌿 Branch operations:"
echo "  git checkout -b feature/your-feature-name"
echo "  git checkout main"
echo "  git branch -a"
echo ""
echo "📋 View commit history:"
echo "  git log --oneline -10"
echo ""
echo "🔍 Check what changed:"
echo "  git diff"
echo "  git diff --staged"
echo ""

# Repository info
echo "📍 Repository Information:"
echo "  Remote: $(git remote get-url origin)"
echo "  Branch: $(git branch --show-current)"
echo "  Last commit: $(git log -1 --pretty=format:'%h - %s (%cr)')"
echo ""

echo "✅ Git setup complete! Your project is connected to GitHub."
echo "📖 For detailed Git workflow, see: docs/GIT_SETUP_GUIDE.md"
