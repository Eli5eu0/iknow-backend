"""company profile in two steps: nullable name and one company row per COMPANY user

Revision ID: b7d3f1a96c25
Revises: e2b7c91a4d60
Create Date: 2026-11-13
"""

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7d3f1a96c25"
down_revision: Union[str, Sequence[str], None] = "e2b7c91a4d60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "companies",
        "name",
        existing_type=sa.String(length=180),
        nullable=True,
    )

    # Aditivo e idempotente: cria a linha em falta para cada conta COMPANY existente.
    users = sa.table("users", sa.column("id", sa.Uuid()), sa.column("role", sa.String()))
    companies = sa.table(
        "companies",
        sa.column("id", sa.Uuid()),
        sa.column("user_id", sa.Uuid()),
        sa.column("verification_status", sa.String()),
    )
    bind = op.get_bind()
    missing = bind.execute(
        sa.select(users.c.id).where(
            users.c.role == "COMPANY",
            ~users.c.id.in_(sa.select(companies.c.user_id)),
        )
    ).all()
    if missing:
        op.bulk_insert(
            companies,
            [
                {"id": uuid.uuid4(), "user_id": row[0], "verification_status": "NOT_SUBMITTED"}
                for row in missing
            ],
        )


def downgrade() -> None:
    # Não apaga linhas: as empresas criadas por esta migração ficam, mas o NOT NULL só
    # pode ser reposto se nenhuma tiver o nome por preencher.
    unnamed = op.get_bind().execute(sa.text("SELECT count(*) FROM companies WHERE name IS NULL")).scalar()
    if unnamed:
        raise RuntimeError(
            f"Cannot restore NOT NULL on companies.name: {unnamed} row(s) have no name. "
            "Fill or remove them first."
        )
    op.alter_column(
        "companies",
        "name",
        existing_type=sa.String(length=180),
        nullable=False,
    )
