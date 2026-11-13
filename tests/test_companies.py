from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.db.session import get_db
from app.models.company import Company, CompanyVerificationStatus
from app.models.user import User
from app.services import company_service

ORIGIN = "http://localhost:5173"
PASSWORD = "a-long-test-password-123"
ME = "/api/v1/companies/me"
PROFILE_FIELDS = ["name", "legal_name", "tax_id", "description", "city", "country"]

COMPLETE = {
    "name": "Tech Solutions Angola",
    "legal_name": "Tech Solutions Angola, Lda.",
    "tax_id": "5417000001",
    "description": "Desenvolvimento de software.",
    "city": "Luanda",
    "country": "Angola",
}


def _register(client, email="company@example.com", role="COMPANY"):
    response = client.post(
        "/api/v1/auth/register",
        headers={"Origin": ORIGIN},
        json={"email": email, "password": PASSWORD, "role": role},
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _db(client):
    return next(client.app.dependency_overrides[get_db]())


def _company_id(client, headers) -> str:
    return client.get(ME, headers=headers).json()["id"]


def _completed_company(client, email="company@example.com", **overrides):
    headers = _register(client, email=email)
    response = client.patch(ME, headers=headers, json={**COMPLETE, **overrides})
    assert response.status_code == 200, response.text
    return headers, response.json()


def _error(response, status, code):
    assert response.status_code == status, response.text
    error = response.json()["error"]
    assert error["code"] == code
    return error


def test_registration_creates_an_empty_company_only_for_company_accounts(client):
    _register(client, email="company@example.com", role="COMPANY")
    _register(client, email="candidate@example.com", role="CANDIDATE")

    db = _db(client)
    try:
        companies = db.scalars(select(Company)).all()
        assert len(companies) == 1
        company = companies[0]
        assert company.name is None and company.tax_id is None
        assert company.verification_status == CompanyVerificationStatus.NOT_SUBMITTED
        owner = db.get(User, company.user_id)
        assert owner.email == "company@example.com"
    finally:
        db.close()


def test_get_my_company_returns_an_empty_incomplete_profile(client):
    headers = _register(client)
    response = client.get(ME, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "id", "name", "legal_name", "tax_id", "description", "website", "city", "country",
        "verification_status", "profile_completed", "missing_fields", "created_at", "updated_at",
    }
    UUID(body["id"])
    assert all(body[field] is None for field in [*PROFILE_FIELDS, "website"])
    assert body["verification_status"] == "NOT_SUBMITTED"
    assert body["profile_completed"] is False
    assert body["missing_fields"] == PROFILE_FIELDS


def test_get_is_side_effect_free_and_stable(client):
    headers = _register(client)
    first = client.get(ME, headers=headers).json()
    second = client.get(ME, headers=headers).json()
    assert first == second


def test_partial_save_then_completion(client):
    headers = _register(client)

    first = client.patch(ME, headers=headers, json={"name": "Tech Solutions Angola"})
    assert first.status_code == 200
    assert first.json()["name"] == "Tech Solutions Angola"
    assert first.json()["profile_completed"] is False
    assert first.json()["missing_fields"] == PROFILE_FIELDS[1:]

    rest = {key: value for key, value in COMPLETE.items() if key != "name"}
    done = client.patch(ME, headers=headers, json=rest)
    assert done.status_code == 200
    body = done.json()
    assert body["profile_completed"] is True
    assert body["missing_fields"] == []
    assert {key: body[key] for key in COMPLETE} == COMPLETE

    assert client.get(ME, headers=headers).json() == body


def test_only_sent_fields_change_and_empty_body_is_a_noop(client):
    headers, before = _completed_company(client)

    changed = client.patch(ME, headers=headers, json={"city": "Benguela"}).json()
    assert changed["city"] == "Benguela"
    assert {key: changed[key] for key in COMPLETE if key != "city"} == {
        key: before[key] for key in COMPLETE if key != "city"
    }

    noop = client.patch(ME, headers=headers, json={})
    assert noop.status_code == 200
    assert noop.json()["city"] == "Benguela"
    assert noop.json()["profile_completed"] is True


@pytest.mark.parametrize("field", PROFILE_FIELDS)
def test_required_fields_reject_null_blank_and_too_long(client, field):
    headers, _ = _completed_company(client)

    null = client.patch(ME, headers=headers, json={field: None})
    error = _error(null, 422, "VALIDATION_ERROR")
    assert error["details"][0]["loc"] == ["body", field]

    for value in ("", "   "):
        blank = client.patch(ME, headers=headers, json={field: value})
        assert blank.status_code == 422, (field, value)

    too_long = client.patch(ME, headers=headers, json={field: "x" * 5001})
    assert too_long.status_code == 422

    assert client.get(ME, headers=headers).json()[field] == COMPLETE[field]


def test_text_values_are_trimmed(client):
    headers = _register(client)
    response = client.patch(ME, headers=headers, json={"name": "  Tech Solutions  ", "tax_id": " 123 "})
    assert response.json()["name"] == "Tech Solutions"
    assert response.json()["tax_id"] == "123"


def test_website_validation_and_clearing(client):
    headers = _register(client)
    for invalid in ("example.com", "ftp://example.com", "http://", "https://", "http://a b.com", ""):
        response = client.patch(ME, headers=headers, json={"website": invalid})
        assert response.status_code == 422, invalid
        assert response.json()["error"]["details"][0]["loc"] == ["body", "website"]

    ok = client.patch(ME, headers=headers, json={"website": "HTTPS://example.com/about"})
    assert ok.status_code == 200 and ok.json()["website"] == "HTTPS://example.com/about"

    cleared = client.patch(ME, headers=headers, json={"website": None})
    assert cleared.status_code == 200 and cleared.json()["website"] is None
    assert client.patch(ME, headers=headers, json={"website": "x" * 250 + ".com"}).status_code == 422


@pytest.mark.parametrize("field", ["verification_status", "id", "user_id", "profile_completed", "missing_fields", "unknown"])
def test_unknown_and_protected_fields_are_rejected(client, field):
    headers = _register(client)
    value = "VERIFIED" if field == "verification_status" else "x"
    response = client.patch(ME, headers=headers, json={field: value})
    error = _error(response, 422, "VALIDATION_ERROR")
    assert error["details"][0]["type"] == "extra_forbidden"
    assert client.get(ME, headers=headers).json()["verification_status"] == "NOT_SUBMITTED"


def test_tax_id_must_be_unique_across_companies(client):
    headers_a, _ = _completed_company(client, email="a@example.com")
    headers_b = _register(client, email="b@example.com")
    client.patch(ME, headers=headers_b, json={"name": "Outra Empresa", "tax_id": "OTHER-1"})

    conflict = client.patch(ME, headers=headers_b, json={"tax_id": COMPLETE["tax_id"]})
    error = _error(conflict, 409, "CONFLICT")
    assert error["message"] == "Tax ID already registered"
    assert client.get(ME, headers=headers_b).json()["tax_id"] == "OTHER-1"

    again = client.patch(ME, headers=headers_a, json={"tax_id": COMPLETE["tax_id"]})
    assert again.status_code == 200


def test_tax_id_conflict_is_also_caught_when_the_database_rejects_it(client):
    _completed_company(client, email="a@example.com")
    _register(client, email="b@example.com")

    db = _db(client)
    try:
        user_b = db.scalar(select(User).where(User.email == "b@example.com"))
        real_scalar = db.scalar
        calls = {"count": 0}

        def scalar_missing_the_precheck(*args, **kwargs):
            calls["count"] += 1
            return None if calls["count"] == 2 else real_scalar(*args, **kwargs)

        db.scalar = scalar_missing_the_precheck
        with pytest.raises(HTTPException) as caught:
            company_service.update_company(db, user_b, {"tax_id": COMPLETE["tax_id"]})
        assert caught.value.status_code == 409
        assert caught.value.detail == "Tax ID already registered"
    finally:
        db.close()


def test_company_endpoints_require_authentication_and_the_company_role(client):
    assert _error(client.get(ME), 401, "UNAUTHORIZED")
    assert _error(client.patch(ME, json={"name": "x"}), 401, "UNAUTHORIZED")

    candidate = _register(client, email="candidate@example.com", role="CANDIDATE")
    assert _error(client.get(ME, headers=candidate), 403, "FORBIDDEN")["message"] == "Insufficient permissions"
    assert _error(client.patch(ME, headers=candidate, json={"name": "x"}), 403, "FORBIDDEN")

    company = _register(client)
    assert client.delete("/api/v1/users/me", headers=company).status_code == 202
    assert _error(client.get(ME, headers=company), 401, "UNAUTHORIZED")


def test_company_without_a_row_gets_404(client):
    headers = _register(client)
    db = _db(client)
    try:
        for company in db.scalars(select(Company)).all():
            db.delete(company)
        db.commit()
    finally:
        db.close()

    assert _error(client.get(ME, headers=headers), 404, "NOT_FOUND")["message"] == "Company profile not found"
    assert _error(client.patch(ME, headers=headers, json={"name": "x"}), 404, "NOT_FOUND")


def test_public_profile_shows_only_public_fields(client):
    _, mine = _completed_company(client, website="https://example.com")
    candidate = _register(client, email="candidate@example.com", role="CANDIDATE")

    response = client.get(f"/api/v1/companies/{mine['id']}", headers=candidate)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"id", "name", "description", "website", "city", "country", "is_verified"}
    assert body == {
        "id": mine["id"],
        "name": COMPLETE["name"],
        "description": COMPLETE["description"],
        "website": "https://example.com",
        "city": COMPLETE["city"],
        "country": COMPLETE["country"],
        "is_verified": False,
    }
    assert COMPLETE["tax_id"] not in response.text and COMPLETE["legal_name"] not in response.text

    other_company = _register(client, email="other@example.com")
    assert client.get(f"/api/v1/companies/{mine['id']}", headers=other_company).status_code == 200


