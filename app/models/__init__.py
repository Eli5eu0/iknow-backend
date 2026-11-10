"""Modelos ORM do domínio iKnow."""

from app.models.candidate import CandidateProfile, CandidateSkill
from app.models.company import Company, CompanyVerificationStatus
from app.models.opportunity import Opportunity, OpportunitySkill, OpportunityStatus
from app.models.skill import Skill
from app.models.user import RefreshToken, User, UserRole

__all__ = [
    "CandidateProfile", "CandidateSkill", "Company", "CompanyVerificationStatus",
    "Opportunity", "OpportunitySkill", "OpportunityStatus", "RefreshToken",
    "Skill", "User", "UserRole",
]
