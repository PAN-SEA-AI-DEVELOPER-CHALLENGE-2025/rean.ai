"""merge heads c9d8 and e1f2 lesson_materials

Revision ID: 19606405495f
Revises: c9d8e7f6a5b4, e1f2a3b4c5d6
Create Date: 2025-09-11 23:07:46.512514

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '19606405495f'
down_revision: Union[str, Sequence[str], None] = ('c9d8e7f6a5b4', 'e1f2a3b4c5d6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
