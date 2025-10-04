"""add_embedding_column_to_lessons_table

Revision ID: f5a97910b694
Revises: a73719455dd4
Create Date: 2025-09-08 20:38:21.820712

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'f5a97910b694'
down_revision: Union[str, Sequence[str], None] = 'a73719455dd4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add embedding column to lessons table
    op.add_column('lessons', sa.Column('embedding', JSONB(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove embedding column from lessons table
    op.drop_column('lessons', 'embedding')
