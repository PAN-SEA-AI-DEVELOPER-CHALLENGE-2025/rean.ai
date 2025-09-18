from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List, Optional
from datetime import datetime

from app.services.class_service import class_service
from app.schemas.class_schemas import ClassCreate, ClassUpdate, ClassResponse
from app.core.dependencies import get_current_teacher, get_current_user, require_teacher, require_student

router = APIRouter()


@router.post("/", response_model=ClassResponse)
async def create_class(
    class_data: ClassCreate,
    current_teacher: dict = Depends(get_current_teacher)
):
    """Create a new class (Teachers only)"""
    try:
        # Convert Pydantic model to dict
        class_dict = class_data.model_dump()
        
        # Add teacher ID from authenticated user
        teacher_id = current_teacher.get("id")
        if not teacher_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Teacher ID not found in token"
            )
        class_dict['teacher_id'] = teacher_id
        
        
        result = await class_service.create_class(class_dict)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create class"
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create class: {str(e)}"
        )


@router.get("/{class_id}", response_model=ClassResponse)
async def get_class(class_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific class by ID. Students can only view classes they are enrolled in."""
    try:
        result = await class_service.get_class(class_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Class {class_id} not found"
            )
        # Enforce: students can only view classes they are enrolled in
        if current_user.get("role") == "student":
            user_id = current_user.get("id")
            is_enrolled = await class_service.is_student_enrolled(class_id, user_id)
            if not is_enrolled:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get class: {str(e)}"
        )


@router.get("/", response_model=List[ClassResponse])
async def get_classes(
    teacher_id: Optional[str] = Query(None, description="Filter by teacher ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of classes to return"),
    offset: int = Query(0, ge=0, description="Number of classes to skip")
):
    """Get classes with optional filters"""
    try:
        result = await class_service.get_classes(
            teacher_id=teacher_id,
            limit=limit,
            offset=offset
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get classes: {str(e)}"
        )


@router.get("/student/me", response_model=List[ClassResponse])
async def get_my_classes(
    limit: int = Query(50, ge=1, le=100, description="Number of classes to return"),
    offset: int = Query(0, ge=0, description="Number of classes to skip"),
    current_student: dict = Depends(require_student)
):
    """List classes for the currently authenticated student (only their enrollments)."""
    try:
        student_id = current_student.get("id")
        result = await class_service.get_classes_for_student(student_id, limit, offset)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get student classes: {str(e)}"
        )


@router.put("/{class_id}", response_model=ClassResponse)
async def update_class(
    class_id: str, 
    update_data: ClassUpdate,
    current_teacher: dict = Depends(get_current_teacher)
):
    """Update a class (Teachers only - own classes)"""
    try:
        # Convert Pydantic model to dict, excluding None values
        update_dict = update_data.model_dump(exclude_none=True)
        
        
        result = await class_service.update_class(class_id, update_dict)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Class {class_id} not found or failed to update"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update class: {str(e)}"
        )


@router.delete("/{class_id}")
async def delete_class(
    class_id: str,
    current_teacher: dict = Depends(get_current_teacher)
):
    """Delete a class (Teachers only - own classes)"""
    try:
        success = await class_service.delete_class(class_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Class {class_id} not found or failed to delete"
            )
        
        return {"message": f"Class {class_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete class: {str(e)}"
        )


@router.get("/teacher/{teacher_id}", response_model=List[ClassResponse])
async def get_classes_by_teacher(
    teacher_id: str,
    limit: int = Query(50, ge=1, le=100, description="Number of classes to return"),
    current_user: dict = Depends(get_current_user)
):
    """Get classes for a specific teacher.

    - Teachers (owner) and admins: full list.
    - Students: only classes they're enrolled in, filtered to that teacher.
    """
    try:
        role = current_user.get("role")
        user_id = current_user.get("id")

        # Teacher owner: can view all their classes
        if role == "teacher" and str(user_id) == str(teacher_id):
            return await class_service.get_classes_by_teacher(teacher_id, limit)

        # Admin: can view any teacher's classes
        if role == "admin":
            return await class_service.get_classes_by_teacher(teacher_id, limit)

        # Student: only see own enrollments for that teacher
        if role == "student":
            my_classes = await class_service.get_classes_for_student(user_id, limit, 0)
            return [c for c in my_classes if str(c.get("teacher_id")) == str(teacher_id)]

        # Other roles: deny
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get teacher classes: {str(e)}"
        )




@router.get("/search/query", response_model=List[ClassResponse])
async def search_classes(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=50, description="Number of results to return")
):
    """Search classes by class_code or subject"""
    try:
        result = await class_service.search_classes(q, limit)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search classes: {str(e)}"
        )


# Enrollment management
@router.post("/{class_id}/students/{student_id}")
async def add_student_to_class(
    class_id: str,
    student_id: str,
    current_teacher: dict = Depends(get_current_teacher)
):
    """Add a student to a class (Teachers only - own classes)."""
    try:
        # Ensure the teacher owns this class
        from app.utils.teacher_validation import validate_teacher_owns_class
        await validate_teacher_owns_class(current_teacher["id"], class_id)

        success = await class_service.add_student_to_class(class_id, student_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add student to class"
            )
        return {"message": "Student added to class"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add student to class: {str(e)}"
        )


@router.delete("/{class_id}/students/{student_id}")
async def remove_student_from_class(
    class_id: str,
    student_id: str,
    current_teacher: dict = Depends(get_current_teacher)
):
    """Remove a student from a class (Teachers only - own classes)."""
    try:
        from app.utils.teacher_validation import validate_teacher_owns_class
        await validate_teacher_owns_class(current_teacher["id"], class_id)

        success = await class_service.remove_student_from_class(class_id, student_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to remove student from class"
            )
        return {"message": "Student removed from class"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove student from class: {str(e)}"
        )


@router.get("/{class_id}/students", response_model=List[dict])
async def list_class_students(
    class_id: str,
    current_user: dict = Depends(get_current_user)
):
    """List students in a class (Teacher who owns it or enrolled student)."""
    try:
        # Check access: teacher owner or enrolled student
        class_data = await class_service.get_class(class_id)
        if not class_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

        user_id = current_user.get("id")
        is_teacher_owner = class_data.get("teacher_id") == str(user_id)
        is_enrolled = await class_service.is_student_enrolled(class_id, user_id)
        if not (is_teacher_owner or is_enrolled):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        students = await class_service.list_class_students(class_id)
        return students
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list class students: {str(e)}"
        )
