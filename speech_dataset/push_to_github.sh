#!/bin/bash
# Push Speech Dataset Code to GitHub
# ==================================

echo "🚀 GitHub Push Script for Speech Dataset Project"
echo "================================================"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not a git repository!"
    echo "Run: git init"
    exit 1
fi

# Check git status
echo "📊 Git Status:"
git status --short

echo ""
echo "📁 Files to be committed (excluding large datasets):"
git add --dry-run . | head -20
if [ $(git add --dry-run . | wc -l) -gt 20 ]; then
    echo "... and $(( $(git add --dry-run . | wc -l) - 20 )) more files"
fi

# Confirm commit
echo ""
read -p "🤔 Continue with commit and push? (y/N): " confirm
if [[ $confirm != [yY] && $confirm != [yY][eE][sS] ]]; then
    echo "Git push cancelled"
    exit 0
fi

# Add files (respecting .gitignore)
echo ""
echo "📝 Adding files to git..."
git add .

# Commit with informative message
echo "💾 Creating commit..."
COMMIT_MSG="Add Whisper SageMaker training setup with mega dataset merger

- Complete mega dataset merger with 110,555 samples (138.56 hours)
- SageMaker Whisper fine-tuning notebook and scripts
- Fixed LSR42 transcript parsing bug
- Comprehensive training guides and documentation
- AWS S3 upload utilities for dataset deployment"

git commit -m "$COMMIT_MSG"

# Push to remote
echo "📤 Pushing to GitHub..."
git push origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Successfully pushed to GitHub!"
    echo "✅ Code is now backed up in your repository"
    echo ""
    echo "📍 Repository: $(git remote get-url origin 2>/dev/null || echo 'Remote URL not found')"
else
    echo "❌ Push failed! Check your GitHub authentication"
    exit 1
fi