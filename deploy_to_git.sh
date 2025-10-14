#!/bin/bash
# 🚀 Git Deployment Script for Amazon SKU Cleanup Tool
# Run this after setting up your remote repository

set -e  # Exit on any error

echo "🚀 Amazon SKU Cleanup Tool - Git Deployment"
echo "=============================================="

# Check if remote is configured
if ! git remote | grep -q origin; then
    echo "❌ No remote 'origin' configured."
    echo ""
    echo "💡 To set up remote:"
    echo "   git remote add origin <your-repository-url>"
    echo "   Example: git remote add origin https://github.com/username/amazon-sku-cleanup.git"
    exit 1
fi

REMOTE_URL=$(git remote get-url origin)
echo "✅ Remote repository: $REMOTE_URL"

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Current branch: $CURRENT_BRANCH"

# Show recent commits
echo ""
echo "📋 Recent commits:"
git log --oneline -5

echo ""
echo "🚀 Pushing to remote repository..."
echo "   This may take a moment..."

# Push to remote
git push -u origin "$CURRENT_BRANCH"

echo ""
echo "🎉 SUCCESS! Your project is now on Git!"
echo ""
echo "📋 What's next:"
echo "   1. Set up automated deployment (CI/CD)"
echo "   2. Configure environment variables for production"
echo "   3. Set up monitoring and alerting"
echo "   4. Schedule daily execution with cron"
echo ""
echo "🔧 Production deployment commands:"
echo "   # Test run"
echo "   DRY_RUN=true python3 sku-cleanup-tool/main.py"
echo ""
echo "   # Production run"
echo "   DRY_RUN=false python3 sku-cleanup-tool/main.py"
echo ""
echo "   # Daily cron job"
echo "   echo '0 2 * * * cd $(pwd) && python3 sku-cleanup-tool/main.py >> logs/daily_cleanup.log 2>&1' | crontab -"
echo ""
echo "✅ Your Amazon SKU Cleanup Tool is ready for production!"
