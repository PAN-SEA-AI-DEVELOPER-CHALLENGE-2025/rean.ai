"""
MFA Training Service for TTS Datasets

This module provides functionality to train MFA acoustic models and dictionaries
using TTS (Text-to-Speech) datasets, specifically designed for Khmer language.
"""

import os
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from collections import defaultdict
import re


class MFATTSTrainingService:
    """
    Service for training MFA models using TTS datasets.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the MFA TTS Training Service.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Paths
        self.project_root = Path(config.get('project_root', '.'))
        self.mfa_models_dir = self.project_root / 'mfa_models'
        self.tts_dataset_dir = self.mfa_models_dir / 'km_kh_male'
        self.training_dir = self.mfa_models_dir / 'training'
        self.output_models_dir = self.mfa_models_dir / 'custom_models'
        
        # MFA settings
        self.mfa_command = config.get('mfa_command', 'mfa')
        self.target_sample_rate = 22050  # Standard for MFA
        
        # Create directories
        self.training_dir.mkdir(parents=True, exist_ok=True)
        self.output_models_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("MFA TTS Training Service initialized")
    
    def prepare_tts_dataset_for_mfa(self) -> Dict[str, Any]:
        """
        Prepare TTS dataset for MFA training by creating proper directory structure.
        
        Returns:
            Dictionary with preparation results
        """
        try:
            self.logger.info("Preparing TTS dataset for MFA training...")
            
            # Check if TTS dataset exists
            line_index_file = self.tts_dataset_dir / 'line_index.tsv'
            wavs_dir = self.tts_dataset_dir / 'wavs'
            
            if not line_index_file.exists() or not wavs_dir.exists():
                return {
                    'success': False,
                    'error': 'TTS dataset not found. Expected line_index.tsv and wavs/ directory.'
                }
            
            # Read the line index
            transcriptions = self._read_line_index(line_index_file)
            
            # Create MFA training structure
            mfa_corpus_dir = self.training_dir / 'corpus'
            mfa_corpus_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy and organize files
            processed_files = 0
            for audio_id, text in transcriptions.items():
                # Source audio file
                source_audio = wavs_dir / f"{audio_id}.wav"
                if not source_audio.exists():
                    self.logger.warning(f"Audio file not found: {source_audio}")
                    continue
                
                # Destination files
                dest_audio = mfa_corpus_dir / f"{audio_id}.wav"
                dest_text = mfa_corpus_dir / f"{audio_id}.txt"
                
                # Copy audio file
                shutil.copy2(source_audio, dest_audio)
                
                # Create text file
                with open(dest_text, 'w', encoding='utf-8') as f:
                    f.write(text.strip())
                
                processed_files += 1
            
            self.logger.info(f"Prepared {processed_files} files for MFA training")
            
            return {
                'success': True,
                'processed_files': processed_files,
                'corpus_dir': str(mfa_corpus_dir),
                'total_files': len(transcriptions)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to prepare TTS dataset: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_khmer_pronunciation_dictionary(self) -> Dict[str, Any]:
        """
        Generate a Khmer pronunciation dictionary from the TTS dataset.
        
        Returns:
            Dictionary with generation results
        """
        try:
            self.logger.info("Generating Khmer pronunciation dictionary...")
            
            # Read transcriptions
            line_index_file = self.tts_dataset_dir / 'line_index.tsv'
            transcriptions = self._read_line_index(line_index_file)
            
            # Extract unique words
            all_words = set()
            for text in transcriptions.values():
                # Clean and split text
                cleaned_text = self._clean_khmer_text(text)
                words = cleaned_text.split()
                all_words.update(words)
            
            # Generate phonetic representations
            # For now, we'll use a simplified mapping - this should be enhanced
            # with proper Khmer phonetic rules
            pronunciation_dict = {}
            for word in sorted(all_words):
                if word and len(word.strip()) > 0:
                    # Basic phonetic mapping for Khmer
                    phonemes = self._khmer_to_phonemes(word)
                    pronunciation_dict[word] = phonemes
            
            # Save dictionary
            dict_file = self.training_dir / 'khmer_lexicon.txt'
            with open(dict_file, 'w', encoding='utf-8') as f:
                for word, phonemes in sorted(pronunciation_dict.items()):
                    f.write(f"{word}\t{phonemes}\n")
            
            self.logger.info(f"Generated dictionary with {len(pronunciation_dict)} words")
            
            return {
                'success': True,
                'dictionary_file': str(dict_file),
                'word_count': len(pronunciation_dict),
                'sample_entries': dict(list(pronunciation_dict.items())[:10])
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate pronunciation dictionary: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def train_acoustic_model(self, dictionary_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Train MFA acoustic model using the prepared TTS dataset.
        
        Args:
            dictionary_path: Path to pronunciation dictionary
            
        Returns:
            Dictionary with training results
        """
        try:
            self.logger.info("Training MFA acoustic model...")
            
            # Paths
            corpus_dir = self.training_dir / 'corpus'
            if dictionary_path is None:
                dictionary_path = str(self.training_dir / 'khmer_lexicon.txt')
            
            output_model_path = self.output_models_dir / 'khmer_acoustic_model.zip'
            
            # MFA training command
            cmd = [
                self.mfa_command,
                'train',
                str(corpus_dir),
                dictionary_path,
                str(output_model_path),
                '--clean',
                '--num_jobs', '4',
                '--verbose'
            ]
            
            self.logger.info(f"Running MFA training: {' '.join(cmd)}")
            
            # Run training
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout
                env=self._get_mfa_env()
            )
            
            if result.returncode == 0:
                self.logger.info("MFA acoustic model training completed successfully")
                return {
                    'success': True,
                    'model_path': str(output_model_path),
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            else:
                self.logger.error(f"MFA training failed: {result.stderr}")
                return {
                    'success': False,
                    'error': result.stderr,
                    'stdout': result.stdout
                }
                
        except subprocess.TimeoutExpired:
            self.logger.error("MFA training timed out")
            return {
                'success': False,
                'error': 'Training timed out after 1 hour'
            }
        except Exception as e:
            self.logger.error(f"Failed to train acoustic model: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_tts_dataset(self) -> Dict[str, Any]:
        """
        Validate the TTS dataset for MFA training compatibility.
        
        Returns:
            Dictionary with validation results
        """
        try:
            self.logger.info("Validating TTS dataset...")
            
            validation_results = {
                'success': True,
                'issues': [],
                'statistics': {},
                'recommendations': []
            }
            
            # Check file structure
            line_index_file = self.tts_dataset_dir / 'line_index.tsv'
            wavs_dir = self.tts_dataset_dir / 'wavs'
            
            if not line_index_file.exists():
                validation_results['issues'].append("Missing line_index.tsv file")
                validation_results['success'] = False
            
            if not wavs_dir.exists():
                validation_results['issues'].append("Missing wavs/ directory")
                validation_results['success'] = False
            
            if not validation_results['success']:
                return validation_results
            
            # Read and validate transcriptions
            transcriptions = self._read_line_index(line_index_file)
            
            # Check audio files
            audio_files = list(wavs_dir.glob('*.wav'))
            missing_audio = []
            existing_pairs = 0
            
            for audio_id in transcriptions.keys():
                audio_file = wavs_dir / f"{audio_id}.wav"
                if audio_file.exists():
                    existing_pairs += 1
                else:
                    missing_audio.append(audio_id)
            
            # Statistics
            validation_results['statistics'] = {
                'total_transcriptions': len(transcriptions),
                'total_audio_files': len(audio_files),
                'valid_pairs': existing_pairs,
                'missing_audio_files': len(missing_audio),
                'orphaned_audio_files': len(audio_files) - existing_pairs
            }
            
            # Text analysis
            text_stats = self._analyze_transcription_texts(transcriptions)
            validation_results['statistics'].update(text_stats)
            
            # Issues and recommendations
            if missing_audio:
                validation_results['issues'].append(f"{len(missing_audio)} audio files missing")
                if len(missing_audio) <= 10:
                    validation_results['issues'].append(f"Missing: {missing_audio}")
            
            if existing_pairs < len(transcriptions) * 0.9:
                validation_results['recommendations'].append(
                    "Consider fixing missing audio files before training"
                )
            
            if text_stats['avg_text_length'] < 10:
                validation_results['recommendations'].append(
                    "Very short transcriptions may affect training quality"
                )
            
            if text_stats['unique_words'] < 1000:
                validation_results['recommendations'].append(
                    "Limited vocabulary may affect model generalization"
                )
            
            validation_results['success'] = len(validation_results['issues']) == 0
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Dataset validation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _read_line_index(self, file_path: Path) -> Dict[str, str]:
        """Read the line index TSV file."""
        transcriptions = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '\t' in line:
                    parts = line.split('\t', 1)
                    if len(parts) == 2:
                        audio_id, text = parts
                        transcriptions[audio_id.strip()] = text.strip()
        return transcriptions
    
    def _clean_khmer_text(self, text: str) -> str:
        """Clean Khmer text for processing."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove non-Khmer characters if needed (be careful with this)
        # For now, just clean whitespace
        return text
    
    def _khmer_to_phonemes(self, word: str) -> str:
        """
        Convert Khmer word to phonemes.
        This is a simplified version - should be enhanced with proper Khmer phonetic rules.
        """
        # This is a basic placeholder - real implementation would need:
        # 1. Proper Khmer Unicode analysis
        # 2. Khmer-specific phonetic rules
        # 3. Syllable structure understanding
        # 4. Tone handling
        
        # For now, use a character-level mapping as placeholder
        phoneme_map = {
            # Consonants (simplified)
            'ក': 'k', 'ខ': 'kh', 'គ': 'g', 'ឃ': 'gh',
            'ច': 'ch', 'ឆ': 'chh', 'ជ': 'j', 'ឈ': 'jh',
            'ដ': 'd', 'ឋ': 'th', 'ឌ': 'dh', 'ឍ': 'dhh',
            'ណ': 'n', 'ត': 't', 'ថ': 'th', 'ទ': 'd',
            'ធ': 'dh', 'ន': 'n', 'ប': 'b', 'ផ': 'ph',
            'ព': 'p', 'ភ': 'ph', 'ម': 'm', 'យ': 'y',
            'រ': 'r', 'ល': 'l', 'វ': 'v', 'ស': 's',
            'ហ': 'h', 'អ': '?', 'ឡ': 'l',
            
            # Vowels (simplified)
            'ា': 'aa', 'ិ': 'i', 'ី': 'ii', 'ុ': 'u', 'ូ': 'uu',
            'េ': 'ee', 'ែ': 'ae', 'ៃ': 'ai', 'ោ': 'oo', 'ៅ': 'au',
            'ើ': 'eu', 'ឿ': 'uea', 'ៀ': 'ia',
        }
        
        phonemes = []
        for char in word:
            if char in phoneme_map:
                phonemes.append(phoneme_map[char])
            elif char == ' ':
                break  # End of word
            # Skip unknown characters for now
        
        return ' '.join(phonemes) if phonemes else 'unk'
    
    def _analyze_transcription_texts(self, transcriptions: Dict[str, str]) -> Dict[str, Any]:
        """Analyze transcription texts for statistics."""
        all_words = []
        text_lengths = []
        
        for text in transcriptions.values():
            words = self._clean_khmer_text(text).split()
            all_words.extend(words)
            text_lengths.append(len(text))
        
        return {
            'total_words': len(all_words),
            'unique_words': len(set(all_words)),
            'avg_words_per_utterance': len(all_words) / len(transcriptions) if transcriptions else 0,
            'avg_text_length': sum(text_lengths) / len(text_lengths) if text_lengths else 0,
            'max_text_length': max(text_lengths) if text_lengths else 0,
            'min_text_length': min(text_lengths) if text_lengths else 0
        }
    
    def _get_mfa_env(self) -> Dict[str, str]:
        """Get environment variables for MFA commands."""
        env = os.environ.copy()
        mfa_bin_dir = Path(self.mfa_command).parent
        if str(mfa_bin_dir) not in env.get('PATH', ''):
            env['PATH'] = str(mfa_bin_dir) + os.pathsep + env.get('PATH', '')
        return env
    
    def get_training_status(self) -> Dict[str, Any]:
        """Get status of training data and models."""
        status = {
            'dataset_prepared': False,
            'dictionary_generated': False,
            'acoustic_model_trained': False,
            'files': {}
        }
        
        # Check prepared corpus
        corpus_dir = self.training_dir / 'corpus'
        if corpus_dir.exists():
            audio_files = list(corpus_dir.glob('*.wav'))
            text_files = list(corpus_dir.glob('*.txt'))
            status['dataset_prepared'] = len(audio_files) > 0 and len(text_files) > 0
            status['files']['corpus_audio_files'] = len(audio_files)
            status['files']['corpus_text_files'] = len(text_files)
        
        # Check dictionary
        dict_file = self.training_dir / 'khmer_lexicon.txt'
        if dict_file.exists():
            status['dictionary_generated'] = True
            status['files']['dictionary_path'] = str(dict_file)
        
        # Check acoustic model
        model_file = self.output_models_dir / 'khmer_acoustic_model.zip'
        if model_file.exists():
            status['acoustic_model_trained'] = True
            status['files']['acoustic_model_path'] = str(model_file)
        
        return status
