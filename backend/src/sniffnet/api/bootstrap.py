from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from sniffnet.api.security import hash_password
from sniffnet.database.db import Base, SessionLocal, engine
from sniffnet.database.db_models import Dataset, Experiment, Role, User

DEFAULT_DATASET_SOURCE = (
    Path(__file__).resolve().parents[5] / "datasets" / "v3"
).resolve().as_posix()


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_timezone_columns()
    with SessionLocal() as db:
        seed_defaults(db)
        reconcile_interrupted_experiments(db)


def ensure_timezone_columns() -> None:
    if engine.dialect.name != "postgresql":
        return

    timestamp_columns = [
        ("users", "createdAt"),
        ("experiments", "startTime"),
        ("experiments", "endTime"),
        ("models", "createdAt"),
        ("uploaded_images", "uploadedAt"),
        ("classification_requests", "createdAt"),
        ("classification_requests", "completedAt"),
    ]

    with engine.begin() as connection:
        for table_name, column_name in timestamp_columns:
            data_type = connection.execute(
                text(
                    """
                    SELECT data_type
                    FROM information_schema.columns
                    WHERE table_schema = current_schema()
                      AND table_name = :table_name
                      AND column_name = :column_name
                    """
                ),
                {"table_name": table_name, "column_name": column_name},
            ).scalar_one_or_none()
            if data_type != "timestamp without time zone":
                continue
            connection.execute(
                text(
                    f'ALTER TABLE {table_name} '
                    f'ALTER COLUMN "{column_name}" TYPE TIMESTAMPTZ '
                    f'USING "{column_name}" AT TIME ZONE \'UTC\''
                )
            )


def seed_defaults(db: Session) -> None:
    role_codes = {role.code for role in db.scalars(select(Role)).all()}
    changed = False

    if "ROLE_USER" not in role_codes:
        db.add(Role(code="ROLE_USER", name="User"))
        changed = True
    if "ROLE_ADMIN" not in role_codes:
        db.add(Role(code="ROLE_ADMIN", name="Administrator"))
        changed = True
    if changed:
        db.commit()

    roles = {role.code: role for role in db.scalars(select(Role)).all()}
    if db.scalar(select(User).where(User.username.ilike("admin")).limit(1)) is None:
        db.add(
            User(
                username="admin",
                email="admin@sniffnet.local",
                password=hash_password("admin123"),
                role_id=roles["ROLE_ADMIN"].id,
            )
        )
        changed = True
    if db.scalar(select(User).where(User.username.ilike("demo")).limit(1)) is None:
        db.add(
            User(
                username="demo",
                email="demo@sniffnet.local",
                password=hash_password("demo123"),
                role_id=roles["ROLE_USER"].id,
            )
        )
        changed = True
    existing_dataset = db.scalar(select(Dataset).where(Dataset.name.ilike("Products Dataset")).limit(1))
    if existing_dataset is None:
        db.add(
            Dataset(
                name="Products Dataset",
                classes_num=2,
                source=DEFAULT_DATASET_SOURCE,
            )
        )
        changed = True
    elif existing_dataset.source != DEFAULT_DATASET_SOURCE:
        existing_dataset.source = DEFAULT_DATASET_SOURCE
        changed = True
    if changed:
        db.commit()


def reconcile_interrupted_experiments(db: Session) -> None:
    interrupted = db.scalars(select(Experiment).where(Experiment.status == "RUNNING")).all()
    for experiment in interrupted:
        experiment.status = "FAILED"
        experiment.error_message = "Python service restarted while training was in progress"
        experiment.end_time = datetime.now(timezone.utc)
        if experiment.external_experiment_id is None:
            experiment.external_experiment_id = experiment.id
    if interrupted:
        db.commit()
