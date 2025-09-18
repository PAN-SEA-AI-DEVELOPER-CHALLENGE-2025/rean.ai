#!/bin/bash

# Pan-Sea Frontend Dependency Fix Script
# This script helps resolve common dependency issues, especially with @google/generative-ai

echo "🔧 Pan-Sea Frontend Dependency Fix Script"
echo "=========================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required tools
if ! command_exists npm; then
    echo "❌ npm is not installed. Please install Node.js first."
    exit 1
fi

if ! command_exists docker; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

echo "✅ Required tools found"
echo ""

# Navigate to frontend directory
FRONTEND_DIR="pan-sea-frontend"
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ Frontend directory not found. Please run this script from the pan-sea root directory."
    exit 1
fi

cd "$FRONTEND_DIR"
echo "📁 Working in $FRONTEND_DIR directory"
echo ""

# Step 1: Clean up existing lockfiles and node_modules
echo "🧹 Step 1: Cleaning up existing dependencies..."
rm -rf node_modules
rm -f package-lock.json yarn.lock

# Check for external lockfiles (the issue mentioned in the error)
if [ -f "/Users/thun/package-lock.json" ]; then
    echo "⚠️  Found external lockfile at /Users/thun/package-lock.json"
    echo "   This might be causing conflicts. Consider removing or moving it."
fi

echo "✅ Cleaned up old dependencies"
echo ""

# Step 2: Reinstall dependencies
echo "📦 Step 2: Reinstalling dependencies..."
npm cache clean --force
npm install

if [ $? -ne 0 ]; then
    echo "❌ npm install failed. Trying alternative approaches..."
    
    # Try with different approaches
    echo "🔄 Trying with --legacy-peer-deps..."
    npm install --legacy-peer-deps
    
    if [ $? -ne 0 ]; then
        echo "🔄 Trying with --force..."
        npm install --force
    fi
fi

echo "✅ Dependencies reinstalled"
echo ""

# Step 3: Verify specific dependency
echo "🔍 Step 3: Verifying @google/generative-ai installation..."
if npm list @google/generative-ai >/dev/null 2>&1; then
    echo "✅ @google/generative-ai is properly installed"
else
    echo "⚠️  @google/generative-ai not found, installing specifically..."
    npm install @google/generative-ai
fi

echo ""

# Step 4: Test build
echo "🏗️  Step 4: Testing build..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo ""
    echo "🐳 Ready to rebuild Docker image. Run:"
    echo "   cd .."
    echo "   docker-compose build --no-cache frontend"
    echo "   docker-compose up"
else
    echo "❌ Build failed. Please check the error messages above."
    echo ""
    echo "🔧 Troubleshooting suggestions:"
    echo "1. Check if all environment variables are set correctly"
    echo "2. Verify that all required dependencies are in package.json"
    echo "3. Try running: npm audit fix"
    echo "4. Check for any conflicting global npm packages"
    
    echo ""
    echo "📋 System information:"
    echo "Node version: $(node --version)"
    echo "npm version: $(npm --version)"
    echo "Platform: $(uname -s)"
fi

echo ""
echo "🏁 Script completed!"
