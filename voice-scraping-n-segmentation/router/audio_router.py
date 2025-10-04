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
from service.database_service import DatabaseService
from service.queue_service import QueueService
from config.settings import get_config, get_sample_rate_configs
from router.models import (
    VideoInfoRequest, AudioExtractionRequest, BatchExtractionRequest,
    URLValidationRequest, VideoInfo, ExtractionResult, BatchExtractionResult,
    ValidationResult, FileListResponse, HealthResponse, ErrorResponse,
    SuccessResponse, ConfigResponse, SampleRateConfig, S3UploadRequest,
    S3ListResponse, S3UploadResponse, PresignedUrlRequest, PresignedUrlResponse,
    # New enhanced models
    EnhancedAudioExtractionRequest, EnhancedExtractionResult,
    EnhancedBatchExtractionRequest, EnhancedBatchExtractionResult,
    QueueRequest, QueueResponse, QueueStatusResponse, QueueListResponse,
    QueueCancellationResponse, URLCheckResponse, ProcessingHistoryResponse,
    DatabaseResponse
)


# Initialize configuration and services
config = get_config()
audio_service = YouTubeAudioService(config)
s3_service = S3Service(config)
db_service = DatabaseService(config)
queue_service = QueueService(config)

# Create router instance
router = APIRouter(prefix="/api/audio", tags=["audio"])

# Note: Service initialization will be handled in main.py startup event


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


@router.post("/extract", response_model=EnhancedExtractionResult)
async def extract_audio(request: EnhancedAudioExtractionRequest):
    """
    Extract audio from a YouTube video with database verification.
    
    Args:
        request: EnhancedAudioExtractionRequest with extraction parameters
        
    Returns:
        EnhancedExtractionResult: Information about the extracted audio file
        
    Raises:
        HTTPException: If extraction fails
    """
    try:
        youtube_url = str(request.url)
        
        # Check if URL exists in database first
        if db_service.is_available():
            url_check = await db_service.check_url_exists(youtube_url)
            
            if url_check['success'] and url_check['exists'] and not request.force_reprocess:
                existing_record = url_check['data']
                
                # If already processed successfully, return existing data
                if existing_record['status'] == 'completed':
                    return EnhancedExtractionResult(
                        success=True,
                        from_database=True,
                        reprocessed=False,
                        message="Audio already extracted (retrieved from database)",
                        data={
                            'output_path': existing_record['file_path'] or '',
                            'filename': os.path.basename(existing_record['file_path']) if existing_record['file_path'] else '',
                            'duration': existing_record['metadata'].get('duration', 0) if existing_record['metadata'] else 0,
                            'sample_rate': existing_record['metadata'].get('sample_rate', 0) if existing_record['metadata'] else 0,
                            'file_size': existing_record['metadata'].get('file_size', 0) if existing_record['metadata'] else 0,
                            'video_title': existing_record['video_title'] or '',
                            'video_id': existing_record['video_id'] or '',
                            'start_time': request.start_time,
                            'extracted_duration': request.duration,
                            's3_uploaded': bool(existing_record['s3_url']),
                            's3_url': existing_record['s3_url'],
                            's3_key': existing_record['s3_key']
                        },
                        database_record=existing_record
                    )
        
        # Update config if sample_rate is provided
        if request.sample_rate:
            audio_service.sample_rate = request.sample_rate
        
        # Create/update URL record in database
        if db_service.is_available():
            # Get video info first for metadata
            video_info = audio_service.get_video_info(youtube_url)
            video_id = video_info['data'].get('video_id') if video_info['success'] else None
            video_title = video_info['data'].get('title') if video_info['success'] else None
            
            await db_service.create_url_record(
                youtube_url=youtube_url,
                video_id=video_id,
                video_title=video_title,
                metadata=request.metadata
            )
            
            # Update status to processing
            await db_service.update_url_status(youtube_url, 'processing')
        
        # Extract audio
        result = audio_service.extract_audio(
            youtube_url=youtube_url,
            output_filename=request.filename,
            start_time=request.start_time,
            duration=request.duration,
            upload_to_s3=request.upload_to_s3
        )
        
        if result['success']:
            # Update database with successful result
            if db_service.is_available():
                data = result['data']
                await db_service.update_url_status(
                    youtube_url, 'completed',
                    file_path=data.get('output_path'),
                    s3_url=data.get('s3_url'),
                    s3_key=data.get('s3_key'),
                    metadata=data
                )
            
            return EnhancedExtractionResult(
                success=True,
                from_database=False,
                reprocessed=request.force_reprocess,
                message="Audio extracted successfully",
                data=result['data']
            )
        else:
            # Update database with failure
            if db_service.is_available():
                await db_service.update_url_status(
                    youtube_url, 'failed',
                    error_message=result['error']
                )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['error']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        # Update database with failure
        if db_service.is_available():
            try:
                await db_service.update_url_status(
                    str(request.url), 'failed',
                    error_message=str(e)
                )
            except:
                pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/extract-async")
