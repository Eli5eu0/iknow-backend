from datetime import datetime, timedelta, timezone

from app.models.user import UserRole


ORIGIN = "http://localhost:5173"
PASSWORD = "a-long-test-password-123"


def _register(client):
    response = client.post(
        "/api/v1/auth/register",
        headers={"Origin": ORIGIN},
        json={"email": "users@example.com", "password": PASSWORD, "role": UserRole.CANDIDATE.value},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def test_read_own_account(client):
    token = _register(client)
    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "users@example.com"
    assert response.json()["role"] == "CANDIDATE"
    assert "password_hash" not in response.json()


def test_change_password_revokes_refresh_sessions(client):
    token = _register(client)
    response = client.patch(
        "/api/v1/users/me/password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": PASSWORD, "new_password": "a-different-long-password-456"},
    )
    assert response.status_code == 204
    login = client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"email": "users@example.com", "password": "a-different-long-password-456"},
    )
    assert login.status_code == 200


def test_deactivation_disables_account_and_recovery_restores_it(client):
    token = _register(client)
    response = client.request(
        "DELETE", "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 202
    assert response.json()["deletion_scheduled_at"]

    blocked = client.post(
        "/api/v1/auth/login",
        headers={"Origin": ORIGIN},
        json={"email": "users@example.com", "password": PASSWORD},
    )
    assert blocked.status_code == 403

    recovered = client.post(
        "/api/v1/users/recover",
        json={"email": "users@example.com", "password": PASSWORD},
    )
    assert recovered.status_code == 200
    assert recovered.json()["is_active"] is True
    assert recovered.json()["deletion_scheduled_at"] is None


def test_recovery_rejects_wrong_password(client):
    token = _register(client)
    response = client.request("DELETE", "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 202
    recovery = client.post(
        "/api/v1/users/recover",
        json={"email": "users@example.com", "password": "incorrect-password"},
    )
    assert recovery.status_code == 401
