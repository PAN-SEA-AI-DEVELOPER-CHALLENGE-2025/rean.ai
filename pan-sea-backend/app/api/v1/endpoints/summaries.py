from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
import re
from pydantic import BaseModel
import logging
from app.schemas.class_schemas import LessonSummaryCreate
from app.services.summary_service import summary_service
from app.services.auth_service import auth_service
from app.services.execute_content_service import execution_service
from app.core.llm import llm_service
from app.core.dependencies import require_student_or_teacher
from app.services.class_service import class_service
import os   

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


class TranscriptionRequest(BaseModel):
    transcription: str


class TranscriptionWithClassRequest(BaseModel):
    transcription: str
    class_id: str


class StudyQuestionsRequest(BaseModel):
    summary: str
    subject: str


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """Get current user from JWT token (optional)"""
    if not credentials:
        return None
    
    token = credentials.credentials
    user_data = await auth_service.verify_token(token)
    return user_data


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Get current user from JWT token"""
    token = credentials.credentials
    user_data = await auth_service.verify_token(token)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    return user_data


@router.get("/", response_model=List[dict])
async def get_summaries(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Get all summaries"""
    summaries = await summary_service.get_summaries(skip=skip, limit=limit)
    return summaries


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_summary(
    summary_data: LessonSummaryCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new class summary"""
    summary = await summary_service.create_summary(summary_data)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create summary"
        )
    return summary


@router.get("/{summary_id}", response_model=dict)
async def get_summary(
    summary_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific summary by ID"""
    summary = await summary_service.get_summary(summary_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not found"
        )
    return summary


@router.get("/class/{class_id}", response_model=List[dict])
async def get_class_summaries(
    class_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(require_student_or_teacher)
):
    """Get all summaries for a specific class (Teacher owner or enrolled student)."""
    user_id = current_user.get("id")
    role = current_user.get("role")
    if role == "student":
        is_enrolled = await class_service.is_student_enrolled(class_id, user_id)
        if not is_enrolled:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    else:
        # teacher: must own the class
        class_data = await class_service.get_class(class_id)
        if not class_data or str(class_data.get("teacher_id")) != str(user_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    summaries = await summary_service.get_class_summaries(class_id, skip=skip, limit=limit)
    return summaries


@router.get("/lesson/{lesson_id}", response_model=List[dict])
async def get_lesson_summaries(
    lesson_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(require_student_or_teacher)
):
    """Get all summaries for a specific lesson (Teacher owner or enrolled student)."""
    # First, get the lesson to find the class_id, then validate ownership
    from app.database.database import db_manager
    
    # Get lesson details to find the class_id
    lesson_query = """
        SELECT l.*, c.teacher_id 
        FROM lessons l
        JOIN classes c ON l.class_id::uuid = c.id
        WHERE l.id = CAST($1 AS uuid)
    """
    lesson_result = await db_manager.execute_query(lesson_query, lesson_id)
    
    if not lesson_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lesson {lesson_id} not found"
        )
    
    lesson_data = dict(lesson_result[0])
    class_id = lesson_data.get("class_id")
    
    # Access checks
    user_id = current_user.get("id")
    role = current_user.get("role")
    if role == "student":
        is_enrolled = await class_service.is_student_enrolled(class_id, user_id)
        if not is_enrolled:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    else:
        class_data = await class_service.get_class(class_id)
        if not class_data or str(class_data.get("teacher_id")) != str(user_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    summaries = await summary_service.get_lesson_summaries(lesson_id, skip=skip, limit=limit)
    return summaries


@router.get("/lesson/{lesson_id}/latest", response_model=dict)
async def get_latest_lesson_summary(
    lesson_id: str,
    current_user: dict = Depends(require_student_or_teacher)
):
    """Get the most recent summary for a specific lesson (Teacher owner or enrolled student)."""
    # First, get the lesson to find the class_id, then validate ownership
    from app.database.database import db_manager
    
    # Get lesson details to find the class_id
    lesson_query = """
        SELECT l.*, c.teacher_id 
        FROM lessons l
        JOIN classes c ON l.class_id::uuid = c.id
        WHERE l.id = CAST($1 AS uuid)
    """
    lesson_result = await db_manager.execute_query(lesson_query, lesson_id)
    
    if not lesson_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lesson {lesson_id} not found"
        )
    
    lesson_data = dict(lesson_result[0])
    class_id = lesson_data.get("class_id")
    
    # Access checks
    user_id = current_user.get("id")
    role = current_user.get("role")
    if role == "student":
        is_enrolled = await class_service.is_student_enrolled(class_id, user_id)
        if not is_enrolled:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    else:
        class_data = await class_service.get_class(class_id)
        if not class_data or str(class_data.get("teacher_id")) != str(user_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    summary = await summary_service.get_lesson_summary(lesson_id)
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No summary found for lesson {lesson_id}"
        )
    
    return summary


class TranscriptionWithSubjectRequest(BaseModel):
    transcription: str
    subject: Optional[str] = None


@router.post("/extract-key-points", response_model=dict)
async def extract_key_points(request: Request):
    """Extract key points from transcription text.

    This endpoint accepts either a JSON body with `transcription` and optional
    `subject`, or a raw text/plain body containing the transcription. If the
    incoming JSON is invalid (e.g. contains unescaped control characters), the
    raw body will be used and control characters will be stripped.
    """
    try:
        transcription = None
        subject = None

        # First try to parse as JSON (normal expected case)
        try:
            body = await request.json()
            if isinstance(body, dict):
                transcription = body.get("transcription")
                subject = body.get("subject")
            else:
                # unexpected JSON, fall back to string representation
                transcription = str(body)
        except Exception:
            # JSON parse failed (possibly invalid control chars) - read raw body
            raw = await request.body()
            text = raw.decode("utf-8", errors="replace")
            # Remove non-printable/control characters except common whitespace
            cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]+", " ", text)
            transcription = cleaned.strip()

        if not transcription:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No transcription provided"
            )

        key_points_response = await llm_service.extract_key_points(
            transcription=transcription,
            subject=subject
        )

        if not key_points_response or not key_points_response.get("key_points"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to extract key points from transcription"
            )

        return key_points_response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract key points: {str(e)}"
        )


