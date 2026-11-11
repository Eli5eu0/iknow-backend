"""add CSRF token hash to refresh token sessions

Revision ID: a91e3d4c7b20
Revises: 0638ca89a4cf
Create Date: 2026-11-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a91e3d4c7b20"
down_revision: Union[str, Sequence[str], None] = "0638ca89a4cf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "refresh_tokens",
        sa.Column("csrf_token_hash", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("refresh_tokens", "csrf_token_hash")
