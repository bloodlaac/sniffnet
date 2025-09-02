import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sniffnet.api.main import app
from sniffnet.api.deps import get_database
from sniffnet.database.db import Base
from sniffnet.database.db_models import User, Dataset, TrainingConfig


@pytest.fixture()
def test_db_and_client(tmp_path):
    # Use a file-based SQLite DB so connections share the same state
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine)

    # Fresh schema for each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Override FastAPI dependency to use our SQLite session
    app.dependency_overrides[get_database] = override_get_db

    client = TestClient(app)
    try:
        yield engine, TestingSessionLocal, client
    finally:
        # Clean override after test
        app.dependency_overrides.pop(get_database, None)


def seed_user(session, username="tester", password="secret", email="t@example.com") -> User:
    user = User(username=username, password=password, email=email)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def seed_dataset(session, name="FoodDataset", classes_num=3, source="local") -> Dataset:
    ds = Dataset(name=name, classes_num=classes_num, source=source)
    session.add(ds)
    session.commit()
    session.refresh(ds)
    return ds


def test_auth_login_success_and_failure(test_db_and_client):
    engine, SessionLocal, client = test_db_and_client
    session = SessionLocal()
    try:
        user = seed_user(session, username="alice", password="wonder", email="a@example.com")

        # Successful login
        resp_ok = client.post("/auth/login", json={"username": "alice", "password": "wonder"})
        assert resp_ok.status_code == 200
        body = resp_ok.json()
        assert body["user_id"] == user.user_id
        assert body["username"] == "alice"

        # Failed login (wrong password)
        resp_bad = client.post("/auth/login", json={"username": "alice", "password": "wrong"})
        assert resp_bad.status_code == 401
    finally:
        session.close()


def test_create_dataset_and_persisted_in_db(test_db_and_client):
    engine, SessionLocal, client = test_db_and_client
    # Create via API (DatasetRequest requires explicit IDs in this API)
    payload = {"dataset_id": 1, "name": "Food", "classes_num": 4, "source": "local"}
    resp = client.post("/datasets", json=payload)
    assert resp.status_code == 200

    # Verify DB has the record
    session = SessionLocal()
    try:
        row = session.query(Dataset).filter(Dataset.dataset_id == 1).first()
        assert row is not None
        assert row.name == "Food"
        assert row.classes_num == 4
        assert row.source == "local"
    finally:
        session.close()


def test_create_training_config_via_api(test_db_and_client):
    _, __, client = test_db_and_client
    cfg_payload = {
        "epochs_num": 5,
        "batch_size": 8,
        "loss_function": "MSELoss",
        "learning_rate": 0.01,
        "optimizer": "Adam",
        "layers_num": 2,
        "neurons_num": 16,
    }
    resp = client.post("/configurations", json=cfg_payload)
    assert resp.status_code == 200
    body = resp.json()
    # Response model excludes ID; validate echo of fields
    for k, v in cfg_payload.items():
        assert body[k] == v


def test_experiment_creation_and_fetch_joined_view(test_db_and_client):
    engine, SessionLocal, client = test_db_and_client
    session = SessionLocal()
    try:
        user = seed_user(session)
        ds = seed_dataset(session)

        exp_req = {
            "user_id": user.user_id,
            "dataset_id": ds.dataset_id,
            "config": {
                "epochs_num": 3,
                "batch_size": 8,
                "loss_function": "MSELoss",
                "learning_rate": 0.01,
                "optimizer": "Adam",
                "layers_num": 2,
                "neurons_num": 16,
            },
        }
        create_resp = client.post("/experiments", json=exp_req)
        assert create_resp.status_code == 200
        exp_id = create_resp.json()["experiment_id"]

        # Joined view contains config fields and optional metrics
        get_resp = client.get(f"/experiments/{exp_id}")
        assert get_resp.status_code == 200
        joined = get_resp.json()
        assert joined["experiment_id"] == exp_id
        assert joined["dataset_id"] == ds.dataset_id
        assert joined["user_id"] == user.user_id
        assert joined["batch_size"] == 8
        assert joined["epochs_num"] == 3
        assert joined["loss_function"] == "MSELoss"
        assert joined["learning_rate"] == 0.01
        assert joined["optimizer"] == "Adam"
        assert joined["layers_num"] == 2
        assert joined["neurons_num"] == 16
        # No metrics yet
        assert joined["train_accuracy"] is None
        assert joined["train_loss"] is None
    finally:
        session.close()


