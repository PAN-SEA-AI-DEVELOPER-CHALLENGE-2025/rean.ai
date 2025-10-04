"""
Montreal Forced Alignment (MFA) Service

This module provides forced alignment functionality using Montreal Forced Alignment
to refine word-level timestamps from transcriptions.
"""

import os
import logging
import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import textgrid
import soundfile as sf
import librosa
import numpy as np


class MFAService:
    """
    Service class for Montreal Forced Alignment operations.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the MFA Service.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # MFA configuration for Khmer
        self.mfa_command = config.get('mfa_command', 'mfa')
        self.language = config.get('mfa_language', 'khmer')
        
        # Model paths - support custom TTS-trained models
        self.project_root = Path(config.get('project_root', '.'))
        self.custom_models_dir = self.project_root / 'mfa_models' / 'custom_models'
        self.training_dir = self.project_root / 'mfa_models' / 'training'
        
        # Check for custom trained models first
        custom_acoustic_model = self.custom_models_dir / 'khmer_acoustic_model.zip'
        custom_dictionary = self.training_dir / 'khmer_lexicon.txt'
        
        if custom_acoustic_model.exists():
            self.acoustic_model = str(custom_acoustic_model)
            self.logger.info(f"Using custom TTS-trained acoustic model: {self.acoustic_model}")
        else:
            self.acoustic_model = config.get('mfa_acoustic_model', 'khmer')
            self.logger.warning("Custom acoustic model not found, using default (may not work well for Khmer)")
        
        if custom_dictionary.exists():
            self.dictionary = str(custom_dictionary)
            self.logger.info(f"Using custom Khmer dictionary: {self.dictionary}")
        else:
            self.dictionary = config.get('mfa_dictionary', 'khmer')
            self.logger.warning("Custom Khmer dictionary not found, using default")
        
        # Audio settings
        self.target_sample_rate = config.get('mfa_sample_rate', 22050)
        
        # Working directories
        self.temp_dir = config.get('temp_dir', 'data/temp')
        self.mfa_temp_dir = os.path.join(self.temp_dir, 'mfa_workspace')
        
        # Create working directories
        Path(self.mfa_temp_dir).mkdir(parents=True, exist_ok=True)
        
        # Check MFA availability
        self._check_mfa_availability()
    
    def _get_mfa_env(self) -> Dict[str, str]:
        """
        Get the environment variables for running MFA commands.
        Ensures the MFA bin directory is in PATH.
        """
        env = os.environ.copy()
        mfa_bin_dir = Path(self.mfa_command).parent
        if str(mfa_bin_dir) not in env.get('PATH', ''):
            env['PATH'] = str(mfa_bin_dir) + os.pathsep + env.get('PATH', '')
        return env

    def _check_mfa_availability(self) -> bool:
        """
        Check if MFA is available in the system.
        
        Returns:
            bool: True if MFA is available
        """
        # Try several ways to probe the MFA CLI. Some builds do not support --version,
        # so we attempt --version, --help, and running without args. If any of these
        # produce output indicating the CLI is present, we mark MFA as available.
        probes = [
            [self.mfa_command, '--version'],
            [self.mfa_command, '--help'],
            [self.mfa_command]
        ]

        try:
            for cmd in probes:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=10,
                        env=self._get_mfa_env() # Pass the modified environment
                    )
                except FileNotFoundError:
                    # Binary not found at this path
                    self.logger.debug(f"MFA probe failed (not found): {' '.join(cmd)}")
                    continue

                stdout = (result.stdout or '').strip()
                stderr = (result.stderr or '').strip()

                # Successful return code -> available
                if result.returncode == 0:
                    self.logger.info(f"MFA available: {stdout or stderr}")
                    self.available = True
                    return True

                # Some MFA builds return non-zero for --version but print an error like
                # "No such option: --version". Presence of stderr or usage text is enough
                # to conclude the binary exists.
                if stderr:
                    # Treat common CLI messages as proof of existence
                    if 'No such option' in stderr or 'Usage:' in stderr or 'Try' in stderr:
                        self.logger.info(f"MFA available (non-zero probe): {stderr}")
                        self.available = True
                        return True

            # If none of the probes succeeded
            self.logger.warning("MFA command failed or not found at configured path")
            self.available = False
            return False

        except subprocess.TimeoutExpired as e:
            self.logger.warning(f"MFA not available (timeout): {e}")
            self.available = False
            return False
    
    def is_available(self) -> bool:
        """
        Check if MFA service is available.
        
        Returns:
            bool: True if service is available
        """
        return getattr(self, 'available', False)
    
    def _prepare_audio_file(self, audio_data: np.ndarray, sample_rate: int, output_path: str) -> bool:
        """
        Prepare audio file for MFA processing.
        
        Args:
            audio_data: Audio data array
            sample_rate: Original sample rate
            output_path: Path to save the prepared audio
            
        Returns:
            bool: True if successful
        """
        try:
            # Resample if needed
            if sample_rate != self.target_sample_rate:
                audio_data = librosa.resample(
                    audio_data,
                    orig_sr=sample_rate,
                    target_sr=self.target_sample_rate
                )
            
            # Ensure mono
            if len(audio_data.shape) > 1:
                audio_data = audio_data.mean(axis=1)
            
            # Save as WAV file for MFA
            sf.write(output_path, audio_data, self.target_sample_rate)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to prepare audio file: {e}")
            return False
    
    def _prepare_transcript_file(self, transcript: str, output_path: str) -> bool:
        """
        Prepare transcript file for MFA processing.
        
        Args:
            transcript: Transcript text
            output_path: Path to save the transcript
            
        Returns:
            bool: True if successful
        """
        try:
            # Clean and normalize transcript
            cleaned_transcript = self._clean_transcript(transcript)
            
            # Save as text file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_transcript)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to prepare transcript file: {e}")
            return False
    
    def _clean_transcript(self, transcript: str) -> str:
        """
        Clean transcript for MFA processing.
        
        Args:
            transcript: Raw transcript text
            
        Returns:
            Cleaned transcript
        """
        # Remove extra whitespace
        cleaned = ' '.join(transcript.split())
        
        # Convert to uppercase (MFA convention)
        cleaned = cleaned.upper()
        
        # Remove or replace problematic characters
        replacements = {
            '"': '',
            '"': '',
            '"': '',
            ''': "'",
            ''': "'",
            '—': '-',
            '–': '-',
            '…': '...',
        }
        
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)
        
        # Remove multiple spaces
        cleaned = ' '.join(cleaned.split())
        
        return cleaned
    
    def _run_mfa_alignment(self, corpus_dir: str, output_dir: str) -> bool:
        """
        Run MFA alignment on the prepared corpus.
        
        Args:
            corpus_dir: Directory containing audio and transcript files
            output_dir: Directory to save alignment results
            
        Returns:
            bool: True if successful
        """
        try:
            # Prepare MFA command
            cmd = [
                self.mfa_command,
                'align',
                corpus_dir,
                self.dictionary,
                self.acoustic_model,
                output_dir,
                '--clean'  # Clean up temporary files
            ]
            
            self.logger.info(f"Running MFA alignment: {' '.join(cmd)}")
            
            # Run MFA alignment
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
                env=self._get_mfa_env() # Pass the modified environment
            )
            
            if result.returncode == 0:
                self.logger.info("MFA alignment completed successfully")
                return True
            else:
                self.logger.error(f"MFA alignment failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("MFA alignment timed out")
            return False
        except Exception as e:
            self.logger.error(f"Failed to run MFA alignment: {e}")
            return False
    
    def _parse_textgrid(self, textgrid_path: str) -> List[Dict[str, Any]]:
        """
        Parse TextGrid file to extract word alignments.
        
        Args:
            textgrid_path: Path to the TextGrid file
            
        Returns:
            List of word alignment dictionaries
        """
        try:
            tg = textgrid.TextGrid.fromFile(textgrid_path)
            
            words = []
            
            # Find the words tier
            word_tier = None
            for tier in tg.tiers:
                if tier.name.lower() in ['words', 'word']:
                    word_tier = tier
                    break
            
            if word_tier is None:
                self.logger.warning(f"No word tier found in TextGrid: {textgrid_path}")
                return []
            
            # Extract word alignments
            for interval in word_tier:
                if interval.mark and interval.mark.strip():
                    words.append({
                        'word': interval.mark.strip(),
                        'start': float(interval.minTime),
                        'end': float(interval.maxTime),
                        'duration': float(interval.maxTime - interval.minTime)
                    })
            
            return words
            
        except Exception as e:
            self.logger.error(f"Failed to parse TextGrid {textgrid_path}: {e}")
            return []
    
    def align_chunk(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        transcript: str,
        chunk_id: str
    ) -> Dict[str, Any]:
        """
        Perform forced alignment on an audio chunk.
        
        Args:
            audio_data: Audio data array
            sample_rate: Sample rate
            transcript: Transcript text
            chunk_id: Identifier for the chunk
            
        Returns:
            Dictionary containing alignment results
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'MFA service not available'
            }
        
        if not transcript or not transcript.strip():
            return {
                'success': False,
                'error': 'Empty transcript provided'
            }
        
        # Create temporary working directory for this chunk
        chunk_workspace = os.path.join(self.mfa_temp_dir, f"chunk_{chunk_id}")
        corpus_dir = os.path.join(chunk_workspace, 'corpus')
        output_dir = os.path.join(chunk_workspace, 'output')
        
        try:
            # Create directories
            os.makedirs(corpus_dir, exist_ok=True)
            os.makedirs(output_dir, exist_ok=True)
            
            # Prepare files
            audio_filename = f"chunk_{chunk_id}.wav"
            transcript_filename = f"chunk_{chunk_id}.txt"
            
            audio_path = os.path.join(corpus_dir, audio_filename)
            transcript_path = os.path.join(corpus_dir, transcript_filename)
            
            # Save audio and transcript files
            if not self._prepare_audio_file(audio_data, sample_rate, audio_path):
                return {
                    'success': False,
                    'error': 'Failed to prepare audio file'
                }
            
            if not self._prepare_transcript_file(transcript, transcript_path):
                return {
                    'success': False,
                    'error': 'Failed to prepare transcript file'
                }
            
            # Run MFA alignment
            if not self._run_mfa_alignment(corpus_dir, output_dir):
                return {
                    'success': False,
                    'error': 'MFA alignment failed'
                }
            
            # Parse results
            textgrid_path = os.path.join(output_dir, f"chunk_{chunk_id}.TextGrid")
            
            if not os.path.exists(textgrid_path):
                return {
                    'success': False,
                    'error': 'TextGrid file not generated'
                }
            
            words = self._parse_textgrid(textgrid_path)
            
            return {
                'success': True,
                'data': {
                    'chunk_id': chunk_id,
                    'words': words,
                    'total_words': len(words),
                    'alignment_duration': words[-1]['end'] if words else 0.0,
                    'textgrid_path': textgrid_path
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to align chunk {chunk_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            # Clean up temporary files
            try:
                if os.path.exists(chunk_workspace):
                    shutil.rmtree(chunk_workspace)
            except Exception as e:
                self.logger.warning(f"Failed to clean up workspace {chunk_workspace}: {e}")
    
    def align_multiple_chunks(self, chunk_transcriptions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Perform forced alignment on multiple chunks.
        
        Args:
            chunk_transcriptions: List of chunk transcription data
            
        Returns:
            List of alignment results
        """
        alignments = []
        
        for chunk_data in chunk_transcriptions:
            if not chunk_data.get('success', False):
                alignments.append({
                    'success': False,
                    'error': 'Chunk transcription failed',
                    'chunk_id': chunk_data.get('chunk_id', 'unknown')
                })
                continue
            
            transcription_data = chunk_data.get('data', {})
            chunk_id = transcription_data.get('chunk_id', 'unknown')
            transcript = transcription_data.get('text', '').strip()
            
            if not transcript:
                alignments.append({
                    'success': False,
                    'error': 'Empty transcript',
                    'chunk_id': chunk_id
                })
                continue
            
            # For this implementation, we'll skip MFA if we don't have audio data
            # In a real scenario, you'd pass the audio data from the VAD chunks
            alignments.append({
                'success': False,
                'error': 'Audio data not provided for alignment',
                'chunk_id': chunk_id
            })
        
        return alignments
    
    def refine_whisper_timestamps(
        self,
        whisper_words: List[Dict[str, Any]],
        mfa_words: List[Dict[str, Any]],
        chunk_start_time: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Refine Whisper timestamps using MFA alignment results.
        
        Args:
            whisper_words: Word-level data from Whisper
            mfa_words: Word-level data from MFA
            chunk_start_time: Start time offset for the chunk
            
        Returns:
            List of refined word alignments
        """
        try:
            refined_words = []
            
            # Simple alignment strategy: match words by text similarity
            mfa_idx = 0
            
            for whisper_word in whisper_words:
                whisper_text = whisper_word.get('word', '').strip().upper()
                
                # Find matching MFA word
                best_match = None
                best_score = 0
                
                for i in range(mfa_idx, min(mfa_idx + 5, len(mfa_words))):
                    mfa_word = mfa_words[i]
                    mfa_text = mfa_word.get('word', '').strip().upper()
                    
                    # Simple text matching
                    if whisper_text == mfa_text:
                        best_match = mfa_word
                        mfa_idx = i + 1
                        break
                    elif whisper_text in mfa_text or mfa_text in whisper_text:
                        score = len(set(whisper_text) & set(mfa_text)) / max(len(whisper_text), len(mfa_text))
                        if score > best_score:
                            best_match = mfa_word
                            best_score = score
                
                # Create refined word entry
                if best_match:
                    refined_word = {
                        'word': whisper_word.get('word', ''),
                        'start': chunk_start_time + best_match['start'],
                        'end': chunk_start_time + best_match['end'],
                        'duration': best_match['duration'],
                        'whisper_start': whisper_word.get('start', 0),
                        'whisper_end': whisper_word.get('end', 0),
                        'whisper_probability': whisper_word.get('probability', 0),
                        'mfa_refined': True
                    }
                else:
                    # Use original Whisper timestamps if no MFA match
                    refined_word = {
                        'word': whisper_word.get('word', ''),
                        'start': chunk_start_time + whisper_word.get('start', 0),
                        'end': chunk_start_time + whisper_word.get('end', 0),
                        'duration': whisper_word.get('end', 0) - whisper_word.get('start', 0),
                        'whisper_start': whisper_word.get('start', 0),
                        'whisper_end': whisper_word.get('end', 0),
                        'whisper_probability': whisper_word.get('probability', 0),
                        'mfa_refined': False
                    }
                
                refined_words.append(refined_word)
            
            return refined_words
            
        except Exception as e:
            self.logger.error(f"Failed to refine timestamps: {e}")
            return whisper_words  # Return original on error
    
    def get_model_status(self) -> Dict[str, Any]:
        """
        Get status of MFA models (custom vs default).
        
        Returns:
            Dictionary containing model status information
        """
        status = {
            'custom_models_available': False,
            'acoustic_model': {
                'path': self.acoustic_model,
                'is_custom': False,
                'exists': False
            },
            'dictionary': {
                'path': self.dictionary,
                'is_custom': False,
                'exists': False
            },
            'recommendations': []
        }
        
        # Check acoustic model
        if str(self.acoustic_model).endswith('.zip') and Path(self.acoustic_model).exists():
            status['acoustic_model']['exists'] = True
            if 'custom_models' in str(self.acoustic_model):
                status['acoustic_model']['is_custom'] = True
                status['custom_models_available'] = True
        
        # Check dictionary
        if Path(self.dictionary).exists():
            status['dictionary']['exists'] = True
            if 'training' in str(self.dictionary) or 'khmer_lexicon' in str(self.dictionary):
                status['dictionary']['is_custom'] = True
        
        # Recommendations
        if not status['acoustic_model']['is_custom']:
            status['recommendations'].append(
                "Consider training custom acoustic model using TTS dataset for better Khmer performance"
            )
        
        if not status['dictionary']['is_custom']:
            status['recommendations'].append(
                "Consider generating custom Khmer dictionary from TTS dataset"
            )
        
        if not status['acoustic_model']['exists']:
            status['recommendations'].append(
                "Acoustic model file not found - MFA alignment will fail"
            )
        
        if not status['dictionary']['exists']:
            status['recommendations'].append(
                "Dictionary file not found - MFA alignment will fail"
            )
        
        return status
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about the MFA service.
        
        Returns:
            Dictionary containing service information
        """
        return {
            'available': self.is_available(),
            'mfa_command': self.mfa_command,
            'acoustic_model': self.acoustic_model,
            'dictionary': self.dictionary,
            'language': self.language,
            'target_sample_rate': self.target_sample_rate,
            'model_status': self.get_model_status()
        }
