"""add_pgvector_extension_and_vector_column

Revision ID: 3f422b7b7775
Revises: 76b5d3262984
Create Date: 2025-09-09 12:46:06.698660

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '3f422b7b7775'
down_revision: Union[str, Sequence[str], None] = '76b5d3262984'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add a text column to store vector data as text (works with or without pgvector)
    op.add_column('lessons', sa.Column('embedding_vector', sa.Text(), nullable=True))
    
    # Migrate existing JSONB embeddings to text format
    op.execute("""
        UPDATE lessons 
        SET embedding_vector = embedding::text 
        WHERE embedding IS NOT NULL 
        AND embedding != 'null'::jsonb
    """)
    
    # Note: avoid indexing full embedding text due to row size limits.
    # pgvector extension and HNSW indexes will be created separately
    # when pgvector is installed on the PostgreSQL server


def downgrade() -> None:
    """Downgrade schema."""
    # Drop vector indexes
    op.execute('DROP INDEX IF EXISTS idx_lessons_embedding_vector_hnsw')
    op.execute('DROP INDEX IF EXISTS idx_lessons_embedding_vector_l2')
    op.execute('DROP INDEX IF EXISTS idx_lessons_embedding_vector_ip')
    
    # Drop vector column
    op.drop_column('lessons', 'embedding_vector')
    
    # Note: We don't drop the pgvector extension as it might be used by other tables
