"""
Teacher-specific dashboard endpoints for managing classes and audio content.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Dict, Any, Optional

from app.core.dependencies import get_current_teacher
from app.utils.teacher_validation import (
    get_teacher_classes_summary,
    validate_teacher_owns_class,
    validate_teacher_owns_audio,
    TeacherActions
)
from app.services.class_service import class_service
from app.services.audio_service import lesson_service

router = APIRouter()


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_teacher_dashboard(
    current_teacher: dict = Depends(get_current_teacher)
) -> Dict[str, Any]:
    """Get teacher dashboard with summary of classes and activities"""
    try:
        teacher_id = current_teacher.get("id")
        
        # Get classes summary
        classes_summary = await get_teacher_classes_summary(teacher_id)
        
        # Get recent audio uploads (last 10)
        recent_audio = []
        for class_data in classes_summary["classes"][:5]:  # Check recent 5 classes
            class_id = class_data.get("id")
            if class_id:
                audio_recordings = await lesson_service.get_audio_recordings_by_class(class_id, skip=0, limit=2)
                recent_audio.extend(audio_recordings[:2])  # Get 2 most recent per class
        
        # Sort by creation date and limit
        recent_audio = sorted(
            recent_audio, 
            key=lambda x: x.get("created_at", ""), 
            reverse=True
        )[:10]
        
        return {
            "teacher_info": {
                "id": teacher_id,
                "name": current_teacher.get("full_name", ""),
                "email": current_teacher.get("email", "")
            },
            "statistics": {
                "total_classes": classes_summary["total_classes"],
                "active_classes": classes_summary["active_classes"],
                "total_audio_uploads": len(recent_audio)
            },
            "recent_classes": classes_summary["classes"][:5],
            "recent_audio_uploads": recent_audio
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load teacher dashboard: {str(e)}"
        )


@router.get("/my-classes", response_model=List[Dict[str, Any]])
async def get_my_classes(
    current_teacher: dict = Depends(get_current_teacher),
    limit: int = Query(50, ge=1, le=100, description="Number of classes to return")
) -> List[Dict[str, Any]]:
    """Get all classes created by the current teacher"""
    try:
        teacher_id = current_teacher.get("id")
        
        # Get all teacher's classes
        classes = await class_service.get_classes_by_teacher(teacher_id, limit)
        
        return classes
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get teacher classes: {str(e)}"
        )


@router.get("/class/{class_id}/audio", response_model=List[Dict[str, Any]])
async def get_class_audio_recordings(
    class_id: str,
    current_teacher: dict = Depends(get_current_teacher)
) -> List[Dict[str, Any]]:
    """Get all audio recordings for a specific class (teacher must own the class)"""
    try:
        teacher_id = current_teacher.get("id")
        
        # Validate teacher owns the class
        await validate_teacher_owns_class(teacher_id, class_id)
        
        # Get audio recordings
        recordings = await lesson_service.get_audio_recordings_by_class(class_id, skip=0, limit=100)
        
        return recordings
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get class audio recordings: {str(e)}"
        )


@router.get("/audio/{audio_id}/details", response_model=Dict[str, Any])
async def get_audio_details(
    audio_id: str,
    current_teacher: dict = Depends(get_current_teacher)
) -> Dict[str, Any]:
    """Get detailed information about a specific audio recording (teacher must own it)"""
    try:
        teacher_id = current_teacher.get("id")
        
        # Validate teacher owns the audio
        audio_data = await validate_teacher_owns_audio(teacher_id, audio_id)
        
        return audio_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audio details: {str(e)}"
        )


@router.get("/permissions/check", response_model=Dict[str, Any])
async def check_teacher_permissions(
    class_id: Optional[str] = Query(None, description="Class ID to check permissions for"),
    audio_id: Optional[str] = Query(None, description="Audio ID to check permissions for"),
    current_teacher: dict = Depends(get_current_teacher)
) -> Dict[str, Any]:
    """Check what permissions the teacher has for specific resources"""
    try:
        teacher_id = current_teacher.get("id")
        permissions = {
            "teacher_id": teacher_id,
            "can_create_classes": True,  # All teachers can create classes
            "can_upload_audio": True     # All teachers can upload audio
        }
        
        if class_id:
            permissions["can_modify_class"] = await TeacherActions.can_modify_class(teacher_id, class_id)
            permissions["can_upload_audio_to_class"] = await TeacherActions.can_upload_audio(teacher_id, class_id)
        
        if audio_id:
            permissions["can_delete_audio"] = await TeacherActions.can_delete_audio(teacher_id, audio_id)
        
        return permissions
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check permissions: {str(e)}"
        )


@router.get("/statistics", response_model=Dict[str, Any])
async def get_teacher_statistics(
    current_teacher: dict = Depends(get_current_teacher)
) -> Dict[str, Any]:
    """Get detailed statistics for the teacher"""
    try:
        teacher_id = current_teacher.get("id")
        
        # Get classes summary
        classes_summary = await get_teacher_classes_summary(teacher_id)
        
        # Count audio recordings across all classes
        total_audio = 0
        total_duration = 0
        
        for class_data in classes_summary["classes"]:
            class_id = class_data.get("id")
            if class_id:
                recordings = await lesson_service.get_audio_recordings_by_class(class_id, skip=0, limit=100)
                total_audio += len(recordings)
                
                # Sum up durations if available
                for recording in recordings:
                    duration = recording.get("duration", 0)
                    if duration:
                        total_duration += duration
        
        return {
            "teacher_id": teacher_id,
            "classes": {
                "total": classes_summary["total_classes"],
                "active": classes_summary["active_classes"],
                "inactive": classes_summary["total_classes"] - classes_summary["active_classes"]
            },
            "audio": {
                "total_recordings": total_audio,
                "total_duration_minutes": total_duration
            },
            "account_info": {
                "name": current_teacher.get("full_name", ""),
                "email": current_teacher.get("email", ""),
                "role": current_teacher.get("role", ""),
                "created_at": current_teacher.get("created_at", "")
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get teacher statistics: {str(e)}"
        )

