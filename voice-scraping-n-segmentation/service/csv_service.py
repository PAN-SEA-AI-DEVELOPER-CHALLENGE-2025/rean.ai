"""
CSV Metadata Service

This module provides functionality for saving and managing metadata in CSV format.
It handles storing information about audio chunks, transcriptions, speakers, and alignments.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import pandas as pd
from datetime import datetime
import uuid


class CSVService:
    """
    Service class for CSV metadata operations.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the CSV Service.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # CSV configuration
        self.output_dir = config.get('csv_output_dir', config.get('result_dir', 'result'))
        self.csv_separator = config.get('csv_separator', ',')
        self.csv_encoding = config.get('csv_encoding', 'utf-8')
        
        # Create output directory
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Define CSV schemas
        self.chunk_schema = [
            'session_id', 'chunk_id', 'source_file', 's3_key', 'file_path',
            'start_time', 'end_time', 'duration', 'sample_rate',
            'transcription', 'language', 'confidence', 'speaker',
            'word_count', 'has_mfa_alignment', 'created_at'
        ]
        
        self.word_schema = [
            'session_id', 'chunk_id', 'word_index', 'word', 'start_time', 'end_time',
            'duration', 'whisper_confidence', 'mfa_refined', 'speaker', 'created_at'
        ]
        
        self.session_schema = [
            'session_id', 'source_file', 's3_key', 'total_chunks', 'total_duration',
            'processing_start', 'processing_end', 'processing_duration',
            'vad_settings', 'transcription_model', 'mfa_used', 'created_at'
        ]
    
    def create_session_record(
        self,
        source_file: str,
        s3_key: Optional[str] = None,
        processing_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new processing session record.
        
        Args:
            source_file: Source audio file path
            s3_key: S3 key if file is from S3
            processing_config: Configuration used for processing
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        session_data = {
            'session_id': session_id,
            'source_file': source_file,
            's3_key': s3_key or '',
            'total_chunks': 0,
            'total_duration': 0.0,
            'processing_start': datetime.now().isoformat(),
            'processing_end': '',
            'processing_duration': 0.0,
            'vad_settings': str(processing_config.get('vad', {})) if processing_config else '',
            'transcription_model': processing_config.get('transcription_model', '') if processing_config else '',
            'mfa_used': processing_config.get('use_mfa', False) if processing_config else False,
            'created_at': datetime.now().isoformat()
        }
        
        # Save session record
        self._save_session_record(session_data)
        
        self.logger.info(f"Created session record: {session_id}")
        return session_id
    
    def finalize_session_record(
        self,
        session_id: str,
        total_chunks: int,
        total_duration: float,
        processing_start: datetime
    ) -> bool:
        """
        Finalize a processing session record.
        
        Args:
            session_id: Session ID
            total_chunks: Total number of chunks processed
            total_duration: Total duration of processed audio
            processing_start: Processing start time
            
        Returns:
            bool: True if successful
        """
        try:
            processing_end = datetime.now()
            processing_duration = (processing_end - processing_start).total_seconds()
            
            # Update session record
            session_file = os.path.join(self.output_dir, 'sessions.csv')
            
            if os.path.exists(session_file):
                df = pd.read_csv(session_file, encoding=self.csv_encoding)
                
                # Update the specific session
                mask = df['session_id'] == session_id
                if mask.any():
                    df.loc[mask, 'total_chunks'] = total_chunks
                    df.loc[mask, 'total_duration'] = total_duration
                    df.loc[mask, 'processing_end'] = processing_end.isoformat()
                    df.loc[mask, 'processing_duration'] = processing_duration
                    
                    # Save updated dataframe
                    df.to_csv(session_file, index=False, encoding=self.csv_encoding, sep=self.csv_separator)
                    
                    self.logger.info(f"Finalized session record: {session_id}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to finalize session {session_id}: {e}")
            return False
    
    def save_chunk_metadata(
        self,
        session_id: str,
        chunks_data: List[Dict[str, Any]],
        transcriptions: List[Dict[str, Any]],
        alignments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Save chunk metadata to CSV.
        
        Args:
            session_id: Session ID
            chunks_data: List of chunk information
            transcriptions: List of transcription results
            alignments: Optional list of MFA alignment results
            
        Returns:
            bool: True if successful
        """
        try:
            chunk_records = []
            
            # Create alignment lookup
            alignment_lookup = {}
            if alignments:
                for alignment in alignments:
                    if alignment.get('success'):
                        chunk_id = alignment.get('data', {}).get('chunk_id')
                        if chunk_id:
                            alignment_lookup[chunk_id] = alignment['data']
            
            # Process each chunk
            for i, chunk in enumerate(chunks_data):
                # Find corresponding transcription
                transcription = None
                if i < len(transcriptions) and transcriptions[i].get('success'):
                    transcription = transcriptions[i]['data']
                
                # Get alignment data if available
                chunk_id = str(chunk.get('chunk_id', i))
                alignment = alignment_lookup.get(chunk_id)
                
                # Create chunk record
                record = {
                    'session_id': session_id,
                    'chunk_id': chunk_id,
                    'source_file': chunk.get('source_file', ''),
                    's3_key': chunk.get('s3_key', ''),
                    'file_path': chunk.get('file_path', ''),
                    'start_time': chunk.get('start_time', 0.0),
                    'end_time': chunk.get('end_time', 0.0),
                    'duration': chunk.get('duration', 0.0),
                    'sample_rate': chunk.get('sample_rate', 16000),
                    'transcription': transcription.get('text', '') if transcription else '',
                    'language': transcription.get('language', '') if transcription else '',
                    'confidence': transcription.get('no_speech_prob', 0.0) if transcription else 0.0,
                    'speaker': self._detect_speaker(transcription, alignment),
                    'word_count': len(transcription.get('words', [])) if transcription else 0,
                    'has_mfa_alignment': alignment is not None,
                    'created_at': datetime.now().isoformat()
                }
                
                chunk_records.append(record)
            
            # Save chunk records
            self._save_chunk_records(chunk_records)
            
            # Save word-level data if available
            if transcriptions:
                self._save_word_level_data(session_id, transcriptions, alignments)
            
            self.logger.info(f"Saved metadata for {len(chunk_records)} chunks")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save chunk metadata: {e}")
            return False
    
    def _detect_speaker(
        self,
        transcription: Optional[Dict[str, Any]],
        alignment: Optional[Dict[str, Any]]
    ) -> str:
        """
        Detect or assign speaker for a chunk.
        
        Args:
            transcription: Transcription data
            alignment: MFA alignment data
            
        Returns:
            Speaker identifier
        """
        # Simple speaker detection logic
        # In a real implementation, you'd use speaker diarization
        
        if not transcription or not transcription.get('text'):
            return 'unknown'
        
        # For now, return a placeholder
        # You could implement voice fingerprinting, speaker embedding, etc.
        return 'speaker_1'
    
    def _save_session_record(self, session_data: Dict[str, Any]) -> None:
        """
        Save session record to CSV.
        
        Args:
            session_data: Session data dictionary
        """
        session_file = os.path.join(self.output_dir, 'sessions.csv')
        
        # Create or append to sessions CSV
        df = pd.DataFrame([session_data])
        
        if os.path.exists(session_file):
            # Append to existing file
            df.to_csv(session_file, mode='a', header=False, index=False, 
                     encoding=self.csv_encoding, sep=self.csv_separator)
        else:
            # Create new file with headers
            df.to_csv(session_file, index=False, encoding=self.csv_encoding, sep=self.csv_separator)
    
    def _save_chunk_records(self, chunk_records: List[Dict[str, Any]]) -> None:
        """
        Save chunk records to CSV.
        
        Args:
            chunk_records: List of chunk data dictionaries
        """
        chunks_file = os.path.join(self.output_dir, 'chunks.csv')
        
        # Create DataFrame
        df = pd.DataFrame(chunk_records, columns=self.chunk_schema)
        
        if os.path.exists(chunks_file):
            # Append to existing file
            df.to_csv(chunks_file, mode='a', header=False, index=False,
                     encoding=self.csv_encoding, sep=self.csv_separator)
        else:
            # Create new file with headers
            df.to_csv(chunks_file, index=False, encoding=self.csv_encoding, sep=self.csv_separator)

        # Optionally upload CSV files to S3 if configured
        try:
            if self.config.get('s3_auto_upload', False) or self.config.get('upload_csv_to_s3', False):
                from service.s3_service import S3Service
                s3 = S3Service(self.config)
                # Upload chunks.csv
                s3_key = f"{self.config.get('s3_prefix','audio-extractions')}/chunks.csv"
                s3.upload_file(chunks_file, s3_key)
                # Upload words.csv if exists
                words_file = os.path.join(self.output_dir, 'words.csv')
                if os.path.exists(words_file):
                    s3_key_w = f"{self.config.get('s3_prefix','audio-extractions')}/words.csv"
                    s3.upload_file(words_file, s3_key_w)
                # Upload sessions.csv if exists
                sessions_file = os.path.join(self.output_dir, 'sessions.csv')
                if os.path.exists(sessions_file):
                    s3_key_s = f"{self.config.get('s3_prefix','audio-extractions')}/sessions.csv"
                    s3.upload_file(sessions_file, s3_key_s)
        except Exception:
            # Don't fail on CSV upload
            pass
    
    def _save_word_level_data(
        self,
        session_id: str,
        transcriptions: List[Dict[str, Any]],
        alignments: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Save word-level data to CSV.
        
        Args:
            session_id: Session ID
            transcriptions: List of transcription results
            alignments: Optional list of MFA alignment results
        """
        try:
            word_records = []
            
            # Create alignment lookup
            alignment_lookup = {}
            if alignments:
                for alignment in alignments:
                    if alignment.get('success'):
                        chunk_id = alignment.get('data', {}).get('chunk_id')
                        if chunk_id:
                            alignment_lookup[chunk_id] = alignment['data']
            
            for transcription in transcriptions:
                if not transcription.get('success'):
                    continue
                
                data = transcription['data']
                chunk_id = data.get('chunk_id')
                words = data.get('words', [])
                
                # Get MFA alignment if available
                alignment = alignment_lookup.get(chunk_id, {})
                mfa_words = alignment.get('words', [])
                
                # Process each word
                for word_index, word in enumerate(words):
                    # Find corresponding MFA word
                    mfa_word = None
                    if word_index < len(mfa_words):
                        mfa_word = mfa_words[word_index]
                    
                    word_record = {
                        'session_id': session_id,
                        'chunk_id': chunk_id,
                        'word_index': word_index,
                        'word': word.get('word', '').strip(),
                        'start_time': mfa_word.get('start', word.get('start', 0.0)) if mfa_word else word.get('start', 0.0),
                        'end_time': mfa_word.get('end', word.get('end', 0.0)) if mfa_word else word.get('end', 0.0),
                        'duration': 0.0,  # Will be calculated
                        'whisper_confidence': word.get('probability', 0.0),
                        'mfa_refined': mfa_word is not None,
                        'speaker': 'speaker_1',  # Placeholder
                        'created_at': datetime.now().isoformat()
                    }
                    
                    # Calculate duration
                    word_record['duration'] = word_record['end_time'] - word_record['start_time']
                    
                    word_records.append(word_record)
            
            if word_records:
                words_file = os.path.join(self.output_dir, 'words.csv')
                df = pd.DataFrame(word_records, columns=self.word_schema)
                
                if os.path.exists(words_file):
                    # Append to existing file
                    df.to_csv(words_file, mode='a', header=False, index=False,
                             encoding=self.csv_encoding, sep=self.csv_separator)
                else:
                    # Create new file with headers
                    df.to_csv(words_file, index=False, encoding=self.csv_encoding, sep=self.csv_separator)
                
                self.logger.info(f"Saved {len(word_records)} word records")
            
        except Exception as e:
            self.logger.error(f"Failed to save word-level data: {e}")
    
    def load_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load session data from CSV.
        
        Args:
            session_id: Session ID to load
            
        Returns:
            Session data dictionary or None
        """
        try:
            session_file = os.path.join(self.output_dir, 'sessions.csv')
            
            if not os.path.exists(session_file):
                return None
            
            df = pd.read_csv(session_file, encoding=self.csv_encoding, sep=self.csv_separator)
            
            # Find session
            session_data = df[df['session_id'] == session_id]
            
            if session_data.empty:
                return None
            
            return session_data.iloc[0].to_dict()
            
        except Exception as e:
            self.logger.error(f"Failed to load session data for {session_id}: {e}")
            return None
    
    def load_chunk_data(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Load chunk data for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of chunk data dictionaries
        """
        try:
            chunks_file = os.path.join(self.output_dir, 'chunks.csv')
            
            if not os.path.exists(chunks_file):
                return []
            
            df = pd.read_csv(chunks_file, encoding=self.csv_encoding, sep=self.csv_separator)
            
            # Filter by session ID
            chunk_data = df[df['session_id'] == session_id]
            
            return chunk_data.to_dict('records')
            
        except Exception as e:
            self.logger.error(f"Failed to load chunk data for {session_id}: {e}")
            return []
    
    def export_session_report(self, session_id: str, output_path: str) -> bool:
        """
        Export a comprehensive session report.
        
        Args:
            session_id: Session ID
            output_path: Path to save the report
            
        Returns:
            bool: True if successful
        """
        try:
            # Load session data
            session_data = self.load_session_data(session_id)
            chunk_data = self.load_chunk_data(session_id)
            
            if not session_data:
                return False
            
            # Create report
            report_lines = []
            report_lines.append(f"Voice Processing Session Report")
            report_lines.append(f"Session ID: {session_id}")
            report_lines.append(f"Generated: {datetime.now().isoformat()}")
            report_lines.append("")
            
            # Session summary
            report_lines.append("Session Summary:")
            report_lines.append(f"  Source File: {session_data.get('source_file', 'N/A')}")
            report_lines.append(f"  Total Chunks: {session_data.get('total_chunks', 0)}")
            report_lines.append(f"  Total Duration: {session_data.get('total_duration', 0):.2f}s")
            report_lines.append(f"  Processing Duration: {session_data.get('processing_duration', 0):.2f}s")
            report_lines.append(f"  MFA Used: {session_data.get('mfa_used', False)}")
            report_lines.append("")
            
            # Chunk details
            if chunk_data:
                report_lines.append("Chunk Details:")
                for chunk in chunk_data:
                    report_lines.append(f"  Chunk {chunk.get('chunk_id')}:")
                    report_lines.append(f"    Time: {chunk.get('start_time', 0):.2f}s - {chunk.get('end_time', 0):.2f}s")
                    report_lines.append(f"    Transcription: {chunk.get('transcription', 'N/A')}")
                    report_lines.append(f"    Word Count: {chunk.get('word_count', 0)}")
                    report_lines.append("")
            
            # Save report
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export session report for {session_id}: {e}")
            return False
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about the CSV service.
        
        Returns:
            Dictionary containing service information
        """
        return {
            'output_dir': self.output_dir,
            'csv_separator': self.csv_separator,
            'csv_encoding': self.csv_encoding,
            'chunk_schema': self.chunk_schema,
            'word_schema': self.word_schema,
            'session_schema': self.session_schema
        }
