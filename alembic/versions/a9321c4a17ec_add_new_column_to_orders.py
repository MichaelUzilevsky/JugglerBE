"""add new column to orders

Revision ID: a9321c4a17ec
Revises: 1b71d44eb01a
Create Date: 2025-09-24 13:56:08.848368

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a9321c4a17ec'
down_revision: Union[str, Sequence[str], None] = '1b71d44eb01a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('orders', sa.Column('order_description', sa.Text(), nullable=False))


def downgrade() -> None:
    op.drop_column('orders', 'order_description')