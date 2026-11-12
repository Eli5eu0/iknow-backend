from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.candidate import CandidateProfile, CandidateSkill
from app.models.candidate_education import CandidateEducation
from app.models.candidate_experience import CandidateExperience
from app.models.user import User, UserRole
from app.schemas.candidate import (
    CandidateProfileRead, CandidateProfileUpdate, CandidatePublicProfile,
    CandidateSkillCreate, CandidateSkillRead, CandidateSkillUpdate,
    CandidateVisibilityUpdate, EducationCreate, EducationRead, EducationUpdate,
    ExperienceCreate, ExperienceRead, ExperienceUpdate,
)
from app.services.candidate_service import (
    add_skill, get_or_create_profile, get_profile, owned_record, update_profile, update_skill,
)

router = APIRouter(prefix="/candidates")
candidate_only = require_roles(UserRole.CANDIDATE)


@router.get("/me", response_model=CandidateProfileRead)
def read_my_profile(user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    return get_profile(db, user)


@router.put("/me", response_model=CandidateProfileRead)
def upsert_my_profile(
    payload: CandidateProfileUpdate,
    user: User = Depends(candidate_only),
    db: Session = Depends(get_db),
):
    return update_profile(db, user, payload.model_dump(exclude_unset=True), create=True)


@router.patch("/me", response_model=CandidateProfileRead)
def patch_my_profile(
    payload: CandidateProfileUpdate,
    user: User = Depends(candidate_only),
    db: Session = Depends(get_db),
):
    return update_profile(
    db,
    user,
    payload.model_dump(exclude_unset=True),
)


@router.patch("/me/visibility", response_model=CandidateProfileRead)
def update_visibility(
    payload: CandidateVisibilityUpdate,
    user: User = Depends(candidate_only),
    db: Session = Depends(get_db),
):
    profile = get_or_create_profile(db, user)
    profile.is_public = payload.is_public
    db.commit()
    return get_profile(db, user)


@router.get("/me/experiences", response_model=list[ExperienceRead])
def list_experiences(user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    profile = get_profile(db, user)
    return db.scalars(
        select(CandidateExperience).where(CandidateExperience.candidate_profile_id == profile.id)
        .order_by(CandidateExperience.start_date.desc())
    ).all()


@router.post("/me/experiences", response_model=ExperienceRead, status_code=status.HTTP_201_CREATED)
def create_experience(payload: ExperienceCreate, user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    profile = get_or_create_profile(db, user)
    record = CandidateExperience(candidate_profile_id=profile.id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.patch("/me/experiences/{record_id}", response_model=ExperienceRead)
def patch_experience(record_id: UUID, payload: ExperienceUpdate, user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    profile = get_or_create_profile(db, user)
    record = owned_record(db, CandidateExperience, record_id, profile.id)
    data = payload.model_dump(exclude_unset=True)
    merged = {**{k: getattr(record, k) for k in ("start_date", "end_date", "is_current")}, **data}
    if merged["end_date"] is not None and merged["end_date"] < merged["start_date"]:
        raise HTTPException(status_code=422, detail="end_date must be on or after start_date")
    if merged["is_current"] and merged["end_date"] is not None:
        raise HTTPException(status_code=422, detail="Current experience cannot have end_date")
    for key, value in data.items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/me/experiences/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experience(record_id: UUID, user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    profile = get_or_create_profile(db, user)
    db.delete(owned_record(db, CandidateExperience, record_id, profile.id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me/educations", response_model=list[EducationRead])
def list_educations(user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    profile = get_profile(db, user)
    return db.scalars(
        select(CandidateEducation).where(CandidateEducation.candidate_profile_id == profile.id)
        .order_by(CandidateEducation.start_date.desc())
    ).all()


@router.post("/me/educations", response_model=EducationRead, status_code=status.HTTP_201_CREATED)
def create_education(payload: EducationCreate, user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    profile = get_or_create_profile(db, user)
    record = CandidateEducation(candidate_profile_id=profile.id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.patch("/me/educations/{record_id}", response_model=EducationRead)
def patch_education(record_id: UUID, payload: EducationUpdate, user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    profile = get_or_create_profile(db, user)
    record = owned_record(db, CandidateEducation, record_id, profile.id)
    data = payload.model_dump(exclude_unset=True)
    merged = {**{k: getattr(record, k) for k in ("start_date", "end_date", "is_current")}, **data}
    if merged["end_date"] is not None and merged["end_date"] < merged["start_date"]:
        raise HTTPException(status_code=422, detail="end_date must be on or after start_date")
    if merged["is_current"] and merged["end_date"] is not None:
        raise HTTPException(status_code=422, detail="Current education cannot have end_date")
    for key, value in data.items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/me/educations/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_education(record_id: UUID, user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    profile = get_or_create_profile(db, user)
    db.delete(owned_record(db, CandidateEducation, record_id, profile.id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me/skills", response_model=list[CandidateSkillRead])
def list_skills(user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    profile = get_profile(db, user)
    return db.scalars(
        select(CandidateSkill).where(CandidateSkill.candidate_profile_id == profile.id)
        .options(selectinload(CandidateSkill.skill)).order_by(CandidateSkill.skill_id)
    ).all()


@router.post("/me/skills", response_model=CandidateSkillRead, status_code=status.HTTP_201_CREATED)
def create_skill(payload: CandidateSkillCreate, user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    profile = get_or_create_profile(db, user)
    return add_skill(db, profile, payload.skill_id, payload.proficiency, payload.years_experience)


@router.patch("/me/skills/{skill_id}", response_model=CandidateSkillRead)
def patch_skill(skill_id: UUID, payload: CandidateSkillUpdate, user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    profile = get_or_create_profile(db, user)
    return update_skill(db, profile, skill_id, payload.model_dump(exclude_unset=True))


@router.delete("/me/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(skill_id: UUID, user: User = Depends(candidate_only), db: Session = Depends(get_db)):
    profile = get_or_create_profile(db, user)
    link = db.get(CandidateSkill, (profile.id, skill_id))
    if link is None:
        raise HTTPException(status_code=404, detail="Candidate skill not found")
    db.delete(link)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{candidate_id}", response_model=CandidatePublicProfile)
def read_public_profile(candidate_id: UUID, db: Session = Depends(get_db)):
    profile = db.scalar(
        select(CandidateProfile)
        .join(User, CandidateProfile.user_id == User.id)
        .where(
            CandidateProfile.id == candidate_id,
            CandidateProfile.is_public.is_(True),
            User.is_active.is_(True),
        )
        .options(
            selectinload(CandidateProfile.skills).selectinload(CandidateSkill.skill),
            selectinload(CandidateProfile.experiences),
            selectinload(CandidateProfile.educations),
        )
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    return CandidatePublicProfile(
        id=profile.id,
        full_name=profile.full_name,
        headline=profile.headline,
        summary=profile.summary,
        city=profile.city,
        country=profile.country,
        availability=profile.availability,
        educations=profile.educations,
        experiences=profile.experiences,
        skills=[
            {"skill": link.skill, "proficiency": link.proficiency, "years_experience": link.years_experience}
            for link in profile.skills
        ],
    )
