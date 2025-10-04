"""add_lesson_chunks_table

Revision ID: b1c2d3e4f5a6
Revises: a73719455dd4
Create Date: 2025-09-10 17:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'a73719455dd4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create lesson_chunks table for per-chunk RAG indexing."""
    op.create_table(
        'lesson_chunks',
        sa.Column('id', sa.UUID(), primary_key=True, nullable=False),
        sa.Column('lesson_id', sa.UUID(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('start_offset', sa.Integer(), nullable=True),
        sa.Column('end_offset', sa.Integer(), nullable=True),
        sa.Column('embedding', JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('embedding_vector', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE')
    )

    op.create_index('idx_lesson_chunks_lesson_id', 'lesson_chunks', ['lesson_id'])
    op.create_index('idx_lesson_chunks_chunk_index', 'lesson_chunks', ['chunk_index'])
    op.create_index('idx_lesson_chunks_created_at', 'lesson_chunks', ['created_at'])


def downgrade() -> None:
    """Drop lesson_chunks table and indexes."""
    op.drop_index('idx_lesson_chunks_created_at', table_name='lesson_chunks')
    op.drop_index('idx_lesson_chunks_chunk_index', table_name='lesson_chunks')
    op.drop_index('idx_lesson_chunks_lesson_id', table_name='lesson_chunks')
    op.drop_table('lesson_chunks')


