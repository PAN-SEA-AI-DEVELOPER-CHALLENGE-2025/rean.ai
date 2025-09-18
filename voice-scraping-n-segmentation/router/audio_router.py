"""
Audio Router

This module provides FastAPI endpoints for YouTube audio extraction functionality.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from fastapi.responses import FileResponse, JSONResponse
import os
import asyncio
from typing import Dict, Any, List
from service.youtube_extractor import YouTubeAudioService
from service.s3_service import S3Service
from config.settings import get_config, get_sample_rate_configs
from router.models import (
    VideoInfoRequest, AudioExtractionRequest, BatchExtractionRequest,
    URLValidationRequest, VideoInfo, ExtractionResult, BatchExtractionResult,
    ValidationResult, FileListResponse, HealthResponse, ErrorResponse,
    SuccessResponse, ConfigResponse, SampleRateConfig, S3UploadRequest,
    S3ListResponse, S3UploadResponse, PresignedUrlRequest, PresignedUrlResponse
)


# Initialize configuration and services
config = get_config()
audio_service = YouTubeAudioService(config)
s3_service = S3Service(config)

# Create router instance
router = APIRouter(prefix="/api/audio", tags=["audio"])


@router.post("/info", response_model=VideoInfo)
async def get_video_info(request: VideoInfoRequest):
    """
    Get YouTube video information without downloading.
    
    Args:
        request: VideoInfoRequest containing YouTube URL
        
    Returns:
        VideoInfo: Video metadata
        
    Raises:
        HTTPException: If video info cannot be retrieved
    """
    try:
        result = audio_service.get_video_info(str(request.url))
        
        if result['success']:
            return VideoInfo(**result['data'])
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['error']
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/extract", response_model=ExtractionResult)
async def extract_audio(request: AudioExtractionRequest):
    """
    Extract audio from a YouTube video.
    
    Args:
        request: AudioExtractionRequest with extraction parameters
        
    Returns:
        ExtractionResult: Information about the extracted audio file
        
    Raises:
        HTTPException: If extraction fails
    """
    try:
        # Update config if sample_rate is provided
        if request.sample_rate:
            audio_service.sample_rate = request.sample_rate
        
        result = audio_service.extract_audio(
            youtube_url=str(request.url),
            output_filename=request.filename,
            start_time=request.start_time,
            duration=request.duration,
            upload_to_s3=request.upload_to_s3
        )
        
        if result['success']:
            return ExtractionResult(
                message="Audio extracted successfully",
                data=result['data']
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['error']
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/extract-async")
async def extract_audio_async(request: AudioExtractionRequest, background_tasks: BackgroundTasks):
    """
    Extract audio from a YouTube video asynchronously.
    
    Args:
        request: AudioExtractionRequest with extraction parameters
        background_tasks: FastAPI background tasks
        
    Returns:
        Dict: Task information for async processing
    """
    import uuid
    
    task_id = str(uuid.uuid4())
    
    def extract_task():
        try:
            if request.sample_rate:
                audio_service.sample_rate = request.sample_rate
                
            result = audio_service.extract_audio(
                youtube_url=str(request.url),
                output_filename=request.filename,
                start_time=request.start_time,
                duration=request.duration
            )
            # In a real implementation, you'd store this result in a database or cache
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    background_tasks.add_task(extract_task)
    
    return {
        "task_id": task_id,
        "status": "accepted",
        "message": "Audio extraction started in background"
    }


@router.post("/extract-batch", response_model=BatchExtractionResult)
async def extract_batch(request: BatchExtractionRequest):
    """
    Extract audio from multiple YouTube videos.
    
    Args:
        request: BatchExtractionRequest with URLs and settings
        
    Returns:
        BatchExtractionResult: Results of batch extraction
    """
    try:
        if request.sample_rate:
            audio_service.sample_rate = request.sample_rate
            
        urls = [str(url) for url in request.urls]
        result = audio_service.extract_multiple(urls, request.prefix)
        
        return BatchExtractionResult(
            message=f"Batch extraction completed. {result['data']['successful_extractions']}/{result['data']['total_requested']} successful",
            data=result['data']
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/validate", response_model=ValidationResult)
async def validate_url(request: URLValidationRequest):
    """
    Validate a YouTube URL.
    
    Args:
        request: URLValidationRequest containing URL to validate
        
    Returns:
        ValidationResult: Validation result
    """
    try:
        result = audio_service.validate_url(str(request.url))
        
        if result['success']:
            return ValidationResult(**result['data'])
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['error']
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download an extracted audio file.
    
    Args:
        filename: Name of the file to download
        
    Returns:
        FileResponse: The requested audio file
        
    Raises:
        HTTPException: If file not found
    """
    try:
        file_path = os.path.join(config['output_dir'], filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='audio/wav'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/files", response_model=FileListResponse)
async def list_files():
    """
    List all extracted audio files.
    
    Returns:
        FileListResponse: List of available audio files
    """
    try:
        output_dir = config['output_dir']
        files = []
        
        if os.path.exists(output_dir):
            for filename in os.listdir(output_dir):
                if filename.endswith('.wav'):
                    file_path = os.path.join(output_dir, filename)
                    file_stats = os.stat(file_path)
                    files.append({
                        'filename': filename,
                        'size': file_stats.st_size,
                        'created': file_stats.st_ctime,
                        'modified': file_stats.st_mtime
                    })
        
        return FileListResponse(
            files=files,
            total_count=len(files)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/cleanup", response_model=SuccessResponse)
async def cleanup():
    """
    Clean up temporary files.
    
    Returns:
        SuccessResponse: Cleanup confirmation
    """
    try:
        audio_service.cleanup_temp_files()
        return SuccessResponse(message="Cleanup completed successfully")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/config", response_model=ConfigResponse)
async def get_config_info():
    """
    Get configuration information including supported formats and sample rates.
    
    Returns:
        ConfigResponse: Configuration information
    """
    try:
        sample_rate_configs = get_sample_rate_configs()
        supported_formats = audio_service.get_supported_formats()
        
        # Convert to Pydantic models
        config_models = {}
        for key, value in sample_rate_configs.items():
            config_models[key] = SampleRateConfig(**value)
        
        return ConfigResponse(
            sample_rate_configs=config_models,
            supported_formats=supported_formats
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# S3 endpoints
@router.post("/s3/upload", response_model=S3UploadResponse)
async def upload_to_s3(request: S3UploadRequest):
    """
    Upload a local audio file to S3.
    
    Args:
        request: S3UploadRequest with file details
        
    Returns:
        S3UploadResponse: Upload result with S3 details
    """
    try:
        if not s3_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="S3 service not available. Check AWS credentials and configuration."
            )
        
        # Check if local file exists
        file_path = os.path.join(config['output_dir'], request.filename)
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {request.filename}"
            )
        
        result = s3_service.upload_file(
            local_file_path=file_path,
            s3_key=request.s3_key,
            metadata=request.metadata,
            tags=request.tags
        )
        
        if result['success']:
            return S3UploadResponse(**result['data'])
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['error']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/s3/files", response_model=S3ListResponse)
async def list_s3_files(prefix: str = None, max_keys: int = 100):
    """
    List files in S3 bucket.
    
    Args:
        prefix: Optional prefix to filter files
        max_keys: Maximum number of files to return
        
    Returns:
        S3ListResponse: List of S3 files
    """
    try:
        if not s3_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="S3 service not available"
            )
        
        result = s3_service.list_files(prefix=prefix, max_keys=max_keys)
        
        if result['success']:
            return S3ListResponse(**result['data'])
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['error']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/s3/{s3_key:path}")
async def delete_s3_file(s3_key: str):
    """
    Delete a file from S3.
    
    Args:
        s3_key: S3 object key to delete
        
    Returns:
        Success message
    """
    try:
        if not s3_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="S3 service not available"
            )
        
        result = s3_service.delete_file(s3_key)
        
        if result['success']:
            return SuccessResponse(
                message=f"Successfully deleted S3 file: {s3_key}",
                data=result['data']
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['error']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/s3/{s3_key:path}/info")
async def get_s3_file_info(s3_key: str):
    """
    Get information about an S3 file.
    
    Args:
        s3_key: S3 object key
        
    Returns:
        S3 file information
    """
    try:
        if not s3_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="S3 service not available"
            )
        
        result = s3_service.get_file_info(s3_key)
        
        if result['success']:
            return result['data']
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result['error']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/s3/presigned-url", response_model=PresignedUrlResponse)
async def generate_presigned_url(request: PresignedUrlRequest):
    """
    Generate a presigned URL for S3 object access.
    
    Args:
        request: PresignedUrlRequest with S3 key and options
        
    Returns:
        PresignedUrlResponse: Generated presigned URL
    """
    try:
        if not s3_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="S3 service not available"
            )
        
        result = s3_service.generate_presigned_url(
            s3_key=request.s3_key,
            expiration=request.expiration,
            method=request.method
        )
        
        if result['success']:
            return PresignedUrlResponse(**result['data'])
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['error']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/s3/status")
async def s3_status():
    """
    Get S3 service status and configuration.
    
    Returns:
        S3 service status information
    """
    return {
        "available": s3_service.is_available(),
        "bucket": config.get('s3_bucket_name'),
        "region": config.get('s3_region'),
        "prefix": config.get('s3_prefix'),
        "auto_upload": config.get('s3_auto_upload'),
        "delete_local_after_upload": config.get('s3_delete_local_after_upload')
    }


# Health check endpoint (separate from audio operations)
health_router = APIRouter(tags=["health"])


@health_router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        HealthResponse: Service health information
    """
    return HealthResponse(
        status="healthy",
        service="YouTube Audio Extractor",
        version="1.0.0"
    )


@health_router.get("/")
async def root():
    """
    Root endpoint with basic service information.
    
    Returns:
        Dict: Basic service information
    """
    return {
        "service": "YouTube Audio Extractor API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }