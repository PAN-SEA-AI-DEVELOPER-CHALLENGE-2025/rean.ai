"""
Voice Activity Detection Service

This module provides WebRTC VAD-based voice activity detection and chunking functionality.
It processes audio files to detect speech segments and creates chunks of 0-5 seconds each.
"""

import os
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import numpy as np
import webrtcvad
import librosa
import soundfile as sf
from collections import deque


class VADService:
    """
    Service class for Voice Activity Detection using WebRTC VAD.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the VAD Service.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # VAD configuration optimized for Khmer speech
        self.vad_aggressiveness = config.get('vad_aggressiveness', 2)  # Slightly less aggressive for tonal languages
        self.frame_duration_ms = config.get('vad_frame_duration_ms', 30)  # 10, 20, or 30 ms
        self.sample_rate = config.get('vad_sample_rate', 16000)  # WebRTC VAD works best at 16kHz
        
        # Chunk configuration optimized for Khmer
        self.min_chunk_duration = config.get('min_chunk_duration', 1.5)  # Slightly longer for Khmer sentences
        self.max_chunk_duration = config.get('max_chunk_duration', 5.0)  # maximum 5 seconds
        self.chunk_padding = config.get('chunk_padding', 0.15)  # 150ms padding for Khmer speech patterns
        
        # Speech detection thresholds
        self.speech_threshold = config.get('speech_threshold', 0.5)  # minimum ratio of speech frames
        self.min_speech_frames = config.get('min_speech_frames', 5)  # minimum consecutive speech frames
        
        # Initialize VAD
        self.vad = webrtcvad.Vad(self.vad_aggressiveness)
        
        self.logger.info(f"VAD Service initialized with aggressiveness={self.vad_aggressiveness}")
    
    def _resample_audio(self, audio_data: np.ndarray, original_sr: int) -> np.ndarray:
        """
        Resample audio to 16kHz for WebRTC VAD.
        
        Args:
            audio_data: Audio data array
            original_sr: Original sample rate
            
        Returns:
            Resampled audio data
        """
        if original_sr != self.sample_rate:
            audio_data = librosa.resample(audio_data, orig_sr=original_sr, target_sr=self.sample_rate)
        return audio_data
    
    def _audio_to_frames(self, audio_data: np.ndarray) -> List[bytes]:
        """
        Convert audio data to frames for VAD processing.
        
        Args:
            audio_data: Audio data array (16kHz, mono)
            
        Returns:
            List of audio frames as bytes
        """
        # Calculate frame size in samples
        frame_size = int(self.sample_rate * self.frame_duration_ms / 1000)
        
        # Convert to 16-bit PCM
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        frames = []
        for i in range(0, len(audio_int16) - frame_size + 1, frame_size):
            frame = audio_int16[i:i + frame_size]
            frames.append(frame.tobytes())
        
        return frames
    
    def _detect_speech_frames(self, frames: List[bytes]) -> List[bool]:
        """
        Detect speech in audio frames using WebRTC VAD.
        
        Args:
            frames: List of audio frames
            
        Returns:
            List of boolean values indicating speech presence
        """
        speech_frames = []
        
        for frame in frames:
            try:
                is_speech = self.vad.is_speech(frame, self.sample_rate)
                speech_frames.append(is_speech)
            except Exception as e:
                # If VAD fails on a frame, assume it's not speech
                self.logger.warning(f"VAD failed on frame: {e}")
                speech_frames.append(False)
        
        return speech_frames
    
    def _find_speech_segments(self, speech_frames: List[bool]) -> List[Tuple[int, int]]:
        """
        Find continuous speech segments from frame-level speech detection.
        
        Args:
            speech_frames: Boolean array indicating speech frames
            
        Returns:
            List of (start_frame, end_frame) tuples
        """
        segments = []
        start_frame = None
        speech_count = 0
        
        for i, is_speech in enumerate(speech_frames):
            if is_speech:
                if start_frame is None:
                    start_frame = i
                speech_count += 1
            else:
                if start_frame is not None:
                    # Check if we have enough speech frames
                    if speech_count >= self.min_speech_frames:
                        segments.append((start_frame, i - 1))
                    start_frame = None
                    speech_count = 0
        
        # Handle segment that ends at the last frame
        if start_frame is not None and speech_count >= self.min_speech_frames:
            segments.append((start_frame, len(speech_frames) - 1))
        
        return segments
    
    def _merge_close_segments(self, segments: List[Tuple[int, int]], max_gap_frames: int) -> List[Tuple[int, int]]:
        """
        Merge speech segments that are close together.
        
        Args:
            segments: List of (start_frame, end_frame) tuples
            max_gap_frames: Maximum gap between segments to merge
            
        Returns:
            List of merged segments
        """
        if not segments:
            return segments
        
        merged = [segments[0]]
        
        for start, end in segments[1:]:
            last_start, last_end = merged[-1]
            
            # If gap is small, merge segments
            if start - last_end <= max_gap_frames:
                merged[-1] = (last_start, end)
            else:
                merged.append((start, end))
        
        return merged
    
    def _create_chunks_from_segments(
        self, 
        segments: List[Tuple[int, int]], 
        audio_data: np.ndarray
    ) -> List[Dict[str, Any]]:
        """
        Create audio chunks from speech segments.
        
        Args:
            segments: List of (start_frame, end_frame) tuples
            audio_data: Original audio data
            
        Returns:
            List of chunk information dictionaries
        """
        chunks = []
        frame_size = int(self.sample_rate * self.frame_duration_ms / 1000)
        padding_samples = int(self.chunk_padding * self.sample_rate)
        
        for i, (start_frame, end_frame) in enumerate(segments):
            # Convert frame indices to sample indices
            start_sample = start_frame * frame_size
            end_sample = (end_frame + 1) * frame_size
            
            # Add padding
            padded_start = max(0, start_sample - padding_samples)
            padded_end = min(len(audio_data), end_sample + padding_samples)
            
            # Extract chunk
            chunk_audio = audio_data[padded_start:padded_end]
            
            # Calculate timing information
            start_time = padded_start / self.sample_rate
            end_time = padded_end / self.sample_rate
            duration = end_time - start_time
            
            # Skip chunks that are too short or too long
            if duration < self.min_chunk_duration or duration > self.max_chunk_duration:
                if duration > self.max_chunk_duration:
                    # Split long chunks
                    sub_chunks = self._split_long_chunk(chunk_audio, start_time, i)
                    chunks.extend(sub_chunks)
                continue
            
            chunk_info = {
                'chunk_id': str(i),
                'audio_data': chunk_audio,
                'start_time': start_time,
                'end_time': end_time,
                'duration': duration,
                'sample_rate': self.sample_rate,
                'start_frame': start_frame,
                'end_frame': end_frame
            }
            
            chunks.append(chunk_info)
        
        return chunks
    
    def _split_long_chunk(self, chunk_audio: np.ndarray, start_time: float, base_id: int) -> List[Dict[str, Any]]:
        """
        Split a long audio chunk into smaller chunks.
        
        Args:
            chunk_audio: Audio data for the long chunk
            start_time: Start time of the original chunk
            base_id: Base ID for sub-chunks
            
        Returns:
            List of sub-chunk information dictionaries
        """
        sub_chunks = []
        chunk_duration = len(chunk_audio) / self.sample_rate
        num_sub_chunks = int(np.ceil(chunk_duration / self.max_chunk_duration))
        
        for i in range(num_sub_chunks):
            sub_start_sample = int(i * self.max_chunk_duration * self.sample_rate)
            sub_end_sample = int(min((i + 1) * self.max_chunk_duration * self.sample_rate, len(chunk_audio)))
            
            sub_chunk_audio = chunk_audio[sub_start_sample:sub_end_sample]
            sub_start_time = start_time + (sub_start_sample / self.sample_rate)
            sub_end_time = start_time + (sub_end_sample / self.sample_rate)
            sub_duration = sub_end_time - sub_start_time
            
            # Skip very short sub-chunks
            if sub_duration < self.min_chunk_duration:
                continue
            
            sub_chunk_info = {
                'chunk_id': f"{base_id}_{i}",
                'audio_data': sub_chunk_audio,
                'start_time': sub_start_time,
                'end_time': sub_end_time,
                'duration': sub_duration,
                'sample_rate': self.sample_rate,
                'is_sub_chunk': True,
                'parent_chunk_id': base_id
            }
            
            sub_chunks.append(sub_chunk_info)
        
        return sub_chunks
    
    def process_audio_file(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Process an audio file to detect speech and create chunks.
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Dictionary containing processing results
        """
        try:
            # Load audio file
            self.logger.info(f"Processing audio file: {audio_file_path}")
            audio_data, original_sr = librosa.load(audio_file_path, sr=None)
            
            # Resample to 16kHz for VAD
            audio_16k = self._resample_audio(audio_data, original_sr)
            
            # Convert to frames
            frames = self._audio_to_frames(audio_16k)
            
            if not frames:
                return {
                    'success': False,
                    'error': 'No audio frames could be extracted'
                }
            
            # Detect speech frames
            speech_frames = self._detect_speech_frames(frames)
            
            # Calculate speech statistics
            total_frames = len(speech_frames)
            speech_frame_count = sum(speech_frames)
            speech_ratio = speech_frame_count / total_frames if total_frames > 0 else 0
            
            self.logger.info(f"Speech detection: {speech_frame_count}/{total_frames} frames ({speech_ratio:.2%})")
            
            if speech_ratio < self.speech_threshold:
                self.logger.warning(f"Low speech content detected: {speech_ratio:.2%}")
            
            # Find speech segments
            segments = self._find_speech_segments(speech_frames)
            
            # Merge close segments (within 0.5 seconds)
            max_gap_frames = int(0.5 * 1000 / self.frame_duration_ms)
            merged_segments = self._merge_close_segments(segments, max_gap_frames)
            
            # Create chunks from segments
            chunks = self._create_chunks_from_segments(merged_segments, audio_16k)
            
            self.logger.info(f"Created {len(chunks)} audio chunks from {len(merged_segments)} speech segments")
            
            return {
                'success': True,
                'data': {
                    'chunks': chunks,
                    'total_chunks': len(chunks),
                    'speech_segments': len(merged_segments),
                    'speech_ratio': speech_ratio,
                    'total_duration': len(audio_data) / original_sr,
                    'speech_duration': sum(chunk['duration'] for chunk in chunks),
                    'original_sample_rate': original_sr,
                    'processing_sample_rate': self.sample_rate
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process audio file {audio_file_path}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def save_chunks(self, chunks: List[Dict[str, Any]], output_dir: str, base_filename: str) -> List[Dict[str, Any]]:
        """
        Save audio chunks to individual files.
        
        Args:
            chunks: List of chunk information dictionaries
            output_dir: Directory to save chunks
            base_filename: Base filename for chunk files
            
        Returns:
            List of saved chunk file information
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            saved_chunks = []
            
            for chunk in chunks:
                chunk_filename = f"{base_filename}_chunk_{chunk['chunk_id']}.wav"
                chunk_file_path = output_path / chunk_filename
                
                # Save chunk as WAV file
                sf.write(
                    str(chunk_file_path),
                    chunk['audio_data'],
                    chunk['sample_rate']
                )
                
                chunk_info = {
                    'chunk_id': chunk['chunk_id'],
                    'file_path': str(chunk_file_path),
                    'filename': chunk_filename,
                    'start_time': chunk['start_time'],
                    'end_time': chunk['end_time'],
                    'duration': chunk['duration'],
                    'sample_rate': chunk['sample_rate'],
                    'file_size': chunk_file_path.stat().st_size
                }
                
                saved_chunks.append(chunk_info)
            
            self.logger.info(f"Saved {len(saved_chunks)} chunks to {output_dir}")
            return saved_chunks
            
        except Exception as e:
            self.logger.error(f"Failed to save chunks: {e}")
            raise
