#!/usr/bin/env python3
"""
Dual-Language Speech-to-Text Service - FastAPI Version
A FastAPI web service for audio transcription using:
- OpenAI Whisper (English) 
- Google Speech-to-Text API (Khmer)

Setup for Google Speech-to-Text:
1. Set up a Google Cloud project and enable Speech-to-Text API
2. Create a service account and download the JSON key file
3. Set the GOOGLE_APPLICATION_CREDENTIALS environment variable to the JSON key file path
   Example: export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
"""

import os
import tempfile
import logging
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import whisper
import torch
from google.cloud import speech
import librosa
import numpy as np
from scipy.signal import butter, filtfilt
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging from environment
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Dual-Language Speech-to-Text API",
    description="FastAPI service for English (Whisper) and Khmer (Google Speech-to-Text) transcription with optimized quality settings",
    version="2.0.0"
)

# Configuration from environment variables
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 100 * 1024 * 1024))  # Default: 100MB
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'webm', 'flac', 'ogg'}

# Google Speech-to-Text configuration for best Khmer quality
KHMER_LANGUAGE_CODE = os.getenv('KHMER_LANGUAGE_CODE', 'km-KH')
GOOGLE_SPEECH_MODEL = os.getenv('GOOGLE_SPEECH_MODEL', 'latest_long')
GOOGLE_SPEECH_USE_ENHANCED = os.getenv('GOOGLE_SPEECH_USE_ENHANCED', 'true').lower() == 'true'
GOOGLE_SPEECH_ENABLE_PUNCTUATION = os.getenv('GOOGLE_SPEECH_ENABLE_PUNCTUATION', 'true').lower() == 'true'
GOOGLE_SPEECH_WORD_TIME_OFFSETS = os.getenv('GOOGLE_SPEECH_WORD_TIME_OFFSETS', 'true').lower() == 'true'
GOOGLE_SPEECH_WORD_CONFIDENCE = os.getenv('GOOGLE_SPEECH_WORD_CONFIDENCE', 'true').lower() == 'true'
GOOGLE_SPEECH_PROFANITY_FILTER = os.getenv('GOOGLE_SPEECH_PROFANITY_FILTER', 'false').lower() == 'true'

# Global variables to store models
whisper_model = None
google_speech_client = None

def allowed_file(filename: str) -> bool:
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_whisper_model() -> bool:
    """Load the Whisper model for English transcription."""
    global whisper_model
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading Whisper model on device: {device}")
        
        model_size = os.getenv('WHISPER_MODEL_SIZE', 'tiny')
        whisper_model = whisper.load_model(model_size, device=device)
        logger.info(f"Whisper model '{model_size}' loaded successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to load Whisper model: {str(e)}")
        return False

def initialize_google_speech() -> bool:
    """Initialize Google Speech-to-Text client for Khmer transcription."""
    global google_speech_client
    try:
        logger.info("Initializing Google Speech-to-Text client...")
        
        # Initialize the Google Speech client
        # Note: Make sure GOOGLE_APPLICATION_CREDENTIALS environment variable is set
        # or use service account key file
        google_speech_client = speech.SpeechClient()
        
        logger.info("Google Speech-to-Text client initialized successfully")
        logger.info(f"Configured for optimal Khmer quality: model={GOOGLE_SPEECH_MODEL}, enhanced={GOOGLE_SPEECH_USE_ENHANCED}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Google Speech client: {str(e)}")
        logger.error("Make sure GOOGLE_APPLICATION_CREDENTIALS is set or service account key is configured")
        return False

