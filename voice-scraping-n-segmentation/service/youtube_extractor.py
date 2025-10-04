"""
YouTube Audio Extraction Service

This module provides the core service for extracting audio from YouTube videos
and converting it to WAV format suitable for machine learning training data.
"""

import os
import tempfile
import logging
from pathlib import Path
from typing import Optional, Dict, List
import yt_dlp
import librosa
import soundfile as sf
from service.s3_service import S3Service


class YouTubeAudioService:
    """
    Service class for YouTube audio extraction operations.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the YouTube Audio Service.
        
        Args:
            config (Dict): Configuration dictionary containing:
                - output_dir: Directory to save extracted audio files
                - sample_rate: Target sample rate for output WAV files
                - temp_dir: Temporary directory for processing
        """
        self.config = config
        self.output_dir = Path(config.get('output_dir', 'result'))
        self.output_dir.mkdir(exist_ok=True)
        self.sample_rate = config.get('sample_rate', 22050)
        self.temp_dir = config.get('temp_dir', 'data/temp')
        
        # Ensure temp directory exists
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Configure yt-dlp options
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'extractaudio': True,
            'audioformat': 'wav',
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }
        
        # Initialize S3 service
        self.s3_service = S3Service(config)
        self.auto_upload_s3 = config.get('s3_auto_upload', False)
        self.delete_local_after_upload = config.get('s3_delete_local_after_upload', False)
    
    def get_video_info(self, youtube_url: str) -> Dict:
        """
        Get information about a YouTube video without downloading.
        
        Args:
            youtube_url (str): YouTube video URL
            
        Returns:
            Dict: Video information including title, duration, etc.
        """
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                return {
                    'success': True,
                    'data': {
                        'title': info.get('title'),
                        'duration': info.get('duration'),
                        'uploader': info.get('uploader'),
                        'view_count': info.get('view_count'),
                        'upload_date': info.get('upload_date'),
                        'description': info.get('description', '')[:200] + '...',
                        'thumbnail': info.get('thumbnail'),
                        'video_id': info.get('id')
                    }
                }
        except Exception as e:
            self.logger.error(f"Failed to get video info: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def extract_audio(
        self, 
        youtube_url: str, 
        output_filename: Optional[str] = None,
        start_time: Optional[float] = None,
        duration: Optional[float] = None,
        upload_to_s3: Optional[bool] = None
    ) -> Dict:
        """
        Extract audio from a YouTube video and convert to WAV format.
        
        Args:
            youtube_url (str): YouTube video URL
            output_filename (str, optional): Custom output filename (without extension)
            start_time (float, optional): Start time in seconds for audio extraction
            duration (float, optional): Duration in seconds for audio extraction
            
        Returns:
            Dict: Result containing success status, file path, and metadata
        """
        try:
            with tempfile.TemporaryDirectory(dir=self.temp_dir) as temp_dir:
                # Configure temporary output directory for yt-dlp
                temp_ydl_opts = self.ydl_opts.copy()
                temp_ydl_opts['outtmpl'] = os.path.join(temp_dir, '%(title)s.%(ext)s')
                
                # Extract audio using yt-dlp
                with yt_dlp.YoutubeDL(temp_ydl_opts) as ydl:
                    self.logger.info(f"Extracting audio from: {youtube_url}")
                    info = ydl.extract_info(youtube_url, download=True)
                    video_title = info.get('title', 'unknown_video')
                    video_id = info.get('id', 'unknown_id')
                    
                    # Find the downloaded audio file
                    audio_files = list(Path(temp_dir).glob('*'))
                    if not audio_files:
                        raise Exception("No audio file was downloaded")
                    
                    temp_audio_path = audio_files[0]
                    
                    # Load audio with librosa
                    self.logger.info("Loading and processing audio...")
                    audio_data, original_sr = librosa.load(
                        str(temp_audio_path), 
                        sr=self.sample_rate,
                        offset=start_time,
                        duration=duration
                    )
                    
                    # Determine output filename
                    if output_filename is None:
                        # Clean the video title for use as filename
                        safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                        safe_title = safe_title.replace(' ', '_')
                        timestamp_suffix = f"_{int(start_time or 0)}s" if start_time else ""
                        duration_suffix = f"_{int(duration)}s" if duration else ""
                        output_filename = f"{safe_title}_{self.sample_rate}hz{timestamp_suffix}{duration_suffix}"
                    
                    # Save as WAV file
                    output_path = self.output_dir / f"{output_filename}.wav"
                    sf.write(str(output_path), audio_data, self.sample_rate)
                    
                    # Calculate metadata
                    audio_duration = len(audio_data) / self.sample_rate
                    file_size = os.path.getsize(output_path)
                    
                    self.logger.info(f"Audio extracted successfully: {output_path}")
                    self.logger.info(f"Duration: {audio_duration:.2f} seconds")
                    
                    # Prepare result data
                    result_data = {
                        'output_path': str(output_path),
                        'filename': f"{output_filename}.wav",
                        'duration': audio_duration,
                        'sample_rate': self.sample_rate,
                        'file_size': file_size,
                        'video_title': video_title,
                        'video_id': video_id,
                        'start_time': start_time,
                        'extracted_duration': duration,
                        's3_uploaded': False,
                        's3_url': None,
                        's3_key': None
                    }
                    
                    # Handle S3 upload
                    should_upload = upload_to_s3 if upload_to_s3 is not None else self.auto_upload_s3
                    
                    if should_upload and self.s3_service.is_available():
                        self.logger.info("Uploading to S3...")
                        
                        # Prepare metadata for S3
                        s3_metadata = {
                            'video_title': video_title,
                            'video_id': video_id,
                            'duration': str(audio_duration),
                            'sample_rate': str(self.sample_rate),
                            'extraction_date': str(os.path.getctime(output_path))
                        }
                        
                        # Prepare tags for S3
                        s3_tags = {
                            'source': 'youtube',
                            'video_id': video_id,
                            'sample_rate': str(self.sample_rate),
                            'type': 'audio_extraction'
                        }
                        
                        s3_result = self.s3_service.upload_file(
                            local_file_path=str(output_path),
                            metadata=s3_metadata,
                            tags=s3_tags
                        )
                        
                        if s3_result['success']:
                            result_data.update({
                                's3_uploaded': True,
                                's3_url': s3_result['data']['s3_url'],
                                's3_key': s3_result['data']['s3_key'],
                                's3_bucket': s3_result['data']['bucket']
                            })
                            self.logger.info(f"Successfully uploaded to S3: {s3_result['data']['s3_key']}")
                            
                            # Delete local file if configured
                            if self.delete_local_after_upload:
                                try:
                                    output_path.unlink()
                                    result_data['local_file_deleted'] = True
                                    self.logger.info(f"Deleted local file: {output_path}")
                                except Exception as e:
                                    self.logger.warning(f"Failed to delete local file: {e}")
                                    result_data['local_file_deleted'] = False
                        else:
                            self.logger.warning(f"S3 upload failed: {s3_result['error']}")
                            result_data['s3_error'] = s3_result['error']
                    
                    return {
                        'success': True,
                        'data': result_data
                    }
                    
        except Exception as e:
            self.logger.error(f"Failed to extract audio: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def extract_multiple(
        self, 
        youtube_urls: List[str], 
        prefix: str = "audio"
    ) -> Dict:
        """
        Extract audio from multiple YouTube videos.
        
        Args:
            youtube_urls (List[str]): List of YouTube video URLs
            prefix (str): Prefix for output filenames
            
        Returns:
            Dict: Result containing success status and list of extracted files
        """
        extracted_files = []
        failed_extractions = []
        
        for i, url in enumerate(youtube_urls):
            try:
                output_filename = f"{prefix}_{i+1:03d}"
                result = self.extract_audio(url, output_filename)
                
                if result['success']:
                    extracted_files.append(result['data'])
                else:
                    failed_extractions.append({
                        'url': url,
                        'error': result['error']
                    })
                    
            except Exception as e:
                self.logger.error(f"Failed to extract audio from {url}: {str(e)}")
                failed_extractions.append({
                    'url': url,
                    'error': str(e)
                })
                continue
        
        return {
            'success': len(extracted_files) > 0,
            'data': {
                'extracted_files': extracted_files,
                'failed_extractions': failed_extractions,
                'total_requested': len(youtube_urls),
                'successful_extractions': len(extracted_files),
                'failed_extractions_count': len(failed_extractions)
            }
        }
    
    def validate_url(self, youtube_url: str) -> Dict:
        """
        Validate if a YouTube URL is accessible and valid.
        
        Args:
            youtube_url (str): YouTube video URL
            
        Returns:
            Dict: Validation result
        """
        try:
            # Quick validation without downloading
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                if info:
                    return {
                        'success': True,
                        'data': {
                            'valid': True,
                            'title': info.get('title'),
                            'duration': info.get('duration')
                        }
                    }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'data': {'valid': False}
            }
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported audio formats.
        
        Returns:
            List[str]: List of supported formats
        """
        return ['wav', 'mp3', 'flac', 'ogg', 'm4a']
    
    def cleanup_temp_files(self) -> None:
        """
        Clean up temporary files.
        """
        try:
            temp_path = Path(self.temp_dir)
            if temp_path.exists():
                for file_path in temp_path.glob('*'):
                    if file_path.is_file():
                        file_path.unlink()
                self.logger.info("Temporary files cleaned up")
        except Exception as e:
            self.logger.error(f"Failed to cleanup temp files: {e}")
