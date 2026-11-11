from datetime import date
from uuid import uuid4

from app.models.skill import Skill
from app.models.user import UserRole

ORIGIN = "http://localhost:5173"
PASSWORD = "a-long-test-password-123"


def _register(client, email="candidate@example.com", role="CANDIDATE"):
    response = client.post(
        "/api/v1/auth/register",
        headers={"Origin": ORIGIN},
        json={"email": email, "password": PASSWORD, "role": role},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_candidate_profile_is_created_by_explicit_upsert_not_get(client):
    token = _register(client)
    headers = _auth(token)

    missing = client.get("/api/v1/candidates/me", headers=headers)
    assert missing.status_code == 404

    created = client.put(
        "/api/v1/candidates/me",
        headers=headers,
        json={"full_name": "Ana Candidate", "availability": "Disponível imediatamente"},
    )
    assert created.status_code == 200
    assert created.json()["full_name"] == "Ana Candidate"
    assert created.json()["is_public"] is True

    fetched = client.get("/api/v1/candidates/me", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["id"] == created.json()["id"]


def test_profile_patch_preserves_omitted_fields(client):
    token = _register(client)
    headers = _auth(token)
    client.put("/api/v1/candidates/me", headers=headers, json={"full_name": "Ana", "city": "Luanda"})

    response = client.patch("/api/v1/candidates/me", headers=headers, json={"headline": "Designer"})
    assert response.status_code == 200
    assert response.json()["full_name"] == "Ana"
    assert response.json()["city"] == "Luanda"
    assert response.json()["headline"] == "Designer"


def test_public_profile_hides_private_fields_and_visibility_can_be_disabled(client):
    token = _register(client)
    headers = _auth(token)
    created = client.put(
        "/api/v1/candidates/me",
        headers=headers,
        json={"full_name": "Ana", "phone": "+244900000000", "headline": "Analista"},
    )
    profile_id = created.json()["id"]

    public = client.get(f"/api/v1/candidates/{profile_id}")
    assert public.status_code == 200
    body = public.json()
    assert body["full_name"] == "Ana"
    assert "phone" not in body
    assert "email" not in body
    assert "user_id" not in body

    hidden = client.patch(
        "/api/v1/candidates/me/visibility", headers=headers, json={"is_public": False}
    )
    assert hidden.status_code == 200
    assert hidden.json()["is_public"] is False
    assert client.get(f"/api/v1/candidates/{profile_id}").status_code == 404


def test_candidate_cannot_access_company_candidate_endpoints(client):
    token = _register(client, email="company@example.com", role=UserRole.COMPANY.value)
    response = client.put("/api/v1/candidates/me", headers=_auth(token), json={"full_name": "No"})
    assert response.status_code == 403


def test_experience_is_optional_and_crud_is_scoped_to_owner(client):
    token = _register(client)
    headers = _auth(token)
    profile = client.put("/api/v1/candidates/me", headers=headers, json={})
    assert profile.status_code == 200
    assert client.get("/api/v1/candidates/me/experiences", headers=headers).json() == []

    created = client.post(
        "/api/v1/candidates/me/experiences",
        headers=headers,
        json={
            "company_name": "Empresa X",
            "job_title": "Estagiário",
            "start_date": "2024-01-01",
            "is_current": True,
        },
    )
    assert created.status_code == 201
    record_id = created.json()["id"]
    assert client.patch(
        f"/api/v1/candidates/me/experiences/{record_id}",
        headers=headers,
        json={"end_date": "2025-01-01"},
    ).status_code == 422

    other_token = _register(client, email="other@example.com")
    client.put("/api/v1/candidates/me", headers=_auth(other_token), json={})
    assert client.patch(
        f"/api/v1/candidates/me/experiences/{record_id}",
        headers=_auth(other_token),
        json={"job_title": "Intrusão"},
    ).status_code == 404


def test_education_and_skill_catalogue_association(client):
    token = _register(client)
    headers = _auth(token)
    client.put("/api/v1/candidates/me", headers=headers, json={})

    education = client.post(
        "/api/v1/candidates/me/educations",
        headers=headers,
        json={"institution": "Universidade A", "start_date": "2022-02-01", "is_current": True},
    )
    assert education.status_code == 201

    db_override = client.app.dependency_overrides
    from app.db.session import get_db
    db = next(db_override[get_db]())
    try:
        skill = Skill(name="Python", slug=f"python-{uuid4().hex[:8]}", category="Technology")
        db.add(skill)
        db.commit()
        skill_id = str(skill.id)
    finally:
        db.close()

    added = client.post(
        "/api/v1/candidates/me/skills",
        headers=headers,
        json={"skill_id": skill_id, "proficiency": "ADVANCED", "years_experience": 2.5},
    )
    assert added.status_code == 201
    assert added.json()["skill"]["name"] == "Python"

    duplicate = client.post(
        "/api/v1/candidates/me/skills",
        headers=headers,
        json={"skill_id": skill_id},
    )
    assert duplicate.status_code == 409


def test_public_profile_is_not_available_for_inactive_account(client):
    token = _register(client)
    headers = _auth(token)
    profile = client.put("/api/v1/candidates/me", headers=headers, json={}).json()
    client.request("DELETE", "/api/v1/users/me", headers=headers)
    assert client.get(f"/api/v1/candidates/{profile['id']}").status_code == 404
