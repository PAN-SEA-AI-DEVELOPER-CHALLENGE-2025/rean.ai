"""Add performance indexes for better query performance

Revision ID: performance_indexes
Revises: 3b27f36b85e4
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'performance_indexes'
down_revision = '3b27f36b85e4'
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes"""
    
    # Users table indexes
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_role', 'users', ['role'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])
    
    # Composite index for login optimization
    op.create_index('idx_users_email_username', 'users', ['email', 'username'])
    
    # Refresh tokens table indexes
    op.create_index('idx_refresh_tokens_token', 'refresh_tokens', ['token'])
    op.create_index('idx_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('idx_refresh_tokens_expires_at', 'refresh_tokens', ['expires_at'])
    op.create_index('idx_refresh_tokens_is_revoked', 'refresh_tokens', ['is_revoked'])
    
    # Classes table indexes
    op.create_index('idx_classes_teacher_id', 'classes', ['teacher_id'])
    op.create_index('idx_classes_subject', 'classes', ['subject'])
    op.create_index('idx_classes_created_at', 'classes', ['created_at'])
    
    # Lessons table indexes (renamed from audio_recordings)
    op.create_index('idx_lessons_class_id', 'lessons', ['class_id'])
    op.create_index('idx_lessons_created_at', 'lessons', ['created_at'])
    op.create_index('idx_lessons_lecture_title', 'lessons', ['lecture_title'])
    # Composite index for common filter + order by
    op.create_index('idx_lessons_class_id_created_at', 'lessons', ['class_id', 'created_at'])
    
    # Lesson summaries table indexes
    # Lesson chunks table indexes
    op.create_index('idx_lesson_chunks_lesson_id', 'lesson_chunks', ['lesson_id'])
    op.create_index('idx_lesson_chunks_lesson_id_chunk_index', 'lesson_chunks', ['lesson_id', 'chunk_index'])
    op.create_index('idx_lesson_summaries_lesson_id', 'lesson_summaries', ['lesson_id'])
    op.create_index('idx_lesson_summaries_class_id', 'lesson_summaries', ['class_id'])
    op.create_index('idx_lesson_summaries_created_at', 'lesson_summaries', ['created_at'])
    
    # Class students junction table indexes
    op.create_index('idx_class_students_class_id', 'class_students', ['class_id'])
    op.create_index('idx_class_students_student_id', 'class_students', ['student_id'])


def downgrade():
    """Remove performance indexes"""
    
    # Drop indexes in reverse order
    op.drop_index('idx_class_students_student_id', 'class_students')
    op.drop_index('idx_class_students_class_id', 'class_students')
    
    op.drop_index('idx_lesson_summaries_created_at', 'lesson_summaries')
    op.drop_index('idx_lesson_summaries_class_id', 'lesson_summaries')
    op.drop_index('idx_lesson_summaries_lesson_id', 'lesson_summaries')
    
    op.drop_index('idx_lesson_chunks_lesson_id_chunk_index', 'lesson_chunks')
    op.drop_index('idx_lesson_chunks_lesson_id', 'lesson_chunks')
    op.drop_index('idx_lessons_lecture_title', 'lessons')
    op.drop_index('idx_lessons_class_id_created_at', 'lessons')
    op.drop_index('idx_lessons_created_at', 'lessons')
    op.drop_index('idx_lessons_class_id', 'lessons')
    
    op.drop_index('idx_classes_created_at', 'classes')
    op.drop_index('idx_classes_subject', 'classes')
    op.drop_index('idx_classes_teacher_id', 'classes')
    
    op.drop_index('idx_refresh_tokens_is_revoked', 'refresh_tokens')
    op.drop_index('idx_refresh_tokens_expires_at', 'refresh_tokens')
    op.drop_index('idx_refresh_tokens_user_id', 'refresh_tokens')
    op.drop_index('idx_refresh_tokens_token', 'refresh_tokens')
    
    op.drop_index('idx_users_email_username', 'users')
    op.drop_index('idx_users_created_at', 'users')
    op.drop_index('idx_users_is_active', 'users')
    op.drop_index('idx_users_role', 'users')
    op.drop_index('idx_users_username', 'users')
    op.drop_index('idx_users_email', 'users')