def transcribe_with_google_speech(audio_path: str, language_code: str = None) -> str:
    """Transcribe audio using Google Speech-to-Text API for Khmer."""
    try:
        # Use environment variable if language_code not provided
        if language_code is None:
            language_code = KHMER_LANGUAGE_CODE
            
        logger.info(f"Loading audio file for Google Speech: {audio_path}")
        logger.info(f"Using language code: {language_code}, model: {GOOGLE_SPEECH_MODEL}")
        
        # Load and preprocess audio for Google Speech-to-Text
        # Google Speech-to-Text supports various sample rates, but 16kHz is optimal
        audio_input, sample_rate = librosa.load(
            audio_path, 
            sr=16000, 
            duration=60.0,  # Google has limits on audio length for sync requests
            res_type='kaiser_best'
        )
        
        # Check audio length and warn if too long
        if len(audio_input) > 16000 * 60:  # 60 seconds at 16kHz
            logger.warning(f"Audio file is long ({len(audio_input)/16000:.1f}s), truncating to 60s for API limits")
            audio_input = audio_input[:16000 * 60]
        
        logger.info(f"Processing {len(audio_input)/16000:.1f} seconds of audio")
        
        # Audio preprocessing for better quality
        logger.info("Preprocessing audio for optimal transcription...")
        
        # Normalize audio amplitude
        if np.max(np.abs(audio_input)) > 0:
            audio_input = audio_input / np.max(np.abs(audio_input))
        
        # Apply mild noise reduction (simple high-pass filter)
        nyquist = 16000 / 2
        low_cutoff = 80 / nyquist  # Remove very low frequency noise
        b, a = butter(1, low_cutoff, btype='high')
        audio_input = filtfilt(b, a, audio_input)
        
        # Convert to 16-bit PCM format for Google Speech API
        audio_content = (audio_input * 32767).astype(np.int16).tobytes()
        
        # Configure the Google Speech request for optimal Khmer transcription
        audio = speech.RecognitionAudio(content=audio_content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=language_code,
            enable_automatic_punctuation=GOOGLE_SPEECH_ENABLE_PUNCTUATION,
            model=GOOGLE_SPEECH_MODEL,
            use_enhanced=GOOGLE_SPEECH_USE_ENHANCED,
            # Advanced settings for best quality Khmer transcription
            enable_word_time_offsets=GOOGLE_SPEECH_WORD_TIME_OFFSETS,    # Word-level timestamps
            enable_word_confidence=GOOGLE_SPEECH_WORD_CONFIDENCE,        # Confidence scores
            audio_channel_count=1,                                       # Mono audio optimization
            profanity_filter=GOOGLE_SPEECH_PROFANITY_FILTER             # Configurable filtering
        )
        
        # Perform the transcription
        logger.info("Starting Google Speech-to-Text transcription...")
        response = google_speech_client.recognize(config=config, audio=audio)
        
        # Extract transcription from response with quality metrics
        transcription = ""
        total_confidence = 0
        word_count = 0
        
        for result in response.results:
            alternative = result.alternatives[0]
            transcription += alternative.transcript
            
            # Log confidence scores for quality monitoring
            if hasattr(alternative, 'confidence'):
                total_confidence += alternative.confidence
                logger.info(f"Segment confidence: {alternative.confidence:.3f}")
            
            # Log word-level details for debugging if needed
            if hasattr(alternative, 'words'):
                for word_info in alternative.words:
                    word_count += 1
                    if hasattr(word_info, 'confidence'):
                        logger.debug(f"Word '{word_info.word}' confidence: {word_info.confidence:.3f}")
        
        if not transcription.strip():
            logger.warning("No transcription received from Google Speech API")
            return ""
        
        # Log overall quality metrics
        if total_confidence > 0 and len(response.results) > 0:
            avg_confidence = total_confidence / len(response.results)
            logger.info(f"Average transcription confidence: {avg_confidence:.3f}")
            if avg_confidence < 0.5:
                logger.warning(f"Low confidence transcription ({avg_confidence:.3f}) - audio quality may be poor")
        
        logger.info(f"Google Speech transcription completed successfully with {word_count} words")
        return transcription.strip()
        
    except Exception as e:
        logger.error(f"Google Speech transcription failed: {str(e)}")
        raise e

@app.on_event("startup")
async def startup_event():
    """Load models on startup with memory optimization."""
    logger.info("Starting Dual-Language Transcription Service...")
    
    # Check if we're in Khmer-only mode for memory optimization
    khmer_only_mode = os.getenv('KHMER_ONLY_MODE', 'false').lower() == 'true'
    
    if khmer_only_mode:
        logger.info("🔧 Running in KHMER_ONLY_MODE for memory optimization")
        whisper_success = False
        google_speech_success = initialize_google_speech()
    else:
        whisper_success = load_whisper_model()
        google_speech_success = initialize_google_speech()
    
    if not whisper_success and not google_speech_success:
        logger.error("Failed to load any models. Exiting.")
        raise Exception("Failed to load any models")
    elif not whisper_success:
        if khmer_only_mode:
            logger.info("✅ Running in Khmer-only mode. English transcription disabled for memory optimization.")
        else:
            logger.warning("Whisper model failed to load. English transcription will not be available.")
    elif not google_speech_success:
        logger.warning("Google Speech client failed to initialize. Khmer transcription will not be available.")
    
    # Log memory optimization tips
    if google_speech_success and whisper_success:
        logger.info("💭 Both Whisper and Google Speech-to-Text are available.")
    
    logger.info("Available endpoints:")
    if whisper_success:
        logger.info("  POST /transcribe/english - English transcription (Whisper)")
    if google_speech_success:
        logger.info("  POST /transcribe/khmer - Khmer transcription (Google Speech-to-Text)")
    
    # Set memory optimization for PyTorch (used by Whisper)
    torch_num_threads = int(os.getenv('TORCH_NUM_THREADS', 2))
    torch.set_num_threads(torch_num_threads)  # Limit CPU threads for memory
    logger.info(f"PyTorch configured with {torch_num_threads} threads")
    
    if torch.cuda.is_available() and whisper_success:
        torch.cuda.empty_cache()
        # Set memory fraction if on GPU for Whisper
        torch.cuda.set_per_process_memory_fraction(0.8)
        logger.info("CUDA memory optimization enabled")

