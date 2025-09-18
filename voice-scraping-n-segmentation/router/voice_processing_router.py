"""
Voice Processing Router

This module provides FastAPI endpoints for the voice processing pipeline
including VAD, transcription, MFA, and CSV export functionality.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from fastapi.responses import FileResponse, JSONResponse
import os
import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from service.voice_processing_service import VoiceProcessingService
from config.settings import get_config
from router.models import (
    VoiceProcessingRequest, VoiceProcessingResult, AsyncProcessingRequest,
    AsyncProcessingResponse, SessionListResponse, SessionDetailsResponse,
    ServiceStatusResponse, SuccessResponse, ErrorResponse
)


# Initialize configuration and services
config = get_config()
voice_processing_service = VoiceProcessingService(config)

# Create router instance
router = APIRouter(prefix="/api/voice", tags=["voice-processing"])

# Store for background tasks (in production, use a proper task queue like Celery)
background_tasks_store = {}


@router.get("/status", response_model=ServiceStatusResponse)
async def get_service_status():
    """
    Get status of all voice processing services.
    
    Returns:
        ServiceStatusResponse: Status of all services
    """
    try:
        status_info = voice_processing_service.get_service_status()
        return ServiceStatusResponse(**status_info)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/process", response_model=VoiceProcessingResult)
async def process_audio(request: VoiceProcessingRequest):
    """
    Process audio file through the voice processing pipeline.
    
    Args:
        request: Voice processing request parameters
        
    Returns:
        VoiceProcessingResult: Processing results
        
    Raises:
        HTTPException: If processing fails
    """
    try:
        # Validate request
        if not request.s3_key and not request.local_file_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either s3_key or local_file_path must be provided"
            )
        
        if request.s3_key and request.local_file_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only one of s3_key or local_file_path should be provided"
            )
        
        # Prepare processing configuration  
        processing_config = {
            'use_mfa': request.use_mfa,
            'save_audio_chunks': request.save_chunks,
            'vad': {
                'vad_aggressiveness': request.vad_aggressiveness,
                'min_chunk_duration': request.min_chunk_duration,
                'max_chunk_duration': request.max_chunk_duration
            },
            'use_google_stt': getattr(request, 'use_google_stt', True),
            'use_external_transcription': getattr(request, 'use_external_transcription', False)
        }
        # Include upload flag if provided
        processing_config['upload_chunks_to_s3'] = getattr(request, 'upload_chunks_to_s3', False)
        processing_config['upload_csv_to_s3'] = getattr(request, 'upload_csv_to_s3', False)
        
        # Update service configuration
        if request.use_mfa is not None:
            voice_processing_service.use_mfa = request.use_mfa
        if request.save_chunks is not None:
            voice_processing_service.save_chunks = request.save_chunks
        
        # Process based on input type
        if request.s3_key:
            result = voice_processing_service.process_s3_file(
                request.s3_key, processing_config
            )
        else:
            # Check if local file exists
            if not os.path.exists(request.local_file_path):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Local file not found: {request.local_file_path}"
                )
            
            result = voice_processing_service.process_local_file(
                request.local_file_path, processing_config=processing_config
            )
        
        if result['success']:
            return VoiceProcessingResult(**result)
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


@router.post("/process-async", response_model=AsyncProcessingResponse)
async def process_audio_async(
    request: AsyncProcessingRequest,
    background_tasks: BackgroundTasks
):
    """
    Process audio file asynchronously through the voice processing pipeline.
    
    Args:
        request: Async processing request parameters
        background_tasks: FastAPI background tasks
        
    Returns:
        AsyncProcessingResponse: Task information
    """
    try:
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Store initial task info
        background_tasks_store[task_id] = {
            'task_id': task_id,
            'status': 'pending',
            'created_at': datetime.now(),
            'result': None,
            'error': None
        }
        
        # Define background processing function
        def process_task():
            try:
                # Update status
                background_tasks_store[task_id]['status'] = 'processing'
                
                # Process the file
                result = voice_processing_service.process_s3_file(
                    request.s3_key,
                    request.processing_config
                )
                
                # Update with result
                background_tasks_store[task_id].update({
                    'status': 'completed' if result['success'] else 'failed',
                    'result': result if result['success'] else None,
                    'error': result.get('error') if not result['success'] else None,
                    'completed_at': datetime.now()
                })
                
                # TODO: Send notification if notification_url is provided
                
            except Exception as e:
                background_tasks_store[task_id].update({
                    'status': 'failed',
                    'error': str(e),
                    'completed_at': datetime.now()
                })
        
        # Add task to background processing
        background_tasks.add_task(process_task)
        
        return AsyncProcessingResponse(
            task_id=task_id,
            status='accepted',
            message='Processing started in background',
            estimated_duration=120.0  # Rough estimate
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """
    Get status of an asynchronous processing task.
    
    Args:
        task_id: Task identifier
        
    Returns:
        Task status information
        
    Raises:
        HTTPException: If task not found
    """
    try:
        if task_id not in background_tasks_store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        task_info = background_tasks_store[task_id]
        
        return {
            'task_id': task_id,
            'status': task_info['status'],
            'created_at': task_info['created_at'].isoformat(),
            'completed_at': task_info.get('completed_at', '').isoformat() if task_info.get('completed_at') else None,
            'result': task_info.get('result'),
            'error': task_info.get('error')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(limit: int = 50):
    """
    List recent processing sessions.
    
    Args:
        limit: Maximum number of sessions to return
        
    Returns:
        SessionListResponse: List of processing sessions
    """
    try:
        sessions = voice_processing_service.list_processing_sessions(limit)
        
        return SessionListResponse(
            sessions=sessions,
            total_count=len(sessions)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/sessions/{session_id}", response_model=SessionDetailsResponse)
async def get_session_details(session_id: str):
    """
    Get detailed information about a processing session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        SessionDetailsResponse: Session details
        
    Raises:
        HTTPException: If session not found
    """
    try:
        session_details = voice_processing_service.get_session_details(session_id)
        
        if session_details is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return SessionDetailsResponse(
            success=True,
            data=session_details
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/sessions/{session_id}/report")
async def download_session_report(session_id: str):
    """
    Download a session report as a text file.
    
    Args:
        session_id: Session identifier
        
    Returns:
        FileResponse: Session report file
        
    Raises:
        HTTPException: If session not found or report generation fails
    """
    try:
        # Check if session exists
        session_details = voice_processing_service.get_session_details(session_id)
        
        if session_details is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Generate report file
        report_filename = f"session_report_{session_id}.txt"
        report_path = os.path.join(config['temp_dir'], report_filename)
        
        success = voice_processing_service.csv_service.export_session_report(
            session_id, report_path
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate session report"
            )
        
        return FileResponse(
            path=report_path,
            filename=report_filename,
            media_type='text/plain'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/sessions/{session_id}/csv")
async def download_session_csv(session_id: str):
    """
    Download session data as CSV files (chunks and words).
    
    Args:
        session_id: Session identifier
        
    Returns:
        Information about available CSV files
        
    Raises:
        HTTPException: If session not found
    """
    try:
        # Check if session exists
        session_details = voice_processing_service.get_session_details(session_id)
        
        if session_details is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        csv_dir = voice_processing_service.csv_service.output_dir
        chunks_file = os.path.join(csv_dir, 'chunks.csv')
        words_file = os.path.join(csv_dir, 'words.csv')
        
        available_files = []
        if os.path.exists(chunks_file):
            available_files.append({
                'type': 'chunks',
                'filename': 'chunks.csv',
                'path': chunks_file,
                'download_url': f"/api/voice/download/chunks.csv"
            })
        
        if os.path.exists(words_file):
            available_files.append({
                'type': 'words',
                'filename': 'words.csv',
                'path': words_file,
                'download_url': f"/api/voice/download/words.csv"
            })
        
        return {
            'session_id': session_id,
            'available_files': available_files,
            'csv_directory': csv_dir
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/download/{filename}")
async def download_csv_file(filename: str):
    """
    Download a CSV file.
    
    Args:
        filename: Name of the CSV file to download
        
    Returns:
        FileResponse: The requested CSV file
        
    Raises:
        HTTPException: If file not found or access denied
    """
    try:
        # Validate filename (security)
        allowed_files = ['chunks.csv', 'words.csv', 'sessions.csv']
        if filename not in allowed_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File not allowed. Allowed files: {allowed_files}"
            )
        
        csv_dir = voice_processing_service.csv_service.output_dir
        file_path = os.path.join(csv_dir, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='text/csv'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/sessions/{session_id}", response_model=SuccessResponse)
async def delete_session_data(session_id: str):
    """
    Delete session data (CSV records only, not audio files).
    
    Args:
        session_id: Session identifier
        
    Returns:
        SuccessResponse: Deletion confirmation
        
    Raises:
        HTTPException: If session not found or deletion fails
    """
    try:
        # Check if session exists
        session_details = voice_processing_service.get_session_details(session_id)
        
        if session_details is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # TODO: Implement session data deletion
        # This would involve removing rows from CSV files that match the session_id
        # For now, return a placeholder response
        
        return SuccessResponse(
            message=f"Session data deletion requested for {session_id}",
            data={'session_id': session_id, 'note': 'Deletion functionality not yet implemented'}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/cleanup", response_model=SuccessResponse)
async def cleanup_temp_files():
    """
    Clean up temporary files and old background task data.
    
    Returns:
        SuccessResponse: Cleanup confirmation
    """
    try:
        # Clean up temporary files
        temp_dir = config.get('temp_dir', 'data/temp')
        if os.path.exists(temp_dir):
            import shutil
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except Exception as e:
                    # Continue with other files even if one fails
                    pass
        
        # Clean up old background tasks (keep only last 100)
        if len(background_tasks_store) > 100:
            # Sort by creation time and keep only recent ones
            sorted_tasks = sorted(
                background_tasks_store.items(),
                key=lambda x: x[1]['created_at'],
                reverse=True
            )
            
            # Keep only the 100 most recent
            recent_tasks = dict(sorted_tasks[:100])
            background_tasks_store.clear()
            background_tasks_store.update(recent_tasks)
        
        return SuccessResponse(
            message="Cleanup completed successfully",
            data={
                'temp_dir_cleaned': True,
                'background_tasks_cleaned': True,
                'remaining_tasks': len(background_tasks_store)
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
