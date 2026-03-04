"""Tests for authentication endpoints."""


def test_register_success(client):
    res = client.post("/api/auth/register", json={
        "email": "new@test.com",
        "username": "newuser",
        "password": "Pass1234",
    })
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "new@test.com"
    assert data["user"]["role"] == "viewer"


def test_register_duplicate_email(client):
    payload = {"email": "dup@test.com", "username": "u1", "password": "Pass1234"}
    client.post("/api/auth/register", json=payload)
    res = client.post("/api/auth/register", json={
        **payload, "username": "u2",
    })
    assert res.status_code == 409


def test_register_duplicate_username(client):
    client.post("/api/auth/register", json={
        "email": "a@test.com", "username": "same", "password": "Pass1234",
    })
    res = client.post("/api/auth/register", json={
        "email": "b@test.com", "username": "same", "password": "Pass1234",
    })
    assert res.status_code == 409


def test_login_success(client):
    client.post("/api/auth/register", json={
        "email": "login@test.com", "username": "loginuser", "password": "Pass1234",
    })
    res = client.post("/api/auth/login", json={
        "email": "login@test.com", "password": "Pass1234",
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_wrong_password(client):
    client.post("/api/auth/register", json={
        "email": "wp@test.com", "username": "wpuser", "password": "Pass1234",
    })
    res = client.post("/api/auth/login", json={
        "email": "wp@test.com", "password": "WrongPass",
    })
    assert res.status_code == 401


def test_login_nonexistent_user(client):
    res = client.post("/api/auth/login", json={
        "email": "noone@test.com", "password": "Pass1234",
    })
    assert res.status_code == 401


def test_me_authenticated(client, auth_headers):
    res = client.get("/api/auth/me", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["username"] == "testuser"


def test_me_unauthenticated(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 403 or res.status_code == 401


def test_me_invalid_token(client):
    res = client.get("/api/auth/me", headers={
        "Authorization": "Bearer invalid-token-here",
    })
    assert res.status_code == 401


def test_refresh_token(client):
    client.post("/api/auth/register", json={
        "email": "ref@test.com", "username": "refuser", "password": "Pass1234",
    })
    login = client.post("/api/auth/login", json={
        "email": "ref@test.com", "password": "Pass1234",
    })
    refresh_token = login.json()["refresh_token"]
    res = client.post("/api/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert res.status_code == 200
    assert "access_token" in res.json()
