"""
Main FastAPI Application

This is the entry point for the YouTube Audio Extractor API service.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from contextlib import asynccontextmanager

from config.settings import get_config
from router.audio_router import router as audio_router, health_router
from router.voice_processing_router import router as voice_router
from router.mfa_training_router import router as mfa_training_router


# Initialize configuration
config = get_config()

# Configure logging
logging.basicConfig(
    level=getattr(logging, config['log_level']),
    format=config['log_format']
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Voice Scraping & Segmentation API")
    logger.info(f"Configuration loaded: {config['project_root']}")
    logger.info("Voice processing pipeline features enabled:")
    logger.info("  - WebRTC VAD for voice chunking")
    logger.info("  - Whisper transcription")
    logger.info("  - Montreal Forced Alignment (MFA)")
    logger.info("  - CSV metadata export")
    logger.info("  - AWS S3 integration")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Voice Scraping & Segmentation API")


# Create FastAPI application
app = FastAPI(
    title="Khmer Voice Scraping & Segmentation API",
    description="""
    A comprehensive API for Khmer voice processing, scraping, and segmentation with advanced ML capabilities.
    
    **🇰🇭 Specialized for Khmer Language Processing**
    
    Perfect for preparing Khmer training data for machine learning models, especially for:
    - Khmer speech recognition systems
    - Khmer audio classification models
    - Khmer voice synthesis training
    - Khmer audio processing research
    - Khmer speaker diarization
    - Forced alignment for Khmer text
    
    ## Core Features
    
    ### Audio Extraction
    - 🎵 Extract audio from YouTube videos
    - 🔄 Convert to WAV format with customizable sample rates
    - ✂️ Extract specific time segments
    - 📦 Batch processing for multiple videos
    - ☁️ AWS S3 integration for storage
    
    ### Khmer Voice Processing Pipeline
    - 🎙️ **WebRTC VAD**: Voice Activity Detection optimized for Khmer speech patterns (1.5-5 seconds chunks)
    - 🗣️ **Specialized Khmer Whisper**: Support for ksoky/whisper-large-khmer-asr (29.5% WER) + fallback to OpenAI Whisper
    - 🔤 **Montreal Forced Alignment (MFA)**: Precise word-level timestamp refinement with custom TTS-trained Khmer models
    - 📊 **CSV Metadata Export**: UTF-8 encoded structured data with Khmer text support
    - 🎯 **Speaker Detection**: Basic speaker identification for Khmer speakers
    - 🇰🇭 **Khmer Language Support**: Native Unicode handling and optimized processing parameters
    
    ## API Endpoints
    
    ### Audio Extraction (`/api/audio/`)
    - Extract and process YouTube videos
    - Manage local and S3 audio files
    - Configuration and health checks
    
    ### Voice Processing (`/api/voice/`)
    - Full voice processing pipeline
    - Session management and tracking
    - CSV export and reporting
    - Asynchronous processing support
    
    ### MFA Training (`/api/mfa-training/`)
    - Train custom MFA acoustic models using TTS datasets
    - Generate Khmer pronunciation dictionaries
    - Validate and prepare TTS datasets for training
    - Full training pipeline automation
    
    ## Sample Rates
    
    - **16kHz**: Speech recognition, voice assistants, VAD processing
    - **22.05kHz**: General audio processing, balanced quality/size
    - **44.1kHz**: High-quality audio, music processing
    - **48kHz**: Professional audio, broadcasting
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(audio_router)
app.include_router(voice_router)
app.include_router(mfa_training_router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled exceptions.
    """
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


# Custom error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Handler for HTTP exceptions.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host=config['host'],
        port=config['port'],
        reload=config['debug'],
        log_level=config['log_level'].lower()
    )
