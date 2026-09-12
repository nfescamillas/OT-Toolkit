from fastapi.testclient import TestClient

from ot_toolkit_backend.api.auth import verify_password


def test_seeded_password_is_hashed(api_client: TestClient):
    user = api_client.app.state.store.get_user("demo")
    assert user is not None
    assert user.password_hash != "demo-password"
    assert user.password_hash.startswith("$argon2")
    assert verify_password("demo-password", user.password_hash)


def test_register_and_login(api_client: TestClient):
    registered = api_client.post(
        "/api/v1/auth/register",
        json={"username": "field.engineer", "password": "correct-horse-battery"},
    )
    assert registered.status_code == 201
    assert registered.json() == {"username": "field.engineer"}

    login = api_client.post(
        "/api/v1/auth/token",
        json={"username": "field.engineer", "password": "correct-horse-battery"},
    )
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"
    assert login.json()["expires_in"] == 28800
    assert len(login.json()["access_token"]) >= 32


def test_duplicate_registration_and_bad_login_use_api_errors(api_client: TestClient):
    payload = {"username": "demo", "password": "another-password"}
    duplicate = api_client.post("/api/v1/auth/register", json=payload)
    assert duplicate.status_code == 400
    assert duplicate.json()["code"] == "invalid_input"

    denied = api_client.post(
        "/api/v1/auth/token",
        json={"username": "demo", "password": "wrong-password"},
    )
    assert denied.status_code == 401
    assert denied.json()["code"] == "unauthorized"
    assert denied.headers["www-authenticate"] == "Bearer"


def test_favorites_require_authentication_and_are_user_scoped(api_client: TestClient, demo_token: str):
    assert api_client.get("/api/v1/favorites").status_code == 401
    headers = {"Authorization": f"Bearer {demo_token}"}
    saved = api_client.put("/api/v1/favorites/profinet", headers=headers, json={"enabled": True})
    assert saved.status_code == 200
    assert saved.json() == {"items": ["profinet"]}
    assert api_client.get("/api/v1/favorites", headers=headers).json() == {"items": ["profinet"]}

    api_client.post("/api/v1/auth/register", json={"username": "other", "password": "other-password"})
    other_login = api_client.post("/api/v1/auth/token", json={"username": "other", "password": "other-password"})
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}
    assert api_client.get("/api/v1/favorites", headers=other_headers).json() == {"items": []}

