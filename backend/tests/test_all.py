from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sniffnet.api.deps import get_database
from sniffnet.api.main import app
from sniffnet.api.security import hash_password
from sniffnet.database.db import Base
from sniffnet.database.db_models import (
    Dataset,
    Experiment,
    Metric,
    Model,
    Role,
    TrainingConfig,
    UploadedImage,
    User,
)


class DummyThread:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def start(self):
        return None


@pytest.fixture()
def test_db_and_client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    dataset_root = tmp_path / "datasets" / "v3"
    (dataset_root / "Fresh").mkdir(parents=True)
    (dataset_root / "Bad").mkdir(parents=True)
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine)

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        user_role = Role(code="ROLE_USER", name="User")
        admin_role = Role(code="ROLE_ADMIN", name="Administrator")
        session.add_all([user_role, admin_role])
        session.flush()

        admin = User(
            username="admin",
            email="admin@sniffnet.local",
            password=hash_password("admin123"),
            role_id=admin_role.id,
        )
        demo = User(
            username="demo",
            email="demo@sniffnet.local",
            password=hash_password("demo123"),
            role_id=user_role.id,
        )
        dataset = Dataset(
            name="Products Dataset",
            classes_num=2,
            source=dataset_root.as_posix(),
        )
        session.add_all([admin, demo, dataset])
        session.commit()
    finally:
        session.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_database] = override_get_db
    monkeypatch.setattr("sniffnet.api.main.initialize_database", lambda: None)
    monkeypatch.setattr("sniffnet.api.bootstrap.initialize_database", lambda: None)
    monkeypatch.setattr("sniffnet.api.helpers.IMAGE_STORAGE_DIR", tmp_path / "images")
    monkeypatch.setattr("sniffnet.api.routes.experiments.threading.Thread", DummyThread)

    client = TestClient(app)
    try:
        yield TestingSessionLocal, client
    finally:
        app.dependency_overrides.pop(get_database, None)


