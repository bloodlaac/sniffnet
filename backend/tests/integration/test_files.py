from __future__ import annotations

from fastapi.testclient import TestClient


def test_files_upload_metadata_content_and_invalid_upload(client: TestClient, auth_headers) -> None:
    headers = auth_headers("demo", "demo123")

    upload = client.post(
        "/api/files/images",
        headers=headers,
        files={"file": ("sample.png", b"\x89PNG\r\n\x1a\ncontent", "image/png")},
    )
    assert upload.status_code == 200, upload.text

    image_id = upload.json()["id"]
    metadata = client.get(f"/api/files/images/{image_id}", headers=headers)
    content = client.get(f"/api/files/images/{image_id}/content", headers=headers)
    invalid = client.post(
        "/api/files/images",
        headers=headers,
        files={"file": ("sample.txt", b"text", "text/plain")},
    )

    assert metadata.status_code == 200
    assert metadata.json()["originalFilename"] == "sample.png"
    assert content.status_code == 200
    assert content.headers["content-type"] == "image/png"
    assert invalid.status_code == 400
    assert invalid.json()["message"] == "Unsupported image content type"
