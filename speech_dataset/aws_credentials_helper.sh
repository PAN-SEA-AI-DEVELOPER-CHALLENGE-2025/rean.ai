#!/bin/bash

echo "🔑 AWS Credentials Setup Helper"
echo "================================"
echo ""

# Function to test credentials
test_credentials() {
    echo "Testing AWS credentials..."
    if aws sts get-caller-identity > /dev/null 2>&1; then
        echo "✅ AWS credentials are working!"
        echo ""
        echo "Your identity:"
        aws sts get-caller-identity
        return 0
    else
        echo "❌ AWS credentials are not working"
        return 1
    fi
}

echo "Option 1: Load credentials from .env file"
echo "   Edit .env file with your current credentials, then run:"
echo "   source .env && aws sts get-caller-identity"
echo ""

echo "Option 2: Export credentials directly"
echo "   Run these commands with your actual values:"
echo "   export AWS_ACCESS_KEY_ID=\"your-access-key\""
echo "   export AWS_SECRET_ACCESS_KEY=\"your-secret-key\""
echo "   export AWS_SESSION_TOKEN=\"your-session-token\""
echo ""

echo "Option 3: Get fresh credentials"
echo ""
echo "🌐 Where to get fresh AWS credentials:"
echo ""
echo "A) AWS Console -> CloudShell:"
echo "   - Go to https://console.aws.amazon.com"
echo "   - Click CloudShell icon (>_) in top bar"
echo "   - Run: aws sts get-session-token --duration-seconds 3600"
echo ""
echo "B) AWS Console -> IAM:"
echo "   - Go to IAM -> Users -> Your user -> Security credentials"
echo "   - Create new Access Key (permanent credentials)"
echo ""
echo "C) AWS CLI Profile:"
echo "   - Run: aws configure --profile myprofile"
echo "   - Use: aws s3 ls --profile myprofile"
echo ""

# Try current credentials
echo "🔍 Testing current credentials..."
if test_credentials; then
    echo ""
    echo "🚀 Ready to proceed! Your next steps:"
    echo "1. List your buckets: aws s3 ls"
    echo "2. Create a bucket: aws s3 mb s3://your-speech-dataset-bucket"
    echo "3. Run upload: python aws_s3_bulk_uploader.py --bucket your-speech-dataset-bucket --directory ./audio --dry-run"
else
    echo ""
    echo "⚠️  Please get fresh credentials and try again."
    echo ""
    echo "Quick test after updating credentials:"
    echo "source .env && aws sts get-caller-identity"
fi