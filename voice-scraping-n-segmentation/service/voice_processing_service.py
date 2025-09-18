"""
Voice Processing Service

This module provides the main voice processing pipeline that orchestrates
VAD, transcription, MFA, and CSV export functionality.
"""

import os
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

from service.s3_service import S3Service
from service.vad_service import VADService
from service.transcription_service import TranscriptionService
from service.mfa_service import MFAService
from service.enhanced_transcription_service import EnhancedTranscriptionService
# WhisperX and SimpleWhisper temporarily disabled due to package conflicts
# from service.whisperx_service import WhisperXService
# from service.simple_whisper_service import SimpleWhisperService
from service.csv_service import CSVService


class VoiceProcessingService:
    """
    Main service class for voice processing pipeline.
    Orchestrates VAD, transcription, MFA, and CSV export.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Voice Processing Service.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize services
        self.s3_service = S3Service(config)
        self.vad_service = VADService(config)
        # Enhanced Transcription Service (with Google STT) replaces traditional transcription
        self.enhanced_transcription_service = EnhancedTranscriptionService(config) 
        self.mfa_service = MFAService(config)
        self.csv_service = CSVService(config)
        
        # Processing settings  
        self.use_mfa = config.get('use_mfa', True)
        self.use_google_stt = config.get('use_google_stt', True)  # Google STT is primary transcription method
        self.save_chunks = config.get('save_audio_chunks', True) 
        self.cleanup_temp_files = config.get('cleanup_temp_files', True)
        
        # Output directories
        self.temp_dir = config.get('temp_dir', 'data/temp')
        self.chunks_dir = os.path.join(config.get('result_dir', 'result'), 'chunks')
        
        # Create directories
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)
        Path(self.chunks_dir).mkdir(parents=True, exist_ok=True)
        
        self.logger.info("Voice Processing Service initialized for Khmer language processing")
        self.logger.info("Khmer-specific optimizations:")
        self.logger.info(f"  - VAD aggressiveness: {self.vad_service.vad_aggressiveness}")
        self.logger.info(f"  - Chunk duration: {self.vad_service.min_chunk_duration}s - {self.vad_service.max_chunk_duration}s")
        self.logger.info(f"  - Primary transcription: Google Speech-to-Text (Khmer)")
        self.logger.info(f"  - CSV encoding: UTF-8 for Khmer Unicode support")
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get status of all services.
        
        Returns:
            Dictionary containing service status information
        """
        return {
            's3_service': self.s3_service.is_available(),
            'vad_service': True,  # VAD service is always available if webrtcvad is installed
            'enhanced_transcription_service': self.enhanced_transcription_service.is_available(),
            'google_stt_enabled': self.use_google_stt,
            'mfa_service': self.mfa_service.is_available(),
            'csv_service': True,  # CSV service is always available
            'use_mfa': self.use_mfa,
            'use_google_stt': self.use_google_stt,
            'save_chunks': self.save_chunks
        }
    
    def process_s3_file(
        self,
        s3_key: str,
        processing_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process an audio file from S3.
        
        Args:
            s3_key: S3 object key
            processing_config: Optional processing configuration
            
        Returns:
            Dictionary containing processing results
        """
        try:
            # Download file from S3
            self.logger.info(f"Processing S3 file: {s3_key}")
            
            # Create temporary file path
            temp_filename = f"temp_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            temp_file_path = os.path.join(self.temp_dir, temp_filename)
            
            # Download from S3
            download_result = self.s3_service.download_file(s3_key, temp_file_path)
            
            if not download_result['success']:
                return {
                    'success': False,
                    'error': f"Failed to download from S3: {download_result['error']}"
                }
            
            # Process the downloaded file
            result = self.process_local_file(
                temp_file_path,
                source_info={'s3_key': s3_key, 'type': 's3'},
                processing_config=processing_config
            )
            
            # Clean up temporary file
            if self.cleanup_temp_files:
                try:
                    os.remove(temp_file_path)
                except Exception as e:
                    self.logger.warning(f"Failed to clean up temp file {temp_file_path}: {e}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to process S3 file {s3_key}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_local_file(
        self,
        file_path: str,
        source_info: Optional[Dict[str, Any]] = None,
        processing_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a local audio file.
        
        Args:
            file_path: Path to the local audio file
            source_info: Optional information about the source
            processing_config: Optional processing configuration
            
        Returns:
            Dictionary containing processing results
        """
        processing_start = datetime.now()
        
        try:
            self.logger.info(f"Starting voice processing pipeline for: {file_path}")
            
            # Create session record
            session_id = self.csv_service.create_session_record(
                source_file=file_path,
                s3_key=source_info.get('s3_key') if source_info else None,
                processing_config=processing_config
            )
            
            # Step 1: Voice Activity Detection and Chunking
            self.logger.info("Step 1: Running Voice Activity Detection...")
            vad_result = self.vad_service.process_audio_file(file_path)
            
            if not vad_result['success']:
                return {
                    'success': False,
                    'error': f"VAD failed: {vad_result['error']}",
                    'session_id': session_id
                }
            
            chunks = vad_result['data']['chunks']
            self.logger.info(f"VAD completed: {len(chunks)} chunks detected")
            
            # Step 2: Save audio chunks (optional)
            saved_chunks = []
            if self.save_chunks:
                self.logger.info("Step 2: Saving audio chunks...")
                try:
                    base_filename = Path(file_path).stem
                    saved_chunks = self.vad_service.save_chunks(
                        chunks, self.chunks_dir, base_filename
                    )
                    self.logger.info(f"Saved {len(saved_chunks)} audio chunks")
                except Exception as e:
                    self.logger.warning(f"Failed to save chunks: {e}")

            # Upload saved chunks to S3 if requested
            try:
                upload_chunks_flag = False
                if isinstance(processing_config, dict):
                    upload_chunks_flag = bool(processing_config.get('upload_chunks_to_s3', False))
                # Respect global auto-upload setting
                if self.config.get('s3_auto_upload', False):
                    upload_chunks_flag = True

                if upload_chunks_flag and saved_chunks:
                    self.logger.info("Uploading saved chunks to S3...")
                    for sc in saved_chunks:
                        local_path = sc.get('file_path')
                        if local_path and os.path.exists(local_path):
                            # Generate s3 key under prefix with session id and chunk filename
                            chunk_filename = Path(local_path).name
                            s3_key = f"{self.config.get('s3_prefix','audio-extractions')}/{chunk_filename}"
                            upload_res = self.s3_service.upload_file(local_path, s3_key)
                            if upload_res.get('success'):
                                sc['s3_key'] = upload_res['data']['s3_key']
                                sc['s3_url'] = upload_res['data']['s3_url']
                            else:
                                self.logger.warning(f"Failed to upload chunk {local_path} to S3: {upload_res.get('error')}")
                    self.logger.info("Finished uploading chunks to S3")
            except Exception as e:
                self.logger.warning(f"Uploading chunks to S3 failed: {e}")
            
            # Step 3: Enhanced Transcription (Google STT + word timestamps)
            self.logger.info("Step 3: Running enhanced transcription with Google STT...")
            # Enhanced transcription handles both transcription and word-level alignment
            transcriptions = []
            alignments = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = str(chunk.get('chunk_id', i))
                try:
                    # Save chunk audio to temporary file for enhanced transcription
                    import tempfile
                    import soundfile as sf
                    
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                        sf.write(
                            temp_audio.name, 
                            chunk['audio_data'], 
                            chunk['sample_rate']
                        )
                        temp_audio_path = temp_audio.name
                    
                    # Run Enhanced Transcription (includes Google STT + alignment)
                    result = self.enhanced_transcription_service.align_audio_chunk(
                        audio_path=temp_audio_path,
                        output_dir=self.temp_dir,
                        chunk_id=chunk_id,
                        processing_config=processing_config
                    )
                    
                    # Clean up temporary audio file
                    if self.cleanup_temp_files:
                        os.unlink(temp_audio_path)
                    
                    # Add transcription result
                    if result.get('success'):
                        # Enhanced transcription service returns 'transcription' field with the API response
                        transcription_result = result.get('transcription', {})
                        transcription_data = transcription_result.get('data', {}) if transcription_result.get('success') else {}
                        transcriptions.append({
                            'success': True,
                            'chunk_id': chunk_id,
                            'data': {
                                'text': transcription_data.get('text', ''),
                                'language': 'km',  # Khmer
                                'confidence': transcription_data.get('confidence', 0.0),
                                'words': result.get('words', [])
                            }
                        })
                        
                        # Also add to alignments since enhanced transcription includes word timestamps
                        alignments.append({
                            'success': True,
                            'chunk_id': chunk_id,
                            'words': result.get('words', []),
                            'transcription': result.get('transcription', {}),
                            'output_file': result.get('output_file', ''),
                            'method': 'enhanced_transcription_google_stt'
                        })
                    else:
                        transcriptions.append({
                            'success': False,
                            'chunk_id': chunk_id,
                            'error': result.get('error', 'Enhanced transcription failed'),
                            'data': {'text': '', 'words': []}
                        })
                        alignments.append({
                            'success': False,
                            'chunk_id': chunk_id,
                            'error': result.get('error', 'Enhanced transcription failed'),
                            'method': 'enhanced_transcription_google_stt'
                        })
                        
                except Exception as e:
                    self.logger.error(f"Enhanced transcription failed for chunk {chunk_id}: {e}")
                    transcriptions.append({
                        'success': False,
                        'chunk_id': chunk_id,
                        'error': str(e),
                        'data': {'text': '', 'words': []}
                    })
                    alignments.append({
                        'success': False,
                        'chunk_id': chunk_id,
                        'error': str(e),
                        'method': 'enhanced_transcription_google_stt'
                    })
                    
                    # Clean up temp file if it exists
                    try:
                        if 'temp_audio_path' in locals():
                            os.unlink(temp_audio_path)
                    except:
                        pass
            
            successful_transcriptions = [t for t in transcriptions if t.get('success')]
            self.logger.info(f"Enhanced transcription with Google STT completed: {len(successful_transcriptions)}/{len(transcriptions)} successful")
            
            # Step 4: Additional MFA alignment (optional, since Google STT already provides word timestamps)
            successful_alignments = [a for a in alignments if a.get('success')]
            self.logger.info(f"Word-level alignment completed: {len(successful_alignments)}/{len(alignments)} successful (via Google STT)")
            
            # Optional: Additional MFA refinement if enabled
            if self.use_mfa and self.mfa_service.is_available() and len(successful_transcriptions) > 0:
                self.logger.info("Step 4b: Running additional MFA refinement...")
                try:
                    # MFA can refine the Google STT word timestamps
                    mfa_alignments = self._run_mfa_alignment(chunks, transcriptions)
                    # Merge MFA results with existing alignments if better
                    for i, mfa_result in enumerate(mfa_alignments):
                        if mfa_result.get('success') and i < len(alignments):
                            alignments[i]['mfa_refined'] = True
                            alignments[i]['mfa_words'] = mfa_result.get('words', [])
                    
                    mfa_successful = [a for a in mfa_alignments if a.get('success')]
                    self.logger.info(f"MFA refinement completed: {len(mfa_successful)}/{len(mfa_alignments)} successful")
                except Exception as e:
                    self.logger.warning(f"MFA refinement failed: {e}")
            else:
                self.logger.info("Step 4b: Skipping MFA refinement (Google STT word timestamps are sufficient)")
            
            # Step 5: CSV Export
            self.logger.info("Step 5: Exporting metadata to CSV...")
            
            # Enhance chunk data with file paths
            enhanced_chunks = []
            for i, chunk in enumerate(chunks):
                enhanced_chunk = chunk.copy()
                enhanced_chunk['source_file'] = file_path
                enhanced_chunk['s3_key'] = source_info.get('s3_key', '') if source_info else ''
                
                if i < len(saved_chunks):
                    enhanced_chunk['file_path'] = saved_chunks[i]['file_path']
                
                enhanced_chunks.append(enhanced_chunk)
            
            # Save metadata
            csv_success = self.csv_service.save_chunk_metadata(
                session_id, enhanced_chunks, transcriptions, alignments
            )
            
            if not csv_success:
                self.logger.warning("Failed to save CSV metadata")
            
            # Finalize session record
            processing_end = datetime.now()
            total_duration = sum(chunk.get('duration', 0) for chunk in chunks)
            
            self.csv_service.finalize_session_record(
                session_id, len(chunks), total_duration, processing_start
            )

            # Upload CSVs to S3 if requested
            try:
                upload_csv_flag = False
                if isinstance(processing_config, dict):
                    upload_csv_flag = bool(processing_config.get('upload_csv_to_s3', False))
                if self.config.get('s3_auto_upload', False):
                    upload_csv_flag = True

                if upload_csv_flag:
                    csv_dir = self.csv_service.output_dir
                    for fname in ['chunks.csv', 'words.csv', 'sessions.csv']:
                        fpath = os.path.join(csv_dir, fname)
                        if os.path.exists(fpath):
                            s3_key = f"{self.config.get('s3_prefix','audio-extractions')}/{fname}"
                            self.s3_service.upload_file(fpath, s3_key)
            except Exception as e:
                self.logger.warning(f"Failed to upload CSVs to S3: {e}")
            
            # Prepare result summary
            result = {
                'success': True,
                'session_id': session_id,
                'processing_duration': (processing_end - processing_start).total_seconds(),
                'data': {
                    'total_chunks': len(chunks),
                    'total_duration': total_duration,
                    'speech_ratio': vad_result['data'].get('speech_ratio', 0),
                    'successful_transcriptions': len(successful_transcriptions),
                    'failed_transcriptions': len(transcriptions) - len(successful_transcriptions),
                    'mfa_alignments': len([a for a in alignments if a.get('success')]),
                    'saved_chunks': len(saved_chunks),
                    'csv_exported': csv_success,
                    'chunks_summary': self._create_chunks_summary(enhanced_chunks, transcriptions, alignments),
                    'processing_steps': {
                        'vad': vad_result['success'],
                        'transcription': len(successful_transcriptions) > 0,
                        'mfa': len(alignments) > 0,
                        'csv_export': csv_success
                    }
                }
            }
            
            self.logger.info(f"Voice processing completed successfully for session {session_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Voice processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'session_id': locals().get('session_id')
            }
    
    def _run_mfa_alignment(
        self,
        chunks: List[Dict[str, Any]],
        transcriptions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Run MFA alignment on chunks with transcriptions.
        
        Args:
            chunks: List of audio chunks
            transcriptions: List of transcription results
            
        Returns:
            List of MFA alignment results
        """
        alignments = []
        
        for i, chunk in enumerate(chunks):
            if i >= len(transcriptions):
                alignments.append({
                    'success': False,
                    'error': 'No transcription available',
                    'chunk_id': str(chunk.get('chunk_id', i))
                })
                continue
            
            transcription = transcriptions[i]
            if not transcription.get('success'):
                alignments.append({
                    'success': False,
                    'error': 'Transcription failed',
                    'chunk_id': str(chunk.get('chunk_id', i))
                })
                continue
            
            transcription_data = transcription['data']
            transcript_text = transcription_data.get('text', '').strip()
            
            if not transcript_text:
                alignments.append({
                    'success': False,
                    'error': 'Empty transcript',
                    'chunk_id': str(chunk.get('chunk_id', i))
                })
                continue
            
            # Run MFA alignment
            alignment_result = self.mfa_service.align_chunk(
                audio_data=chunk['audio_data'],
                sample_rate=chunk['sample_rate'],
                transcript=transcript_text,
                chunk_id=str(chunk.get('chunk_id', i))
            )
            
            alignments.append(alignment_result)
        
        return alignments
    
    def _run_whisperx_alignment(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Run WhisperX alignment on chunks (combines transcription + alignment).
        
        Args:
            chunks: List of audio chunks
            
        Returns:
            List of WhisperX alignment results
        """
        alignments = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = str(chunk.get('chunk_id', i))
            
            try:
                # Save chunk audio to temporary file for WhisperX
                import tempfile
                import soundfile as sf
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                    sf.write(
                        temp_audio.name, 
                        chunk['audio_data'], 
                        chunk['sample_rate']
                    )
                    temp_audio_path = temp_audio.name
                
                # Create temporary output directory
                temp_output_dir = os.path.join(self.temp_dir, f'whisperx_output_{chunk_id}')
                os.makedirs(temp_output_dir, exist_ok=True)
                
                # Run WhisperX alignment
                result = self.whisperx_service.align_audio_chunk(
                    audio_path=temp_audio_path,
                    output_dir=temp_output_dir,
                    chunk_id=chunk_id
                )
                
                # Clean up temporary audio file
                if self.cleanup_temp_files:
                    os.unlink(temp_audio_path)
                
                if result.get('words'):
                    alignments.append({
                        'success': True,
                        'chunk_id': chunk_id,
                        'words': result['words'],
                        'transcription': result.get('transcription', {}),
                        'output_file': result.get('output_file', ''),
                        'method': 'whisperx'
                    })
                else:
                    alignments.append({
                        'success': False,
                        'error': 'No words found in WhisperX result',
                        'chunk_id': chunk_id,
                        'method': 'whisperx'
                    })
                
            except Exception as e:
                self.logger.error(f"WhisperX alignment failed for chunk {chunk_id}: {e}")
                alignments.append({
                    'success': False,
                    'error': str(e),
                    'chunk_id': chunk_id,
                    'method': 'whisperx'
                })
                
                # Clean up temp file if it exists
                try:
                    if 'temp_audio_path' in locals():
                        os.unlink(temp_audio_path)
                except:
                    pass
        
        return alignments
    
    def _run_simple_whisper_alignment(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Run Simple Whisper transcription on chunks (fallback for WhisperX).
        
        Args:
            chunks: List of audio chunks
            
        Returns:
            List of Simple Whisper transcription results
        """
        alignments = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = str(chunk.get('chunk_id', i))
            
            try:
                # Save chunk audio to temporary file
                import tempfile
                import soundfile as sf
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                    sf.write(
                        temp_audio.name, 
                        chunk['audio_data'], 
                        chunk['sample_rate']
                    )
                    temp_audio_path = temp_audio.name
                
                # Create temporary output directory
                temp_output_dir = os.path.join(self.temp_dir, f'simple_whisper_output_{chunk_id}')
                os.makedirs(temp_output_dir, exist_ok=True)
                
                # Run Simple Whisper transcription
                result = self.simple_whisper_service.align_audio_chunk(
                    audio_path=temp_audio_path,
                    output_dir=temp_output_dir,
                    chunk_id=chunk_id
                )
                
                # Clean up temporary audio file
                if self.cleanup_temp_files:
                    os.unlink(temp_audio_path)
                
                if result.get('success') and result.get('words'):
                    alignments.append({
                        'success': True,
                        'chunk_id': chunk_id,
                        'words': result['words'],
                        'transcription': result.get('transcription', {}),
                        'output_file': result.get('output_file', ''),
                        'method': 'simple_whisper'
                    })
                else:
                    alignments.append({
                        'success': False,
                        'error': result.get('error', 'No words found in transcription'),
                        'chunk_id': chunk_id,
                        'method': 'simple_whisper'
                    })
                
            except Exception as e:
                self.logger.error(f"Simple Whisper transcription failed for chunk {chunk_id}: {e}")
                alignments.append({
                    'success': False,
                    'error': str(e),
                    'chunk_id': chunk_id,
                    'method': 'simple_whisper'
                })
                
                # Clean up temp file if it exists
                try:
                    if 'temp_audio_path' in locals():
                        os.unlink(temp_audio_path)
                except:
                    pass
        
        return alignments
    
    def _run_enhanced_transcription_alignment(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Run Enhanced Transcription service on chunks (best fallback option).
        
        Args:
            chunks: List of audio chunks
            
        Returns:
            List of Enhanced Transcription results with word timestamps
        """
        alignments = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = str(chunk.get('chunk_id', i))
            
            try:
                # Save chunk audio to temporary file
                import tempfile
                import soundfile as sf
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                    sf.write(
                        temp_audio.name, 
                        chunk['audio_data'], 
                        chunk['sample_rate']
                    )
                    temp_audio_path = temp_audio.name
                
                # Create temporary output directory
                temp_output_dir = os.path.join(self.temp_dir, f'enhanced_transcription_output_{chunk_id}')
                os.makedirs(temp_output_dir, exist_ok=True)
                
                # Run Enhanced Transcription
                result = self.enhanced_transcription_service.align_audio_chunk(
                    audio_path=temp_audio_path,
                    output_dir=temp_output_dir,
                    chunk_id=chunk_id
                )
                
                # Clean up temporary audio file
                if self.cleanup_temp_files:
                    os.unlink(temp_audio_path)
                
                if result.get('success') and result.get('words'):
                    alignments.append({
                        'success': True,
                        'chunk_id': chunk_id,
                        'words': result['words'],
                        'transcription': result.get('transcription', {}),
                        'output_file': result.get('output_file', ''),
                        'method': 'enhanced_transcription'
                    })
                else:
                    alignments.append({
                        'success': False,
                        'error': result.get('error', 'No words found in transcription'),
                        'chunk_id': chunk_id,
                        'method': 'enhanced_transcription'
                    })
                
            except Exception as e:
                self.logger.error(f"Enhanced Transcription failed for chunk {chunk_id}: {e}")
                alignments.append({
                    'success': False,
                    'error': str(e),
                    'chunk_id': chunk_id,
                    'method': 'enhanced_transcription'
                })
                
                # Clean up temp file if it exists
                try:
                    if 'temp_audio_path' in locals():
                        os.unlink(temp_audio_path)
                except:
                    pass
        
        return alignments
    
    def _create_chunks_summary(
        self,
        chunks: List[Dict[str, Any]],
        transcriptions: List[Dict[str, Any]],
        alignments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create a summary of chunks with their processing results.
        
        Args:
            chunks: List of chunk data
            transcriptions: List of transcription results
            alignments: List of alignment results
            
        Returns:
            List of chunk summaries
        """
        summaries = []
        
        for i, chunk in enumerate(chunks):
            summary = {
                'chunk_id': str(chunk.get('chunk_id', i)),
                'start_time': chunk.get('start_time', 0),
                'end_time': chunk.get('end_time', 0),
                'duration': chunk.get('duration', 0),
                'transcription_success': False,
                'transcription_text': '',
                'word_count': 0,
                'mfa_success': False,
                'mfa_words': 0
            }
            
            # Add transcription info
            if i < len(transcriptions) and transcriptions[i].get('success'):
                trans_data = transcriptions[i]['data']
                summary.update({
                    'transcription_success': True,
                    'transcription_text': trans_data.get('text', ''),
                    'word_count': len(trans_data.get('words', [])),
                    'language': trans_data.get('language', ''),
                    'confidence': 1.0 - trans_data.get('no_speech_prob', 0)
                })
            
            # Add MFA info
            if i < len(alignments) and alignments[i].get('success'):
                alignment = alignments[i]
                summary.update({
                    'mfa_success': True,
                    'mfa_words': len(alignment.get('words', []))
                })
            
            summaries.append(summary)
        
        return summaries
    
    async def process_s3_file_async(
        self,
        s3_key: str,
        processing_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Asynchronously process an audio file from S3.
        
        Args:
            s3_key: S3 object key
            processing_config: Optional processing configuration
            
        Returns:
            Dictionary containing processing results
        """
        loop = asyncio.get_event_loop()
        
        # Run the synchronous processing in a thread pool
        result = await loop.run_in_executor(
            None,
            self.process_s3_file,
            s3_key,
            processing_config
        )
        
        return result
    
    def list_processing_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List recent processing sessions.
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of session data
        """
        try:
            sessions_file = os.path.join(self.csv_service.output_dir, 'sessions.csv')
            
            if not os.path.exists(sessions_file):
                return []
            
            import pandas as pd
            df = pd.read_csv(sessions_file)
            
            # Sort by creation date and limit
            df = df.sort_values('created_at', ascending=False).head(limit)
            
            return df.to_dict('records')
            
        except Exception as e:
            self.logger.error(f"Failed to list sessions: {e}")
            return []
    
    def get_session_details(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a processing session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session details or None
        """
        try:
            session_data = self.csv_service.load_session_data(session_id)
            if not session_data:
                return None
            
            chunk_data = self.csv_service.load_chunk_data(session_id)
            
            return {
                'session': session_data,
                'chunks': chunk_data,
                'summary': {
                    'total_chunks': len(chunk_data),
                    'total_transcription_length': sum(len(chunk.get('transcription', '')) for chunk in chunk_data),
                    'average_chunk_duration': sum(chunk.get('duration', 0) for chunk in chunk_data) / len(chunk_data) if chunk_data else 0,
                    'languages_detected': list(set(chunk.get('language', '') for chunk in chunk_data if chunk.get('language')))
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get session details for {session_id}: {e}")
            return None
