#!/bin/bash

# Whisper Service Startup Script for EC2
# This script sets up and starts the Whisper transcription service

set -e

echo "Starting Whisper Service setup..."

# Update system packages
sudo apt-get update

# Install Docker if not already installed
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# Install Docker Compose if not already installed
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Set environment variables (optimized for whisper-tiny)
export WHISPER_MODEL_SIZE=${WHISPER_MODEL_SIZE:-tiny}
export PORT=${PORT:-8000}

echo "Building optimized Docker image for whisper-tiny..."
docker build -t whisper-service .

echo "Stopping any existing containers..."
docker stop whisper-service-container 2>/dev/null || true
docker rm whisper-service-container 2>/dev/null || true

echo "Starting Whisper service container..."
docker run -d \
    --name whisper-service-container \
    --restart unless-stopped \
    -p 80:8000 \
    -p 8000:8000 \
    -e WHISPER_MODEL_SIZE=$WHISPER_MODEL_SIZE \
    -e PORT=8000 \
    -e HOST=0.0.0.0 \
    whisper-service

echo "FastAPI Whisper-tiny service started successfully!"
echo "Service is available at:"
echo "  - http://localhost:8000 (direct)"
echo "  - http://localhost:80 (port 80)"
echo ""
echo "Health check: curl http://localhost:8000/health"
echo "API docs: http://localhost:8000/docs"
echo "Alternative docs: http://localhost:8000/redoc"

# Show container logs
echo "Container logs (last 20 lines):"
sleep 5
docker logs --tail 20 whisper-service-container
