#!/bin/bash

# Quick AWS S3 Setup Test Script

echo "🔍 Testing AWS Configuration..."

# Test credentials
echo "1. Testing AWS Identity..."
aws sts get-caller-identity

if [ $? -eq 0 ]; then
    echo "✅ AWS credentials are valid!"
    
    echo ""
    echo "2. Listing your S3 buckets..."
    aws s3 ls
    
    echo ""
    echo "3. Testing S3 access..."
    echo "Do you want to create a test bucket for your speech dataset? (y/n)"
    read -r create_bucket
    
    if [[ $create_bucket == "y" || $create_bucket == "Y" ]]; then
        echo "Enter your desired bucket name (e.g., your-speech-dataset-bucket):"
        read -r bucket_name
        
        echo "Creating bucket: $bucket_name"
        aws s3 mb s3://$bucket_name --region us-east-1
        
        if [ $? -eq 0 ]; then
            echo "✅ Bucket created successfully!"
            echo ""
            echo "🚀 Ready to upload! Run this command:"
            echo "python aws_s3_bulk_uploader.py --bucket $bucket_name --directory ./audio --dry-run"
        else
            echo "❌ Failed to create bucket. It might already exist or you may need different permissions."
        fi
    fi
else
    echo "❌ AWS credentials are not working. Please:"
    echo "   1. Get fresh credentials from AWS Console"
    echo "   2. Run 'aws configure' again"
    echo "   3. Or set environment variables for session credentials"
fi