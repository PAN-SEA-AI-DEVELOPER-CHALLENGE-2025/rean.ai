# AWS S3 Bulk Upload Guide

This guide will help you efficiently upload your 90,033 audio files (12GB) to AWS S3 using parallel processing.

## Prerequisites

1. **AWS Account**: You need an AWS account with S3 access
2. **S3 Bucket**: Create an S3 bucket where you want to store your files
3. **AWS CLI**: Install and configure AWS CLI (recommended)

## Step 1: AWS Setup

### Option A: Using AWS CLI (Recommended)
```bash
# Install AWS CLI if not already installed
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Configure AWS credentials
aws configure
```

You'll be prompted to enter:
- **AWS Access Key ID**: Your access key
- **AWS Secret Access Key**: Your secret key  
- **Default region name**: e.g., `us-east-1`, `us-west-2`
- **Default output format**: `json`

### Option B: Using Environment Variables
```bash
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### Option C: Using AWS Credentials File
Create `~/.aws/credentials`:
```ini
[default]
aws_access_key_id = your-access-key-id
aws_secret_access_key = your-secret-access-key

[speech-dataset]
aws_access_key_id = your-access-key-id
aws_secret_access_key = your-secret-access-key
```

## Step 2: Create S3 Bucket

```bash
# Create bucket (replace 'your-bucket-name' with your desired name)
aws s3 mb s3://your-speech-dataset-bucket --region us-east-1

# Set bucket policy for your use case (optional)
aws s3api put-bucket-versioning --bucket your-speech-dataset-bucket --versioning-configuration Status=Enabled
```

## Step 3: Test Connection

```bash
# Test your AWS setup
aws s3 ls

# Test access to your specific bucket
aws s3 ls s3://your-speech-dataset-bucket
```

## Step 4: Upload Your Files

### Quick Start (Recommended Settings)
```bash
cd /Users/thun/Desktop/speech_dataset

# Dry run first to verify everything looks correct
python aws_s3_bulk_uploader.py --bucket your-speech-dataset-bucket --directory ./audio --dry-run

# Start the actual upload with optimized settings
python aws_s3_bulk_uploader.py \
    --bucket your-speech-dataset-bucket \
    --directory ./audio \
    --prefix audio/speech_dataset/ \
    --workers 30 \
    --region us-east-1
```

### Advanced Options

```bash
# With custom AWS profile
python aws_s3_bulk_uploader.py \
    --bucket your-speech-dataset-bucket \
    --directory ./audio \
    --profile speech-dataset \
    --workers 25

# Resume interrupted upload (if stopped at file #45000)
python aws_s3_bulk_uploader.py \
    --bucket your-speech-dataset-bucket \
    --directory ./audio \
    --resume 45000 \
    --workers 30

# Custom S3 organization structure
python aws_s3_bulk_uploader.py \
    --bucket your-speech-dataset-bucket \
    --directory ./audio \
    --prefix datasets/speech/audio_files/ \
    --workers 20
```

## Performance Optimization

### Recommended Settings for Your Dataset (90k files, 12GB)

- **Workers**: 20-30 (balance between speed and AWS rate limits)
- **Region**: Choose closest to your location
- **Instance Type**: If running on EC2, use instances with high network performance

### Expected Performance
- **Upload Speed**: 50-200 MB/s (depending on connection and AWS region)
- **Files per second**: 50-150 files/s
- **Estimated Total Time**: 15-45 minutes for all files

## Monitoring Progress

The script provides:
- **Real-time progress bar** showing current upload status
- **Success rate percentage** during upload
- **Detailed logs** saved to timestamped log files
- **Failed uploads** saved to JSON file for retry
- **Final summary** with statistics

## Error Handling & Recovery

### If Upload Fails or Gets Interrupted

1. **Check the log file** for error details
2. **Resume from where it stopped** using `--resume` option
3. **Retry failed uploads** using the generated failed uploads JSON file

### Common Issues & Solutions

```bash
# Rate limiting errors - reduce workers
python aws_s3_bulk_uploader.py --workers 10 ...

# Network timeout - the script auto-retries, but you can resume
python aws_s3_bulk_uploader.py --resume XXXX ...

# Permission errors - check your AWS credentials and bucket permissions
aws s3 ls s3://your-bucket-name
```

## Cost Estimation

### AWS S3 Costs (us-east-1 pricing as of 2024):
- **Storage**: ~$0.29/month for 12GB (Standard tier)
- **PUT requests**: ~$0.0054 for 90k requests (90k × $0.0005/1000)
- **Total first month**: ~$0.30

### Cost Optimization Tips:
- Use **S3 Intelligent Tiering** for automatic cost optimization
- Consider **S3 Standard-IA** if files aren't accessed frequently
- Use **S3 Glacier** for long-term archival

## Verification

After upload completes, verify your files:

```bash
# Count files in S3
aws s3 ls s3://your-speech-dataset-bucket/audio/ --recursive | wc -l

# Check total size
aws s3 ls s3://your-speech-dataset-bucket/audio/ --recursive --human-readable --summarize
```

## Security Best Practices

1. **Use IAM roles** instead of access keys when possible
2. **Enable bucket versioning** for data protection
3. **Set up bucket policies** to restrict access
4. **Enable server-side encryption**:
   ```bash
   aws s3api put-bucket-encryption \
       --bucket your-speech-dataset-bucket \
       --server-side-encryption-configuration file://encryption.json
   ```

## Troubleshooting

### Common Error Messages:
- `NoCredentialsError`: AWS credentials not configured properly
- `BucketNotFound`: Bucket name incorrect or doesn't exist
- `AccessDenied`: Insufficient permissions
- `SlowDown`: Too many requests - reduce worker count

### Debug Commands:
```bash
# Test AWS credentials
aws sts get-caller-identity

# List your buckets
aws s3 ls

# Check bucket permissions
aws s3api get-bucket-location --bucket your-bucket-name
```

## Alternative: AWS CLI Sync (Simpler but Slower)

If you prefer a simpler approach (though slower):

```bash
# Basic sync
aws s3 sync ./audio s3://your-speech-dataset-bucket/audio/

# With progress and parallel uploads
aws s3 sync ./audio s3://your-speech-dataset-bucket/audio/ \
    --cli-read-timeout 0 \
    --cli-write-timeout 0 \
    --storage-class STANDARD
```

The Python script above is recommended for better control, progress tracking, and error handling.