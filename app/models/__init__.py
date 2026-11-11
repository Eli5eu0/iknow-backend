"""Modelos ORM do domínio iKnow."""

from app.models.application import Application, ApplicationStatus
from app.models.candidate import CandidateProfile, CandidateSkill
from app.models.candidate_education import CandidateEducation
from app.models.candidate_experience import CandidateExperience
from app.models.company import Company, CompanyVerificationStatus
from app.models.matching import (
    Match,
    MatchEvaluationStatus,
    MatchingJob,
    MatchingJobScope,
    MatchingJobStatus,
)
from app.models.notification import Notification
from app.models.opportunity import Opportunity, OpportunitySkill, OpportunityStatus
from app.models.skill import Skill
from app.models.user import RefreshToken, User, UserRole

__all__ = [
    "Application",
    "ApplicationStatus",
    "CandidateEducation",
    "CandidateExperience",
    "CandidateProfile",
    "CandidateSkill",
    "Company",
    "CompanyVerificationStatus",
    "Match",
    "MatchEvaluationStatus",
    "MatchingJob",
    "MatchingJobScope",
    "MatchingJobStatus",
    "Notification",
    "Opportunity",
    "OpportunitySkill",
    "OpportunityStatus",
    "RefreshToken",
    "Skill",
    "User",
    "UserRole",
]
