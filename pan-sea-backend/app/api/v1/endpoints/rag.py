from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.services.rag_service import rag_service
from app.services.auth_service import auth_service
from app.database.database import db_manager
from app.services.class_service import class_service

router = APIRouter()
security = HTTPBearer()


class SearchAudioRequest(BaseModel):
    query: str
    class_id: Optional[str] = None
    lesson_id: Optional[str] = None
    limit: int = 10
    similarity_threshold: float = 0.7


class GetAudioByClassRequest(BaseModel):
    class_id: str
    limit: int = 10


class AskRequest(BaseModel):
    question: str
    top_k: int = 8


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


@router.get("/lessons/{lesson_id}/index-status", response_model=Dict[str, Any])
async def get_index_status(lesson_id: str, current_user: dict = Depends(get_current_user)):
    try:
        return await rag_service.get_index_status(lesson_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get index status: {str(e)}"
        )


@router.post("/lessons/{lesson_id}/ask", response_model=Dict[str, Any])
async def ask_question(lesson_id: str, request: AskRequest, current_user: dict = Depends(get_current_user)):
    try:
        # Access control: teacher owner of the class or enrolled student
        rows = await db_manager.execute_query(
            """
            SELECT l.class_id, c.teacher_id
            FROM lessons l
            JOIN classes c ON l.class_id::uuid = c.id
            WHERE l.id = $1
            """,
            lesson_id,
        )
        if not rows:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
        class_id = rows[0].get("class_id")
        teacher_id = str(rows[0].get("teacher_id")) if rows[0].get("teacher_id") else None
        user_id = current_user.get("id")
        is_owner = teacher_id == str(user_id)
        is_enrolled = await class_service.is_student_enrolled(class_id, user_id)
        if not (is_owner or is_enrolled):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        result = await rag_service.answer_question(lesson_id, request.question, request.top_k)
        if not result.get("success") and result.get("error") == "no_chunks_found":
            # Return 200 with informative message
            return {"success": False, "message": "No chunks indexed for this lesson yet. Reindex and try again.", "error": result.get("error")}
        if not result.get("success"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error", "Unknown error"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to answer question: {str(e)}"
        )


@router.post("/lessons/{lesson_id}/reindex", response_model=Dict[str, Any])
async def reindex_lesson(lesson_id: str, current_user: dict = Depends(get_current_user)):
    try:
        rows = await db_manager.execute_query(
            "SELECT transcription FROM lessons WHERE id = $1", lesson_id
        )
        if not rows:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
        transcription = rows[0].get("transcription")
        if not transcription:
            return {"success": False, "message": "Lesson has no transcription to index"}
        # Enqueue background indexing
        await rag_service.indexer.enqueue_indexing(lesson_id, transcription)
        return {"success": True, "message": "Indexing enqueued"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reindex lesson: {str(e)}"
        )
