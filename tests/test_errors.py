import logging
from uuid import UUID

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.errors import error_code_for_status
from app.main import create_application

ORIGIN = "http://localhost:5173"
PASSWORD = "a-long-test-password-123"
ENVELOPE_KEYS = {"code", "message", "details", "request_id"}


def _register(client, email="candidate@example.com", role="CANDIDATE", password=PASSWORD):
    return client.post(
        "/api/v1/auth/register",
        headers={"Origin": ORIGIN},
        json={"email": email, "password": password, "role": role},
    )


def _auth(client):
    token = _register(client).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _assert_envelope(response, status, code, message=None):
    assert response.status_code == status
    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    assert set(body) == {"error"}
    error = body["error"]
    assert set(error) == ENVELOPE_KEYS
    assert error["code"] == code
    if message is not None:
        assert error["message"] == message
    assert str(UUID(error["request_id"])) == error["request_id"]
    assert response.headers["x-request-id"] == error["request_id"]
    return error


@pytest.fixture
def error_app():
    """Aplicação nova com rotas que provocam erros que a API real não provoca."""
    application = create_application()

    @application.get("/boom")
    def boom():
        raise RuntimeError("secret-internal-detail")

    @application.get("/rule")
    def rule():
        raise HTTPException(status_code=422, detail="business rule violated")

    @application.get("/structured")
    def structured():
        raise HTTPException(status_code=400, detail={"internal": "value"})

    @application.get("/limited")
    def limited():
        raise HTTPException(status_code=429, detail="Too many requests", headers={"Retry-After": "5"})

    @application.get("/unavailable")
    def unavailable():
        raise HTTPException(status_code=503, detail="Database connection unavailable")

    @application.get("/gone")
    def gone():
        raise HTTPException(status_code=410, detail="Account recovery period has expired")

    return application


def test_error_code_mapping():
    expected = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        410: "GONE",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
        500: "INTERNAL_ERROR",
        503: "HTTP_ERROR",
        418: "HTTP_ERROR",
    }
    for status, code in expected.items():
        assert error_code_for_status(status) == code


def test_unauthorized_keeps_www_authenticate_header(client):
    response = client.get("/api/v1/skills")
    error = _assert_envelope(response, 401, "UNAUTHORIZED", "Invalid or expired access token")
    assert error["details"] is None
    assert response.headers["www-authenticate"] == "Bearer"


def test_forbidden_for_untrusted_origin(client):
    response = client.post(
        "/api/v1/auth/login", json={"email": "a@example.com", "password": PASSWORD}
    )
    _assert_envelope(response, 403, "FORBIDDEN", "Untrusted request origin")


def test_forbidden_for_wrong_role(client):
    token = _register(client, email="company@example.com", role="COMPANY").json()["access_token"]
    response = client.get("/api/v1/candidates/me", headers={"Authorization": f"Bearer {token}"})
    error = _assert_envelope(response, 403, "FORBIDDEN", "Insufficient permissions")
    assert error["details"] is None


def test_not_found_resource(client):
    headers = _auth(client)
    response = client.get("/api/v1/skills/00000000-0000-4000-8000-000000000000", headers=headers)
    error = _assert_envelope(response, 404, "NOT_FOUND", "Skill not found")
    assert error["details"] is None


def test_unknown_route_is_not_found_in_envelope(client):
    _assert_envelope(client.get("/api/v1/does-not-exist"), 404, "NOT_FOUND", "Not Found")


def test_method_not_allowed(client):
    _assert_envelope(client.post("/api/v1/health"), 405, "METHOD_NOT_ALLOWED", "Method Not Allowed")


def test_conflict_on_duplicate_email(client):
    assert _register(client).status_code == 201
    _assert_envelope(_register(client), 409, "CONFLICT", "Email already registered")


def test_bad_request_on_wrong_current_password(client):
    headers = _auth(client)
    response = client.patch(
        "/api/v1/users/me/password",
        headers=headers,
        json={"current_password": "not-the-password", "new_password": "another-long-password-1"},
    )
    _assert_envelope(response, 400, "BAD_REQUEST", "Current password is incorrect")


