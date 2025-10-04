"""merge_migration_heads

Revision ID: a73719455dd4
Revises: 213242fe231d, performance_indexes
Create Date: 2025-09-08 20:38:18.836769

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a73719455dd4'
down_revision: Union[str, Sequence[str], None] = ('213242fe231d', 'performance_indexes')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
