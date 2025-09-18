#!/usr/bin/env python3
"""
Server Startup Script

This script starts the YouTube Audio Extractor FastAPI server with proper configuration.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import get_config


def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = [
        'fastapi', 'uvicorn', 'yt_dlp', 'librosa', 'soundfile', 'pydantic'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages


def install_dependencies():
    """Install missing dependencies."""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def check_ffmpeg():
    """Check if FFmpeg is available."""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def start_server(host='0.0.0.0', port=8000, reload=False, workers=1):
    """Start the FastAPI server."""
    config = get_config()
    
    # Override with command line arguments
    host = host or config['host']
    port = port or config['port']
    
    print(f"🚀 Starting YouTube Audio Extractor API server...")
    print(f"📍 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🔄 Reload: {reload}")
    print(f"👥 Workers: {workers}")
    print(f"📁 Output directory: {config['output_dir']}")
    print(f"🎵 Default sample rate: {config['sample_rate']}Hz")
    
    try:
        import uvicorn
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers if not reload else 1,  # Workers > 1 not compatible with reload
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Start YouTube Audio Extractor API server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to (default: 8000)')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload for development')
    parser.add_argument('--workers', type=int, default=1, help='Number of worker processes')
    parser.add_argument('--install-deps', action='store_true', help='Install dependencies before starting')
    parser.add_argument('--skip-checks', action='store_true', help='Skip dependency and FFmpeg checks')
    
    args = parser.parse_args()
    
    print("🎵 YouTube Audio Extractor API")
    print("=" * 50)
    
    if not args.skip_checks:
        # Check dependencies
        print("🔍 Checking dependencies...")
        missing = check_dependencies()
        
        if missing:
            print(f"❌ Missing packages: {', '.join(missing)}")
            if args.install_deps:
                if not install_dependencies():
                    sys.exit(1)
            else:
                print("💡 Run with --install-deps to install automatically")
                print("   Or run: pip install -r requirements.txt")
                sys.exit(1)
        else:
            print("✅ All dependencies are installed")
        
        # Check FFmpeg
        print("🔍 Checking FFmpeg...")
        if not check_ffmpeg():
            print("❌ FFmpeg not found. Please install FFmpeg:")
            print("   macOS: brew install ffmpeg")
            print("   Ubuntu: sudo apt install ffmpeg")
            print("   Windows: Download from https://ffmpeg.org/")
            if not args.skip_checks:
                sys.exit(1)
        else:
            print("✅ FFmpeg is available")
    
    # Start server
    print("\n🚀 Starting server...")
    start_server(
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers
    )


if __name__ == "__main__":
    main()
