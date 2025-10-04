"""
API Client Examples

This module demonstrates how to use the YouTube Audio Extractor API.
"""

import requests
import json
import time
from typing import Dict, Any, List


class AudioExtractionClient:
    """
    Client for interacting with the YouTube Audio Extractor API.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the API service
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the API service is healthy."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def get_video_info(self, youtube_url: str) -> Dict[str, Any]:
        """
        Get information about a YouTube video.
        
        Args:
            youtube_url: YouTube video URL
            
        Returns:
            Dict containing video information or error
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/audio/info",
                json={"url": youtube_url}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def extract_audio(
        self,
        youtube_url: str,
        filename: str = None,
        start_time: float = None,
        duration: float = None,
        sample_rate: int = None,
        upload_to_s3: bool = None
    ) -> Dict[str, Any]:
        """
        Extract audio from a YouTube video.
        
        Args:
            youtube_url: YouTube video URL
            filename: Custom output filename
            start_time: Start time in seconds
            duration: Duration in seconds
            sample_rate: Target sample rate
            upload_to_s3: Upload extracted audio to S3
            
        Returns:
            Dict containing extraction result or error
        """
        try:
            payload = {"url": youtube_url}
            
            if filename:
                payload["filename"] = filename
            if start_time is not None:
                payload["start_time"] = start_time
            if duration is not None:
                payload["duration"] = duration
            if sample_rate is not None:
                payload["sample_rate"] = sample_rate
            if upload_to_s3 is not None:
                payload["upload_to_s3"] = upload_to_s3
            
            response = self.session.post(
                f"{self.base_url}/api/audio/extract",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def extract_batch(
        self,
        youtube_urls: List[str],
        prefix: str = "batch_audio",
        sample_rate: int = None
    ) -> Dict[str, Any]:
        """
        Extract audio from multiple YouTube videos.
        
        Args:
            youtube_urls: List of YouTube video URLs
            prefix: Prefix for output filenames
            sample_rate: Target sample rate
            
        Returns:
            Dict containing batch extraction results or error
        """
        try:
            payload = {
                "urls": youtube_urls,
                "prefix": prefix
            }
            
            if sample_rate is not None:
                payload["sample_rate"] = sample_rate
            
            response = self.session.post(
                f"{self.base_url}/api/audio/extract-batch",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def validate_url(self, youtube_url: str) -> Dict[str, Any]:
        """
        Validate a YouTube URL.
        
        Args:
            youtube_url: YouTube video URL to validate
            
        Returns:
            Dict containing validation result or error
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/audio/validate",
                json={"url": youtube_url}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def list_files(self) -> Dict[str, Any]:
        """
        List all extracted audio files.
        
        Returns:
            Dict containing file list or error
        """
        try:
            response = self.session.get(f"{self.base_url}/api/audio/files")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def download_file(self, filename: str, save_path: str = None) -> bool:
        """
        Download an extracted audio file.
        
        Args:
            filename: Name of the file to download
            save_path: Local path to save the file
            
        Returns:
            True if download successful, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/audio/download/{filename}",
                stream=True
            )
            response.raise_for_status()
            
            if save_path is None:
                save_path = filename
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
        except requests.RequestException as e:
            print(f"Download failed: {e}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get API configuration information.
        
        Returns:
            Dict containing configuration info or error
        """
        try:
            response = self.session.get(f"{self.base_url}/api/audio/config")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def cleanup(self) -> Dict[str, Any]:
        """
        Clean up temporary files.
        
        Returns:
            Dict containing cleanup result or error
        """
        try:
            response = self.session.post(f"{self.base_url}/api/audio/cleanup")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    # S3 Methods
    def upload_to_s3(
        self,
        filename: str,
        s3_key: str = None,
        metadata: Dict[str, str] = None,
        tags: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Upload a local file to S3.
        
        Args:
            filename: Local filename to upload
            s3_key: Custom S3 object key
            metadata: Additional metadata
            tags: S3 object tags
            
        Returns:
            Dict containing upload result or error
        """
        try:
            payload = {"filename": filename}
            
            if s3_key:
                payload["s3_key"] = s3_key
            if metadata:
                payload["metadata"] = metadata
            if tags:
                payload["tags"] = tags
            
            response = self.session.post(
                f"{self.base_url}/api/audio/s3/upload",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def list_s3_files(
        self,
        prefix: str = None,
        max_keys: int = 100
    ) -> Dict[str, Any]:
        """
        List files in S3 bucket.
        
        Args:
            prefix: Optional prefix to filter files
            max_keys: Maximum number of files to return
            
        Returns:
            Dict containing S3 file list or error
        """
        try:
            params = {"max_keys": max_keys}
            if prefix:
                params["prefix"] = prefix
            
            response = self.session.get(
                f"{self.base_url}/api/audio/s3/files",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def delete_s3_file(self, s3_key: str) -> Dict[str, Any]:
        """
        Delete a file from S3.
        
        Args:
            s3_key: S3 object key to delete
            
        Returns:
            Dict containing deletion result or error
        """
        try:
            response = self.session.delete(
                f"{self.base_url}/api/audio/s3/{s3_key}"
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def get_s3_file_info(self, s3_key: str) -> Dict[str, Any]:
        """
        Get information about an S3 file.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            Dict containing S3 file info or error
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/audio/s3/{s3_key}/info"
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def generate_presigned_url(
        self,
        s3_key: str,
        expiration: int = 3600,
        method: str = "get_object"
    ) -> Dict[str, Any]:
        """
        Generate a presigned URL for S3 object access.
        
        Args:
            s3_key: S3 object key
            expiration: Expiration time in seconds
            method: HTTP method
            
        Returns:
            Dict containing presigned URL or error
        """
        try:
            payload = {
                "s3_key": s3_key,
                "expiration": expiration,
                "method": method
            }
            
            response = self.session.post(
                f"{self.base_url}/api/audio/s3/presigned-url",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def get_s3_status(self) -> Dict[str, Any]:
        """
        Get S3 service status and configuration.
        
        Returns:
            Dict containing S3 status or error
        """
        try:
            response = self.session.get(f"{self.base_url}/api/audio/s3/status")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}


def main():
    """
    Example usage of the API client.
    """
    # Initialize client
    client = AudioExtractionClient()
    
    # Check service health
    print("🔍 Checking service health...")
    health = client.health_check()
    if "error" in health:
        print(f"❌ Service not available: {health['error']}")
        return
    else:
        print(f"✅ Service is {health['status']}")
    
    # Get configuration
    print("\n📋 Getting configuration...")
    config = client.get_config()
    if "error" not in config:
        print("Available sample rate configurations:")
        for name, info in config['sample_rate_configs'].items():
            print(f"  {name}: {info['sample_rate']}Hz - {info['description']}")
    
    # Example YouTube URL (replace with actual URL)
    youtube_url = input("\n🎬 Enter YouTube URL: ").strip()
    
    if not youtube_url:
        print("No URL provided, using example workflow with test URL")
        youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    # Validate URL first
    print(f"\n🔍 Validating URL: {youtube_url}")
    validation = client.validate_url(youtube_url)
    if "error" in validation:
        print(f"❌ URL validation failed: {validation['error']}")
        return
    elif validation.get('valid'):
        print(f"✅ URL is valid: {validation.get('title', 'Unknown title')}")
    
    # Get video info
    print("\n📺 Getting video information...")
    info = client.get_video_info(youtube_url)
    if "error" in info:
        print(f"❌ Failed to get video info: {info['error']}")
        return
    else:
        print(f"Title: {info.get('title', 'Unknown')}")
        print(f"Duration: {info.get('duration', 'Unknown')} seconds")
        print(f"Uploader: {info.get('uploader', 'Unknown')}")
    
    # Extract audio
    print("\n🎵 Extracting audio...")
    extraction = client.extract_audio(
        youtube_url=youtube_url,
        filename="test_extraction",
        sample_rate=16000,  # 16kHz for speech recognition
        start_time=0,       # Start from beginning
        duration=30         # Extract 30 seconds only for demo
    )
    
    if "error" in extraction:
        print(f"❌ Extraction failed: {extraction['error']}")
        return
    else:
        print(f"✅ {extraction['message']}")
        data = extraction['data']
        print(f"File: {data['filename']}")
        print(f"Duration: {data['duration']:.2f} seconds")
        print(f"File size: {data['file_size']} bytes")
    
    # List files
    print("\n📁 Listing extracted files...")
    files = client.list_files()
    if "error" not in files:
        print(f"Total files: {files['total_count']}")
        for file_info in files['files'][:5]:  # Show first 5 files
            print(f"  {file_info['filename']} ({file_info['size']} bytes)")
    
    # Check S3 status
    print("\n☁️  Checking S3 integration...")
    s3_status = client.get_s3_status()
    if "error" not in s3_status:
        if s3_status.get('available'):
            print(f"✅ S3 available: {s3_status['bucket']} in {s3_status['region']}")
            
            # Try extracting with S3 upload
            print("\n☁️  Testing extraction with S3 upload...")
            s3_extraction = client.extract_audio(
                youtube_url=youtube_url,
                filename="s3_test_extraction",
                sample_rate=16000,
                start_time=0,
                duration=15,  # 15 seconds for S3 test
                upload_to_s3=True
            )
            
            if "error" not in s3_extraction:
                data = s3_extraction['data']
                if data.get('s3_uploaded'):
                    print(f"✅ Successfully uploaded to S3!")
                    print(f"   S3 URL: {data['s3_url']}")
                    print(f"   S3 Key: {data['s3_key']}")
                    
                    # List S3 files
                    print("\n📁 Listing S3 files...")
                    s3_files = client.list_s3_files(max_keys=5)
                    if "error" not in s3_files:
                        print(f"S3 files found: {s3_files['total_count']}")
                        for file_info in s3_files['files'][:3]:
                            print(f"  {file_info['s3_key']} ({file_info['size']} bytes)")
                else:
                    print(f"⚠️  Extraction succeeded but S3 upload failed: {data.get('s3_error', 'Unknown error')}")
            else:
                print(f"❌ S3 extraction test failed: {s3_extraction['error']}")
        else:
            print(f"⚠️  S3 not available: Check AWS credentials and configuration")
    else:
        print(f"❌ S3 status check failed: {s3_status['error']}")
    
    # Cleanup
    print("\n🧹 Cleaning up temporary files...")
    cleanup_result = client.cleanup()
    if "error" not in cleanup_result:
        print(f"✅ {cleanup_result['message']}")


if __name__ == "__main__":
    main()
