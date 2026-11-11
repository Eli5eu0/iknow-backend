from app.models.user import UserRole


ORIGIN = "http://localhost:5173"


def _register(client):
    return client.post(
        "/api/v1/auth/register",
        headers={"Origin": ORIGIN},
        json={
            "email": "candidate@example.com",
            "password": "a-long-test-password-123",
            "role": UserRole.CANDIDATE.value,
        },
    )


def test_register_sets_httponly_refresh_cookie_and_returns_access_and_csrf(client):
    response = _register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["csrf_token"]
    assert body["user"]["email"] == "candidate@example.com"
    assert "refresh_token" not in body
    cookie = response.headers["set-cookie"].lower()
    assert "iknow_refresh=" in cookie
    assert "httponly" in cookie
    assert "samesite=lax" in cookie


def test_login_and_authenticated_me(client):
    _register(client)
    response = client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"email": "CANDIDATE@example.com", "password": "a-long-test-password-123"},
    )

    assert response.status_code == 200
    access_token = response.json()["access_token"]
    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me.status_code == 200
    assert me.json()["role"] == "CANDIDATE"


def test_login_rejects_wrong_password(client):
    _register(client)
    response = client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"email": "candidate@example.com", "password": "incorrect-password"},
    )
    assert response.status_code == 401


def test_refresh_rotates_refresh_and_csrf_tokens(client):
    registered = _register(client)
    old_refresh = client.cookies.get("iknow_refresh")
    old_csrf = registered.json()["csrf_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": ORIGIN, "X-CSRF-Token": old_csrf},
    )

    assert response.status_code == 200
    assert response.json()["csrf_token"] != old_csrf
    assert client.cookies.get("iknow_refresh") != old_refresh


def test_refresh_requires_csrf_token(client):
    _register(client)
    response = client.post("/api/v1/auth/refresh", headers={"Origin": ORIGIN})
    assert response.status_code == 403


def test_reuse_of_revoked_refresh_token_revokes_token_family(client):
    registered = _register(client)
    old_refresh = client.cookies.get("iknow_refresh")
    old_csrf = registered.json()["csrf_token"]

    rotated = client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": ORIGIN, "X-CSRF-Token": old_csrf},
    )
    assert rotated.status_code == 200
    new_refresh = client.cookies.get("iknow_refresh")

    reused = client.post(
        "/api/v1/auth/refresh",
        headers={
            "Origin": ORIGIN,
            "X-CSRF-Token": old_csrf,
            "Cookie": f"iknow_refresh={old_refresh}",
        },
    )
    assert reused.status_code == 401

    # A token from the same family is now invalid after reuse was detected.
    client.cookies.set("iknow_refresh", new_refresh, path="/api/v1/auth")
    after_reuse = client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": ORIGIN, "X-CSRF-Token": rotated.json()["csrf_token"]},
    )
    assert after_reuse.status_code == 401


def test_logout_revokes_session_and_clears_cookie(client):
    registered = _register(client)
    csrf_token = registered.json()["csrf_token"]

    response = client.post(
        "/api/v1/auth/logout",
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_token},
    )
    assert response.status_code == 204
    assert "iknow_refresh=" in response.headers.get("set-cookie", "")


def test_auth_endpoints_reject_untrusted_origin(client):
    response = client.post(
        "/api/v1/auth/register",
        headers={"Origin": "https://attacker.example"},
        json={
            "email": "attacker@example.com",
            "password": "a-long-test-password-123",
            "role": "CANDIDATE",
        },
    )
    assert response.status_code == 403


def test_me_requires_bearer_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_csrf_endpoint_returns_stable_token_for_existing_session(client):
    registered = _register(client)
    original_csrf = registered.json()["csrf_token"]

    response = client.get("/api/v1/auth/csrf", headers={"Origin": ORIGIN})

    assert response.status_code == 200
    assert response.json()["csrf_token"] == original_csrf