@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers."""
    return {
        'status': 'healthy',
        'models': {
            'whisper_loaded': whisper_model is not None,
            'google_speech_loaded': google_speech_client is not None
        },
        'service': 'dual-language-transcription'
    }

@app.post("/transcribe/english")
async def transcribe_english(
    file: UploadFile = File(...),
    task: str = Form("transcribe")
):
    """
    Transcribe audio file to text using Whisper (English).
    
    - **file**: Audio file to transcribe
    - **task**: 'transcribe' or 'translate' (default: 'transcribe')
    """
    try:
        # Check if model is loaded
        if whisper_model is None:
            khmer_only = os.getenv('KHMER_ONLY_MODE', 'false').lower() == 'true'
            if khmer_only:
                raise HTTPException(
                    status_code=503, 
                    detail="English transcription disabled in KHMER_ONLY_MODE. Use /transcribe/khmer endpoint."
                )
            else:
                raise HTTPException(status_code=500, detail="Whisper model not loaded")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        if not allowed_file(file.filename):
            raise HTTPException(
                status_code=400, 
                detail=f"File type not supported. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Validate task parameter
        if task not in ['transcribe', 'translate']:
            raise HTTPException(
                status_code=400, 
                detail='Task must be either "transcribe" or "translate"'
            )
        
        # Check file size
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 100MB.")
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.audio') as temp_file:
            temp_file.write(file_content)
            temp_filename = temp_file.name
        
        try:
            # Transcribe the audio
            logger.info(f"Transcribing English file: {file.filename}")
            result = whisper_model.transcribe(
                temp_filename,
                language='en',
                task=task,
                verbose=False
            )
            
            # Prepare response
            response_data = {
                'text': result['text'].strip(),
                'language': 'en',
                'model': 'whisper',
                'task': task,
                'filename': file.filename
            }
            
            # Include segments if available
            if 'segments' in result and result['segments']:
                response_data['segments'] = [{
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text'].strip()
                } for segment in result['segments']]
            
            logger.info(f"English transcription completed for: {file.filename}")
            return response_data
            
        except Exception as e:
            logger.error(f"English transcription failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"English transcription failed: {str(e)}")
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_filename)
            except OSError:
                pass
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in English endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/transcribe/khmer")
async def transcribe_khmer(file: UploadFile = File(...)):
    """
    Transcribe audio file to text using Google Speech-to-Text (Khmer).
    
    - **file**: Audio file to transcribe
    """
    try:
        # Check if Google Speech client is loaded
        if google_speech_client is None:
            raise HTTPException(status_code=500, detail="Google Speech client not initialized")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        if not allowed_file(file.filename):
            raise HTTPException(
                status_code=400, 
                detail=f"File type not supported. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 100MB.")
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.audio') as temp_file:
            temp_file.write(file_content)
            temp_filename = temp_file.name
        
        try:
            # Transcribe the audio
            logger.info(f"Transcribing Khmer file: {file.filename}")
            transcription = transcribe_with_google_speech(temp_filename)
            
            # Prepare response
            response_data = {
                'text': transcription.strip(),
                'language': 'khm',
                'model': 'google-speech-to-text',
                'task': 'transcribe',
                'filename': file.filename
            }
            
            logger.info(f"Khmer transcription completed for: {file.filename}")
            return response_data
            
        except Exception as e:
            logger.error(f"Khmer transcription failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Khmer transcription failed: {str(e)}")
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_filename)
            except OSError:
                pass
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in Khmer endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/transcribe")
async def transcribe_legacy(
    file: UploadFile = File(...),
    task: str = Form("transcribe")
):
    """
    Legacy endpoint - defaults to English transcription for backward compatibility.
    """
    logger.info("Using legacy endpoint - redirecting to English transcription")
    return await transcribe_english(file, task)

@app.get("/models")
async def list_models():
    """List available models and their status."""
    return {
        'whisper': {
            'available_models': ['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3', 'turbo'],
            'current_model': os.getenv('WHISPER_MODEL_SIZE', 'tiny'),
            'model_loaded': whisper_model is not None,
            'language': 'English',
            'parameters': '39M - 1550M depending on model',
            'accuracy': 'Very High for English'
        },
        'google_speech': {
            'service': 'Google Speech-to-Text API',
            'client_initialized': google_speech_client is not None,
            'language': 'Khmer',
            'language_code': 'km-KH'
        }
    }

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        'service': 'Dual-Language Speech-to-Text API',
        'version': '2.0.0',
        'models': {
            'english': f'OpenAI Whisper ({os.getenv("WHISPER_MODEL_SIZE", "tiny")})',
            'khmer': 'Google Speech-to-Text API'
        },
        'endpoints': {
            'POST /transcribe/english': 'Transcribe English audio using Whisper',
            'POST /transcribe/khmer': 'Transcribe Khmer audio using Google Speech-to-Text',
            'POST /transcribe': 'Legacy endpoint (defaults to English)',
            'GET /health': 'Health check',
            'GET /models': 'List available models',
            'GET /': 'This information',
            'GET /docs': 'Interactive API documentation',
            'GET /redoc': 'Alternative API documentation'
        },
        'supported_formats': list(ALLOWED_EXTENSIONS)
    }

if __name__ == '__main__':
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    
    logger.info(f"Starting FastAPI server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
