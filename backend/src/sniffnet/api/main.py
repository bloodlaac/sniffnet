from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from alembic import command
from alembic.config import Config
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy import inspect
from sniffnet.api.routes import (
    experiments,
    predict,
)
from sniffnet.database.db import SessionLocal, engine
from sniffnet.database.db_models import Experiment

import uvicorn

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_prefix = "/api"
app.include_router(experiments.router, prefix=api_prefix)
app.include_router(predict.router, prefix=api_prefix)

@app.get("/")
def get_main_page():
    return {"message": "Hello, World!"}


def run_migrations() -> None:
    project_root = Path(__file__).resolve().parents[3]
    alembic_cfg = Config(str(project_root / "alembic.ini"))
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    shared_schema_tables = {
        "roles",
        "users",
        "datasets",
        "training_configs",
        "experiments",
        "models",
        "metrics",
    }

    if "alembic_version" not in existing_tables and shared_schema_tables.issubset(existing_tables):
        command.stamp(alembic_cfg, "head")
        return

    command.upgrade(alembic_cfg, "head")


def reconcile_interrupted_experiments() -> None:
    db = SessionLocal()
    try:
        interrupted = (
            db.query(Experiment)
            .filter(Experiment.status == "RUNNING")
            .all()
        )
        for experiment in interrupted:
            experiment.status = "FAILED"
            experiment.error_message = "Python service restarted while training was in progress"
            experiment.end_time = datetime.now(timezone.utc).replace(tzinfo=None)
            experiment.external_experiment_id = experiment.experiment_id
        if interrupted:
            db.commit()
    finally:
        db.close()


def main() -> None:
    run_migrations()
    reconcile_interrupted_experiments()
    uvicorn.run(app, host="localhost", port=8000)

if __name__ == "__main__":
    main()
