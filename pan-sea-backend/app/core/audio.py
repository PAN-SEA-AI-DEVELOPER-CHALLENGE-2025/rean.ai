import os
import time
import speech_recognition as sr
import whisper
from pydub import AudioSegment
from typing import Optional, List
import tempfile
import logging
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Service for audio processing, transcription, and analysis using local Whisper"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
        # Initialize local Whisper model
        try:
            # You can choose different model sizes: "tiny", "base", "small", "medium", "large"
            # Smaller models are faster but less accurate
            self.whisper_model_size = getattr(settings, 'whisper_model_size')
            self.whisper_device = getattr(settings, 'whisper_device', 'cpu')
            
            logger.info(f"Loading Whisper model: {self.whisper_model_size} on {self.whisper_device}")
            self.whisper_model = whisper.load_model(self.whisper_model_size, device=self.whisper_device)
            logger.info(f"Successfully loaded Whisper model: {self.whisper_model_size}")
        except Exception as e:
            logger.warning(f"Failed to load Whisper model: {str(e)}")
            logger.info("Whisper will not be available. Install with: pip install openai-whisper")
            self.whisper_model = None
    
    def is_whisper_available(self) -> bool:
        """Check if local Whisper model is available"""
        return self.whisper_model is not None
    
    def is_supported_format(self, file_path: str) -> bool:
        """Check if audio format is supported"""
        file_extension = Path(file_path).suffix.lower()
        logger.info(f"Checking file: {file_path}, extension: {file_extension}")
        logger.info(f"Supported formats: {settings.supported_audio_formats}")
        is_supported = file_extension in settings.supported_audio_formats
        logger.info(f"Format {file_extension} is supported: {is_supported}")
        return is_supported
    
    def convert_to_wav(self, input_path: str, output_path: Optional[str] = None) -> str:
        """Convert audio file to WAV format"""
        logger.info(f"Converting file: {input_path}")
        if not self.is_supported_format(input_path):
            file_extension = Path(input_path).suffix.lower()
            logger.error(f"Unsupported audio format: {file_extension} for file: {input_path}")
            raise ValueError(f"Unsupported audio format: {file_extension}")
        
        if output_path is None:
            output_path = str(Path(input_path).with_suffix('.wav'))
        
        try:
            # Load audio file
            audio = AudioSegment.from_file(input_path)
            
            # Convert to mono and set sample rate
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(16000)
            
            # Export as WAV
            audio.export(output_path, format="wav")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting audio: {str(e)}")
            raise Exception(f"Failed to convert audio: {str(e)}")
    
    def get_audio_duration(self, file_path: str) -> int:
        """Get audio duration in seconds"""
        try:
            audio = AudioSegment.from_file(file_path)
            return int(len(audio) / 1000)  # Convert milliseconds to seconds
        except Exception as e:
            logger.error(f"Error getting audio duration: {str(e)}")
            return 0
    
    def split_audio_chunks(self, file_path: str, chunk_duration: int = None) -> List[str]:
        """Split audio into smaller chunks for processing"""
        if chunk_duration is None:
            chunk_duration = settings.audio_chunk_duration
        
        try:
            audio = AudioSegment.from_file(file_path)
            chunk_length_ms = chunk_duration * 1000  # Convert to milliseconds
            
            chunks = []
            for i, chunk_start in enumerate(range(0, len(audio), chunk_length_ms)):
                chunk_end = min(chunk_start + chunk_length_ms, len(audio))
                chunk = audio[chunk_start:chunk_end]
                
                # Create temporary file for chunk
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    chunk_path = temp_file.name
                    chunk.export(chunk_path, format="wav")
                    chunks.append(chunk_path)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error splitting audio: {str(e)}")
            raise Exception(f"Failed to split audio: {str(e)}")
    
    async def transcribe_with_whisper(self, file_path: str, language: str = None) -> str:
        """Transcribe audio using local Whisper model, with chunking for long files"""
        if not self.whisper_model:
            raise ValueError("Local Whisper model not available")
        try:
            logger.info(f"Starting transcription for file: {file_path}")
            
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"File does not exist: {file_path}")
                raise ValueError(f"File does not exist: {file_path}")
            
            # Log file info
            file_size = os.path.getsize(file_path)
            logger.info(f"File size: {file_size} bytes")
            
            # Ensure file is in WAV format for better compatibility
            if not file_path.endswith('.wav'):
                logger.info(f"Converting {file_path} to WAV format")
                file_path = self.convert_to_wav(file_path)

            duration = self.get_audio_duration(file_path)
            chunk_duration = getattr(settings, 'audio_chunk_duration', 30)

            if duration > chunk_duration:
                logger.info(f"Audio duration {duration}s exceeds chunk duration {chunk_duration}s. Splitting into chunks.")
                chunk_paths = self.split_audio_chunks(file_path, chunk_duration=chunk_duration)
                transcriptions = []
                start_time = time.time()
                try:
                    for chunk_path in chunk_paths:
                        transcribe_options = {}
                        if language:
                            transcribe_options['language'] = language
                        result = self.whisper_model.transcribe(chunk_path, **transcribe_options)
                        text = result["text"].strip()
                        transcriptions.append(text)
                    transcription = " ".join(transcriptions)
                    elapsed = time.time() - start_time
                    logger.info(f"Chunked transcription completed. Length: {len(transcription)} characters. Time taken: {elapsed:.2f} seconds")
                    print(f"[Chunked transcription] Time taken: {elapsed:.2f} seconds")
                    return transcription
                finally:
                    self.cleanup_temp_files(chunk_paths)
            else:
                logger.info(f"Transcribing with local Whisper model: {self.whisper_model_size}")
                transcribe_options = {}
                if language:
                    transcribe_options['language'] = language
                    logger.info(f"Using language: {language}")
                result = self.whisper_model.transcribe(file_path, **transcribe_options)
                transcription = result["text"].strip()
                logger.info(f"Transcription completed. Length: {len(transcription)} characters")
                return transcription
        except Exception as e:
            logger.error(f"Error transcribing with local Whisper: {str(e)}")
            raise Exception(f"Failed to transcribe audio: {str(e)}")
    
    def transcribe_with_speech_recognition(self, file_path: str) -> str:
        """Transcribe audio using SpeechRecognition library (fallback)"""
        try:
            # Ensure file is in WAV format
            if not file_path.endswith('.wav'):
                file_path = self.convert_to_wav(file_path)
            
            with sr.AudioFile(file_path) as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source)
                
                # Record the audio
                audio = self.recognizer.record(source)
                
                # Transcribe using Google Speech Recognition
                text = self.recognizer.recognize_google(audio)
                return text
                
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return ""
        except sr.RequestError as e:
            logger.error(f"Speech recognition error: {str(e)}")
            raise Exception(f"Speech recognition failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            raise Exception(f"Failed to transcribe audio: {str(e)}")
    
    async def transcribe_audio(self, file_path: str, language: str = None, use_whisper: bool = True) -> str:
        """Main transcription method with local Whisper preferred, supports chunking for long files"""
        try:
            if use_whisper and self.whisper_model:
                logger.info("Using local Whisper for transcription (with chunking support)")
                return await self.transcribe_with_whisper(file_path, language)
            else:
                logger.info("Using SpeechRecognition fallback")
                return self.transcribe_with_speech_recognition(file_path)
        except Exception as e:
            logger.error(f"Primary transcription failed: {str(e)}")
            # Try fallback method
            if use_whisper and self.whisper_model:
                try:
                    logger.info("Whisper failed, trying SpeechRecognition fallback")
                    return self.transcribe_with_speech_recognition(file_path)
                except Exception as fallback_error:
                    logger.error(f"Fallback transcription also failed: {str(fallback_error)}")
                    raise Exception(f"Both Whisper and fallback transcription failed: {str(e)}")
            else:
                raise Exception(f"Transcription failed: {str(e)}")
    
    def cleanup_temp_files(self, file_paths: List[str]):
        """Clean up temporary files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception as e:
                logger.warning(f"Could not delete temp file {file_path}: {str(e)}")


# Global instance
audio_processor = AudioProcessor()
