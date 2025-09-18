from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class ClassBase(BaseModel):
    class_code: str = Field(..., min_length=1, max_length=255)
    subject: str = Field(..., min_length=1, max_length=100)
    grade: Optional[str] = Field(None, max_length=20)


class ClassCreate(ClassBase):
    teacher_id: str
    student_ids: List[str] = []


class ClassUpdate(BaseModel):
    class_code: Optional[str] = Field(None, min_length=1, max_length=255)
    subject: Optional[str] = Field(None, min_length=1, max_length=100)
    grade: Optional[str] = Field(None, max_length=20)


class ClassResponse(ClassBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    teacher_id: str
    teacher_name: Optional[str] = None
    duration: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    students: List[str] = []


class LessonSummaryBase(BaseModel):
    lecture_title: str = Field(..., min_length=1, max_length=255)
    summary: str = Field(..., min_length=1)
    topics_discussed: List[str] = []
    learning_objectives: List[str] = []
    homework: List[str] = []
    announcements: List[str] = []
    duration: int = Field(..., gt=0)
    next_class_preview: Optional[str] = None


class LessonSummaryCreate(LessonSummaryBase):
    class_id: str
    lesson_id: Optional[str] = None


class LessonSummaryResponse(LessonSummaryBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    class_id: str
    lesson_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
