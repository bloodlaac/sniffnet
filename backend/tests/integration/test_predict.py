from __future__ import annotations

import torch
from fastapi.testclient import TestClient

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\x99c\xf8\xff\xff?"
    b"\x00\x05\xfe\x02\xfeA\xa4\x8e\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
)


class FakeModel:
    def __init__(self) -> None:
        self._param = torch.nn.Parameter(torch.zeros(1))

    def parameters(self):
        yield self._param

    def __call__(self, tensor):
        return torch.tensor([[0.2, 0.8]], dtype=torch.float32)


def test_predict_endpoint_returns_class_probabilities(client: TestClient, seed_inference_model, monkeypatch) -> None:
    seeded = seed_inference_model(weights_filename="predict-success.pth")
    monkeypatch.setattr(
        "sniffnet.api.routes.predict.load_model_for_weights",
        lambda path, device: (FakeModel(), lambda image: torch.zeros(3, 224, 224), ["Fresh", "Bad"]),
    )

    response = client.post(
        "/api/predict",
        data={"model_id": str(seeded["model_id"])},
        files={"file": ("sample.png", PNG_BYTES, "image/png")},
    )

    assert response.status_code == 200, response.text
    assert response.json()["class"] == "Bad"
    assert response.json()["probs"]["Bad"] > response.json()["probs"]["Fresh"]


def test_predict_endpoint_handles_missing_model_and_loading_errors(
    client: TestClient,
    seed_inference_model,
    model_weights_dir,
    session_factory,
    monkeypatch,
) -> None:
    missing_model = client.post(
        "/api/predict",
        data={"model_id": "9999"},
        files={"file": ("sample.png", PNG_BYTES, "image/png")},
    )
    assert missing_model.status_code == 404

    seeded = seed_inference_model(weights_filename="predict-error.pth")
    (model_weights_dir / "predict-error.pth").unlink()
    missing_weights = client.post(
        "/api/predict",
        data={"model_id": str(seeded["model_id"])},
        files={"file": ("sample.png", PNG_BYTES, "image/png")},
    )
    assert missing_weights.status_code == 404

    seeded = seed_inference_model(weights_filename="predict-loader.pth")
    monkeypatch.setattr("sniffnet.api.routes.predict.load_model_for_weights", lambda path, device: (_ for _ in ()).throw(RuntimeError("boom")))
    loader_error = client.post(
        "/api/predict",
        data={"model_id": str(seeded["model_id"])},
        files={"file": ("sample.png", PNG_BYTES, "image/png")},
    )

    assert loader_error.status_code == 400
    assert loader_error.json()["detail"] == "boom"
