"""
Pydantic Models for API Request/Response Validation

This module defines the data models used for API request and response validation
in the YouTube audio extraction service.
"""

from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class VideoInfoRequest(BaseModel):
    """Request model for getting video information."""
    url: HttpUrl = Field(..., description="YouTube video URL")


class AudioExtractionRequest(BaseModel):
    """Request model for audio extraction."""
    url: HttpUrl = Field(..., description="YouTube video URL")
    filename: Optional[str] = Field(None, description="Custom output filename (without extension)")
    start_time: Optional[float] = Field(None, ge=0, description="Start time in seconds")
    duration: Optional[float] = Field(None, gt=0, description="Duration in seconds")
    sample_rate: Optional[int] = Field(None, description="Target sample rate")
    upload_to_s3: Optional[bool] = Field(None, description="Upload extracted audio to S3")
    
    @validator('filename')
    def validate_filename(cls, v):
        if v is not None:
            # Remove invalid characters for filenames
            invalid_chars = '<>:"/\\|?*'
            for char in invalid_chars:
                if char in v:
                    raise ValueError(f"Filename cannot contain '{char}'")
        return v
    
    @validator('sample_rate')
    def validate_sample_rate(cls, v):
        if v is not None and v not in [8000, 16000, 22050, 44100, 48000]:
            raise ValueError("Sample rate must be one of: 8000, 16000, 22050, 44100, 48000")
        return v


class BatchExtractionRequest(BaseModel):
    """Request model for batch audio extraction."""
    urls: List[HttpUrl] = Field(..., min_items=1, max_items=10, description="List of YouTube video URLs")
    prefix: Optional[str] = Field("batch_audio", description="Prefix for output filenames")
    sample_rate: Optional[int] = Field(None, description="Target sample rate for all extractions")
    
    @validator('prefix')
    def validate_prefix(cls, v):
        if v is not None:
            # Remove invalid characters for filenames
            invalid_chars = '<>:"/\\|?*'
            for char in invalid_chars:
                if char in v:
                    raise ValueError(f"Prefix cannot contain '{char}'")
        return v


class URLValidationRequest(BaseModel):
    """Request model for URL validation."""
    url: HttpUrl = Field(..., description="YouTube video URL to validate")


class VideoInfo(BaseModel):
    """Response model for video information."""
    title: Optional[str] = Field(None, description="Video title")
    duration: Optional[int] = Field(None, description="Video duration in seconds")
    uploader: Optional[str] = Field(None, description="Video uploader")
    view_count: Optional[int] = Field(None, description="View count")
    upload_date: Optional[str] = Field(None, description="Upload date")
    description: Optional[str] = Field(None, description="Video description (truncated)")
    thumbnail: Optional[str] = Field(None, description="Thumbnail URL")
    video_id: Optional[str] = Field(None, description="YouTube video ID")


class AudioFileInfo(BaseModel):
    """Response model for audio file information."""
    output_path: str = Field(..., description="Full path to the extracted audio file")
    filename: str = Field(..., description="Filename of the extracted audio")
    duration: float = Field(..., description="Audio duration in seconds")
    sample_rate: int = Field(..., description="Audio sample rate")
    file_size: int = Field(..., description="File size in bytes")
    video_title: str = Field(..., description="Original video title")
    video_id: str = Field(..., description="YouTube video ID")
    start_time: Optional[float] = Field(None, description="Start time of extraction")
    extracted_duration: Optional[float] = Field(None, description="Duration of extracted segment")
    s3_uploaded: bool = Field(False, description="Whether file was uploaded to S3")
    s3_url: Optional[str] = Field(None, description="S3 URL if uploaded")
    s3_key: Optional[str] = Field(None, description="S3 object key if uploaded")
    s3_bucket: Optional[str] = Field(None, description="S3 bucket name if uploaded")
    local_file_deleted: Optional[bool] = Field(None, description="Whether local file was deleted after S3 upload")
    s3_error: Optional[str] = Field(None, description="S3 upload error if any")