async def extract_audio_async(request: EnhancedAudioExtractionRequest, background_tasks: BackgroundTasks):
    """
    Extract audio from a YouTube video asynchronously with database verification.
    
    Args:
        request: EnhancedAudioExtractionRequest with extraction parameters
        background_tasks: FastAPI background tasks
        
    Returns:
        Dict: Task information for async processing
    """
    import uuid
    
    task_id = str(uuid.uuid4())
    youtube_url = str(request.url)
    
    # Check database first if available
    if db_service.is_available() and not request.force_reprocess:
        url_check = await db_service.check_url_exists(youtube_url)
        if url_check['success'] and url_check['exists']:
            existing_record = url_check['data']
            if existing_record['status'] == 'completed':
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "message": "Audio already extracted (retrieved from database)",
                    "from_database": True,
                    "result": {
                        'output_path': existing_record['file_path'] or '',
                        'filename': os.path.basename(existing_record['file_path']) if existing_record['file_path'] else '',
                        's3_url': existing_record['s3_url'],
                        's3_key': existing_record['s3_key']
                    }
                }
    
    async def extract_task():
        try:
            # Create/update database record
            if db_service.is_available():
                video_info = audio_service.get_video_info(youtube_url)
                video_id = video_info['data'].get('video_id') if video_info['success'] else None
                video_title = video_info['data'].get('title') if video_info['success'] else None
                
                await db_service.create_url_record(
                    youtube_url=youtube_url,
                    video_id=video_id,
                    video_title=video_title,
                    metadata=request.metadata
                )
                await db_service.update_url_status(youtube_url, 'processing')
            
            # Extract audio
            if request.sample_rate:
                audio_service.sample_rate = request.sample_rate
                
            result = audio_service.extract_audio(
                youtube_url=youtube_url,
                output_filename=request.filename,
                start_time=request.start_time,
                duration=request.duration,
                upload_to_s3=request.upload_to_s3
            )
            
            # Update database with result
            if db_service.is_available():
                if result['success']:
                    data = result['data']
                    await db_service.update_url_status(
                        youtube_url, 'completed',
                        file_path=data.get('output_path'),
                        s3_url=data.get('s3_url'),
                        s3_key=data.get('s3_key'),
                        metadata=data
                    )
                else:
                    await db_service.update_url_status(
                        youtube_url, 'failed',
                        error_message=result['error']
                    )
            
            return result
        except Exception as e:
            # Update database with failure
            if db_service.is_available():
                try:
                    await db_service.update_url_status(
                        youtube_url, 'failed',
                        error_message=str(e)
                    )
                except:
                    pass
            return {'success': False, 'error': str(e)}
    
    background_tasks.add_task(extract_task)
    
    return {
        "task_id": task_id,
        "status": "accepted",
        "message": "Audio extraction started in background",
        "from_database": False
    }


