#!/bin/bash

# Setup script for Fly.io deployment with GitHub Actions
# This script helps you get the necessary tokens and set up deployment

echo "🚀 Fly.io Deployment Setup"
echo "=========================="

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl is not installed. Please install it first:"
    echo "   curl -L https://fly.io/install.sh | sh"
    exit 1
fi

echo "✅ flyctl is installed"

# Check if user is authenticated
if ! flyctl auth whoami &> /dev/null; then
    echo "🔐 You need to authenticate with Fly.io first:"
    echo "   flyctl auth login"
    exit 1
fi

echo "✅ Authenticated with Fly.io"

# Get Fly.io API token
echo ""
echo "🔑 Getting Fly.io API token..."
FLY_TOKEN=$(flyctl auth token)
echo "✅ Fly.io API token generated"
echo ""
echo "📋 Add this token to your GitHub repository secrets:"
echo "   Name: FLY_API_TOKEN"
echo "   Value: $FLY_TOKEN"
echo ""
echo "🔗 Go to: https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]\([^/]*\/[^/]*\).*/\1/')/settings/secrets/actions"
echo ""

# Check if app exists
if flyctl apps list | grep -q "cvgen-c-jysq"; then
    echo "✅ Fly.io app 'cvgen-c-jysq' exists"
else
    echo "⚠️  Fly.io app 'cvgen-c-jysq' not found"
    echo "   You may need to create it first with: flyctl apps create cvgen-c-jysq"
fi

echo ""
echo "📝 Next steps:"
echo "1. Add FLY_API_TOKEN to GitHub repository secrets"
echo "2. Add OPENROUTER_API_KEY to GitHub repository secrets"
echo "3. Push to main branch to trigger automatic deployment"
echo ""
echo "📚 For more information, see: docs/DEPLOYMENT.md" 