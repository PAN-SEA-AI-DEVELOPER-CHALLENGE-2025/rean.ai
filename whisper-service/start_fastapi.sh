#!/bin/bash

# FastAPI Whisper Service Startup Script
# Optimized for MacBook Pro M3 8GB RAM

set -e

echo "🚀 FastAPI Dual-Language Transcription Service"
echo "=============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements_fastapi.txt"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check mode argument
MODE=${1:-"auto"}

case $MODE in
    "khmer-only")
        echo "🔧 Starting in KHMER-ONLY mode (Memory optimized for 8GB RAM)"
        export KHMER_ONLY_MODE=true
        export WHISPER_MODEL_SIZE=tiny
        ;;
    "dual")
        echo "🔧 Starting in DUAL mode (Both English + Khmer)"
        echo "⚠️  Warning: This may use significant memory on 8GB systems"
        export KHMER_ONLY_MODE=false
        export WHISPER_MODEL_SIZE=tiny
        ;;
    "auto")
        echo "🔧 Starting in AUTO mode (Tiny Whisper + MMS)"
        echo "💡 Tip: Use './start_fastapi.sh khmer-only' for memory optimization"
        export KHMER_ONLY_MODE=false
        export WHISPER_MODEL_SIZE=tiny
        ;;
    *)
        echo "❌ Invalid mode. Use: auto, dual, or khmer-only"
        echo ""
        echo "Usage:"
        echo "  ./start_fastapi.sh auto        # Both models with tiny Whisper (default)"
        echo "  ./start_fastapi.sh dual        # Both models with tiny Whisper"  
        echo "  ./start_fastapi.sh khmer-only  # Only Khmer (saves ~1GB RAM)"
        exit 1
        ;;
esac

# Set other environment variables
export HOST=${HOST:-"0.0.0.0"}
export PORT=${PORT:-"8000"}

echo ""
echo "📊 Configuration:"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Whisper Model: ${WHISPER_MODEL_SIZE}"
echo "  Khmer Only Mode: ${KHMER_ONLY_MODE}"
echo ""

# Kill any existing processes on the port
echo "🧹 Cleaning up any existing processes on port $PORT..."
lsof -ti:$PORT | xargs kill -9 2>/dev/null || true

echo "🚀 Starting FastAPI server..."
echo "📚 API Documentation will be available at: http://localhost:$PORT/docs"
echo "📖 Alternative docs: http://localhost:$PORT/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python app_fastapi.py
