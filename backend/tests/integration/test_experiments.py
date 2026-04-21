from __future__ import annotations

import json

from fastapi.testclient import TestClient
from sqlalchemy import select

from sniffnet.database.db_models import ClassificationRequest, Experiment, Metric, Model, TrainingConfig, UploadedImage


def test_experiments_create_list_detail_state_and_status_update(
    client: TestClient,
    auth_headers,
    dataset: dict[str, object],
    test_context,
) -> None:
    headers = auth_headers("demo", "demo123")
    admin_headers = auth_headers("admin", "admin123")

    created = client.post(
        "/api/experiments",
        headers=headers,
        json={
            "datasetId": dataset["id"],
            "config": {
                "epochsNum": 3,
                "batchSize": 8,
                "learningRate": 0.01,
                "optimizer": "Adam",
                "lossFunction": "CrossEntropyLoss",
                "validationSplit": 0.2,
                "layersNum": 2,
                "neuronsNum": 32,
            },
        },
    )
    assert created.status_code == 201, created.text
    experiment_id = created.json()["id"]

    listing = client.get("/api/experiments", headers=headers)
    detail = client.get(f"/api/experiments/{experiment_id}", headers=headers)
    state = client.get(f"/api/experiments/{experiment_id}/state", headers=headers)
    updated = client.patch(
        f"/api/experiments/{experiment_id}/status",
        headers=admin_headers,
        json={"status": "FAILED"},
    )

    assert len(test_context.started_threads) == 1
    assert test_context.started_threads[0].started is True
    assert listing.status_code == 200
    assert listing.json()[0]["id"] == experiment_id
    assert detail.status_code == 200
    assert detail.json()["datasetName"] == "Products Dataset"
    assert state.status_code == 200
    assert state.json()["experiment_id"] == experiment_id
    assert updated.status_code == 200
    assert updated.json()["status"] == "FAILED"
    assert updated.json()["errorMessage"] is None


def test_experiments_delete_removes_related_model_metrics_classifications_and_files(
    client: TestClient,
    auth_headers,
    session_factory,
    seed_inference_model,
    model_weights_dir,
    image_storage_dir,
) -> None:
    seeded = seed_inference_model(weights_filename="model-delete.pth")
    history_path = model_weights_dir / "model-delete.json"
    history_path.write_text(
        json.dumps(
            {
                "train_accuracy_history": [0.7],
                "val_accuracy_history": [0.68],
                "train_loss_history": [0.3],
                "val_loss_history": [0.35],
            }
        ),
        encoding="utf-8",
    )
    image_path = image_storage_dir / "uploaded.png"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.write_bytes(b"png")

    with session_factory() as session:
        image = UploadedImage(
            user_id=seeded["user_id"],
            original_filename="uploaded.png",
            stored_filename="uploaded.png",
            content_type="image/png",
            size_bytes=3,
            storage_path=str(image_path),
        )
        session.add(image)
        session.flush()
        session.add(
            ClassificationRequest(
                user_id=seeded["user_id"],
                model_id=seeded["model_id"],
                image_id=image.id,
                status="COMPLETED",
                probabilities_json='{"Fresh": 1.0}',
            )
        )
        session.commit()

    response = client.delete(f"/api/experiments/{seeded['experiment_id']}", headers=auth_headers("admin", "admin123"))
    assert response.status_code == 204

    with session_factory() as session:
        assert session.get(Experiment, seeded["experiment_id"]) is None
        assert session.get(Model, seeded["model_id"]) is None
        assert session.scalar(select(Metric).where(Metric.config_id == seeded["config_id"])) is None
        assert session.scalar(select(TrainingConfig).where(TrainingConfig.id == seeded["config_id"])) is None
        assert session.scalar(select(UploadedImage)) is None
        assert session.scalar(select(ClassificationRequest)) is None

    assert (model_weights_dir / "model-delete.pth").exists() is False
    assert history_path.exists() is False
    assert image_path.exists() is False
