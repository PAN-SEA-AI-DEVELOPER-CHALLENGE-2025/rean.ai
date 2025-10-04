from pydantic_settings import BaseSettings
from typing import Optional, List, Union
from pydantic import field_validator
from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    # Application
    app_name: str = "Pan-Sea Backend"
    debug: bool = False
    version: str = "1.0.0"
    enable_docs: bool = True  # Enable API documentation endpoints
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 2
    
    # Database Configuration
    database_url: str = ""  # PostgreSQL connection string
    database_url_async: str = ""  # Async version
    
    # Security
    secret_key: str = ""  # Must be set via environment variable
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_chat_model: str = "gpt-4o-mini"
    openai_embeddings_model: str = "text-embedding-3-small"

    # Gemini (Google Generative AI)
    gemini_api_key: Optional[str] = None
    gemini_chat_model: str = "gemini-1.5-flash"
    gemini_embeddings_model: str = "text-embedding-004"
    
    # Sea Lion AI (for text generation)
    sea_lion_api_key: str = ""
    sea_lion_model: str = "aisingapore/Llama-SEA-LION-v3-70B-IT"
    sea_lion_base_url: str = "https://api.sea-lion.ai/v1"
    
    # AWS Bedrock (for embeddings via Cohere Embed Multilingual)
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "ap-southeast-1"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # CORS
    allowed_origins: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    # Hosts
    allowed_hosts: Union[List[str], str] = ["*"]
    
    @field_validator('allowed_origins', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @field_validator('allowed_hosts', mode='before')
    @classmethod
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(',')]
        return v
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v):
        if not v or v == "your-secret-key-here":
            raise ValueError("SECRET_KEY must be set via environment variable")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    # File Upload
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    upload_dir: str = "uploads"
    
    # Audio Processing
    audio_chunk_duration: int = 30  # seconds
    supported_audio_formats: list = [".wav", ".mp3", ".m4a", ".ogg"]
    
    # Local Whisper Configuration
    whisper_model_size: str = "base"  # tiny, base, small, medium, large
    whisper_device: str = "cpu"  # cpu or cuda (for GPU acceleration)
    
    # External Transcription Service Configuration
    transcription_service_url: str = ""  # External Whisper API endpoint (loaded from env)
    transcription_service_timeout: int = 300  # Timeout in seconds (5 minutes)
    
    # AWS S3 Configuration
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    aws_s3_bucket: str = ""
    aws_s3_endpoint_url: Optional[str] = None  # For custom endpoints (e.g., MinIO)
    aws_s3_use_ssl: bool = True
    aws_s3_verify_ssl: bool = True
    
    class Config:
        env_file = ".env"


settings = Settings()
