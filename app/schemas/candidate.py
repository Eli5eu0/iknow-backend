from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Proficiency(str, Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"


class CandidateProfileFields(BaseModel):
    full_name: str | None = Field(default=None, max_length=160)
    phone: str | None = Field(default=None, max_length=32)
    headline: str | None = Field(default=None, max_length=180)
    summary: str | None = Field(default=None, max_length=5000)
    city: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    availability: str | None = Field(default=None, max_length=255)


class CandidateProfileUpdate(CandidateProfileFields):
    model_config = ConfigDict(extra="forbid")


class CandidateProfileRead(CandidateProfileFields):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    is_public: bool
    created_at: datetime
    updated_at: datetime


class CandidateVisibilityUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_public: bool


class SkillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    slug: str
    category: str | None


class CandidateSkillCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    skill_id: UUID
    proficiency: Proficiency | None = None
    years_experience: float | None = Field(default=None, ge=0, le=80)


class CandidateSkillUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    proficiency: Proficiency | None = None
    years_experience: float | None = Field(default=None, ge=0, le=80)


class CandidateSkillRead(BaseModel):
    skill: SkillRead
    proficiency: Proficiency | None
    years_experience: float | None


class ExperienceFields(BaseModel):
    company_name: str = Field(min_length=1, max_length=180)
    job_title: str = Field(min_length=1, max_length=180)
    employment_type: str | None = Field(default=None, max_length=40)
    description: str | None = Field(default=None, max_length=5000)
    city: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    start_date: date
    end_date: date | None = None
    is_current: bool = False

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        if self.is_current and self.end_date is not None:
            raise ValueError("Current experience cannot have end_date")
        return self


class ExperienceCreate(ExperienceFields):
    model_config = ConfigDict(extra="forbid")


class ExperienceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company_name: str | None = Field(default=None, min_length=1, max_length=180)
    job_title: str | None = Field(default=None, min_length=1, max_length=180)
    employment_type: str | None = Field(default=None, max_length=40)
    description: str | None = Field(default=None, max_length=5000)
    city: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        if self.is_current and self.end_date is not None:
            raise ValueError("Current experience cannot have end_date")
        return self


class ExperienceRead(ExperienceFields):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


class EducationFields(BaseModel):
    institution: str = Field(min_length=1, max_length=180)
    degree: str | None = Field(default=None, max_length=120)
    field_of_study: str | None = Field(default=None, max_length=160)
    description: str | None = Field(default=None, max_length=5000)
    city: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    start_date: date
    end_date: date | None = None
    is_current: bool = False

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        if self.is_current and self.end_date is not None:
            raise ValueError("Current education cannot have end_date")
        return self


class EducationCreate(EducationFields):
    model_config = ConfigDict(extra="forbid")


class EducationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    institution: str | None = Field(default=None, min_length=1, max_length=180)
    degree: str | None = Field(default=None, max_length=120)
    field_of_study: str | None = Field(default=None, max_length=160)
    description: str | None = Field(default=None, max_length=5000)
    city: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        if self.is_current and self.end_date is not None:
            raise ValueError("Current education cannot have end_date")
        return self


class EducationRead(EducationFields):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


class CandidatePublicProfile(BaseModel):
    id: UUID
    full_name: str | None
    headline: str | None
    summary: str | None
    city: str | None
    country: str | None
    availability: str | None
    educations: list[EducationRead]
    experiences: list[ExperienceRead]
    skills: list[CandidateSkillRead]
