#!/usr/bin/env python3
"""
Example usage of the S3 Bulk Uploader for speech dataset
"""

import os
from aws_s3_bulk_uploader import S3BulkUploader

def main():
    """Example usage of the S3BulkUploader class."""
    
    # Configuration
    BUCKET_NAME = "your-speech-dataset-bucket"  # Replace with your bucket name
    LOCAL_AUDIO_DIR = "/Users/thun/Desktop/speech_dataset/audio"
    S3_PREFIX = "audio/speech_dataset/"
    MAX_WORKERS = 25  # Adjust based on your network and AWS limits
    
    try:
        print("🚀 Starting S3 Bulk Upload Example")
        print("=" * 50)
        
        # Initialize the uploader
        uploader = S3BulkUploader(
            bucket_name=BUCKET_NAME,
            max_workers=MAX_WORKERS,
            region='us-east-1'  # Change to your preferred region
        )
        
        # Scan files in the audio directory
        print(f"📁 Scanning files in: {LOCAL_AUDIO_DIR}")
        files_to_upload = uploader.scan_files(
            local_directory=LOCAL_AUDIO_DIR,
            file_extensions=['.wav'],  # Only WAV files for this dataset
            s3_prefix=S3_PREFIX
        )
        
        if not files_to_upload:
            print("❌ No audio files found to upload!")
            return
        
        # Show preview of first few files
        print("\n📋 Preview of files to upload:")
        for i, file_info in enumerate(files_to_upload[:5]):
            print(f"   {i+1}. {os.path.basename(file_info['path'])} → {file_info['key']}")
        
        if len(files_to_upload) > 5:
            print(f"   ... and {len(files_to_upload) - 5} more files")
        
        # Get user confirmation
        total_size_mb = sum(f['size'] for f in files_to_upload) / (1024 * 1024)
        print(f"\n📊 Upload Summary:")
        print(f"   Total files: {len(files_to_upload)}")
        print(f"   Total size: {total_size_mb:.1f} MB")
        print(f"   S3 bucket: {BUCKET_NAME}")
        print(f"   S3 prefix: {S3_PREFIX}")
        print(f"   Parallel workers: {MAX_WORKERS}")
        
        # Uncomment the line below to skip confirmation for automated runs
        # proceed = 'y'
        proceed = input("\n❓ Proceed with upload? (y/N): ").strip().lower()
        
        if proceed != 'y':
            print("❌ Upload cancelled by user.")
            return
        
        # Start the upload
        print("\n🚀 Starting parallel upload...")
        uploader.upload_files(files_to_upload)
        
        print("\n✅ Upload process completed!")
        print("📝 Check the log file for detailed results.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check your AWS credentials are configured")
        print("2. Verify the S3 bucket exists and you have write permissions")
        print("3. Check your internet connection")
        print("4. Review the log file for more details")

if __name__ == "__main__":
    main()