@router.post("/generate-study-questions", response_model=List[str])
async def generate_study_questions(request: Request):
    """Generate study questions from class summary.

    Accepts a JSON body with `summary` and optional `subject`, or a raw
    text/plain body containing the summary. If incoming JSON is invalid, the
    raw body will be used and control characters will be stripped.
    """
    try:
        summary_text = None
        subject = None

        # Try normal JSON parsing first
        try:
            body = await request.json()
            if isinstance(body, dict):
                summary_text = body.get("summary")
                subject = body.get("subject")
            else:
                summary_text = str(body)
        except Exception:
            raw = await request.body()
            text = raw.decode("utf-8", errors="replace")
            # Remove non-printable/control characters except common whitespace
            cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]+", " ", text)
            summary_text = cleaned.strip()

        if not summary_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No summary provided"
            )

        questions = await llm_service.generate_study_questions(
            summary=summary_text,
            subject=subject
        )

        if not questions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to generate study questions"
            )

        return questions
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate study questions: {str(e)}"
        )


@router.put("/{summary_id}", response_model=dict)
async def update_summary(
    summary_id: str,
    summary_data: LessonSummaryCreate,
    current_user: dict = Depends(get_current_user)
):
    """Update a summary"""
    updated_summary = await summary_service.update_summary(summary_id, summary_data)
    if not updated_summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not found"
        )
    return updated_summary


@router.delete("/{summary_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_summary(
    summary_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a summary"""
    success = await summary_service.delete_summary(summary_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not found"
        )