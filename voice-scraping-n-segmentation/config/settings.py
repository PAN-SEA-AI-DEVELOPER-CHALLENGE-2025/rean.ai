"""
Configuration Settings

This module provides configuration management for the YouTube audio extraction service.
"""

import os
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv


def get_config() -> Dict[str, Any]:
    """
    Get application configuration.
    
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # Load environment variables from .env file
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Try loading from config directory as well
        config_env_path = project_root / 'config' / '.env'
        if config_env_path.exists():
            load_dotenv(config_env_path)
    
    config = {
        # Directories
        'project_root': str(project_root),
        'data_dir': str(project_root / 'data'),
        'result_dir': str(project_root / 'result'),
        'output_dir': str(project_root / 'result'),
        'temp_dir': str(project_root / 'data' / 'temp'),
        'log_dir': str(project_root / 'data' / 'logs'),
        
        # Audio settings
        'sample_rate': int(os.getenv('SAMPLE_RATE', 22050)),
        'audio_format': os.getenv('AUDIO_FORMAT', 'wav'),
        'max_duration': int(os.getenv('MAX_DURATION', 3600)),  # 1 hour max
        
        # API settings
        'host': os.getenv('HOST', '0.0.0.0'),
        'port': int(os.getenv('PORT', 8000)),
        'debug': os.getenv('DEBUG', 'False').lower() == 'true',
        
        # Processing settings
        'max_concurrent_downloads': int(os.getenv('MAX_CONCURRENT_DOWNLOADS', 3)),
        'chunk_size': int(os.getenv('CHUNK_SIZE', 1024)),
        'timeout': int(os.getenv('TIMEOUT', 300)),  # 5 minutes
        
        # File settings
        'max_file_size': int(os.getenv('MAX_FILE_SIZE', 100 * 1024 * 1024)),  # 100MB
        'allowed_extensions': ['wav', 'mp3', 'flac', 'ogg', 'm4a'],
        
        # Logging
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
        'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        
        # YouTube-dlp settings
        'ytdlp_format': os.getenv('YTDLP_FORMAT', 'bestaudio/best'),
        'ytdlp_extract_audio': True,
        'ytdlp_audio_format': 'wav',
        'ytdlp_quiet': True,
        
        # Security settings
        'allowed_domains': [
            'youtube.com',
            'www.youtube.com',
            'youtu.be',
            'm.youtube.com'
        ],
        
        # Rate limiting
        'rate_limit_requests': int(os.getenv('RATE_LIMIT_REQUESTS', 100)),
        'rate_limit_window': int(os.getenv('RATE_LIMIT_WINDOW', 3600)),  # 1 hour
        
        # AWS S3 settings
        'aws_access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
        'aws_secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
        'aws_region': os.getenv('AWS_REGION', 'ap-southeast-1'),
        's3_bucket_name': os.getenv('AWS_S3_BUCKET', os.getenv('S3_BUCKET_NAME', 'pansea-storage')),
        's3_region': os.getenv('AWS_REGION', 'ap-southeast-1'),
        's3_prefix': os.getenv('S3_PREFIX', 'audio-extractions'),
        's3_endpoint_url': os.getenv('AWS_S3_ENDPOINT_URL'),
        's3_use_ssl': os.getenv('AWS_S3_USE_SSL', 'true').lower() == 'true',
        's3_verify_ssl': os.getenv('AWS_S3_VERIFY_SSL', 'true').lower() == 'true',
        's3_auto_upload': os.getenv('S3_AUTO_UPLOAD', 'False').lower() == 'true',
        's3_delete_local_after_upload': os.getenv('S3_DELETE_LOCAL_AFTER_UPLOAD', 'False').lower() == 'true',
        
        # Transcription service settings
        'transcription_service_url': os.getenv('TRANSCRIPTION_SERVICE_URL'),
        'transcription_service_timeout': int(os.getenv('TRANSCRIPTION_SERVICE_TIMEOUT', 300)),
        # Google STT settings (default enabled for Khmer)
        'use_google_stt': os.getenv('USE_GOOGLE_STT', 'true').lower() == 'true',
        'GOOGLE_APPLICATION_CREDENTIALS': os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
        'GOOGLE_STT_USE_ENHANCED': os.getenv('GOOGLE_STT_USE_ENHANCED', 'false').lower() == 'true',
        'GOOGLE_STT_MODEL': os.getenv('GOOGLE_STT_MODEL', 'default'),
        
        # Khmer language specific settings
        'target_language': 'khmer',
        'language_code': 'km',
        'whisper_language': 'km',  # Khmer language code for Whisper
        'whisper_model': os.getenv('WHISPER_MODEL', 'base'),  # base model works well for Khmer
        
        # Specialized Khmer Whisper model from Hugging Face
        'use_khmer_whisper_hf': os.getenv('USE_KHMER_WHISPER_HF', 'false').lower() == 'true',
        'khmer_whisper_model_id': os.getenv('KHMER_WHISPER_MODEL_ID', 'ksoky/whisper-large-khmer-asr'),
        'whisper_device': os.getenv('WHISPER_DEVICE', 'auto'),  # auto, cuda, cpu
        
        # MFA settings for Khmer (if available)
        'mfa_language': 'khmer',
        'mfa_command': os.getenv('MFA_COMMAND', 'mfa'),
        'mfa_acoustic_model': os.getenv('MFA_ACOUSTIC_MODEL', 'khmer'),  # May need custom model
        'mfa_dictionary': os.getenv('MFA_DICTIONARY', 'khmer'),
        
        # VAD settings optimized for Khmer speech
        'vad_aggressiveness': int(os.getenv('VAD_AGGRESSIVENESS', 2)),  # Slightly less aggressive for tonal languages
        'min_chunk_duration': float(os.getenv('MIN_CHUNK_DURATION', 1.5)),  # Slightly longer for Khmer
        'max_chunk_duration': float(os.getenv('MAX_CHUNK_DURATION', 5.0)),
        
        # CSV encoding for Khmer text
        'csv_encoding': 'utf-8',  # Essential for Khmer Unicode support
        'csv_separator': ',',
    }
    
    # Create directories if they don't exist
    for dir_key in ['data_dir', 'result_dir', 'temp_dir', 'log_dir']:
        Path(config[dir_key]).mkdir(parents=True, exist_ok=True)
    
    return config


def get_sample_rate_configs() -> Dict[str, Dict[str, Any]]:
    """
    Get predefined sample rate configurations for different use cases.
    
    Returns:
        Dict[str, Dict[str, Any]]: Sample rate configurations
    """
    return {
        'speech_recognition': {
            'sample_rate': 16000,
            'description': 'Optimized for speech recognition and voice assistants',
            'use_cases': ['ASR', 'voice commands', 'phone calls']
        },
        'general_audio': {
            'sample_rate': 22050,
            'description': 'Balanced quality and file size for general audio',
            'use_cases': ['podcasts', 'audiobooks', 'general ML training']
        },
        'music_quality': {
            'sample_rate': 44100,
            'description': 'CD quality for music and high-fidelity audio',
            'use_cases': ['music analysis', 'audio classification', 'high-quality training']
        },
        'professional': {
            'sample_rate': 48000,
            'description': 'Professional audio and broadcasting standard',
            'use_cases': ['professional audio', 'broadcasting', 'studio work']
        }
    }


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration parameters.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary
        
    Returns:
        bool: True if configuration is valid
    """
    required_keys = [
        'data_dir', 'result_dir', 'output_dir', 'temp_dir',
        'sample_rate', 'audio_format', 'host', 'port'
    ]
    
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required configuration key: {key}")
    
    # Validate sample rate
    if config['sample_rate'] not in [8000, 16000, 22050, 44100, 48000]:
        raise ValueError(f"Invalid sample rate: {config['sample_rate']}")
    
    # Validate audio format
    if config['audio_format'] not in config['allowed_extensions']:
        raise ValueError(f"Invalid audio format: {config['audio_format']}")
    
    # Validate port
    if not (1024 <= config['port'] <= 65535):
        raise ValueError(f"Invalid port number: {config['port']}")
    
    return True


class ConfigManager:
    """
    Configuration manager for dynamic config updates.
    """
    
    def __init__(self):
        self._config = get_config()
        validate_config(self._config)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self._config[key] = value
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple configuration values."""
        self._config.update(updates)
        validate_config(self._config)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self._config.copy()
    
    def reset(self) -> None:
        """Reset configuration to defaults."""
        self._config = get_config()
        validate_config(self._config)


# Global configuration instance
config_manager = ConfigManager()
