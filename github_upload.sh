#!/bin/bash

# Quick GitHub Upload Script
# This script automates the GitHub upload process

echo "🚀 GitHub Upload Assistant for Real-Time Video Dehazing"
echo "========================================================"
echo ""

# Check if Git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Error: Git is not installed!"
    echo "Download from: https://git-scm.com/downloads"
    exit 1
fi

echo "✅ Git is installed"
echo ""

# Get GitHub username
read -p "Enter your GitHub username: " github_username

if [ -z "$github_username" ]; then
    echo "❌ GitHub username cannot be empty!"
    exit 1
fi

echo ""
echo "📦 Preparing repository..."
echo ""

# Initialize Git if not already initialized
if [ ! -d ".git" ]; then
    echo "Initializing Git repository..."
    git init
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already initialized"
fi

# Check git status
echo ""
echo "📋 Files to be committed:"
git status --short

echo ""
read -p "Do you want to proceed with commit? (y/n): " proceed

if [ "$proceed" != "y" ]; then
    echo "❌ Upload cancelled"
    exit 0
fi

# Add all files
echo ""
echo "📝 Adding files..."
git add .

# Create commit
echo ""
read -p "Enter commit message (or press Enter for default): " commit_msg

if [ -z "$commit_msg" ]; then
    commit_msg="Initial commit: Real-time video dehazing with web interface and Colab GPU support"
fi

git commit -m "$commit_msg"
echo "✅ Commit created"

# Add remote
echo ""
echo "🔗 Connecting to GitHub..."
repo_url="https://github.com/$github_username/Real-time-dehazing-deep-learning.git"

# Check if remote already exists
if git remote | grep -q "origin"; then
    echo "Remote 'origin' already exists. Updating URL..."
    git remote set-url origin "$repo_url"
else
    git remote add origin "$repo_url"
fi

echo "✅ Connected to: $repo_url"

# Rename branch to main if needed
current_branch=$(git branch --show-current)
if [ "$current_branch" != "main" ]; then
    echo "Renaming branch to 'main'..."
    git branch -M main
fi

# Push to GitHub
echo ""
echo "🚀 Pushing to GitHub..."
echo "You may be prompted for your GitHub credentials"
echo "(Use Personal Access Token, not password)"
echo ""

if git push -u origin main; then
    echo ""
    echo "🎉 SUCCESS! Your project is now on GitHub!"
    echo ""
    echo "📍 Repository URL: https://github.com/$github_username/Real-time-dehazing-deep-learning"
    echo ""
    echo "⚠️  NEXT STEPS:"
    echo "1. Update README_NEW.md:"
    echo "   - Replace YOUR_USERNAME with: $github_username"
    echo "   - Add your name and email"
    echo "   - Add model weights download links"
    echo "2. Rename README_NEW.md to README.md"
    echo "3. Push updates: git add . && git commit -m 'Update README' && git push"
    echo "4. Add repository topics on GitHub"
    echo "5. Create your first release"
    echo ""
else
    echo ""
    echo "❌ Push failed!"
    echo ""
    echo "Troubleshooting:"
    echo "1. Make sure repository exists on GitHub:"
    echo "   → Go to https://github.com/new"
    echo "   → Create repo named: Real-time-dehazing-deep-learning"
    echo "   → Do NOT initialize with README"
    echo ""
    echo "2. Authentication issues?"
    echo "   → Use Personal Access Token instead of password"
    echo "   → GitHub → Settings → Developer settings → Personal access tokens"
    echo ""
    echo "3. Large files detected?"
    echo "   → Review .gitignore file"
    echo "   → Remove large files: git rm --cached <file>"
    echo ""
    exit 1
fi
