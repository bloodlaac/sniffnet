from __future__ import annotations

import sys
from collections.abc import Callable, Generator
from pathlib import Path
from types import SimpleNamespace
import types

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = BACKEND_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from sniffnet.api.deps import get_database
from sniffnet.api.main import app
from sniffnet.api.security import hash_password
from sniffnet.database.db import Base
from sniffnet.database.db_models import Dataset, Experiment, Metric, Model, Role, TrainingConfig, User


class DummyTrainingThread:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.started = False

    def start(self) -> None:
        self.started = True


@pytest.fixture()
def test_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from sniffnet.api import bootstrap, helpers, main
    from sniffnet.api.routes import classifications, experiments, predict

    db_path = tmp_path / "test.db"
    dataset_root = tmp_path / "datasets" / "v3"
    images_dir = tmp_path / "images"
    models_dir = tmp_path / "models"

    for class_name in ("Fresh", "Bad"):
        (dataset_root / class_name).mkdir(parents=True)

    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    testing_session_local = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    with testing_session_local() as session:
        user_role = Role(code="ROLE_USER", name="User")
        admin_role = Role(code="ROLE_ADMIN", name="Administrator")
        session.add_all([user_role, admin_role])
        session.flush()
        session.add_all(
            [
                User(
                    username="admin",
                    email="admin@sniffnet.local",
                    password=hash_password("admin123"),
                    role_id=admin_role.id,
                ),
                User(
                    username="demo",
                    email="demo@sniffnet.local",
                    password=hash_password("demo123"),
                    role_id=user_role.id,
                ),
                Dataset(
                    name="Products Dataset",
                    classes_num=2,
                    source=dataset_root.as_posix(),
                ),
            ]
        )
        session.commit()

    def override_get_db() -> Generator:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    started_threads: list[DummyTrainingThread] = []

    def thread_factory(*args, **kwargs) -> DummyTrainingThread:
        thread = DummyTrainingThread(*args, **kwargs)
        started_threads.append(thread)
        return thread

    app.dependency_overrides[get_database] = override_get_db
    monkeypatch.setattr(main, "initialize_database", lambda: None)
    monkeypatch.setattr(bootstrap, "initialize_database", lambda: None)
    monkeypatch.setattr(helpers, "IMAGE_STORAGE_DIR", images_dir)
    monkeypatch.setattr(experiments, "MODEL_WEIGHTS_DIR", models_dir)
    monkeypatch.setattr(classifications, "MODEL_WEIGHTS_DIR", models_dir)
    monkeypatch.setattr(predict, "MODEL_WEIGHTS_DIR", models_dir)
    monkeypatch.setattr(experiments, "threading", types.SimpleNamespace(Thread=thread_factory))

    client = TestClient(app)
    try:
        yield SimpleNamespace(
            client=client,
            session_factory=testing_session_local,
            dataset_root=dataset_root,
            images_dir=images_dir,
            models_dir=models_dir,
            started_threads=started_threads,
        )
    finally:
        app.dependency_overrides.pop(get_database, None)


@pytest.fixture()
def client(test_context):
    return test_context.client


@pytest.fixture()
def session_factory(test_context):
    return test_context.session_factory


@pytest.fixture()
def dataset_root(test_context) -> Path:
    return test_context.dataset_root


@pytest.fixture()
def image_storage_dir(test_context) -> Path:
    return test_context.images_dir


@pytest.fixture()
def model_weights_dir(test_context) -> Path:
    return test_context.models_dir


@pytest.fixture()
def roles(session_factory) -> dict[str, int]:
    with session_factory() as session:
        return {role.code: role.id for role in session.scalars(select(Role)).all()}


@pytest.fixture()
def users(session_factory) -> dict[str, dict[str, object]]:
    with session_factory() as session:
        result: dict[str, dict[str, object]] = {}
        for user in session.scalars(select(User)).all():
            result[user.username] = {
                "id": user.id,
                "email": user.email,
                "password": f"{user.username}123",
            }
        return result


@pytest.fixture()
def dataset(session_factory) -> dict[str, object]:
    with session_factory() as session:
        item = session.scalar(select(Dataset).where(Dataset.name == "Products Dataset"))
        assert item is not None
        return {"id": item.id, "name": item.name, "source": item.source}


@pytest.fixture()
def auth_headers(client: TestClient) -> Callable[[str, str], dict[str, str]]:
    def factory(username: str, password: str) -> dict[str, str]:
        response = client.post("/api/auth/login", json={"username": username, "password": password})
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['token']}"}

    return factory


@pytest.fixture()
def seed_inference_model(
    session_factory,
    dataset: dict[str, object],
    users: dict[str, dict[str, object]],
    model_weights_dir: Path,
):
    def factory(
        *,
        username: str = "demo",
        available_for_inference: bool = True,
        weights_filename: str = "model-test.pth",
    ) -> dict[str, int]:
        with session_factory() as session:
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
                dataset_id=int(dataset["id"]),
                config_id=config.id,
                user_id=int(users[username]["id"]),
                status="COMPLETED",
                report_path="/api/experiments/1/report",
                external_experiment_id=None,
            )
            session.add(experiment)
            session.flush()

            model = Model(
                name=f"model{experiment.id}",
                dataset_id=int(dataset["id"]),
                config_id=config.id,
                experiment_id=experiment.id,
                params_num=123,
                training_time_seconds=10,
                available_for_inference=available_for_inference,
                weights_path=weights_filename,
                external_model_id=None,
            )
            metric = Metric(
                dataset_id=int(dataset["id"]),
                config_id=config.id,
                train_accuracy=0.91,
                train_loss=0.12,
                validation_accuracy=0.89,
                validation_loss=0.20,
                details_json='{"source":"test"}',
            )
            session.add_all([model, metric])
            session.commit()
            session.refresh(model)
            session.refresh(experiment)

            if weights_filename:
                weights_path = model_weights_dir / weights_filename
                weights_path.parent.mkdir(parents=True, exist_ok=True)
                weights_path.write_bytes(b"stub-weights")

            return {
                "model_id": model.id,
                "experiment_id": experiment.id,
                "config_id": config.id,
                "user_id": int(users[username]["id"]),
            }

    return factory