def test_public_profile_reports_verification_only_as_a_boolean(client):
    _, mine = _completed_company(client)
    viewer = _register(client, email="candidate@example.com", role="CANDIDATE")

    db = _db(client)
    try:
        for status in (CompanyVerificationStatus.REJECTED, CompanyVerificationStatus.SUSPENDED,
                       CompanyVerificationStatus.PENDING, CompanyVerificationStatus.VERIFIED):
            company = db.get(Company, UUID(mine["id"]))
            company.verification_status = status
            db.commit()
            body = client.get(f"/api/v1/companies/{mine['id']}", headers=viewer).json()
            assert body["is_verified"] is (status == CompanyVerificationStatus.VERIFIED)
            assert "verification_status" not in body
    finally:
        db.close()


def test_public_profile_is_hidden_when_incomplete_unknown_or_owner_inactive(client):
    viewer = _register(client, email="candidate@example.com", role="CANDIDATE")

    incomplete_headers = _register(client, email="incomplete@example.com")
    incomplete_id = _company_id(client, incomplete_headers)
    client.patch(ME, headers=incomplete_headers, json={"name": "So o nome"})
    error = _error(client.get(f"/api/v1/companies/{incomplete_id}", headers=viewer), 404, "NOT_FOUND")
    assert error["message"] == "Company not found"

    assert _error(client.get(f"/api/v1/companies/{uuid4()}", headers=viewer), 404, "NOT_FOUND")

    owner, mine = _completed_company(client, email="active@example.com")
    assert client.get(f"/api/v1/companies/{mine['id']}", headers=viewer).status_code == 200
    assert client.delete("/api/v1/users/me", headers=owner).status_code == 202
    assert _error(client.get(f"/api/v1/companies/{mine['id']}", headers=viewer), 404, "NOT_FOUND")