class ExtractionResult(BaseModel):
    """Response model for successful audio extraction."""
    message: str = Field(..., description="Success message")
    data: AudioFileInfo = Field(..., description="Extracted audio file information")


class BatchExtractionResult(BaseModel):
    """Response model for batch extraction results."""
    message: str = Field(..., description="Batch extraction message")
    data: Dict[str, Any] = Field(..., description="Batch extraction data")


class ValidationResult(BaseModel):
    """Response model for URL validation."""
    valid: bool = Field(..., description="Whether the URL is valid")
    title: Optional[str] = Field(None, description="Video title if valid")
    duration: Optional[int] = Field(None, description="Video duration if valid")


class FileInfo(BaseModel):
    """Response model for file information."""
    filename: str = Field(..., description="File name")
    size: int = Field(..., description="File size in bytes")
    created: float = Field(..., description="Creation timestamp")
    modified: float = Field(..., description="Modification timestamp")


class FileListResponse(BaseModel):
    """Response model for file listing."""
    files: List[FileInfo] = Field(..., description="List of files")
    total_count: int = Field(..., description="Total number of files")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.now, description="Current timestamp")


class ErrorResponse(BaseModel):
    """Response model for error responses."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")


class SuccessResponse(BaseModel):
    """Generic success response model."""
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")


class SampleRateConfig(BaseModel):
    """Model for sample rate configuration."""
    sample_rate: int = Field(..., description="Sample rate in Hz")
    description: str = Field(..., description="Description of the sample rate")
    use_cases: List[str] = Field(..., description="Common use cases")


class ConfigResponse(BaseModel):
    """Response model for configuration information."""
    sample_rate_configs: Dict[str, SampleRateConfig] = Field(..., description="Available sample rate configurations")
    supported_formats: List[str] = Field(..., description="Supported audio formats")


class ExtractionProgress(BaseModel):
    """Model for extraction progress tracking."""
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Current status (pending, processing, completed, failed)")
    progress: float = Field(..., ge=0, le=100, description="Progress percentage")
    message: Optional[str] = Field(None, description="Current status message")
    result: Optional[AudioFileInfo] = Field(None, description="Result data if completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(default_factory=datetime.now, description="Task creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")


class S3UploadRequest(BaseModel):
    """Request model for S3 upload."""
    filename: str = Field(..., description="Local filename to upload")
    s3_key: Optional[str] = Field(None, description="Custom S3 object key")
    metadata: Optional[Dict[str, str]] = Field(None, description="Additional metadata")
    tags: Optional[Dict[str, str]] = Field(None, description="S3 object tags")


class S3FileInfo(BaseModel):
    """Model for S3 file information."""
    s3_key: str = Field(..., description="S3 object key")
    size: int = Field(..., description="File size in bytes")
    last_modified: str = Field(..., description="Last modified timestamp")
    etag: str = Field(..., description="S3 ETag")
    storage_class: str = Field(..., description="S3 storage class")
    url: str = Field(..., description="S3 object URL")


class S3ListResponse(BaseModel):
    """Response model for S3 file listing."""
    files: List[S3FileInfo] = Field(..., description="List of S3 files")
    total_count: int = Field(..., description="Total number of files")
    is_truncated: bool = Field(..., description="Whether results are truncated")
    bucket: str = Field(..., description="S3 bucket name")
    prefix: str = Field(..., description="Search prefix used")


class S3UploadResponse(BaseModel):
    """Response model for S3 upload."""
    s3_key: str = Field(..., description="S3 object key")
    s3_url: str = Field(..., description="S3 object URL")
    bucket: str = Field(..., description="S3 bucket name")
    region: str = Field(..., description="S3 region")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="Content type")


class PresignedUrlRequest(BaseModel):
    """Request model for presigned URL generation."""
    s3_key: str = Field(..., description="S3 object key")
    expiration: Optional[int] = Field(3600, ge=60, le=604800, description="Expiration time in seconds")
    method: Optional[str] = Field("get_object", description="HTTP method (get_object or put_object)")


class PresignedUrlResponse(BaseModel):
    """Response model for presigned URL."""
    presigned_url: str = Field(..., description="Presigned URL")
    s3_key: str = Field(..., description="S3 object key")
    expires_in: int = Field(..., description="Expiration time in seconds")
    method: str = Field(..., description="HTTP method")


# Voice Processing Models

class VoiceProcessingRequest(BaseModel):
    """Request model for voice processing pipeline."""
    s3_key: Optional[str] = Field(None, description="S3 object key of audio file to process")
    local_file_path: Optional[str] = Field(None, description="Local file path to process")
    use_mfa: Optional[bool] = Field(True, description="Enable MFA for word-level timestamp refinement")
    save_chunks: Optional[bool] = Field(True, description="Save individual audio chunks")
    vad_aggressiveness: Optional[int] = Field(3, ge=0, le=3, description="VAD aggressiveness level (0-3)")
    min_chunk_duration: Optional[float] = Field(1.0, ge=0.1, description="Minimum chunk duration in seconds")
    max_chunk_duration: Optional[float] = Field(5.0, ge=1.0, description="Maximum chunk duration in seconds")
    use_google_stt: Optional[bool] = Field(True, description="Use Google Speech-to-Text for transcription (recommended for Khmer)")
    use_external_transcription: Optional[bool] = Field(False, description="Use external transcription service as fallback")
    external_transcription_url: Optional[HttpUrl] = Field(None, description="Optional full URL to external transcription endpoint for fallback")
    upload_chunks_to_s3: Optional[bool] = Field(False, description="Upload saved chunk files to S3 after processing")
    upload_csv_to_s3: Optional[bool] = Field(False, description="Upload generated CSV files (chunks.csv, words.csv, sessions.csv) to S3 after processing")


class WordAlignment(BaseModel):
    """Model for word-level alignment data."""
    word: str = Field(..., description="Word text")
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    duration: float = Field(..., description="Duration in seconds")
    whisper_confidence: Optional[float] = Field(None, description="Whisper confidence score")
    mfa_refined: bool = Field(False, description="Whether MFA was used for refinement")
    speaker: Optional[str] = Field(None, description="Speaker identifier")


class ChunkSummary(BaseModel):
    """Model for chunk processing summary."""
    chunk_id: str = Field(..., description="Chunk identifier")
    start_time: float = Field(..., description="Start time in original audio")
    end_time: float = Field(..., description="End time in original audio")
    duration: float = Field(..., description="Chunk duration in seconds")
    transcription_success: bool = Field(..., description="Whether transcription succeeded")
    transcription_text: str = Field(..., description="Transcribed text")
    word_count: int = Field(..., description="Number of words")
    mfa_success: bool = Field(False, description="Whether MFA alignment succeeded")
    mfa_words: int = Field(0, description="Number of MFA-aligned words")
    language: Optional[str] = Field(None, description="Detected language")
    confidence: Optional[float] = Field(None, description="Transcription confidence")


class ProcessingSteps(BaseModel):
    """Model for processing step results."""
    vad: bool = Field(..., description="VAD processing success")
    transcription: bool = Field(..., description="Transcription processing success")
    mfa: bool = Field(..., description="MFA alignment success")
    csv_export: bool = Field(..., description="CSV export success")


class VoiceProcessingData(BaseModel):
    """Model for voice processing result data."""
    total_chunks: int = Field(..., description="Total number of chunks created")
    total_duration: float = Field(..., description="Total duration of processed audio")
    speech_ratio: float = Field(..., description="Ratio of speech to total audio")
    successful_transcriptions: int = Field(..., description="Number of successful transcriptions")
    failed_transcriptions: int = Field(..., description="Number of failed transcriptions")
    mfa_alignments: int = Field(..., description="Number of successful MFA alignments")
    saved_chunks: int = Field(..., description="Number of saved audio chunks")
    csv_exported: bool = Field(..., description="Whether CSV metadata was exported")
    chunks_summary: List[ChunkSummary] = Field(..., description="Summary of all chunks")
    processing_steps: ProcessingSteps = Field(..., description="Processing step results")


class VoiceProcessingResult(BaseModel):
    """Response model for voice processing pipeline."""
    success: bool = Field(..., description="Overall processing success")
    session_id: str = Field(..., description="Processing session identifier")
    processing_duration: float = Field(..., description="Total processing time in seconds")
    error: Optional[str] = Field(None, description="Error message if processing failed")
    data: Optional[VoiceProcessingData] = Field(None, description="Processing results")


class ProcessingSessionSummary(BaseModel):
    """Model for processing session summary."""
    session_id: str = Field(..., description="Session identifier")
    source_file: str = Field(..., description="Source audio file")
    s3_key: Optional[str] = Field(None, description="S3 key if from S3")
    total_chunks: int = Field(..., description="Total number of chunks")
    total_duration: float = Field(..., description="Total audio duration")
    processing_start: str = Field(..., description="Processing start timestamp")
    processing_end: Optional[str] = Field(None, description="Processing end timestamp")
    processing_duration: float = Field(..., description="Processing duration in seconds")
    mfa_used: bool = Field(..., description="Whether MFA was used")
    created_at: str = Field(..., description="Session creation timestamp")


class SessionListResponse(BaseModel):
    """Response model for session listing."""
    sessions: List[ProcessingSessionSummary] = Field(..., description="List of processing sessions")
    total_count: int = Field(..., description="Total number of sessions")


class ChunkMetadata(BaseModel):
    """Model for chunk metadata."""
    session_id: str = Field(..., description="Session identifier")
    chunk_id: str = Field(..., description="Chunk identifier")
    source_file: str = Field(..., description="Source audio file")
    file_path: str = Field(..., description="Path to chunk audio file")
    start_time: float = Field(..., description="Start time in original audio")
    end_time: float = Field(..., description="End time in original audio")
    duration: float = Field(..., description="Chunk duration")
    transcription: str = Field(..., description="Transcribed text")
    language: str = Field(..., description="Detected language")
    confidence: float = Field(..., description="Transcription confidence")
    speaker: str = Field(..., description="Speaker identifier")
    word_count: int = Field(..., description="Number of words")
    has_mfa_alignment: bool = Field(..., description="Whether MFA alignment is available")


class SessionDetails(BaseModel):
    """Model for detailed session information."""
    session: ProcessingSessionSummary = Field(..., description="Session information")
    chunks: List[ChunkMetadata] = Field(..., description="Chunk metadata")
    summary: Dict[str, Any] = Field(..., description="Session summary statistics")


class SessionDetailsResponse(BaseModel):
    """Response model for session details."""
    success: bool = Field(..., description="Request success")
    data: Optional[SessionDetails] = Field(None, description="Session details")
    error: Optional[str] = Field(None, description="Error message if failed")


class ServiceStatusResponse(BaseModel):
    """Response model for service status check."""
    s3_service: bool = Field(..., description="S3 service availability")
    vad_service: bool = Field(..., description="VAD service availability")
    transcription_service: bool = Field(..., description="Transcription service availability")
    mfa_service: bool = Field(..., description="MFA service availability")
    csv_service: bool = Field(..., description="CSV service availability")
    use_mfa: bool = Field(..., description="Whether MFA is enabled")
    save_chunks: bool = Field(..., description="Whether chunk saving is enabled")


class AsyncProcessingRequest(BaseModel):
    """Request model for asynchronous voice processing."""
    s3_key: str = Field(..., description="S3 object key of audio file to process")
    processing_config: Optional[Dict[str, Any]] = Field(None, description="Processing configuration")
    notification_url: Optional[str] = Field(None, description="URL to notify when processing is complete")


class AsyncProcessingResponse(BaseModel):
    """Response model for asynchronous processing request."""
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Initial task status")
    message: str = Field(..., description="Status message")
    estimated_duration: Optional[float] = Field(None, description="Estimated processing duration in seconds")
