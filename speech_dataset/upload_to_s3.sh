#!/bin/bash
# Upload Mega Dataset to S3 for SageMaker Training
# ==============================================

echo "🚀 S3 Upload Script for Khmer Whisper Dataset"
echo "=============================================="

# Configuration
DATASET_PATH="/Users/thun/Desktop/speech_dataset/mega_dataset"
S3_BUCKET_NAME="pan-sea-khmer-speech-dataset"  # Bucket for Khmer speech data
S3_PREFIX="khmer-whisper-dataset"

# Check if AWS CLI is configured
echo "🔍 Checking AWS credentials..."
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS credentials not configured!"
    echo "Please run: aws configure"
    echo "Or set these environment variables:"
    echo "   export AWS_ACCESS_KEY_ID=your-access-key"
    echo "   export AWS_SECRET_ACCESS_KEY=your-secret-key"
    echo "   export AWS_DEFAULT_REGION=us-east-1"
    exit 1
fi

echo "✅ AWS credentials configured"
aws sts get-caller-identity

# Check dataset exists
if [ ! -d "$DATASET_PATH" ]; then
    echo "❌ Dataset not found: $DATASET_PATH"
    exit 1
fi

# Get dataset info
DATASET_SIZE=$(du -sh "$DATASET_PATH" | cut -f1)
TOTAL_FILES=$(find "$DATASET_PATH" -type f | wc -l | tr -d ' ')

echo ""
echo "📊 Dataset Information:"
echo "   Path: $DATASET_PATH"
echo "   Size: $DATASET_SIZE"
echo "   Files: $TOTAL_FILES"
echo "   Target: s3://$S3_BUCKET_NAME/$S3_PREFIX/"

# Confirm upload
echo ""
read -p "🤔 Continue with upload? (y/N): " confirm
if [[ $confirm != [yY] && $confirm != [yY][eE][sS] ]]; then
    echo "Upload cancelled"
    exit 0
fi

# Create S3 bucket if it doesn't exist
echo ""
echo "🪣 Checking/creating S3 bucket..."
if ! aws s3 ls "s3://$S3_BUCKET_NAME" > /dev/null 2>&1; then
    echo "Creating bucket: $S3_BUCKET_NAME"
    aws s3 mb "s3://$S3_BUCKET_NAME"
else
    echo "✅ Bucket exists: $S3_BUCKET_NAME"
fi

# Start upload with progress
echo ""
echo "📤 Starting S3 upload..."
echo "   This may take 20-40 minutes for 16GB"
echo "   You can monitor progress in another terminal with:"
echo "   aws s3 ls s3://$S3_BUCKET_NAME/$S3_PREFIX/ --recursive --human-readable"

# Sync with progress and multipart upload for large files
aws s3 sync "$DATASET_PATH" "s3://$S3_BUCKET_NAME/$S3_PREFIX/data" \
    --storage-class STANDARD_IA \
    --cli-write-timeout 0 \
    --cli-read-timeout 0

# Check upload success
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Upload Complete!"
    echo "✅ Dataset uploaded to: s3://$S3_BUCKET_NAME/$S3_PREFIX/data"
    
    # Verify upload
    echo ""
    echo "🔍 Verifying upload..."
    aws s3 ls "s3://$S3_BUCKET_NAME/$S3_PREFIX/data/" --recursive --summarize
    
    echo ""
    echo "📝 S3 Path for SageMaker:"
    echo "   s3://$S3_BUCKET_NAME/$S3_PREFIX/data"
    
else
    echo "❌ Upload failed!"
    exit 1
fi