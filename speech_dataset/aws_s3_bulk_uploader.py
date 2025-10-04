#!/usr/bin/env python3
"""
Fast Bulk S3 Uploader for Speech Dataset
Optimized for uploading 90k+ audio files to AWS S3 with parallel processing.
"""

import os
import boto3
import logging
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from tqdm import tqdm
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config
import hashlib
import time

class S3BulkUploader:
    def __init__(self, bucket_name, aws_profile=None, region='us-east-1', max_workers=20):
        """
        Initialize the S3 bulk uploader.
        
        Args:
            bucket_name (str): S3 bucket name
            aws_profile (str): AWS profile name (optional)
            region (str): AWS region
            max_workers (int): Number of parallel upload threads
        """
        self.bucket_name = bucket_name
        self.max_workers = max_workers
        
        # Configure S3 client with optimized settings
        config = Config(
            region_name=region,
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'
            },
            max_pool_connections=max_workers + 10
        )
        
        try:
            if aws_profile:
                session = boto3.Session(profile_name=aws_profile)
                self.s3_client = session.client('s3', config=config)
            else:
                self.s3_client = boto3.client('s3', config=config)
                
            # Test connection
            self.s3_client.head_bucket(Bucket=bucket_name)
            print(f"✅ Successfully connected to S3 bucket: {bucket_name}")
            
        except NoCredentialsError:
            raise Exception("❌ AWS credentials not found. Please configure your credentials.")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise Exception(f"❌ Bucket '{bucket_name}' not found.")
            else:
                raise Exception(f"❌ Error connecting to S3: {e}")
        
        # Setup logging
        self.setup_logging()
        
        # Statistics
        self.stats = {
            'total_files': 0,
            'uploaded': 0,
            'skipped': 0,
            'failed': 0,
            'total_size': 0,
            'uploaded_size': 0,
            'start_time': None,
            'end_time': None
        }
        
    def setup_logging(self):
        """Setup logging for upload tracking."""
        log_filename = f"s3_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        print(f"📝 Logging to: {log_filename}")
        
    def file_exists_in_s3(self, s3_key):
        """Check if file already exists in S3."""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False
            
    def get_file_md5(self, file_path):
        """Calculate MD5 hash of local file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
        
    def upload_file(self, file_info):
        """
        Upload a single file to S3.
        
        Args:
            file_info (dict): Dictionary containing file path and S3 key
            
        Returns:
            dict: Upload result
        """
        file_path = file_info['path']
        s3_key = file_info['key']
        file_size = file_info['size']
        
        try:
            # Check if file already exists in S3 (optional skip)
            if self.file_exists_in_s3(s3_key):
                return {
                    'status': 'skipped',
                    'file': file_path,
                    's3_key': s3_key,
                    'size': file_size,
                    'message': 'File already exists in S3'
                }
            
            # Upload with metadata
            extra_args = {
                'ContentType': 'audio/wav',
                'Metadata': {
                    'original_filename': os.path.basename(file_path),
                    'upload_timestamp': datetime.now().isoformat(),
                    'file_size': str(file_size)
                }
            }
            
            # Perform upload
            self.s3_client.upload_file(file_path, self.bucket_name, s3_key, ExtraArgs=extra_args)
            
            return {
                'status': 'success',
                'file': file_path,
                's3_key': s3_key,
                'size': file_size,
                'message': 'Upload successful'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to upload {file_path}: {str(e)}")
            return {
                'status': 'failed',
                'file': file_path,
                's3_key': s3_key,
                'size': file_size,
                'message': str(e)
            }
    
    def scan_files(self, local_directory, file_extensions=None, s3_prefix="audio/"):
        """
        Scan local directory for files to upload.
        
        Args:
            local_directory (str): Path to local directory
            file_extensions (list): List of file extensions to include
            s3_prefix (str): S3 key prefix
            
        Returns:
            list: List of file information dictionaries
        """
        if file_extensions is None:
            file_extensions = ['.wav', '.mp3', '.m4a', '.flac']
            
        files_to_upload = []
        total_size = 0
        
        print(f"🔍 Scanning directory: {local_directory}")
        
        for root, dirs, files in os.walk(local_directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                
                if file_ext in file_extensions:
                    # Create S3 key maintaining directory structure
                    rel_path = os.path.relpath(file_path, local_directory)
                    s3_key = f"{s3_prefix}{rel_path}".replace("\\", "/")  # Ensure forward slashes
                    
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    
                    files_to_upload.append({
                        'path': file_path,
                        'key': s3_key,
                        'size': file_size
                    })
        
        self.stats['total_files'] = len(files_to_upload)
        self.stats['total_size'] = total_size
        
        print(f"📊 Found {len(files_to_upload)} files ({self.format_size(total_size)})")
        return files_to_upload
    
    def format_size(self, size_bytes):
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def upload_files(self, files_to_upload, resume_from=0):
        """
        Upload files to S3 with parallel processing.
        
        Args:
            files_to_upload (list): List of file information
            resume_from (int): Index to resume from (for interrupted uploads)
        """
        if resume_from > 0:
            files_to_upload = files_to_upload[resume_from:]
            print(f"🔄 Resuming from file #{resume_from}")
        
        self.stats['start_time'] = datetime.now()
        failed_uploads = []
        
        print(f"🚀 Starting upload of {len(files_to_upload)} files using {self.max_workers} threads...")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all upload jobs
            future_to_file = {
                executor.submit(self.upload_file, file_info): file_info 
                for file_info in files_to_upload
            }
            
            # Process results with progress bar
            with tqdm(total=len(files_to_upload), desc="Uploading", unit="files") as pbar:
                for future in as_completed(future_to_file):
                    result = future.result()
                    
                    if result['status'] == 'success':
                        self.stats['uploaded'] += 1
                        self.stats['uploaded_size'] += result['size']
                    elif result['status'] == 'skipped':
                        self.stats['skipped'] += 1
                    elif result['status'] == 'failed':
                        self.stats['failed'] += 1
                        failed_uploads.append(result)
                    
                    pbar.update(1)
                    
                    # Update progress description
                    success_rate = (self.stats['uploaded'] / (self.stats['uploaded'] + self.stats['failed'])) * 100 if (self.stats['uploaded'] + self.stats['failed']) > 0 else 100
                    pbar.set_description(f"Uploading (Success: {success_rate:.1f}%)")
        
        self.stats['end_time'] = datetime.now()
        self.print_summary()
        
        # Save failed uploads for retry
        if failed_uploads:
            self.save_failed_uploads(failed_uploads)
            
    def save_failed_uploads(self, failed_uploads):
        """Save failed uploads to file for retry."""
        failed_file = f"failed_uploads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(failed_file, 'w') as f:
            json.dump(failed_uploads, f, indent=2)
        print(f"💾 Failed uploads saved to: {failed_file}")
        
    def print_summary(self):
        """Print upload summary statistics."""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        print("\n" + "="*60)
        print("📈 UPLOAD SUMMARY")
        print("="*60)
        print(f"Total files scanned: {self.stats['total_files']}")
        print(f"Successfully uploaded: {self.stats['uploaded']}")
        print(f"Skipped (already exist): {self.stats['skipped']}")
        print(f"Failed uploads: {self.stats['failed']}")
        print(f"Total size: {self.format_size(self.stats['total_size'])}")
        print(f"Uploaded size: {self.format_size(self.stats['uploaded_size'])}")
        print(f"Duration: {duration}")
        
        if self.stats['uploaded'] > 0:
            avg_speed = self.stats['uploaded_size'] / duration.total_seconds()
            print(f"Average speed: {self.format_size(avg_speed)}/s")
            files_per_second = self.stats['uploaded'] / duration.total_seconds()
            print(f"Files per second: {files_per_second:.2f}")
        
        success_rate = (self.stats['uploaded'] / self.stats['total_files']) * 100 if self.stats['total_files'] > 0 else 0
        print(f"Success rate: {success_rate:.2f}%")
        print("="*60)

def main():
    """Main function with example usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bulk upload files to AWS S3')
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--directory', required=True, help='Local directory to upload')
    parser.add_argument('--prefix', default='audio/', help='S3 key prefix (default: audio/)')
    parser.add_argument('--workers', type=int, default=20, help='Number of parallel workers (default: 20)')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
    parser.add_argument('--resume', type=int, default=0, help='Resume from file index')
    parser.add_argument('--dry-run', action='store_true', help='Scan files but don\'t upload')
    
    args = parser.parse_args()
    
    try:
        # Initialize uploader
        uploader = S3BulkUploader(
            bucket_name=args.bucket,
            aws_profile=args.profile,
            region=args.region,
            max_workers=args.workers
        )
        
        # Scan files
        files_to_upload = uploader.scan_files(
            local_directory=args.directory,
            s3_prefix=args.prefix
        )
        
        if not files_to_upload:
            print("❌ No files found to upload.")
            return
            
        if args.dry_run:
            print("🔍 Dry run completed. Use without --dry-run to start upload.")
            return
            
        # Confirm upload
        total_size_gb = uploader.stats['total_size'] / (1024**3)
        print(f"\n⚠️  You are about to upload {len(files_to_upload)} files ({total_size_gb:.2f} GB)")
        print(f"   to bucket '{args.bucket}' with prefix '{args.prefix}'")
        
        response = input("\nProceed with upload? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Upload cancelled.")
            return
            
        # Start upload
        uploader.upload_files(files_to_upload, resume_from=args.resume)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())