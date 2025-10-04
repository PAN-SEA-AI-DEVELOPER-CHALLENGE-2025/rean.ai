#!/bin/bash
# Simple S3 Upload Script
# =======================

# Set credentials directly
export AWS_ACCESS_KEY_ID="AKIATTYXGZXINEV2DKPN"
export AWS_SECRET_ACCESS_KEY="GdQCTKLnMfyozTfA9p2km3zxBcbaPGaWiI+eXBja"
export AWS_DEFAULT_REGION="us-east-1"

echo "🚀 Starting S3 upload..."
echo "📊 Dataset: 16GB, 110,555 samples"
echo "📍 Target: s3://pan-sea-khmer-speech-dataset/khmer-whisper-dataset/data"
echo ""

# Upload with progress
aws s3 sync /Users/thun/Desktop/speech_dataset/mega_dataset s3://pan-sea-khmer-speech-dataset/khmer-whisper-dataset/data \
    --storage-class STANDARD_IA \
    --cli-write-timeout 0 \
    --cli-read-timeout 0

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Upload Complete!"
    echo "✅ Dataset uploaded to: s3://pan-sea-khmer-speech-dataset/khmer-whisper-dataset/data"
else
    echo "❌ Upload failed!"
fi