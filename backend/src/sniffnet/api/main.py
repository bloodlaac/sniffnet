from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from alembic import command
from alembic.config import Config
from pathlib import Path
from sniffnet.api.routes import (
    datasets,
    experiments,
    metrics,
    models,
    training_configs,
    users,
    auth,
    predict,
    model_load,
)

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
app.include_router(datasets.router, prefix=api_prefix)
app.include_router(experiments.router, prefix=api_prefix)
app.include_router(metrics.router, prefix=api_prefix)
app.include_router(models.router, prefix=api_prefix)
app.include_router(training_configs.router, prefix=api_prefix)
app.include_router(users.router, prefix=api_prefix)
app.include_router(auth.router, prefix=api_prefix)
app.include_router(predict.router, prefix=api_prefix)
app.include_router(model_load.router, prefix=api_prefix)

@app.get("/")
def get_main_page():
    return {"message": "Hello, World!"}


def run_migrations() -> None:
    project_root = Path(__file__).resolve().parents[3]
    alembic_cfg = Config(str(project_root / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")


def main() -> None:
    run_migrations()
    uvicorn.run(app, host="localhost", port=8000)

if __name__ == "__main__":
    main()
