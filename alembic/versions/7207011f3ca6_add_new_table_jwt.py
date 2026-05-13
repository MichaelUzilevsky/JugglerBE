"""add new table, jwt

Revision ID: 7207011f3ca6
Revises: a9321c4a17ec
Create Date: 2025-10-04 12:07:13.140514

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7207011f3ca6'
down_revision: Union[str, Sequence[str], None] = 'a9321c4a17ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "jwt_refresh_tokens",
        sa.Column("id", sa.String(length=64), primary_key=True, index=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("replaced_by", sa.String(length=64), nullable=True),
    )

    # Composite index on (id, user_id)
    op.create_index("ix_jti_hash_user", "jwt_refresh_tokens", ["id", "user_id"])
    # Index for expires_at
    op.create_index("ix_jwt_refresh_tokens_expires_at", "jwt_refresh_tokens", ["expires_at"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_jti_hash_user", table_name="jwt_refresh_tokens")
    op.drop_index("ix_jwt_refresh_tokens_expires_at", table_name="jwt_refresh_tokens")
    op.drop_table("jwt_refresh_tokens")