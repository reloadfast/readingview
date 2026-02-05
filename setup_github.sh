#!/bin/bash
# GitHub Repository Setup Script
# This script helps you set up a GitHub repository using a personal access token

echo "🐙 GitHub Repository Setup Helper"
echo "=================================="
echo ""

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "⚠️  Not a git repository. Initializing..."
    git init
    echo "✅ Git repository initialized"
else
    echo "✅ Already a git repository"
fi

# Get GitHub username
echo ""
read -p "Enter your GitHub username: " GITHUB_USERNAME

# Get repository name
echo ""
read -p "Enter repository name [jelu-abs-sync]: " REPO_NAME
REPO_NAME=${REPO_NAME:-jelu-abs-sync}

# Get GitHub token
echo ""
echo "⚠️  You need a GitHub Personal Access Token"
echo "   Go to: https://github.com/settings/tokens"
echo "   Generate a new token with 'repo' scope"
echo ""
read -sp "Enter your GitHub token: " GITHUB_TOKEN
echo ""

# Ask if private
echo ""
read -p "Make repository private? (y/N): " MAKE_PRIVATE
if [[ $MAKE_PRIVATE =~ ^[Yy]$ ]]; then
    PRIVATE="true"
else
    PRIVATE="false"
fi

# Create repository via GitHub API
echo ""
echo "📦 Creating repository on GitHub..."
RESPONSE=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
     -d "{
       \"name\": \"$REPO_NAME\",
       \"description\": \"Sync middleware for Jelu and Audiobookshelf\",
       \"private\": $PRIVATE
     }" \
     https://api.github.com/user/repos)

# Check if successful
if echo "$RESPONSE" | grep -q "\"id\""; then
    echo "✅ Repository created successfully!"
    REPO_URL="https://github.com/$GITHUB_USERNAME/$REPO_NAME"
    echo "   URL: $REPO_URL"
else
    echo "❌ Failed to create repository"
    echo "   Response: $RESPONSE"
    exit 1
fi

# Add remote
echo ""
echo "🔗 Adding remote origin..."
git remote remove origin 2>/dev/null  # Remove if exists
git remote add origin "https://$GITHUB_TOKEN@github.com/$GITHUB_USERNAME/$REPO_NAME.git"
echo "✅ Remote added"

# Check if there are files to commit
if [ -z "$(git status --porcelain)" ]; then
    echo ""
    echo "⚠️  No files to commit. Add some files first:"
    echo "   git add ."
    echo "   git commit -m 'Initial commit'"
else
    # Stage all files
    echo ""
    echo "📝 Staging files..."
    git add .
    
    # Commit
    echo ""
    read -p "Enter commit message [Initial commit]: " COMMIT_MSG
    COMMIT_MSG=${COMMIT_MSG:-Initial commit}
    git commit -m "$COMMIT_MSG"
    echo "✅ Files committed"
fi

# Ensure we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo ""
    echo "🔀 Renaming branch to 'main'..."
    git branch -M main
fi

# Push
echo ""
read -p "Push to GitHub now? (Y/n): " DO_PUSH
if [[ ! $DO_PUSH =~ ^[Nn]$ ]]; then
    echo "⬆️  Pushing to GitHub..."
    git push -u origin main
    echo "✅ Pushed successfully!"
    echo ""
    echo "🎉 All done! Your repository is at:"
    echo "   $REPO_URL"
else
    echo ""
    echo "⏸️  Skipped push. You can push later with:"
    echo "   git push -u origin main"
fi

echo ""
echo "📚 Next steps:"
echo "   1. View your repository: $REPO_URL"
echo "   2. Edit README.md with your specific details"
echo "   3. Configure settings in your repository"
echo ""
echo "💡 Tip: In Zed, you can use Git commands via Command Palette (Cmd/Ctrl+Shift+P)"
