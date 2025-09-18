#!/bin/bash

# Pan-Sea Minimal Docker Startup Script
# This script starts the application with minimal configuration for testing

echo "🌊 Starting Pan-Sea with Minimal Configuration"
echo "=============================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Docker
if ! command_exists docker; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose found"
echo ""

# Stop any existing containers
echo "🛑 Stopping any existing containers..."
docker-compose down --remove-orphans 2>/dev/null
docker-compose -f docker-compose.minimal.yml down --remove-orphans 2>/dev/null

echo ""
echo "🏗️  Building and starting with minimal configuration..."
echo "This setup includes:"
echo "   - Backend with dummy Supabase configuration"
echo "   - Frontend connected to backend"
echo "   - No external dependencies required"
echo "   - Suitable for testing basic functionality"
echo ""

# Start the minimal setup
docker-compose -f docker-compose.minimal.yml up --build

echo ""
echo "🏁 Startup complete!"
echo ""
echo "📋 Access your applications:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo "   - API Documentation: http://localhost:8000/docs"
echo ""
echo "⚠️  Note: This is a minimal setup for testing."
echo "   Some features requiring external services may not work."
echo "   For full functionality, set up real API keys in your .env files."
