from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.candidate import CandidateProfile, CandidateSkill
from app.models.candidate_education import CandidateEducation
from app.models.candidate_experience import CandidateExperience
from app.models.skill import Skill
from app.models.user import User


def get_or_create_profile(db: Session, user: User) -> CandidateProfile:
    profile = db.scalar(
        select(CandidateProfile)
        .where(CandidateProfile.user_id == user.id)
        .options(
            selectinload(CandidateProfile.skills).selectinload(CandidateSkill.skill),
            selectinload(CandidateProfile.experiences),
            selectinload(CandidateProfile.educations),
        )
    )
    if profile is None:
        profile = CandidateProfile(user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def get_profile(db: Session, user: User) -> CandidateProfile:
    profile = db.scalar(
        select(CandidateProfile)
        .where(CandidateProfile.user_id == user.id)
        .options(
            selectinload(CandidateProfile.skills).selectinload(CandidateSkill.skill),
            selectinload(CandidateProfile.experiences),
            selectinload(CandidateProfile.educations),
        )
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    return profile



def update_profile(
    db: Session,
    user: User,
    data: dict,
    *,
    create: bool = False,
) -> CandidateProfile:
    profile = db.scalar(
        select(CandidateProfile).where(
            CandidateProfile.user_id == user.id
        )
    )

    if profile is None:
        if not create:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate profile not found",
            )

        profile = CandidateProfile(user_id=user.id)
        db.add(profile)

    for key, value in data.items():
        setattr(profile, key, value)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return get_profile(db, user)



def owned_record(db: Session, model, record_id: UUID, profile_id: UUID):
    record = db.scalar(
        select(model).where(model.id == record_id, model.candidate_profile_id == profile_id)
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


def add_skill(db: Session, profile: CandidateProfile, skill_id: UUID, proficiency, years_experience):
    skill = db.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found in catalogue")
    link = db.get(CandidateSkill, (profile.id, skill_id))
    if link is not None:
        raise HTTPException(status_code=409, detail="Skill already added to candidate profile")
    link = CandidateSkill(
        candidate_profile_id=profile.id,
        skill_id=skill_id,
        proficiency=proficiency.value if proficiency else None,
        years_experience=years_experience,
    )
    db.add(link)
    db.commit()
    return db.scalar(
        select(CandidateSkill)
        .where(CandidateSkill.candidate_profile_id == profile.id, CandidateSkill.skill_id == skill_id)
        .options(selectinload(CandidateSkill.skill))
    )


def update_skill(db: Session, profile: CandidateProfile, skill_id: UUID, data: dict):
    link = db.get(CandidateSkill, (profile.id, skill_id))
    if link is None:
        raise HTTPException(status_code=404, detail="Candidate skill not found")
    for key, value in data.items():
        setattr(link, key, value.value if hasattr(value, "value") else value)
    db.commit()
    return db.scalar(
        select(CandidateSkill)
        .where(CandidateSkill.candidate_profile_id == profile.id, CandidateSkill.skill_id == skill_id)
        .options(selectinload(CandidateSkill.skill))
    )
