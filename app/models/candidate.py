from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    full_name: Mapped[str | None] = mapped_column(String(160))
    phone: Mapped[str | None] = mapped_column(String(32))
    headline: Mapped[str | None] = mapped_column(String(180))
    summary: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    availability: Mapped[str | None] = mapped_column(String(255))
    is_public: Mapped[bool] = mapped_column(default=True, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="candidate_profile")
    skills: Mapped[list["CandidateSkill"]] = relationship(
        "CandidateSkill", back_populates="candidate_profile", cascade="all, delete-orphan"
    )
    experiences: Mapped[list["CandidateExperience"]] = relationship(
        "CandidateExperience", back_populates="candidate_profile", cascade="all, delete-orphan"
    )
    educations: Mapped[list["CandidateEducation"]] = relationship(
        "CandidateEducation", back_populates="candidate_profile", cascade="all, delete-orphan"
    )


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"
    __table_args__ = (
        CheckConstraint(
            "years_experience IS NULL OR years_experience >= 0",
            name="ck_candidate_skills_years_experience_nonnegative",
        ),
        CheckConstraint(
            "proficiency IS NULL OR proficiency IN ('BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'EXPERT')",
            name="ck_candidate_skills_proficiency",
        ),
        Index("ix_candidate_skills_skill_id", "skill_id"),
    )

    candidate_profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    proficiency: Mapped[str | None] = mapped_column(String(30))
    years_experience: Mapped[float | None] = mapped_column(Float, nullable=True)

    candidate_profile: Mapped[CandidateProfile] = relationship("CandidateProfile", back_populates="skills")
    skill: Mapped["Skill"] = relationship("Skill", back_populates="candidate_links")
