from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from typing import List
from app.services.audio_service import lesson_service
from app.services.transcription_service import transcription_service
from app.core.dependencies import require_student_or_teacher
from app.utils.teacher_validation import validate_teacher_owns_class
from app.utils.file_optimization import file_optimizer, audio_optimizer
from app.services.class_service import class_service
import tempfile
import os

router = APIRouter()
@router.get("/lessons/{class_id}", response_model=List[dict])
async def get_lessons_by_class(
    class_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(require_student_or_teacher)
):
    """Get all lessons for a specific class.
    Access: teacher (owner) or enrolled student.
    Returns minimal fields: id and lecture_title.
    """
    # Access checks
    user_id = current_user.get("id")
    role = current_user.get("role")
    if role == "student":
        is_enrolled = await class_service.is_student_enrolled(class_id, user_id)
        if not is_enrolled:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        # teacher
        await validate_teacher_owns_class(user_id, class_id)
    
    try:
        lessons = await lesson_service.list_lessons_minimal_by_class(class_id, limit, skip)
        # Ensure only id and lecture_title are returned
        return [{"id": l.get("id"), "lecture_title": l.get("lecture_title")} for l in lessons]
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get lessons: {str(e)}"
        )

@router.delete("/lessons/{lesson_id}")
async def delete_lesson(
    lesson_id: str,
    current_teacher: dict = Depends(require_student_or_teacher)
):
    """Delete a specific lesson (Teachers only - must own the class)"""
    try:
        # First, get the lesson to find the class_id and validate ownership
        lesson = await lesson_service.get_audio_recording(lesson_id)
        
        if not lesson:
            raise HTTPException(
                status_code=404,
                detail=f"Lesson {lesson_id} not found"
            )
        
        class_id = lesson.get("class_id")
        if not class_id:
            raise HTTPException(
                status_code=400,
                detail="Lesson has no associated class"
            )
        
        # Validate that the teacher owns this class
        await validate_teacher_owns_class(current_teacher["id"], class_id)
        
        # Delete the lesson with embeddings cleanup
        success = await lesson_service.delete_audio_recording(lesson_id)
        
        if success:
            return {
                "message": "Lesson deleted successfully",
                "data": {
                    "lesson_id": lesson_id,
                    "class_id": class_id,
                    "lecture_title": lesson.get("lecture_title", ""),
                    "deleted": True
                }
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete lesson"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to delete lesson: {str(e)}"
        )

@router.delete("/recordings/{audio_id}")
async def delete_audio_recording(
    audio_id: str,
    current_teacher: dict = Depends(require_student_or_teacher)
):
    """Delete an audio recording and its embeddings (Teachers only)"""
    try:
        success = await lesson_service.delete_audio_recording(audio_id)
        if success:
            return {"message": "Audio recording and embeddings deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete audio recording")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@router.get("/recordings/{audio_id}/url")
async def get_audio_file_url(audio_id: str, expires_in: int = 0):
    """Get a presigned URL for an audio file"""
    try:
        url = await lesson_service.get_audio_file_url(audio_id, expires_in)
        if url:
            return {"url": url, "expires_in": expires_in}
        else:
            raise HTTPException(status_code=404, detail="Audio file not found or URL generation failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file URL: {str(e)}")

