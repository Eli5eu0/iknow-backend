import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base


class MatchEvaluationStatus(str, enum.Enum):
    READY = "READY"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class MatchingJobScope(str, enum.Enum):
    CANDIDATE = "CANDIDATE"
    OPPORTUNITY = "OPPORTUNITY"
    ALL = "ALL"


class MatchingJobStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        CheckConstraint(
            "score IS NULL OR (score >= 0 AND score <= 100)",
            name="ck_matches_score_range",
        ),
        CheckConstraint(
            "coverage >= 0 AND coverage <= 100",
            name="ck_matches_coverage_range",
        ),
        CheckConstraint(
            "(evaluation_status = 'READY' AND score IS NOT NULL) OR "
            "(evaluation_status = 'INSUFFICIENT_DATA' AND score IS NULL)",
            name="ck_matches_evaluation_score_consistency",
        ),
        Index("ix_matches_opportunity_score", "opportunity_id", "score"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        nullable=False,
    )
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    coverage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"), nullable=False)
    evaluation_status: Mapped[MatchEvaluationStatus] = mapped_column(
        Enum(
            MatchEvaluationStatus,
            native_enum=False,
            create_constraint=True,
            length=24,
            name="match_evaluation_status",
        ),
        default=MatchEvaluationStatus.INSUFFICIENT_DATA,
        nullable=False,
    )
    is_eligible: Mapped[bool] = mapped_column(default=False, nullable=False)
    score_breakdown: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    eligibility_details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String(32), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    candidate_profile: Mapped["CandidateProfile"] = relationship("CandidateProfile")
    opportunity: Mapped["Opportunity"] = relationship("Opportunity")


class MatchingJob(Base):
    __tablename__ = "matching_jobs"
    __table_args__ = (
        CheckConstraint(
            "(scope = 'CANDIDATE' AND candidate_profile_id IS NOT NULL AND opportunity_id IS NULL) "
            "OR (scope = 'OPPORTUNITY' AND opportunity_id IS NOT NULL AND candidate_profile_id IS NULL) "
            "OR (scope = 'ALL' AND candidate_profile_id IS NULL AND opportunity_id IS NULL)",
            name="ck_matching_jobs_scope_targets",
        ),
        CheckConstraint("attempts >= 0", name="ck_matching_jobs_attempts_nonnegative"),
        Index("ix_matching_jobs_status_created", "status", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scope: Mapped[MatchingJobScope] = mapped_column(
        Enum(
            MatchingJobScope,
            native_enum=False,
            create_constraint=True,
            length=16,
            name="matching_job_scope",
        ),
        nullable=False,
    )
    status: Mapped[MatchingJobStatus] = mapped_column(
        Enum(
            MatchingJobStatus,
            native_enum=False,
            create_constraint=True,
            length=16,
            name="matching_job_status",
        ),
        default=MatchingJobStatus.PENDING,
        nullable=False,
    )
    candidate_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
    )
    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("opportunities.id", ondelete="CASCADE"),
    )
    requested_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    candidate_profile: Mapped["CandidateProfile | None"] = relationship("CandidateProfile")
    opportunity: Mapped["Opportunity | None"] = relationship("Opportunity")
    requested_by: Mapped["User | None"] = relationship("User")
