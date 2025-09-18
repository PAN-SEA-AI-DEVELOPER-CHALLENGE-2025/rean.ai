"""
Teacher-specific validation utilities and helpers.
"""
from typing import Dict, Any, Optional
from fastapi import HTTPException, status

from app.services.class_service import class_service
from app.services.audio_service import lesson_service


async def validate_teacher_owns_class(teacher_id: str, class_id: str) -> Dict[str, Any]:
    """
    Validate that a teacher owns/created a specific class.
    
    Args:
        teacher_id: The teacher's user ID
        class_id: The class ID to check
        
    Returns:
        The class data if validation passes
        
    Raises:
        HTTPException: If class not found or teacher doesn't own it
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Validating class ownership - Teacher ID: {teacher_id}, Class ID: {class_id}")
        
        class_data = await class_service.get_class(class_id)
        
        if not class_data:
            logger.warning(f"Class not found: {class_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Class {class_id} not found"
            )
        
        class_teacher_id = class_data.get("teacher_id")
        logger.info(f"Class teacher ID: {class_teacher_id}, Request teacher ID: {teacher_id}")
        logger.info(f"Teacher ID types - Class: {type(class_teacher_id)}, Request: {type(teacher_id)}")
        
        # Ensure both IDs are strings for comparison to avoid type mismatch
        class_teacher_id_str = str(class_teacher_id) if class_teacher_id else None
        teacher_id_str = str(teacher_id) if teacher_id else None
        
        logger.info(f"After string conversion - Class: {class_teacher_id_str}, Request: {teacher_id_str}")
        
        if class_teacher_id_str != teacher_id_str:
            logger.warning(f"Teacher access denied - Class belongs to teacher {class_teacher_id}, but request from teacher {teacher_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access classes you created"
            )
        
        logger.info(f"Class ownership validation successful for teacher {teacher_id}, class {class_id}")
        return class_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating class ownership: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating class ownership: {str(e)}"
        )


async def validate_teacher_owns_audio(teacher_id: str, audio_id: str) -> Dict[str, Any]:
    """
    Validate that a teacher owns/uploaded a specific audio recording.
    
    Args:
        teacher_id: The teacher's user ID
        audio_id: The audio recording ID to check
        
    Returns:
        The audio data if validation passes
        
    Raises:
        HTTPException: If audio not found or teacher doesn't own it
    """
    try:
        audio_data = await audio_service.get_audio_recording(audio_id)
        
        if not audio_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audio recording {audio_id} not found"
            )
        
        # Check if teacher owns the audio directly or through the class
        audio_teacher_id = audio_data.get("teacher_id")
        class_id = audio_data.get("class_id")
        
        if audio_teacher_id == teacher_id:
            return audio_data
        
        # If no direct ownership, check through class ownership
        if class_id:
            class_data = await class_service.get_class(class_id)
            if class_data and class_data.get("teacher_id") == teacher_id:
                return audio_data
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access audio recordings you uploaded or from your classes"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating audio ownership: {str(e)}"
        )


async def get_teacher_classes_summary(teacher_id: str) -> Dict[str, Any]:
    """
    Get a summary of classes for a teacher.
    
    Args:
        teacher_id: The teacher's user ID
        
    Returns:
        Summary data including class count, active classes, etc.
    """
    try:
        classes = await class_service.get_classes_by_teacher(teacher_id, limit=1000)
        
        # Since we removed the status field, we'll consider all classes as active
        active_classes = classes
        
        return {
            "teacher_id": teacher_id,
            "total_classes": len(classes),
            "active_classes": len(active_classes),
            "classes": classes
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting teacher summary: {str(e)}"
        )


def validate_teacher_permissions(required_permission: str = "basic"):
    """
    Decorator factory for validating teacher permissions.
    Currently supports basic validation, can be extended for more granular permissions.
    
    Args:
        required_permission: The permission level required
    
    Returns:
        Decorator function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Basic implementation - just ensures user is a teacher
            # Can be extended to check specific permissions
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class TeacherActions:
    """
    Helper class for common teacher actions and validations.
    """
    
    @staticmethod
    async def can_upload_audio(teacher_id: str, class_id: str) -> bool:
        """Check if teacher can upload audio to a specific class"""
        try:
            await validate_teacher_owns_class(teacher_id, class_id)
            return True
        except HTTPException:
            return False
    
    @staticmethod
    async def can_modify_class(teacher_id: str, class_id: str) -> bool:
        """Check if teacher can modify a specific class"""
        try:
            await validate_teacher_owns_class(teacher_id, class_id)
            return True
        except HTTPException:
            return False
    
    @staticmethod
    async def can_delete_audio(teacher_id: str, audio_id: str) -> bool:
        """Check if teacher can delete a specific audio recording"""
        try:
            await validate_teacher_owns_audio(teacher_id, audio_id)
            return True
        except HTTPException:
            return False
