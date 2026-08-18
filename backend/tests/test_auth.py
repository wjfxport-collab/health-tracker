import pytest
import auth_service
import database

def test_user_registration_success(client):
    res = client.post("/api/auth/register", json={
        "username": "auth_reg_user",
        "password": "ValidPassword123!"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["success"] is True
    assert "token" in data
    assert data["user"]["username"] == "auth_reg_user"

def test_user_registration_duplicate_username(client):
    # Second attempt with same username should return 409 Conflict
    res = client.post("/api/auth/register", json={
        "username": "auth_reg_user",
        "password": "ValidPassword123!"
    })
    assert res.status_code == 409
    data = res.get_json()
    assert data["success"] is False
    assert "already taken" in data["error"]

def test_user_registration_validation_errors(client):
    # Short username (< 3 chars)
    res = client.post("/api/auth/register", json={
        "username": "ab",
        "password": "ValidPassword123!"
    })
    assert res.status_code == 400

    # Short password (< 6 chars)
    res = client.post("/api/auth/register", json={
        "username": "valid_user",
        "password": "123"
    })
    assert res.status_code == 400

def test_user_login_success(client):
    res = client.post("/api/auth/login", json={
        "username": "auth_reg_user",
        "password": "ValidPassword123!"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "token" in data
    assert data["user"]["username"] == "auth_reg_user"

def test_user_login_invalid_password(client):
    res = client.post("/api/auth/login", json={
        "username": "auth_reg_user",
        "password": "WrongPassword!"
    })
    assert res.status_code == 401
    data = res.get_json()
    assert data["success"] is False
    assert "Invalid username or password" in data["error"]

def test_auth_me_endpoint_with_valid_token(client, test_user):
    res = client.get("/api/auth/me", headers=test_user["auth_headers"])
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["user"]["username"] == test_user["username"]
    assert "passkeys" in data["user"]

def test_auth_me_endpoint_unauthorized(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401
    data = res.get_json()
    assert data["success"] is False

def test_webauthn_register_options(client, test_user):
    res = client.post("/api/auth/webauthn/register/options", headers=test_user["auth_headers"])
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "challenge" in data["options"]
    assert "rp" in data["options"]
    assert data["options"]["user"]["name"] == test_user["username"]

def test_webauthn_login_options(client):
    res = client.post("/api/auth/webauthn/login/options", json={"username": "auth_reg_user"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "challenge" in data["options"]
