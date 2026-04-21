from __future__ import annotations

from fastapi.testclient import TestClient
import pytest


def test_classifications_support_file_upload_history_and_detail(
    client: TestClient,
    auth_headers,
    seed_inference_model,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_inference_model()
    headers = auth_headers("demo", "demo123")
    monkeypatch.setattr(
        "sniffnet.api.routes.classifications._predict_image",
        lambda model, image_path: ("Fresh", 0.98, {"Fresh": 0.98, "Bad": 0.02}),
    )

    created = client.post(
        "/api/classifications",
        headers=headers,
        files={"file": ("sample.png", b"\x89PNG\r\n\x1a\ncontent", "image/png")},
        data={"modelId": str(seeded["model_id"])},
    )
    assert created.status_code == 201, created.text

    classification_id = created.json()["id"]
    listing = client.get("/api/classifications", headers=headers)
    detail = client.get(f"/api/classifications/{classification_id}", headers=headers)

    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert detail.status_code == 200
    assert detail.json()["predictedClass"] == "Fresh"
    assert detail.json()["probabilities"]["Fresh"] == pytest.approx(0.98)


def test_classifications_support_image_id_and_owner_access_control(
    client: TestClient,
    auth_headers,
    seed_inference_model,
    monkeypatch,
) -> None:
    seeded = seed_inference_model()
    headers = auth_headers("demo", "demo123")
    client.post(
        "/api/auth/register",
        json={"username": "outsider", "email": "outsider@sniffnet.local", "password": "secret123"},
    )
    outsider_headers = auth_headers("outsider", "secret123")

    uploaded = client.post(
        "/api/files/images",
        headers=headers,
        files={"file": ("sample.png", b"\x89PNG\r\n\x1a\ncontent", "image/png")},
    )
    assert uploaded.status_code == 200, uploaded.text

    monkeypatch.setattr(
        "sniffnet.api.routes.classifications._predict_image",
        lambda model, image_path: ("Bad", 0.76, {"Fresh": 0.24, "Bad": 0.76}),
    )
    created = client.post(
        "/api/classifications",
        headers=headers,
        data={"modelId": str(seeded["model_id"]), "imageId": str(uploaded.json()["id"])},
    )
    assert created.status_code == 201, created.text

    forbidden_classification = client.get(f"/api/classifications/{created.json()['id']}", headers=outsider_headers)
    forbidden_image = client.get(f"/api/files/images/{uploaded.json()['id']}", headers=outsider_headers)

    assert created.json()["predictedClass"] == "Bad"
    assert forbidden_classification.status_code == 404
    assert forbidden_image.status_code == 404
