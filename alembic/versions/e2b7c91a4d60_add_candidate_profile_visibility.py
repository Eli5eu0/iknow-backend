"""add candidate profile visibility and availability capacity

Revision ID: e2b7c91a4d60
Revises: c4f2a9b81d30
Create Date: 2026-11-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e2b7c91a4d60"
down_revision: Union[str, Sequence[str], None] = "c4f2a9b81d30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "candidate_profiles",
        sa.Column("is_public", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.alter_column(
        "candidate_profiles",
        "availability",
        existing_type=sa.String(length=40),
        type_=sa.String(length=255),
        existing_nullable=True,
    )
    op.create_check_constraint(
        "ck_candidate_skills_proficiency",
        "candidate_skills",
        "proficiency IS NULL OR proficiency IN ('BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'EXPERT')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_candidate_skills_proficiency", "candidate_skills", type_="check")
    op.alter_column(
        "candidate_profiles",
        "availability",
        existing_type=sa.String(length=255),
        type_=sa.String(length=40),
        existing_nullable=True,
    )
    op.drop_column("candidate_profiles", "is_public")
