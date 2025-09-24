"""add new column

Revision ID: 1b71d44eb01a
Revises: 
Create Date: 2025-09-23 15:02:03.831885

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1b71d44eb01a'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('base_resources', sa.Column('general_description', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('base_resources', 'general_description')