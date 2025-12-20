from typing import Annotated
import logging
from pathlib import Path
import threading
import json
from io import BytesIO
from sniffnet.schemas.experiments import (
    CreateExperimentRequest,
    ExperimentJoined,
    StartExperimentRequest,
    StartExperimentResponse,
    TrainExperimentRequest,
    TrainExperimentResponse,
)
from sqlalchemy.orm import Session
from sniffnet.database.db_models import Experiment, TrainingConfig, Metric, Dataset, Model
from sniffnet.api.deps import get_database
from sniffnet.api.config import MODEL_WEIGHTS_DIR
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse


router = APIRouter(tags=["experiments"])
logger = logging.getLogger(__name__)


def _normalize_series(values: list[float] | None):
    return list(values) if values else []


def _ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def run_training_job(experiment_id: int) -> None:
    from sniffnet.database.db import SessionLocal
    from sniffnet.core.net import train_with_config

    db = SessionLocal()
    try:
        experiment = (
            db.query(Experiment)
            .filter(Experiment.experiment_id == experiment_id)
            .first()
        )
        if experiment is None:
            return

        experiment.status = "running"
        experiment.error_message = None
        db.commit()

        config: TrainingConfig = experiment.config

        model = Model(
            dataset_id=experiment.dataset_id,
            config_id=experiment.config_id,
        )
        db.add(model)
        db.commit()
        db.refresh(model)

        weights_filename = f"model{model.model_id}.pth"
        weights_path = Path(MODEL_WEIGHTS_DIR) / weights_filename
        weights_path.parent.mkdir(parents=True, exist_ok=True)

        metrics = train_with_config(
            epochs_num=config.epochs_num,
            batch_size=config.batch_size,
            learning_rate=config.learning_rate,
            optimizer_name=config.optimizer,
            loss_function=config.loss_function,
            val_split=config.val_split if config.val_split is not None else 0.2,
            checkpoint_path=weights_path,
        )

        metric = Metric(
            dataset_id=experiment.dataset_id,
            config_id=experiment.config_id,
            train_accuracy=metrics.get("train_accuracy"),
            train_loss=metrics.get("train_loss"),
        )
        db.add(metric)

        history_path = weights_path.with_suffix(".json")
        with history_path.open("w", encoding="utf-8") as handle:
            json.dump(
                {
                    "train_accuracy_history": metrics.get("train_accuracy_history", []),
                    "train_loss_history": metrics.get("train_loss_history", []),
                    "val_accuracy_history": metrics.get("val_accuracy_history", []),
                    "val_loss_history": metrics.get("val_loss_history", []),
                },
                handle,
            )

        model.name = f"model{model.model_id}"
        model.weights_path = weights_filename
        if experiment.start_time:
            model.training_time = datetime.now(timezone.utc) - experiment.start_time
        experiment.model_id = model.model_id
        experiment.status = "success"
        experiment.end_time = datetime.now(timezone.utc)
        db.commit()

    except Exception as exc:
        db.rollback()
        experiment = (
            db.query(Experiment)
            .filter(Experiment.experiment_id == experiment_id)
            .first()
        )
        if experiment:
            experiment.status = "failed"
            experiment.error_message = str(exc)
            experiment.end_time = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


def _load_history(weights_path: Path) -> dict:
    history_path = weights_path.with_suffix(".json")
    if not history_path.exists():
        return {}
    try:
        with history_path.open("r", encoding="utf-8") as handle:
            return json.load(handle) or {}
    except Exception:
        return {}


@router.get("/experiments/{id}/report")
def get_experiment_report(
    id: int,
    db: Annotated[Session, Depends(get_database)],
):
    experiment = (
        db.query(Experiment)
        .join(TrainingConfig)
        .filter(Experiment.experiment_id == id)
        .first()
    )
    if experiment is None:
        raise HTTPException(status_code=404, detail="Эксперимент не найден")
    if experiment.status != "success":
        raise HTTPException(status_code=409, detail="Отчёт доступен после завершения обучения")

    cfg: TrainingConfig = experiment.config
    model = experiment.model
    if model is None or not model.weights_path:
        raise HTTPException(status_code=404, detail="Модель эксперимента не найдена")

    weights_path = Path(MODEL_WEIGHTS_DIR) / model.weights_path
    history = _load_history(weights_path)

    train_accuracy_history = _normalize_series(history.get("train_accuracy_history"))
    val_accuracy_history = _normalize_series(history.get("val_accuracy_history"))
    train_loss_history = _normalize_series(history.get("train_loss_history"))
    val_loss_history = _normalize_series(history.get("val_loss_history"))

    if not val_accuracy_history and train_accuracy_history:
        logger.warning(
            "Experiment %s missing validation accuracy history; using train accuracy",
            experiment.experiment_id,
        )
        val_accuracy_history = list(train_accuracy_history)
    if not val_loss_history and train_loss_history:
        logger.warning(
            "Experiment %s missing validation loss history; using train loss",
            experiment.experiment_id,
        )
        val_loss_history = list(train_loss_history)

    lengths = (
        len(train_accuracy_history),
        len(val_accuracy_history),
        len(train_loss_history),
        len(val_loss_history),
    )
    if len(set(lengths)) != 1:
        logger.warning(
            "Experiment %s history length mismatch: %s",
            experiment.experiment_id,
            lengths,
        )

    n = min(lengths) if lengths else 0
    if n < 1:
        logger.warning(
            "Experiment %s has no epoch history; lengths=%s",
            experiment.experiment_id,
            lengths,
        )
        raise HTTPException(status_code=422, detail="Нет данных по эпохам для отчёта")

    if cfg.epochs_num and n != cfg.epochs_num:
        logger.warning(
            "Experiment %s epochs mismatch: expected %s, got %s",
            experiment.experiment_id,
            cfg.epochs_num,
            n,
        )

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.ticker import MaxNLocator

    epochs = np.arange(1, n + 1)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    ax1.plot(epochs, train_accuracy_history[:n], color="#3b82f6", linewidth=2, label="Train accuracy")
    ax1.plot(
        epochs,
        val_accuracy_history[:n],
        color="#22c55e",
        linewidth=2,
        linestyle="--",
        label="Validation accuracy",
    )
    ax1.set_title(f"Accuracy on {n} epochs")
    ax1.set_xlabel("Epochs")
    ax1.set_ylabel("Accuracy")
    ax1.grid(True)
    ax1.legend()
    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))

    ax2.plot(epochs, train_loss_history[:n], color="#ef4444", linewidth=2, label="Train loss")
    ax2.plot(
        epochs,
        val_loss_history[:n],
        color="#f97316",
        linewidth=2,
        linestyle="--",
        label="Validation loss",
    )
    ax2.set_title(f"Loss on {n} epochs")
    ax2.set_xlabel("Epochs")
    ax2.set_ylabel("Loss")
    ax2.grid(True)
    ax2.legend()
    ax2.xaxis.set_major_locator(MaxNLocator(integer=True))

    fig.tight_layout()

    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=150)
    plt.close(fig)
    buffer.seek(0)

    filename = f"experiment_{experiment.experiment_id}.png"
    headers = {"Content-Disposition": f'inline; filename="{filename}"'}
    return StreamingResponse(buffer, media_type="image/png", headers=headers)

