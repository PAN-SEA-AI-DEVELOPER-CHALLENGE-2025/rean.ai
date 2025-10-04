from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List

from app.core.dependencies import require_student
from app.schemas.class_schemas import ClassResponse
from app.services.class_service import class_service
from app.services.audio_service import lesson_service


router = APIRouter()


@router.get("/classes", response_model=List[ClassResponse])
async def get_my_classes(
    limit: int = Query(50, ge=1, le=100, description="Number of classes to return"),
    offset: int = Query(0, ge=0, description="Number of classes to skip"),
    current_student: dict = Depends(require_student),
):
    """List classes for the currently authenticated student (only their enrollments)."""
    student_id = current_student.get("id")
    return await class_service.get_classes_for_student(student_id, limit, offset)


@router.get("/classes/{class_id}/lessons", response_model=List[dict])
async def get_my_class_lessons(
    class_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_student: dict = Depends(require_student),
):
    """List lessons within one of the student's enrolled classes."""
    student_id = current_student.get("id")
    is_enrolled = await class_service.is_student_enrolled(class_id, student_id)
    if not is_enrolled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return await lesson_service.get_audio_recordings_by_class(class_id, skip=skip, limit=limit)


