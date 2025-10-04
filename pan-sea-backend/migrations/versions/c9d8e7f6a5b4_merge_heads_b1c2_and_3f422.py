"""merge_heads_b1c2_and_3f422

Revision ID: c9d8e7f6a5b4
Revises: b1c2d3e4f5a6, 3f422b7b7775
Create Date: 2025-09-10 17:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9d8e7f6a5b4'
down_revision: Union[str, Sequence[str], None] = ('b1c2d3e4f5a6', '3f422b7b7775')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Schema merge - no structural changes."""
    pass


def downgrade() -> None:
    """Schema merge - no structural changes."""
    pass


