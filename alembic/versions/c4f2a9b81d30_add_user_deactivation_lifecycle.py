"""add user account deactivation lifecycle fields

Revision ID: c4f2a9b81d30
Revises: a91e3d4c7b20
Create Date: 2026-11-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4f2a9b81d30"
down_revision: Union[str, Sequence[str], None] = "a91e3d4c7b20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("deletion_requested_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("deletion_scheduled_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_users_deletion_scheduled_at", "users", ["deletion_scheduled_at"])


def downgrade() -> None:
    op.drop_index("ix_users_deletion_scheduled_at", table_name="users")
    op.drop_column("users", "deletion_scheduled_at")
    op.drop_column("users", "deletion_requested_at")
