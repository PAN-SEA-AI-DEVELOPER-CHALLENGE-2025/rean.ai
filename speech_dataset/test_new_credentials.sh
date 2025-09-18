#!/bin/bash

echo "🧪 Testing your new IAM credentials..."
echo ""

# Load credentials from .env
source .env

# Test the connection
echo "Testing AWS connection..."
if aws sts get-caller-identity; then
    echo ""
    echo "✅ SUCCESS! Your credentials work!"
    echo ""
    echo "Next steps:"
    echo "1. List S3 buckets: aws s3 ls"
    echo "2. Create bucket: aws s3 mb s3://your-speech-dataset-bucket"
    echo "3. Test upload: python aws_s3_bulk_uploader.py --bucket your-speech-dataset-bucket --directory ./audio --dry-run"
    echo ""
    echo "🎯 Ready to upload your 90,033 audio files!"
else
    echo ""
    echo "❌ Credentials not working. Please check:"
    echo "1. Access Key ID is correct in .env file"
    echo "2. Secret Access Key is correct in .env file"  
    echo "3. No extra spaces or quotes in the values"
    echo ""
    echo "Current credentials being tested:"
    echo "Access Key ID: ${AWS_ACCESS_KEY_ID:0:10}..."
    echo "Secret Key: ${AWS_SECRET_ACCESS_KEY:0:10}..."
fi