def test_validation_error_details_have_no_input_or_context(client):
    submitted = "Zq9!x"  # curta de mais: provoca o erro e não deve ser devolvida
    response = _register(client, password=submitted)
    error = _assert_envelope(response, 422, "VALIDATION_ERROR", "Request validation failed")
    assert isinstance(error["details"], list) and error["details"]
    for issue in error["details"]:
        assert set(issue) == {"type", "loc", "msg"}
    assert error["details"][0]["loc"] == ["body", "password"]
    assert submitted not in response.text
    assert '"input"' not in response.text and '"ctx"' not in response.text


def test_validation_error_for_query_and_path_parameters(client):
    headers = _auth(client)
    query = client.get("/api/v1/skills", headers=headers, params={"page": 0})
    error = _assert_envelope(query, 422, "VALIDATION_ERROR")
    assert error["details"][0]["loc"] == ["query", "page"]

    path = client.get("/api/v1/skills/not-a-uuid", headers=headers)
    error = _assert_envelope(path, 422, "VALIDATION_ERROR")
    assert error["details"][0]["loc"] == ["path", "skill_id"]


def test_business_rule_422_has_null_details(error_app):
    response = TestClient(error_app).get("/rule")
    error = _assert_envelope(response, 422, "VALIDATION_ERROR", "business rule violated")
    assert error["details"] is None


def test_non_string_detail_is_not_leaked(error_app):
    response = TestClient(error_app).get("/structured")
    error = _assert_envelope(response, 400, "BAD_REQUEST", "Bad Request")
    assert "internal" not in response.text


def test_rate_limited_and_custom_headers_are_preserved(error_app):
    response = TestClient(error_app).get("/limited")
    _assert_envelope(response, 429, "RATE_LIMITED", "Too many requests")
    assert response.headers["retry-after"] == "5"


def test_other_statuses_use_generic_code(error_app):
    client = TestClient(error_app)
    _assert_envelope(client.get("/unavailable"), 503, "HTTP_ERROR", "Database connection unavailable")
    _assert_envelope(client.get("/gone"), 410, "GONE", "Account recovery period has expired")


def test_unhandled_exception_returns_500_without_leaking(error_app, caplog):
    client = TestClient(error_app, raise_server_exceptions=False)
    with caplog.at_level(logging.ERROR, logger="iknow.errors"):
        response = client.get("/boom", headers={"Origin": ORIGIN})
    error = _assert_envelope(response, 500, "INTERNAL_ERROR", "Internal server error")
    assert error["details"] is None
    assert "secret-internal-detail" not in response.text
    assert response.headers["access-control-allow-origin"] == ORIGIN
    assert error["request_id"] in caplog.text
    assert "secret-internal-detail" in caplog.text


def test_request_id_is_generated_per_request_and_ignores_client_value(client):
    first = client.get("/api/v1/does-not-exist", headers={"X-Request-ID": "client-chosen"})
    second = client.get("/api/v1/does-not-exist")
    first_id = first.json()["error"]["request_id"]
    assert first_id != "client-chosen"
    assert first_id != second.json()["error"]["request_id"]
    assert first.headers["x-request-id"] == first_id


def test_request_id_header_is_present_on_success(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    UUID(response.headers["x-request-id"])
    assert "error" not in response.json()


def test_cors_preflight_is_not_affected(client):
    response = client.options(
        "/api/v1/skills",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ORIGIN
    assert "error" not in response.text


def test_openapi_documents_the_error_format(client):
    schema = client.app.openapi()
    components = schema["components"]["schemas"]
    assert {"ErrorResponse", "ErrorBody", "ValidationIssue"} <= set(components)
    assert "HTTPValidationError" not in components and "ValidationError" not in components
    refs = {
        operation["responses"]["422"]["content"]["application/json"]["schema"]["$ref"]
        for path in schema["paths"].values()
        for operation in path.values()
        if "422" in operation["responses"]
    }
    assert refs == {"#/components/schemas/ErrorResponse"}
    assert set(components["ErrorBody"]["required"]) == {"code", "message", "request_id"}
