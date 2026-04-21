from __future__ import annotations

from fastapi.testclient import TestClient


def test_catalog_exposes_datasets_and_config_crud_lite(
    client: TestClient,
    auth_headers,
    dataset: dict[str, object],
) -> None:
    headers = auth_headers("demo", "demo123")

    datasets = client.get("/api/datasets", headers=headers)
    assert datasets.status_code == 200
    assert datasets.json() == [
        {
            "id": dataset["id"],
            "name": "Products Dataset",
            "classesNum": 2,
            "source": dataset["source"],
        }
    ]

    created = client.post(
        "/api/configs",
        headers=headers,
        json={
            "epochsNum": 4,
            "batchSize": 16,
            "learningRate": 0.001,
            "optimizer": "Adam",
            "lossFunction": "CrossEntropyLoss",
            "validationSplit": 0.2,
            "layersNum": 3,
            "neuronsNum": 64,
        },
    )
    assert created.status_code == 201, created.text
    config_id = created.json()["id"]

    fetched = client.get(f"/api/configs/{config_id}", headers=headers)
    updated = client.put(
        f"/api/configs/{config_id}",
        headers=headers,
        json={
            "epochsNum": 5,
            "batchSize": 8,
            "learningRate": 0.002,
            "optimizer": "Adam",
            "lossFunction": "CrossEntropyLoss",
            "validationSplit": 0.3,
            "layersNum": 2,
            "neuronsNum": 32,
        },
    )
    deleted = client.delete(f"/api/configs/{config_id}", headers=headers)

    assert fetched.status_code == 200
    assert fetched.json()["batchSize"] == 16
    assert updated.status_code == 200
    assert updated.json()["validationSplit"] == 0.3
    assert deleted.status_code == 204


def test_catalog_prevents_deleting_used_config(
    client: TestClient,
    auth_headers,
    dataset: dict[str, object],
) -> None:
    headers = auth_headers("demo", "demo123")
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

    config_id = created.json()["config"]["id"]
    deleted = client.delete(f"/api/configs/{config_id}", headers=headers)

    assert deleted.status_code == 400
    assert deleted.json()["message"] == "Training config is already used by an experiment"
