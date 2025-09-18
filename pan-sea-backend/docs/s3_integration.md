# AWS S3 Integration Guide

This document provides comprehensive information about integrating AWS S3 with your Pan-Sea Backend project.

## Overview

The AWS S3 integration allows you to:
- Store audio files, documents, and other media files in the cloud
- Generate presigned URLs for secure file access
- Manage file metadata and organization
- Scale file storage without managing local storage infrastructure

## Prerequisites

1. **AWS Account**: You need an active AWS account
2. **IAM User**: Create an IAM user with S3 permissions
3. **S3 Bucket**: Create an S3 bucket for your files
4. **Access Keys**: Generate access key ID and secret access key

## AWS S3 Setup

### 1. Create S3 Bucket

1. Go to AWS S3 Console
2. Click "Create bucket"
3. Choose a unique bucket name
4. Select your preferred region
5. Configure bucket settings (recommendations):
   - Block all public access: Enabled
   - Bucket versioning: Optional
   - Tags: Add relevant tags for cost tracking

### 2. Create IAM User

1. Go to AWS IAM Console
2. Create a new user
3. Attach the following policy (or create a custom one):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket",
                "s3:GetObjectVersion"
            ],
            "Resource": [
                "arn:aws:s3:::YOUR_BUCKET_NAME",
                "arn:aws:s3:::YOUR_BUCKET_NAME/*"
            ]
        }
    ]
}
```

### 3. Generate Access Keys

1. Select your IAM user
2. Go to "Security credentials" tab
3. Create access key
4. Save the Access Key ID and Secret Access Key securely

## Configuration

### Environment Variables

Add the following variables to your `.env` file:

```bash
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_id_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key_here
AWS_REGION=us-east-1
AWS_S3_BUCKET=your_s3_bucket_name_here
AWS_S3_ENDPOINT_URL=
AWS_S3_USE_SSL=true
AWS_S3_VERIFY_SSL=true
```

### Configuration Options

- `AWS_ACCESS_KEY_ID`: Your AWS access key ID
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret access key
- `AWS_REGION`: AWS region where your S3 bucket is located
- `AWS_S3_BUCKET`: Name of your S3 bucket
- `AWS_S3_ENDPOINT_URL`: Custom endpoint URL (leave empty for AWS S3)
- `AWS_S3_USE_SSL`: Whether to use SSL for connections
- `AWS_S3_VERIFY_SSL`: Whether to verify SSL certificates

## Usage

### 1. S3 Service

The `S3Service` class provides the core S3 functionality:

```python
from app.core.s3 import s3_service

# Upload a file
success = await s3_service.upload_file(
    file_path="/path/to/file.mp3",
    s3_key="audio/class123/file.mp3",
    content_type="audio/mpeg"
)

# Download a file
success = await s3_service.download_file(
    s3_key="audio/class123/file.mp3",
    local_path="/local/path/file.mp3"
)

# Delete a file
success = await s3_service.delete_file("audio/class123/file.mp3")

# Get presigned URL
url = s3_service.get_file_url("audio/class123/file.mp3", expires_in=3600)
```

### 2. API Endpoints

The S3 integration provides several REST API endpoints:

#### Upload File
```http
POST /api/v1/s3/upload
Content-Type: multipart/form-data

file: [file]
folder: uploads
```

#### List Files
```http
GET /api/v1/s3/files?prefix=audio&max_keys=100
```

#### Get File URL
```http
GET /api/v1/s3/file/{s3_key}/url?expires_in=3600
```

#### Delete File
```http
DELETE /api/v1/s3/file/{s3_key}
```

#### Get File Metadata
```http
GET /api/v1/s3/file/{s3_key}/metadata
```

#### Check File Exists
```http
GET /api/v1/s3/file/{s3_key}/exists
```

### 3. Audio Service Integration

The audio service now automatically stores files in S3:

```python
from app.services.audio_service import audio_service

# Transcribe and store in S3
result = await audio_service.transcribe_recording(
    file_path="/path/to/audio.mp3",
    class_id="class123"
)

# The audio file is automatically uploaded to S3 with key: audio/class123/{uuid}.mp3
```

## File Organization

### Recommended S3 Key Structure

```
bucket/
├── audio/
│   ├── class_id_1/
│   │   ├── uuid1.mp3
│   │   └── uuid2.wav
│   └── class_id_2/
│       └── uuid3.m4a
├── documents/
│   ├── user_id_1/
│   │   ├── uuid4.pdf
│   │   └── uuid5.docx
│   └── user_id_2/
│       └── uuid6.txt
└── uploads/
    └── user_id_1/
        └── uuid7.jpg
```

### Metadata

Each file includes metadata for better organization:
- `user_id`: ID of the user who uploaded the file
- `class_id`: ID of the class (for audio files)
- `original_filename`: Original filename
- `content_type`: MIME type of the file
- `upload_timestamp`: When the file was uploaded

## Security Considerations

### 1. Access Control
- Files are not publicly accessible
- Access is controlled through presigned URLs
- URLs expire after a configurable time (default: 1 hour)

### 2. IAM Permissions
- Use least privilege principle
- Regularly rotate access keys
- Monitor access logs

### 3. File Validation
- Validate file types and sizes
- Scan for malware (consider AWS GuardDuty)
- Implement rate limiting

## Cost Optimization

### 1. Storage Classes
- Use S3 Standard for frequently accessed files
- Use S3 Standard-IA for infrequently accessed files
- Use S3 Glacier for long-term archival

### 2. Lifecycle Policies
- Automatically transition files to cheaper storage classes
- Delete old files automatically
- Archive files after a certain period

### 3. Monitoring
- Set up CloudWatch alarms for costs
- Monitor storage usage
- Track API request costs

## Troubleshooting

### Common Issues

1. **Access Denied**
   - Check IAM permissions
   - Verify bucket name and region
   - Ensure access keys are correct

2. **File Not Found**
   - Check S3 key path
   - Verify file exists in bucket
   - Check bucket permissions

3. **Upload Failures**
   - Check file size limits
   - Verify network connectivity
   - Check AWS service status

### Debug Mode

Enable debug logging in your `.env` file:

```bash
DEBUG=true
```

### AWS CLI Testing

Test your S3 configuration with AWS CLI:

```bash
# List buckets
aws s3 ls

# List objects in bucket
aws s3 ls s3://your-bucket-name

# Upload test file
aws s3 cp test.txt s3://your-bucket-name/

# Download test file
aws s3 cp s3://your-bucket-name/test.txt ./
```

## Best Practices

1. **File Naming**: Use UUIDs to avoid conflicts
2. **Error Handling**: Implement proper error handling and retries
3. **Monitoring**: Set up logging and monitoring
4. **Backup**: Consider cross-region replication
5. **Versioning**: Enable bucket versioning for critical files
6. **Encryption**: Use server-side encryption for sensitive data

## Migration from Local Storage

If you're migrating from local file storage:

1. **Backup**: Create backups of all local files
2. **Upload**: Use the S3 service to upload existing files
3. **Update Database**: Update file references to use S3 keys
4. **Verify**: Test file access through S3
5. **Cleanup**: Remove local files after verification

## Support

For issues related to:
- **AWS S3**: Check AWS documentation and support
- **Integration**: Check application logs and error messages
- **Configuration**: Verify environment variables and permissions
