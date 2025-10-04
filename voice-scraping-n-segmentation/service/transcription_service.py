"""
Transcription Service

This module provides audio transcription functionality using either:
1. Local OpenAI Whisper model
2. External transcription API (for better Khmer support)
"""

import os
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import numpy as np
import torch
import whisper
import librosa
import soundfile as sf
import requests
import base64
import io

# Hugging Face transformers for specialized models
try:
    from transformers import (
        WhisperProcessor, 
        WhisperForConditionalGeneration,
        pipeline
    )
    HF_TRANSFORMERS_AVAILABLE = True
except ImportError:
    HF_TRANSFORMERS_AVAILABLE = False


class TranscriptionService:
    """
    Service class for audio transcription using local Whisper or external API.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Transcription Service.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # External transcription service settings
        self.external_service_url = config.get('transcription_service_url')
        self.external_service_timeout = config.get('transcription_service_timeout', 300)
        self.use_external_service = bool(self.external_service_url)
        
        # Whisper configuration (fallback or primary)
        self.model_name = config.get('whisper_model', 'base')  # tiny, base, small, medium, large
        self.language = config.get('whisper_language', 'km')  # Khmer language by default
        self.device = config.get('whisper_device', 'auto')
        
        # Hugging Face Khmer Whisper model settings
        self.use_khmer_whisper_hf = config.get('use_khmer_whisper_hf', False)
        self.khmer_whisper_model_id = config.get('khmer_whisper_model_id', 'ksoky/whisper-large-khmer-asr')
        self.hf_model = None
        self.hf_processor = None
        
        # Transcription settings
        self.word_timestamps = config.get('word_timestamps', True)
        self.no_speech_threshold = config.get('no_speech_threshold', 0.6)
        self.logprob_threshold = config.get('logprob_threshold', -1.0)
        self.condition_on_previous_text = config.get('condition_on_previous_text', True)
        
        # Audio preprocessing
        self.target_sample_rate = 16000  # Both Whisper and most APIs expect 16kHz
        
        # Initialize transcription method
        if self.use_external_service:
            self.logger.info(f"Primary: external transcription service: {self.external_service_url}")
            self._test_external_service()
            # Always load Whisper as fallback, even when external service is primary
            self.logger.info("Loading Whisper model as fallback")
            self._load_whisper_models()
        else:
            self.logger.info("Using local Whisper transcription")
            self._load_whisper_models()
    
    def _load_whisper_models(self):
        """Load Whisper models (both original and specialized Khmer model if requested)."""
        try:
            # Initialize device
            if self.device == 'auto':
                self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            
            # Load Hugging Face Khmer Whisper model if requested
            if self.use_khmer_whisper_hf:
                self._load_hf_khmer_model()
            
            # Always load original Whisper as fallback
            self.logger.info(f"Loading OpenAI Whisper model '{self.model_name}' on device '{self.device}'")
            self.model = whisper.load_model(self.model_name, device=self.device)
            self.logger.info("OpenAI Whisper model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load Whisper models: {e}")
            self.model = None
    
    def _load_hf_khmer_model(self):
        """Load Hugging Face Khmer Whisper model."""
        if not HF_TRANSFORMERS_AVAILABLE:
            self.logger.error("Transformers library not available. Install with: pip install transformers")
            return
        
        try:
            self.logger.info(f"Loading Hugging Face Khmer Whisper model: {self.khmer_whisper_model_id}")
            
            # Load processor and model
            self.hf_processor = WhisperProcessor.from_pretrained(self.khmer_whisper_model_id)
            self.hf_model = WhisperForConditionalGeneration.from_pretrained(self.khmer_whisper_model_id)
            
            # Move to device
            self.hf_model = self.hf_model.to(self.device)
            
            self.logger.info(f"Hugging Face Khmer Whisper model loaded successfully on {self.device}")
            
        except Exception as e:
            self.logger.error(f"Failed to load Hugging Face Khmer model: {e}")
            self.hf_model = None
            self.hf_processor = None
    
    def _test_external_service(self):
        """Test connection to external transcription service."""
        try:
            # Simple health check or info endpoint
            response = requests.get(
                f"{self.external_service_url.rstrip('/')}/health",
                timeout=10
            )
            if response.status_code == 200:
                self.logger.info("External transcription service is available")
            else:
                self.logger.warning(f"External service responded with status {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Cannot connect to external transcription service: {e}")
            self.logger.info("Will fall back to local Whisper if available")
    
    def is_available(self) -> bool:
        """
        Check if transcription service is available.
        
        Returns:
            bool: True if service is available
        """
        # Service is available if any of these are true:
        # 1. External service is configured
        # 2. Original Whisper model is loaded  
        # 3. HF Khmer Whisper model is loaded
        external_available = self.use_external_service and bool(self.external_service_url)
        whisper_available = self.model is not None
        hf_khmer_available = self.hf_model is not None and self.hf_processor is not None
        
        return external_available or whisper_available or hf_khmer_available
    
    def _preprocess_audio(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Preprocess audio for Whisper transcription.
        
        Args:
            audio_data: Audio data array
            sample_rate: Original sample rate
            
        Returns:
            Preprocessed audio data
        """
        # Resample to 16kHz if needed
        if sample_rate != self.target_sample_rate:
            audio_data = librosa.resample(
                audio_data, 
                orig_sr=sample_rate, 
                target_sr=self.target_sample_rate
            )
        
        # Ensure mono
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        # Normalize to [-1, 1]
        if np.max(np.abs(audio_data)) > 1.0:
            audio_data = audio_data / np.max(np.abs(audio_data))
        
        return audio_data
    
    def _transcribe_with_external_api(self, audio_data: np.ndarray, sample_rate: int, override_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribe audio using external API service.
        
        Args:
            audio_data: Audio data array
            sample_rate: Sample rate
            
        Returns:
            Dictionary containing transcription results
        """
        try:
            # Preprocess audio
            processed_audio = self._preprocess_audio(audio_data, sample_rate)
            
            # Convert audio to WAV bytes
            audio_bytes = io.BytesIO()
            sf.write(audio_bytes, processed_audio, self.target_sample_rate, format='WAV')
            audio_bytes.seek(0)

            # Encode audio as base64 for API transmission
            # audio_b64 = base64.b64encode(audio_bytes.read()).decode('utf-8')

            # Prepare API request
            # payload = {
            # 'audio_data': audio_b64,
            # 'sample_rate': self.target_sample_rate,
            # 'language': 'km',  # Khmer
            # 'format': 'wav'
            # }
            
            files = {'file': ('audio.wav', audio_bytes, 'audio/wav')}
            data = {
                'sample_rate': str(self.target_sample_rate),
                'language': 'km',  # Khmer
                'format': 'wav'
            }

            # Call external transcription service (allow per-request override URL)
            url = override_url if override_url else self.external_service_url

            response = requests.post(
                url,
                files=files,
                data=data,
                timeout=self.external_service_timeout,
                # headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Standardize response format to match Whisper
                return {
                    'text': result.get('transcription', result.get('text', '')),
                    'language': 'km',
                    'segments': result.get('segments', []),
                    'words': result.get('words', []),
                    'duration': len(processed_audio) / self.target_sample_rate,
                    'no_speech_prob': result.get('no_speech_prob', 0.0),
                    'external_api': True
                }
            else:
                self.logger.error(f"External API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            self.logger.error("External transcription service timed out")
            return None
        except Exception as e:
            self.logger.error(f"External transcription failed: {e}")
            return None
    
    def transcribe_audio_file(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Transcribe an audio file.
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Dictionary containing transcription results
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'Transcription service not available'
            }
        
        try:
            # Load audio
            audio_data, sample_rate = librosa.load(audio_file_path, sr=None)
            
            # Preprocess audio
            audio_data = self._preprocess_audio(audio_data, sample_rate)
            
            # Transcribe using Whisper
            result = self.model.transcribe(
                audio_data,
                language=self.language,
                word_timestamps=self.word_timestamps,
                no_speech_threshold=self.no_speech_threshold,
                logprob_threshold=self.logprob_threshold,
                condition_on_previous_text=self.condition_on_previous_text
            )
            
            return {
                'success': True,
                'data': {
                    'text': result['text'].strip(),
                    'language': result['language'],
                    'segments': result.get('segments', []),
                    'words': self._extract_words_from_segments(result.get('segments', [])),
                    'duration': len(audio_data) / self.target_sample_rate,
                    'no_speech_prob': result.get('no_speech_prob', 0.0)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to transcribe audio file {audio_file_path}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def transcribe_audio_chunk(self, audio_data: np.ndarray, sample_rate: int, chunk_id: str, processing_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Transcribe an audio chunk.
        
        Args:
            audio_data: Audio data array
            sample_rate: Sample rate
            chunk_id: Identifier for the chunk
            
        Returns:
            Dictionary containing transcription results
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'Transcription service not available'
            }
        
        try:
            # Preprocess audio
            processed_audio = self._preprocess_audio(audio_data, sample_rate)
            
            # Skip very short chunks
            duration = len(processed_audio) / self.target_sample_rate
            if duration < 0.1:  # Less than 100ms
                return {
                    'success': True,
                    'data': {
                        'chunk_id': chunk_id,
                        'text': '',
                        'language': 'km',
                        'segments': [],
                        'words': [],
                        'duration': duration,
                        'no_speech_prob': 1.0
                    }
                }
            
            # Choose transcription method (allow per-request override)
            use_external = self.use_external_service # Start with global setting
            override_url = None

            if processing_config and isinstance(processing_config, dict):
                if 'use_external_transcription' in processing_config:
                    use_external = bool(processing_config['use_external_transcription'])
                override_url = processing_config.get('external_transcription_url')

            if use_external:
                transcription_result = self._transcribe_with_external_api(audio_data, sample_rate, override_url=override_url)
                transcription_method = 'external_api'
                
                # If external fails and Whisper is available, fallback to Whisper
                if transcription_result is None and self.model is not None:
                    self.logger.warning(f"External transcription failed for chunk {chunk_id}, falling back to Whisper")
                    transcription_result = self._transcribe_with_whisper(audio_data, sample_rate)
                    transcription_method = 'whisper_fallback'
            else:
                # Choose between HF Khmer model and original Whisper
                if self.use_khmer_whisper_hf and self.hf_model is not None:
                    transcription_result = self._transcribe_with_hf_khmer(audio_data, sample_rate)
                    transcription_method = 'whisper_hf_khmer'
                elif self.model is not None:
                    transcription_result = self._transcribe_with_whisper(audio_data, sample_rate)
                    transcription_method = 'whisper_local'
                else:
                    raise Exception("No Whisper model available for transcription")
            
            if transcription_result is None:
                return {
                    'success': False,
                    'error': 'Transcription failed',
                    'chunk_id': chunk_id
                }
            
            return {
                'success': True,
                'data': {
                    'chunk_id': chunk_id,
                    'text': transcription_result.get('text', '').strip(),
                    'language': transcription_result.get('language', 'km'),
                    'segments': transcription_result.get('segments', []),
                    'words': transcription_result.get('words', []),
                    'duration': duration,
                    'no_speech_prob': transcription_result.get('no_speech_prob', 0.0),
                    'transcription_method': transcription_method
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to transcribe audio chunk {chunk_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'chunk_id': chunk_id
            }
    
    def transcribe_multiple_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transcribe multiple audio chunks.
        
        Args:
            chunks: List of audio chunk dictionaries
            
        Returns:
            List of transcription results
        """
        transcriptions = []
        
        for chunk in chunks:
            chunk_id = chunk.get('chunk_id', 'unknown')
            audio_data = chunk.get('audio_data')
            sample_rate = chunk.get('sample_rate', 16000)
            
            if audio_data is None:
                self.logger.warning(f"No audio data for chunk {chunk_id}")
                continue
            
            # Pass processing_config from chunk if provided
            processing_config = chunk.get('processing_config') if isinstance(chunk.get('processing_config'), dict) else None
            result = self.transcribe_audio_chunk(audio_data, sample_rate, chunk_id, processing_config=processing_config)
            
            # Add chunk timing information
            if result['success']:
                result['data'].update({
                    'chunk_start_time': chunk.get('start_time', 0.0),
                    'chunk_end_time': chunk.get('end_time', 0.0),
                    'chunk_duration': chunk.get('duration', 0.0)
                })
            
            transcriptions.append(result)
        
        return transcriptions
    
    def _transcribe_with_whisper(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """
        Transcribe audio using local Whisper model.
        
        Args:
            audio_data: Audio data array
            sample_rate: Sample rate
            
        Returns:
            Dictionary containing transcription results
        """
        if self.model is None:
            raise Exception("Whisper model not loaded")
        
        # Preprocess audio
        processed_audio = self._preprocess_audio(audio_data, sample_rate)
        
        # Transcribe using Whisper
        result = self.model.transcribe(
            processed_audio,
            language=self.language,
            word_timestamps=self.word_timestamps,
            no_speech_threshold=self.no_speech_threshold,
            logprob_threshold=self.logprob_threshold,
            condition_on_previous_text=False  # Each chunk is independent
        )
        
        return {
            'text': result['text'],
            'language': result['language'],
            'segments': result.get('segments', []),
            'words': self._extract_words_from_segments(result.get('segments', [])),
            'duration': len(processed_audio) / self.target_sample_rate,
            'no_speech_prob': result.get('no_speech_prob', 0.0)
        }
    
    def _transcribe_with_hf_khmer(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """
        Transcribe audio using Hugging Face Khmer Whisper model.
        
        Args:
            audio_data: Audio data array
            sample_rate: Sample rate
            
        Returns:
            Dictionary containing transcription results
        """
        if self.hf_model is None or self.hf_processor is None:
            raise Exception("Hugging Face Khmer Whisper model not loaded")
        
        try:
            # Preprocess audio
            processed_audio = self._preprocess_audio(audio_data, sample_rate)
            
            # Prepare input features
            input_features = self.hf_processor(
                processed_audio, 
                sampling_rate=self.target_sample_rate, 
                return_tensors="pt"
            ).input_features
            
            # Move to device
            input_features = input_features.to(self.device)
            
            # Generate transcription
            with torch.no_grad():
                predicted_ids = self.hf_model.generate(
                    input_features,
                    max_length=448,  # Standard for Whisper
                    num_beams=5,
                    early_stopping=True,
                    use_cache=True
                )
            
            # Decode transcription
            transcription = self.hf_processor.batch_decode(
                predicted_ids, 
                skip_special_tokens=True
            )[0]
            
            # Create response in standard format
            return {
                'text': transcription.strip(),
                'language': 'km',  # Khmer
                'segments': [],  # HF model doesn't provide detailed segments by default
                'words': [],     # Would need additional processing for word timestamps
                'duration': len(processed_audio) / self.target_sample_rate,
                'no_speech_prob': 0.0,  # Not available from HF model
                'model_used': 'hf_khmer_whisper'
            }
            
        except Exception as e:
            self.logger.error(f"HF Khmer Whisper transcription failed: {e}")
            return None
    
    def _extract_words_from_segments(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract word-level information from Whisper segments.
        
        Args:
            segments: List of segment dictionaries from Whisper
            
        Returns:
            List of word dictionaries
        """
        words = []
        
        for segment in segments:
            if 'words' in segment:
                for word_info in segment['words']:
                    words.append({
                        'word': word_info.get('word', '').strip(),
                        'start': word_info.get('start', 0.0),
                        'end': word_info.get('end', 0.0),
                        'probability': word_info.get('probability', 0.0)
                    })
        
        return words
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the transcription service.
        
        Returns:
            Dictionary containing service information
        """
        if not self.is_available():
            return {
                'available': False,
                'error': 'Transcription service not available'
            }
        
        info = {
            'available': True,
            'language': self.language,
            'target_sample_rate': self.target_sample_rate,
            'word_timestamps': self.word_timestamps
        }
        
        # Determine primary transcription method
        if self.use_external_service:
            primary_method = 'external_api'
        elif self.use_khmer_whisper_hf and self.hf_model is not None:
            primary_method = 'whisper_hf_khmer'
        else:
            primary_method = 'whisper_local'
        
        info['transcription_method'] = primary_method
        
        if self.use_external_service:
            info.update({
                'external_service_url': self.external_service_url,
                'external_service_timeout': self.external_service_timeout,
            })
        
        # Whisper model info
        info.update({
            'whisper_available': self.model is not None,
            'whisper_model_name': self.model_name,
            'device': self.device,
        })
        
        # HF Khmer model info
        info.update({
            'hf_khmer_enabled': self.use_khmer_whisper_hf,
            'hf_khmer_available': self.hf_model is not None and self.hf_processor is not None,
            'hf_khmer_model_id': self.khmer_whisper_model_id if self.use_khmer_whisper_hf else None,
        })
        
        return info
    
    def save_transcription_to_file(self, transcription_data: Dict[str, Any], output_path: str) -> bool:
        """
        Save transcription data to a file.
        
        Args:
            transcription_data: Transcription result data
            output_path: Path to save the transcription
            
        Returns:
            bool: True if saved successfully
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create a formatted transcription
            content = []
            content.append(f"Transcription Result")
            content.append(f"Language: {transcription_data.get('language', 'unknown')}")
            content.append(f"Duration: {transcription_data.get('duration', 0):.2f}s")
            content.append(f"No Speech Probability: {transcription_data.get('no_speech_prob', 0):.3f}")
            content.append("")
            content.append("Full Text:")
            content.append(transcription_data.get('text', ''))
            content.append("")
            
            # Add word-level timestamps if available
            words = transcription_data.get('words', [])
            if words:
                content.append("Word-level Timestamps:")
                for word in words:
                    content.append(f"{word['start']:.2f}-{word['end']:.2f}: {word['word']} (prob: {word['probability']:.3f})")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save transcription to {output_path}: {e}")
            return False