@router.post("/extract-batch", response_model=EnhancedBatchExtractionResult)
async def extract_batch(request: EnhancedBatchExtractionRequest):
    """
    Extract audio from multiple YouTube videos with queue support and database verification.
    
    Args:
        request: EnhancedBatchExtractionRequest with URLs and settings
        
    Returns:
        EnhancedBatchExtractionResult: Results of batch extraction
    """
    try:
        urls = [str(url) for url in request.urls]
        
        # Check for existing URLs if skip_existing is enabled
        skipped_count = 0
        urls_to_process = urls.copy()
        
        if request.skip_existing and db_service.is_available():
            urls_to_process = []
            for url in urls:
                url_check = await db_service.check_url_exists(url)
                if url_check['success'] and url_check['exists']:
                    existing_record = url_check['data']
                    if existing_record['status'] == 'completed':
                        skipped_count += 1
                        continue
                urls_to_process.append(url)
        
        # If using queue (default for multiple URLs)
        if request.use_queue and len(urls_to_process) > 1:
            # Add to processing queue
            queue_result = await queue_service.add_to_queue(
                urls=urls_to_process,
                batch_size=request.batch_size,
                metadata={
                    'prefix': request.prefix,
                    'sample_rate': request.sample_rate,
                    'upload_to_s3': request.upload_to_s3,
                    'original_request_metadata': request.metadata
                }
            )
            
            if queue_result['success']:
                return EnhancedBatchExtractionResult(
                    success=True,
                    queue_based=True,
                    queue_id=queue_result['data']['queue_id'],
                    immediate_processing=False,
                    skipped_existing=skipped_count,
                    message=f"Added {len(urls_to_process)} URLs to processing queue. {skipped_count} URLs skipped (already processed).",
                    data=queue_result['data']
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to add URLs to queue: {queue_result['error']}"
                )
        
        # Process immediately (single URL or disabled queue)
        else:
            if request.sample_rate:
                audio_service.sample_rate = request.sample_rate
            
            # Process URLs sequentially with database tracking
            results = []
            successful_count = 0
            failed_count = 0
            
            for i, url in enumerate(urls_to_process):
                try:
                    # Create database record
                    if db_service.is_available():
                        video_info = audio_service.get_video_info(url)
                        video_id = video_info['data'].get('video_id') if video_info['success'] else None
                        video_title = video_info['data'].get('title') if video_info['success'] else None
                        
                        await db_service.create_url_record(
                            youtube_url=url,
                            video_id=video_id,
                            video_title=video_title,
                            metadata=request.metadata
                        )
                        await db_service.update_url_status(url, 'processing')
                    
                    # Extract audio
                    filename = f"{request.prefix}_{i+1:03d}" if request.prefix else None
                    result = audio_service.extract_audio(
                        youtube_url=url,
                        output_filename=filename,
                        upload_to_s3=request.upload_to_s3
                    )
                    
                    if result['success']:
                        successful_count += 1
                        results.append(result['data'])
                        
                        # Update database
                        if db_service.is_available():
                            data = result['data']
                            await db_service.update_url_status(
                                url, 'completed',
                                file_path=data.get('output_path'),
                                s3_url=data.get('s3_url'),
                                s3_key=data.get('s3_key'),
                                metadata=data
                            )
                    else:
                        failed_count += 1
                        
                        # Update database
                        if db_service.is_available():
                            await db_service.update_url_status(
                                url, 'failed',
                                error_message=result['error']
                            )
                            
                except Exception as e:
                    failed_count += 1
                    
                    # Update database
                    if db_service.is_available():
                        try:
                            await db_service.update_url_status(
                                url, 'failed',
                                error_message=str(e)
                            )
                        except:
                            pass
            
            return EnhancedBatchExtractionResult(
                success=successful_count > 0,
                queue_based=False,
                immediate_processing=True,
                skipped_existing=skipped_count,
                message=f"Batch extraction completed. {successful_count}/{len(urls_to_process)} successful, {skipped_count} skipped.",
                data={
                    'extracted_files': results,
                    'total_requested': len(urls),
                    'urls_to_process': len(urls_to_process),
                    'successful_extractions': successful_count,
                    'failed_extractions': failed_count,
                    'skipped_existing': skipped_count
                }
            )
        
    except HTTPException:
        raise
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


