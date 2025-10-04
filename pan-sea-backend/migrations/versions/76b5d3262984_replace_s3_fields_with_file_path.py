"""replace_s3_fields_with_file_path

Revision ID: 76b5d3262984
Revises: f5a97910b694
Create Date: 2025-09-08 23:22:00.277578

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '76b5d3262984'
down_revision: Union[str, Sequence[str], None] = 'f5a97910b694'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
