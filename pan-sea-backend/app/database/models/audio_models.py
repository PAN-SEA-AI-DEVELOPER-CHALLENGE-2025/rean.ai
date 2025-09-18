from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from pgvector.sqlalchemy import Vector

from app.database.database import Base


class Lesson(Base):
    __tablename__ = "lessons"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    class_id = Column(String(255), nullable=False, index=True)  # Using String instead of FK for flexibility
    lecture_title = Column(String(500), nullable=False)
    s3_key = Column(String(1000), nullable=False, unique=True, index=True)
    s3_url = Column(Text, nullable=False)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    file_extension = Column(String(10), nullable=True)  # .mp3, .wav, etc.
    duration = Column(Integer, nullable=True)  # Duration in seconds
    transcription = Column(Text, nullable=True)  # Audio transcription
    embedding = Column(JSONB, nullable=True)  # Legacy embedding vector (JSONB format)
    embedding_vector = Column(Vector(1024), nullable=True)  # pgvector embedding for semantic search
    transcription_status = Column(String(20), default='pending')  # pending, processing, completed, failed
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lesson_summary = relationship("LessonSummary", back_populates="lesson", uselist=False)
    
    def __repr__(self):
        return f"<Lesson(id={self.id}, class_id={self.class_id}, lecture_title={self.lecture_title})>"