def auth_headers(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def seed_inference_model(session_factory) -> tuple[int, int]:
    session = session_factory()
    try:
        user = session.query(User).filter_by(username="demo").one()
        dataset = session.query(Dataset).filter_by(name="Products Dataset").one()
        config = TrainingConfig(
            epochs_num=5,
            batch_size=8,
            learning_rate=0.01,
            optimizer="Adam",
            loss_function="CrossEntropyLoss",
            validation_split=0.2,
            layers_num=2,
            neurons_num=32,
        )
        session.add(config)
        session.flush()

        experiment = Experiment(
            dataset_id=dataset.id,
            config_id=config.id,
            user_id=user.id,
            status="COMPLETED",
            report_path="/api/experiments/1/report",
            external_experiment_id=1,
        )
        session.add(experiment)
        session.flush()

        model = Model(
            name="model1",
            dataset_id=dataset.id,
            config_id=config.id,
            experiment_id=experiment.id,
            params_num=123,
            training_time_seconds=10,
            available_for_inference=True,
            weights_path="model1.pth",
            external_model_id=1,
        )
        metric = Metric(
            dataset_id=dataset.id,
            config_id=config.id,
            train_accuracy=0.91,
            train_loss=0.12,
            validation_accuracy=0.89,
            validation_loss=0.2,
            details_json='{"source":"test"}',
        )
        session.add_all([model, metric])
        session.commit()
        return model.id, user.id
    finally:
        session.close()


def test_auth_register_login_and_me(test_db_and_client):
    _, client = test_db_and_client

    register = client.post(
        "/api/auth/register",
        json={"username": "newuser", "email": "new@sniffnet.local", "password": "secret123"},
    )
    assert register.status_code == 201
    body = register.json()
    assert body["username"] == "newuser"
    assert body["role"] == "ROLE_USER"

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {body['token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "new@sniffnet.local"


def test_admin_users_endpoints_require_admin_and_support_update(test_db_and_client):
    session_factory, client = test_db_and_client
    demo_headers = auth_headers(client, "demo", "demo123")
    admin_headers = auth_headers(client, "admin", "admin123")

    forbidden = client.get("/api/users", headers=demo_headers)
    assert forbidden.status_code == 403

    listing = client.get("/api/users", headers=admin_headers)
    assert listing.status_code == 200
    assert {item["username"] for item in listing.json()} == {"admin", "demo"}

    session = session_factory()
    try:
        demo_id = session.query(User).filter_by(username="demo").one().id
    finally:
        session.close()

    updated = client.put(
        f"/api/users/{demo_id}",
        headers=admin_headers,
        json={"username": "demo_user", "email": "demo@sniffnet.local", "role": "ROLE_USER"},
    )
    assert updated.status_code == 200
    assert updated.json()["username"] == "demo_user"

    search = client.get("/api/users", headers=admin_headers, params={"search": "demo_"})
    assert search.status_code == 200
    assert len(search.json()) == 1


def test_configs_and_datasets_are_available_for_authenticated_users(test_db_and_client):
    _, client = test_db_and_client
    headers = auth_headers(client, "demo", "demo123")

    datasets = client.get("/api/datasets", headers=headers)
    assert datasets.status_code == 200
    assert datasets.json()[0]["name"] == "Products Dataset"

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
    assert created.status_code == 201
    config_id = created.json()["id"]

    fetched = client.get(f"/api/configs/{config_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["batchSize"] == 16


def test_experiment_create_and_list_follow_java_contract(test_db_and_client):
    session_factory, client = test_db_and_client
    headers = auth_headers(client, "demo", "demo123")
    admin_headers = auth_headers(client, "admin", "admin123")

    session = session_factory()
    try:
        dataset_id = session.query(Dataset).filter_by(name="Products Dataset").one().id
        demo_id = session.query(User).filter_by(username="demo").one().id
    finally:
        session.close()

    created = client.post(
        "/api/experiments",
        headers=headers,
        json={
            "datasetId": dataset_id,
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
    body = created.json()
    assert body["status"] == "RUNNING"
    assert body["datasetName"] == "Products Dataset"
    assert body["username"] == "demo"
    assert body["config"]["epochsNum"] == 3

    listing = client.get("/api/experiments", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    admin_filtered = client.get("/api/experiments", headers=admin_headers, params={"userId": demo_id})
    assert admin_filtered.status_code == 200
    assert len(admin_filtered.json()) == 1

    detail = client.get(f"/api/experiments/{body['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["id"] == body["id"]


def test_models_files_and_classifications_flow(test_db_and_client, monkeypatch):
    session_factory, client = test_db_and_client
    headers = auth_headers(client, "demo", "demo123")
    model_id, _ = seed_inference_model(session_factory)

    monkeypatch.setattr(
        "sniffnet.api.routes.classifications._predict_image",
        lambda model, image_path: ("Fresh", 0.98, {"Fresh": 0.98, "Bad": 0.02}),
    )

    models = client.get("/api/models", headers=headers)
    assert models.status_code == 200
    assert models.json()[0]["availableForInference"] is True

    metrics = client.get(f"/api/models/{model_id}/metrics", headers=headers)
    assert metrics.status_code == 200
    assert metrics.json()["trainAccuracy"] == pytest.approx(0.91)

    content = b"\x89PNG\r\n\x1a\nstub"
    classified = client.post(
        "/api/classifications",
        headers=headers,
        files={"file": ("sample.png", content, "image/png")},
        data={"modelId": str(model_id)},
    )
    assert classified.status_code == 201, classified.text
    result = classified.json()
    assert result["predictedClass"] == "Fresh"
    assert result["modelId"] == model_id
    assert result["probabilities"]["Fresh"] == pytest.approx(0.98)

    image_blob = client.get(f"/api/files/images/{result['imageId']}/content", headers=headers)
    assert image_blob.status_code == 200
    assert image_blob.headers["content-type"] == "image/png"

    history = client.get("/api/classifications", headers=headers)
    assert history.status_code == 200
    assert len(history.json()) == 1
