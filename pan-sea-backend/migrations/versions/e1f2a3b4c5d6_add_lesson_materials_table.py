"""add_lesson_materials_table

Revision ID: e1f2a3b4c5d6
Revises: f5a97910b694
Create Date: 2025-09-11 23:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, Sequence[str], None] = 'f5a97910b694'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'lesson_materials',
        sa.Column('id', sa.UUID(), primary_key=True, nullable=False),
        sa.Column('lesson_id', sa.UUID(), sa.ForeignKey('lessons.id', ondelete='CASCADE'), nullable=False),
        sa.Column('class_id', sa.String(length=255), nullable=False),
        sa.Column('filename', sa.String(length=500), nullable=True),
        sa.Column('s3_key', sa.String(length=1000), nullable=False, unique=True, index=True),
        sa.Column('s3_url', sa.Text(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_extension', sa.String(length=10), nullable=True),
        sa.Column('content_type', sa.String(length=100), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('idx_lesson_materials_lesson_id', 'lesson_materials', ['lesson_id'])
    op.create_index('idx_lesson_materials_class_id', 'lesson_materials', ['class_id'])


def downgrade() -> None:
    op.drop_index('idx_lesson_materials_class_id', table_name='lesson_materials')
    op.drop_index('idx_lesson_materials_lesson_id', table_name='lesson_materials')
    op.drop_table('lesson_materials')