@router.post("/transcribe/{audio_id}")
async def transcribe_existing_audio(
    audio_id: str,
    language: str = Form("english", description="Transcription language: 'english' or 'khmer'"),
    current_teacher: dict = Depends(require_student_or_teacher)
):
    """Manually transcribe an existing audio recording"""
    try:
        # Validate language parameter
        if language not in ["english", "khmer"]:
            raise HTTPException(status_code=400, detail="Language must be 'english' or 'khmer'")
        
        # Get audio recording
        recording = await lesson_service.get_audio_recording(audio_id)
        if not recording:
            raise HTTPException(status_code=404, detail="Audio recording not found")
        
        # Download audio file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix=recording.get("file_extension", ".mp3")) as temp_file:
            temp_path = temp_file.name
        
        try:
            download_success = await lesson_service.download_audio_file(audio_id, temp_path)
            if not download_success:
                raise HTTPException(status_code=500, detail="Failed to download audio file for transcription")
            
            # Transcribe the audio file
            transcription_result = await transcription_service.transcribe_audio(
                file_path=temp_path,
                language=language
            )
            
            if not transcription_result or not transcription_result.get("success"):
                error_msg = transcription_result.get("error", "Unknown transcription error") if transcription_result else "Transcription service unavailable"
                raise HTTPException(status_code=500, detail=f"Transcription failed: {error_msg}")
            
            # Update the audio record with transcription and embeddings
            transcription_text = transcription_result.get("transcription", "")
            if transcription_text:
                update_result = await lesson_service.update_transcription(
                    audio_id=audio_id,
                    transcription=transcription_text
                )
                
                if update_result.get("success"):
                    return {
                        "message": "Audio transcribed successfully",
                        "data": {
                            "audio_id": audio_id,
                            "transcription": transcription_text,
                            "language": language,
                            "embeddings_updated": update_result.get("embeddings_updated", False)
                        }
                    }
                else:
                    return {
                        "message": "Audio transcribed but embedding update failed",
                        "data": {
                            "audio_id": audio_id,
                            "transcription": transcription_text,
                            "language": language,
                            "embedding_error": update_result.get("error", "Unknown embedding error")
                        }
                    }
            else:
                raise HTTPException(status_code=500, detail="Empty transcription result")
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@router.get("/lessons/class/{class_id}/count")
async def get_lessons_count_by_class(
    class_id: str,
    current_teacher: dict = Depends(require_student_or_teacher)
):
    """Get the count of lessons for a specific class (Teachers only - must own the class)"""
    try:
        # Validate that the teacher owns this class
        await validate_teacher_owns_class(current_teacher["id"], class_id)
        
        # Get lessons count
        count = await lesson_service.get_lessons_count_by_class(class_id)
        
        return {
            "message": "Lessons count retrieved successfully",
            "data": {
                "class_id": class_id,
                "lessons_count": count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get lessons count: {str(e)}"
        )

@router.get("/debug/class-ownership/{class_id}")
async def debug_class_ownership(
    class_id: str,
    current_teacher: dict = Depends(require_student_or_teacher)
):
    """Debug endpoint to check class ownership validation"""
    try:
        from app.services.class_service import class_service
        
        teacher_id = current_teacher.get("id")
        
        # Get class data
        class_data = await class_service.get_class(class_id)
        
        if not class_data:
            return {
                "debug_info": {
                    "request_teacher_id": teacher_id,
                    "request_teacher_type": str(type(teacher_id)),
                    "class_id": class_id,
                    "class_found": False,
                    "class_data": None,
                    "ownership_match": False,
                    "error": "Class not found"
                }
            }
        
        class_teacher_id = class_data.get("teacher_id")
        ownership_match = class_teacher_id == teacher_id
        
        return {
            "debug_info": {
                "request_teacher_id": teacher_id,
                "request_teacher_type": str(type(teacher_id)),
                "class_id": class_id,
                "class_found": True,
                "class_teacher_id": class_teacher_id,
                "class_teacher_type": str(type(class_teacher_id)),
                "ownership_match": ownership_match,
                "teacher_data_from_token": current_teacher,
                "class_data": {
                    "id": class_data.get("id"),
                    "class_code": class_data.get("class_code"),
                    "subject": class_data.get("subject"),
                    "teacher_id": class_data.get("teacher_id"),
                    "teacher_name": class_data.get("teacher_name")
                }
            }
        }
        
    except Exception as e:
        return {
            "debug_info": {
                "error": str(e),
                "request_teacher_id": current_teacher.get("id") if current_teacher else None,
                "class_id": class_id
            }
        }