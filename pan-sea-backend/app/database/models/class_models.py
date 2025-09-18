from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.database.database import Base

# Association table for many-to-many relationship between classes and students
class_students_association = Table(
    'class_students',
    Base.metadata,
    Column('class_id', UUID(as_uuid=True), ForeignKey('classes.id'), primary_key=True),
    Column('student_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True)
)


class Class(Base):
    __tablename__ = "classes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_code = Column(String(255), nullable=False)
    subject = Column(String(100), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    duration = Column(Integer, nullable=True)  # in minutes
    grade = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    teacher = relationship("User", foreign_keys=[teacher_id], back_populates="taught_classes")
    students = relationship("User", secondary=class_students_association, back_populates="enrolled_classes")
    summaries = relationship("LessonSummary", back_populates="class_session")


class LessonSummary(Base):
    __tablename__ = "lesson_summaries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id = Column(UUID(as_uuid=True), ForeignKey('classes.id'), nullable=False)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey('lessons.id'), nullable=True)
    lecture_title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    topics_discussed = Column(Text, nullable=True)  # JSON array stored as text
    learning_objectives = Column(Text, nullable=True)  # JSON array stored as text
    homework = Column(Text, nullable=True)  # JSON array stored as text
    announcements = Column(Text, nullable=True)  # JSON array stored as text
    key_points = Column(Text, nullable=True)  # JSON array stored as text
    study_questions = Column(Text, nullable=True)  # JSON array stored as text
    duration = Column(Integer, nullable=False)  # in minutes
    next_class_preview = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    class_session = relationship("Class", back_populates="summaries")
    lesson = relationship("Lesson", back_populates="lesson_summary")
