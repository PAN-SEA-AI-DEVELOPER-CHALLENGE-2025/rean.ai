"""Add embedding column to audio table

Revision ID: 17e4e8bb8a7a
Revises: 
Create Date: 2025-09-05 10:32:47.877464

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '17e4e8bb8a7a'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add embedding column to audio table
    op.add_column('audio', sa.Column('embedding', JSONB(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove embedding column from audio table
    op.drop_column('audio', 'embedding')
