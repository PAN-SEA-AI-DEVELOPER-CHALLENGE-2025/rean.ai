#!/bin/bash

echo "🖥️  S3 Upload Performance Options"
echo "================================"
echo ""

# Check system resources
echo "Your system info:"
echo "CPU cores: $(sysctl -n hw.ncpu)"
echo "Memory: $(sysctl -n hw.memsize | awk '{print $1/1024/1024/1024 " GB"}')"
echo ""

echo "Upload configuration options:"
echo ""

echo "🚀 FAST (Recommended for good internet & modern laptop)"
echo "   Command: --workers 25"
echo "   CPU usage: Low-Medium"
echo "   Upload speed: Maximum"
echo "   Time estimate: 15-25 minutes"
echo ""

echo "⚡ BALANCED (Good for most laptops)"
echo "   Command: --workers 15"
echo "   CPU usage: Low"
echo "   Upload speed: Very good"
echo "   Time estimate: 20-30 minutes"
echo ""

echo "🐢 CONSERVATIVE (Light on resources)"
echo "   Command: --workers 8"
echo "   CPU usage: Very low"
echo "   Upload speed: Good"
echo "   Time estimate: 30-45 minutes"
echo ""

echo "🔋 BATTERY SAVER (Minimal resources)"
echo "   Command: --workers 4"
echo "   CPU usage: Minimal"
echo "   Upload speed: Moderate"
echo "   Time estimate: 45-60 minutes"
echo ""

echo "Which option would you like to use?"
echo "1) Fast (25 workers)"
echo "2) Balanced (15 workers)"  
echo "3) Conservative (8 workers)"
echo "4) Battery Saver (4 workers)"
echo ""
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        workers=25
        echo "🚀 Using FAST mode with 25 workers"
        ;;
    2)
        workers=15
        echo "⚡ Using BALANCED mode with 15 workers"
        ;;
    3)
        workers=8
        echo "🐢 Using CONSERVATIVE mode with 8 workers"
        ;;
    4)
        workers=4
        echo "🔋 Using BATTERY SAVER mode with 4 workers"
        ;;
    *)
        workers=15
        echo "⚡ Default: BALANCED mode with 15 workers"
        ;;
esac

echo ""
echo "Running upload command:"
cmd="source .env && python aws_s3_bulk_uploader.py --bucket pansea-storage --directory /Users/thun/Desktop/speech_dataset/audio --prefix audio_dataset/ --workers $workers --region us-east-1"
echo "$cmd"
echo ""
echo "Press Enter to execute, or Ctrl+C to cancel"
read

eval $cmd