@router.get("/experiments")
def get_experiments(db: Annotated[Session, Depends(get_database)]):
    return db.query(Experiment).all()


@router.get("/experiments/{id}", response_model=ExperimentJoined)
def get_experiment(
    id: int,
    db: Annotated[Session, Depends(get_database)]
):
    experiment = (
        db.query(Experiment)
        .join(TrainingConfig)
        .filter(Experiment.experiment_id == id)
        .first()
    )
    if experiment is None:
        raise HTTPException(status_code=404, detail="Эксперимент не найден")

    cfg: TrainingConfig = experiment.config

    metric = (
        db.query(Metric)
        .filter(Metric.config_id == cfg.config_id)
        .first()
    )

    return ExperimentJoined(
        experiment_id=experiment.experiment_id,
        dataset_id=experiment.dataset_id,
        config_id=experiment.config_id,
        user_id=experiment.user_id,
        model_id=experiment.model_id,
        start_time=_ensure_utc(experiment.start_time),
        end_time=_ensure_utc(experiment.end_time),
        status=experiment.status,
        error_message=experiment.error_message,
        batch_size=cfg.batch_size,
        epochs_num=cfg.epochs_num,
        loss_function=cfg.loss_function,
        learning_rate=cfg.learning_rate,
        optimizer=cfg.optimizer,
        val_split=cfg.val_split if cfg.val_split is not None else 0.2,
        train_accuracy=metric.train_accuracy if metric else None,
        train_loss=metric.train_loss if metric else None,
    )


@router.post("/experiments")
def create_experiment(request: CreateExperimentRequest, db: Session = Depends(get_database)):
    config = TrainingConfig(**request.config.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)

    experiment = Experiment(
        user_id=request.user_id,
        dataset_id=request.dataset_id,
        config_id=config.config_id,
        start_time=datetime.now(timezone.utc)
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)

    return {"experiment_id": experiment.experiment_id}


@router.post("/experiments/train", response_model=StartExperimentResponse, status_code=202)
def start_experiment(
    request: StartExperimentRequest,
    db: Session = Depends(get_database)
):
    dataset = db.query(Dataset).filter(Dataset.dataset_id == request.dataset_id).first()
    if dataset is None:
        raise HTTPException(status_code=404, detail="Датасет не найден")

    config = TrainingConfig(**request.config.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)

    experiment = Experiment(
        user_id=request.user_id,
        dataset_id=request.dataset_id,
        config_id=config.config_id,
        start_time=datetime.now(timezone.utc),
        status="queued",
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)

    thread = threading.Thread(
        target=run_training_job,
        args=(experiment.experiment_id,),
        daemon=True,
    )
    thread.start()

    return {"experiment_id": experiment.experiment_id, "status": "queued"}


@router.post("/experiments/run", response_model=TrainExperimentResponse, status_code=202)
def train_experiment(
    request: TrainExperimentRequest,
    db: Session = Depends(get_database)
):
    config = (
        db.query(TrainingConfig)
        .filter(TrainingConfig.config_id == request.training_config_id)
        .first()
    )
    if config is None:
        raise HTTPException(status_code=404, detail="Конфигурация обучения не найдена")

    experiment = Experiment(
        user_id=request.user_id,
        dataset_id=request.dataset_id,
        config_id=config.config_id,
        start_time=datetime.now(timezone.utc),
        status="queued",
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)

    thread = threading.Thread(
        target=run_training_job,
        args=(experiment.experiment_id,),
        daemon=True,
    )
    thread.start()

    return {"experiment_id": experiment.experiment_id, "status": "started"}
