"""add_extracted_text_to_lesson_materials

Revision ID: 2d3c4b5a6e7f
Revises: 19606405495f
Create Date: 2025-09-12 10:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2d3c4b5a6e7f'
down_revision: Union[str, Sequence[str], None] = '19606405495f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('lesson_materials', sa.Column('extracted_text', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('lesson_materials', 'extracted_text')

