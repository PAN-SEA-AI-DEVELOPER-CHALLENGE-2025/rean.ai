from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from typing import List, Optional
import logging
from app.core.s3 import s3_service
from app.utils.helpers import sanitize_s3_metadata
import uuid
import os

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    folder: str = Query("uploads", description="S3 folder path")
):
    """Upload a file to S3 (No authentication required for testing)"""
    try:
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        s3_key = f"{folder}/test_user/{uuid.uuid4()}{file_extension}"
        
        # Save file temporarily
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Prepare metadata and sanitize for S3 (S3 only supports ASCII characters in metadata)
        metadata = {
            "user_id": "test_user",
            "original_filename": file.filename,
            "content_type": file.content_type,
            "test_mode": "true"
        }
        sanitized_metadata = sanitize_s3_metadata(metadata)
        
        # Upload to S3
        upload_success = await s3_service.upload_file(
            file_path=temp_path,
            s3_key=s3_key,
            content_type=file.content_type,
            metadata=sanitized_metadata
        )
        
        # Clean up temp file
        os.remove(temp_path)
        
        if upload_success:
            return {
                "message": "File uploaded successfully",
                "s3_key": s3_key,
                "s3_url": s3_service.get_file_url(s3_key),
                "filename": file.filename,
                "file_size": os.path.getsize(temp_path) if os.path.exists(temp_path) else "unknown"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to upload file to S3")
            
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/files")
async def list_files(
    prefix: str = Query("", description="S3 prefix/folder path"),
    max_keys: int = Query(100, description="Maximum number of files to return")
):
    """List files in S3 (No authentication required for testing)"""
    try:
        files = s3_service.list_files(prefix=prefix, max_keys=max_keys)
        return {"files": files, "count": len(files)}
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.get("/file/{s3_key:path}/url")
async def get_file_url(
    s3_key: str,
    expires_in: int = Query(3600, description="URL expiration time in seconds")
):
    """Get a presigned URL for a file (No authentication required for testing)"""
    try:
        url = s3_service.get_file_url(s3_key, expires_in)
        if url:
            return {"url": url, "expires_in": expires_in, "s3_key": s3_key}
        else:
            raise HTTPException(status_code=404, detail="File not found or URL generation failed")
    except Exception as e:
        logger.error(f"Error getting file URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get file URL: {str(e)}")


@router.delete("/file/{s3_key:path}")
async def delete_file(s3_key: str):
    """Delete a file from S3 (No authentication required for testing)"""
    try:
        delete_success = await s3_service.delete_file(s3_key)
        if delete_success:
            return {"message": "File deleted successfully", "s3_key": s3_key}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete file from S3")
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


@router.get("/file/{s3_key:path}/metadata")
async def get_file_metadata(s3_key: str):
    """Get metadata for a file (No authentication required for testing)"""
    try:
        metadata = s3_service.get_file_metadata(s3_key)
        if metadata:
            return {"s3_key": s3_key, "metadata": metadata}
        else:
            raise HTTPException(status_code=404, detail="File not found or metadata unavailable")
    except Exception as e:
        logger.error(f"Error getting file metadata: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get file metadata: {str(e)}")


@router.get("/file/{s3_key:path}/exists")
async def check_file_exists(s3_key: str):
    """Check if a file exists in S3 (No authentication required for testing)"""
    try:
        exists = s3_service.file_exists(s3_key)
        return {"s3_key": s3_key, "exists": exists}
    except Exception as e:
        logger.error(f"Error checking file existence: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check file existence: {str(e)}")


@router.get("/test")
async def test_s3_connection():
    """Test S3 connection and basic operations"""
    try:
        # Test basic operations
        bucket_name = s3_service.bucket_name
        region = s3_service.region
        
        # Try to list files (this will test the connection)
        files = s3_service.list_files(prefix="", max_keys=1)
        
        return {
            "message": "S3 connection successful",
            "bucket": bucket_name,
            "region": region,
            "files_count": len(files),
            "status": "connected"
        }
    except Exception as e:
        logger.error(f"S3 connection test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"S3 connection failed: {str(e)}")
