from __future__ import annotations

from fastapi.testclient import TestClient


def test_users_admin_access_update_and_search(
    client: TestClient,
    auth_headers,
    users: dict[str, dict[str, object]],
) -> None:
    demo_response = client.get("/api/users", headers=auth_headers("demo", "demo123"))
    assert demo_response.status_code == 403

    admin_headers = auth_headers("admin", "admin123")
    listing = client.get("/api/users", headers=admin_headers)
    assert listing.status_code == 200
    assert {item["username"] for item in listing.json()} == {"admin", "demo"}

    update = client.put(
        f"/api/users/{users['demo']['id']}",
        headers=admin_headers,
        json={"username": "demo_user", "email": "demo@sniffnet.local", "role": "ROLE_USER"},
    )
    assert update.status_code == 200
    assert update.json()["username"] == "demo_user"

    search = client.get("/api/users", headers=admin_headers, params={"search": "demo_"})
    assert search.status_code == 200
    assert [item["username"] for item in search.json()] == ["demo_user"]