# Queue Management Endpoints
@router.post("/queue/add", response_model=QueueResponse)
async def add_to_queue(request: QueueRequest):
    """
    Add URLs to the processing queue.
    
    Args:
        request: QueueRequest with URLs and configuration
        
    Returns:
        QueueResponse: Queue addition result with queue ID
    """
    try:
        if not db_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service not available for queue operations"
            )
        
        urls = [str(url) for url in request.urls]
        result = await queue_service.add_to_queue(
            urls=urls,
            batch_size=request.batch_size,
            metadata=request.metadata
        )
        
        if result['success']:
            return QueueResponse(
                success=True,
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


@router.get("/queue/{queue_id}/status", response_model=QueueStatusResponse)
async def get_queue_status(queue_id: str):
    """
    Get status of a specific processing queue.
    
    Args:
        queue_id: Queue identifier
        
    Returns:
        QueueStatusResponse: Queue status information
    """
    try:
        if not db_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service not available for queue operations"
            )
        
        result = await queue_service.get_queue_status(queue_id)
        
        if result['success']:
            return QueueStatusResponse(
                success=True,
                data=result['data']
            )
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


@router.get("/queue/list", response_model=QueueListResponse)
async def list_queues(status: str = None, limit: int = 100):
    """
    List processing queues with optional status filter.
    
    Args:
        status: Optional status filter (queued, processing, completed, failed, cancelled)
        limit: Maximum number of queues to return
        
    Returns:
        QueueListResponse: List of queues
    """
    try:
        if not db_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service not available for queue operations"
            )
        
        result = await queue_service.list_queues(status=status, limit=limit)
        
        if result['success']:
            return QueueListResponse(
                success=True,
                data=result['data'],
                total_count=result['total_count']
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


@router.delete("/queue/{queue_id}/cancel", response_model=QueueCancellationResponse)
async def cancel_queue(queue_id: str):
    """
    Cancel a queued processing job.
    
    Args:
        queue_id: Queue identifier to cancel
        
    Returns:
        QueueCancellationResponse: Cancellation result
    """
    try:
        if not db_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service not available for queue operations"
            )
        
        result = await queue_service.cancel_queue(queue_id)
        
        if result['success']:
            return QueueCancellationResponse(
                success=True,
                message=result['message']
            )
        else:
            return QueueCancellationResponse(
                success=False,
                message="Failed to cancel queue",
                error=result['error']
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Database Management Endpoints
@router.get("/database/url-check")
async def check_url_in_database(url: str):
    """
    Check if a YouTube URL exists in the processing database.
    
    Args:
        url: YouTube URL to check
        
    Returns:
        URLCheckResponse: URL existence and record information
    """
    try:
        if not db_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service not available"
            )
        
        result = await db_service.check_url_exists(url)
        
        if result['success']:
            return URLCheckResponse(
                exists=result['exists'],
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


@router.get("/database/history", response_model=ProcessingHistoryResponse)
async def get_processing_history(limit: int = 100, status: str = None):
    """
    Get URL processing history from database.
    
    Args:
        limit: Maximum number of records to return
        status: Optional status filter
        
    Returns:
        ProcessingHistoryResponse: Processing history records
    """
    try:
        if not db_service.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service not available"
            )
        
        result = await db_service.get_processing_history(limit=limit, status=status)
        
        if result['success']:
            return ProcessingHistoryResponse(
                success=True,
                data=result['data'],
                total_count=result['total_count']
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


@router.get("/database/status")
async def database_status():
    """
    Get database and queue service status.
    
    Returns:
        Database and queue service status information
    """
    return {
        "database_available": db_service.is_available(),
        "queue_processing": queue_service.is_processing if hasattr(queue_service, 'is_processing') else False,
        "active_queues": len(queue_service.active_queues) if hasattr(queue_service, 'active_queues') else 0,
        "completed_queues": len(queue_service.completed_queues) if hasattr(queue_service, 'completed_queues') else 0,
        "database_url_configured": bool(config.get('database_url')),
        "queue_service_initialized": hasattr(queue_service, 'processing_queue')
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