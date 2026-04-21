from __future__ import annotations

from fastapi.testclient import TestClient


def test_auth_flow_register_login_and_me(client: TestClient) -> None:
    register = client.post(
        "/api/auth/register",
        json={"username": "student", "email": "student@sniffnet.local", "password": "secret123"},
    )
    assert register.status_code == 201, register.text

    login = client.post("/api/auth/login", json={"username": "student", "password": "secret123"})
    assert login.status_code == 200, login.text

    token = login.json()["token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert me.status_code == 200
    assert me.json()["username"] == "student"
    assert me.json()["role"] == "ROLE_USER"