def test_metrics_reflected_in_experiment_join(test_db_and_client):
    engine, SessionLocal, client = test_db_and_client
    session = SessionLocal()
    try:
        user = seed_user(session)
        ds = seed_dataset(session)

        # Create experiment with a new training config
        exp_req = {
            "user_id": user.user_id,
            "dataset_id": ds.dataset_id,
            "config": {
                "epochs_num": 2,
                "batch_size": 4,
                "loss_function": "MSELoss",
                "learning_rate": 0.02,
                "optimizer": "Adam",
                "layers_num": 1,
                "neurons_num": 8,
            },
        }
        create_resp = client.post("/experiments", json=exp_req)
        assert create_resp.status_code == 200
        exp_id = create_resp.json()["experiment_id"]

        # Get the config_id created alongside the experiment
        cfg = (
            session.query(TrainingConfig)
            .order_by(TrainingConfig.config_id.desc())
            .first()
        )
        assert cfg is not None

        # Post metrics for that (dataset_id, config_id)
        metric_payload = {
            "metric_id": 1,
            "dataset_id": ds.dataset_id,
            "config_id": cfg.config_id,
            "train_accuracy": 0.9,
            "train_loss": 0.5,
        }
        m_resp = client.post("/metrics", json=metric_payload)
        assert m_resp.status_code == 200

        # Now the experiment joined view should include metrics
        get_resp = client.get(f"/experiments/{exp_id}")
        assert get_resp.status_code == 200
        joined = get_resp.json()
        assert joined["train_accuracy"] == pytest.approx(0.9)
        assert joined["train_loss"] == pytest.approx(0.5)
    finally:
        session.close()


def test_get_users_empty_list(test_db_and_client):
    _, __, client = test_db_and_client
    resp = client.get("/users")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_user_not_found(test_db_and_client):
    _, __, client = test_db_and_client
    resp = client.get("/users/9999")
    assert resp.status_code == 404


def test_delete_user_not_found(test_db_and_client):
    _, __, client = test_db_and_client
    resp = client.delete("/users/9999")
    assert resp.status_code == 404


def test_seeded_user_list_and_fetch_by_id(test_db_and_client):
    _, SessionLocal, client = test_db_and_client
    session = SessionLocal()
    try:
        u = seed_user(session, username="bob", password="pw", email="b@example.com")
        resp_list = client.get("/users")
        assert resp_list.status_code == 200
        data = resp_list.json()
        assert isinstance(data, list) and len(data) == 1
        assert any(item.get("username") == "bob" for item in data)

        resp_one = client.get(f"/users/{u.user_id}")
        assert resp_one.status_code == 200
        assert resp_one.json().get("user_id") == u.user_id
    finally:
        session.close()


def test_get_datasets_empty_list(test_db_and_client):
    _, __, client = test_db_and_client
    resp = client.get("/datasets")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_dataset_not_found(test_db_and_client):
    _, __, client = test_db_and_client
    resp = client.get("/datasets/12345")
    assert resp.status_code == 404


def test_get_models_empty_list(test_db_and_client):
    _, __, client = test_db_and_client
    resp = client.get("/models")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_model_not_found(test_db_and_client):
    _, __, client = test_db_and_client
    resp = client.get("/models/1")
    assert resp.status_code == 404


def test_get_training_configs_empty_list(test_db_and_client):
    _, __, client = test_db_and_client
    resp = client.get("/configurations")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_training_config_not_found(test_db_and_client):
    _, __, client = test_db_and_client
    resp = client.get("/configurations/1")
    assert resp.status_code == 404


def test_list_experiments_empty(test_db_and_client):
    _, __, client = test_db_and_client
    resp = client.get("/experiments")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_experiment_not_found(test_db_and_client):
    _, __, client = test_db_and_client
    resp = client.get("/experiments/424242")
    assert resp.status_code == 404