def test_public_profile_requires_authentication_and_a_valid_uuid(client):
    assert _error(client.get(f"/api/v1/companies/{uuid4()}"), 401, "UNAUTHORIZED")

    viewer = _register(client, email="candidate@example.com", role="CANDIDATE")
    error = _error(client.get("/api/v1/companies/not-a-uuid", headers=viewer), 422, "VALIDATION_ERROR")
    assert error["details"][0]["loc"] == ["path", "company_id"]


def test_me_is_not_shadowed_by_the_company_id_route(client):
    headers = _register(client)
    assert client.get(ME, headers=headers).status_code == 200
    candidate = _register(client, email="candidate@example.com", role="CANDIDATE")
    assert client.get(ME, headers=candidate).status_code == 403


def test_only_company_endpoints_of_the_contract_exist(client):
    headers = _register(client)
    assert client.post(ME, headers=headers, json={}).status_code == 405
    assert client.put(ME, headers=headers, json={}).status_code == 405
    assert client.delete(ME, headers=headers).status_code == 405
    # GET /companies/me/opportunities pertence ao módulo OPPORTUNITIES (decisão aprovada).
    assert client.get(f"{ME}/opportunities", headers=headers).status_code == 404


def test_openapi_documents_the_company_contract(client):
    schema = client.app.openapi()
    assert set(schema["paths"]["/api/v1/companies/me"]) == {"get", "patch"}
    assert set(schema["paths"]["/api/v1/companies/{company_id}"]) == {"get"}
    components = schema["components"]["schemas"]
    assert "verification_status" not in components["CompanyUpdate"]["properties"]
    assert components["CompanyUpdate"]["additionalProperties"] is False
    assert set(components["CompanyPublicRead"]["properties"]) == {
        "id", "name", "description", "website", "city", "country", "is_verified",
    }
