"""Fix resource environment enum

Revision ID: 2911f7c257cf
Revises: 804f316bbf10
Create Date: 2025-09-13 17:28:02.899949

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2911f7c257cf'
down_revision: Union[str, Sequence[str], None] = '804f316bbf10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old enums if they exist
    op.execute("DROP TYPE IF EXISTS resource_environment")
    op.execute("DROP TYPE IF EXISTS resourceenvironment")

    # Create only the correct enum
    resource_env = postgresql.ENUM('ZNIF', 'FIVENIVE', 'PREP', name='resourceenvironment', create_type=True)
    resource_env.create(op.get_bind(), checkfirst=True)

    # Update all tables that use this enum
    for table_name in ["stations", "crawler_routes", "pandemic_routes"]:
        # Drop old column if it exists
        op.drop_column(table_name, "environment")
        # Recreate column using correct enum
        op.add_column(
            table_name,
            sa.Column("environment", sa.Enum('ZNIF', 'FIVENIVE', 'PREP', name='resourceenvironment'), nullable=False)
        )


def downgrade() -> None:
    """Downgrade schema."""
    pass
