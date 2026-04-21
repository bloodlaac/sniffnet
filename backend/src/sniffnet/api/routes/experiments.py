from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from sniffnet.api.config import MODEL_WEIGHTS_DIR
from sniffnet.api.deps import get_database
from sniffnet.api.errors import ApiException, BadRequestException, NotFoundException
from sniffnet.api.helpers import (
    delete_classifications_for_model,
    ensure_experiment_access,
    get_experiment_with_relations,
    get_metric,
    get_role_entity,
    get_user_entity,
    is_admin,
    remove_path,
)
from sniffnet.api.mappers import to_experiment_response
from sniffnet.api.security import get_current_principal, require_admin
from sniffnet.core.net import train_with_config
from sniffnet.database.db import SessionLocal
from sniffnet.database.db_models import Dataset, Experiment, Metric, Model, TrainingConfig, User
from sniffnet.schemas.contracts import (
    ExperimentCreateRequest,
    ExperimentResponse,
    ExperimentStatusUpdateRequest,
    LegacyStartExperimentRequest,
    LegacyStartExperimentResponse,
)


router = APIRouter(prefix="/experiments", tags=["experiments"])
logger = logging.getLogger(__name__)

VALID_EXPERIMENT_STATUSES = {"CREATED", "RUNNING", "COMPLETED", "FAILED"}


def _trim_error_message(message: str, limit: int = 255) -> str:
    return message if len(message) <= limit else message[: limit - 3] + "..."


def _resolve_food_dir(dataset: Dataset) -> Path | None:
    if not dataset.source:
        return None

    source = dataset.source.strip()
    return Path(source).expanduser().resolve()


def _history_path_for(weights_path: Path) -> Path:
    return weights_path.with_suffix(".json")


def _run_training_job(experiment_id: int) -> None:
    db = SessionLocal()
    model_id: int | None = None
    weights_path: Path | None = None

    try:
        experiment = db.scalar(
            select(Experiment)
            .options(
                joinedload(Experiment.dataset),
                joinedload(Experiment.config),
                joinedload(Experiment.user),
            )
            .where(Experiment.id == experiment_id)
        )
        if experiment is None:
            return

        experiment.status = "RUNNING"
        experiment.error_message = None
        experiment.external_experiment_id = experiment.id
        db.commit()

        model = Model(
            dataset_id=experiment.dataset_id,
            config_id=experiment.config_id,
            experiment_id=experiment.id,
            name=f"model-tmp-{experiment.id}",
            training_time_seconds=0,
            available_for_inference=False,
        )
        db.add(model)
        db.commit()
        db.refresh(model)
        model_id = model.id

        weights_filename = f"model{model.id}.pth"
        MODEL_WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
        weights_path = MODEL_WEIGHTS_DIR / weights_filename

        metrics = train_with_config(
            epochs_num=experiment.config.epochs_num,
            batch_size=experiment.config.batch_size,
            learning_rate=float(experiment.config.learning_rate),
            optimizer_name=experiment.config.optimizer,
            loss_function=experiment.config.loss_function,
            val_split=float(experiment.config.validation_split),
            checkpoint_path=weights_path,
            food_dir=_resolve_food_dir(experiment.dataset),
        )

        metric = Metric(
            dataset_id=experiment.dataset_id,
            config_id=experiment.config_id,
            train_accuracy=metrics.get("train_accuracy") or 0.0,
            train_loss=metrics.get("train_loss") or 0.0,
            validation_accuracy=metrics.get("val_accuracy"),
            validation_loss=metrics.get("val_loss"),
            details_json=json.dumps(
                {
                    "source": "python-training",
                    "externalExperimentId": experiment.id,
                    "externalModelId": model.id,
                    "status": "COMPLETED",
                }
            ),
        )
        db.add(metric)

        history_payload = {
            "train_accuracy_history": metrics.get("train_accuracy_history", []),
            "train_loss_history": metrics.get("train_loss_history", []),
            "val_accuracy_history": metrics.get("val_accuracy_history", []),
            "val_loss_history": metrics.get("val_loss_history", []),
        }
        _history_path_for(weights_path).write_text(json.dumps(history_payload), encoding="utf-8")

        start_time = experiment.start_time
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        training_seconds = int((datetime.now(timezone.utc) - start_time).total_seconds())

        model.name = f"model{model.id}"
        model.params_num = metrics.get("params_num")
        model.weights_path = weights_filename
        model.training_time_seconds = max(training_seconds, 0)
        model.available_for_inference = True
        model.external_model_id = model.id

        experiment.status = "COMPLETED"
        experiment.end_time = datetime.now(timezone.utc)
        experiment.report_path = f"/api/experiments/{experiment.id}/report"
        experiment.external_experiment_id = experiment.id
        db.commit()
    except Exception as exc:
        db.rollback()
        experiment = db.get(Experiment, experiment_id)
        if experiment is not None:
            experiment.status = "FAILED"
            experiment.error_message = _trim_error_message(f"{type(exc).__name__}: {exc}")
            experiment.end_time = datetime.now(timezone.utc)
            experiment.external_experiment_id = experiment.id
            db.commit()
        if model_id is not None:
            model = db.get(Model, model_id)
            if model is not None:
                db.delete(model)
                db.commit()
        if weights_path is not None:
            remove_path(str(weights_path))
            remove_path(str(_history_path_for(weights_path)))
    finally:
        db.close()


def _load_history(weights_path: Path) -> dict[str, list[float]]:
    history_path = _history_path_for(weights_path)
    if not history_path.exists():
        return {}
    try:
        return json.loads(history_path.read_text(encoding="utf-8")) or {}
    except Exception:
        logger.warning("Failed to read history file %s", history_path)
        return {}


def _resolve_config(db: Session, request: ExperimentCreateRequest) -> TrainingConfig:
    if request.configId is not None:
        config = db.get(TrainingConfig, request.configId)
        if config is None:
            raise NotFoundException("Training config not found")
        return config

    assert request.config is not None
    config = TrainingConfig(
        epochs_num=request.config.epochsNum,
        batch_size=request.config.batchSize,
        learning_rate=request.config.learningRate,
        optimizer=request.config.optimizer,
        loss_function=request.config.lossFunction,
        validation_split=request.config.validationSplit,
        layers_num=request.config.layersNum,
        neurons_num=request.config.neuronsNum,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def _create_experiment_for_user(db: Session, user: User, request: ExperimentCreateRequest) -> Experiment:
    dataset = db.get(Dataset, request.datasetId)
    if dataset is None:
        raise NotFoundException("Dataset not found")
    config = _resolve_config(db, request)
    experiment = Experiment(
        dataset_id=dataset.id,
        config_id=config.id,
        user_id=user.id,
        status="RUNNING",
        start_time=datetime.now(timezone.utc),
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    experiment.external_experiment_id = experiment.id
    db.commit()
    db.refresh(experiment)

    thread = threading.Thread(target=_run_training_job, args=(experiment.id,), daemon=True)
    thread.start()
    return get_experiment_with_relations(db, experiment.id)


@router.post("", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
def create_experiment(
    request: ExperimentCreateRequest,
    principal=Depends(get_current_principal),
    db: Session = Depends(get_database),
) -> ExperimentResponse:
    user = get_user_entity(db, principal)
    if user.role.code == "ROLE_ADMIN":
        raise BadRequestException("Administrators cannot start training")
    experiment = _create_experiment_for_user(db, user, request)
    return to_experiment_response(experiment)


@router.get("", response_model=list[ExperimentResponse])
def get_experiments(
    userId: int | None = None,
    status_: str | None = Query(default=None, alias="status"),
    principal=Depends(get_current_principal),
    db: Session = Depends(get_database),
) -> list[ExperimentResponse]:
    stmt = (
        select(Experiment)
        .options(
            joinedload(Experiment.dataset),
            joinedload(Experiment.config),
            joinedload(Experiment.user).joinedload(User.role),
            joinedload(Experiment.model).joinedload(Model.dataset),
            joinedload(Experiment.model).joinedload(Model.config),
        )
        .order_by(Experiment.start_time.desc())
    )
    if is_admin(principal):
        if userId is not None:
            stmt = stmt.where(Experiment.user_id == userId)
    else:
        stmt = stmt.where(Experiment.user_id == principal.id)
    if status_:
        if status_ not in VALID_EXPERIMENT_STATUSES:
            raise BadRequestException("No enum constant for experiment status")
        stmt = stmt.where(Experiment.status == status_)

    experiments = db.scalars(stmt).unique().all()
    return [
        to_experiment_response(
            experiment,
            experiment.model,
            get_metric(db, experiment.dataset_id, experiment.config_id),
        )
        for experiment in experiments
    ]


@router.get("/{id}", response_model=ExperimentResponse)
def get_experiment(
    id: int,
    principal=Depends(get_current_principal),
    db: Session = Depends(get_database),
) -> ExperimentResponse:
    experiment = ensure_experiment_access(get_experiment_with_relations(db, id), principal)
    metric = get_metric(db, experiment.dataset_id, experiment.config_id)
    return to_experiment_response(experiment, experiment.model, metric)


@router.get("/{id}/state")
def get_experiment_state(
    id: int,
    db: Session = Depends(get_database),
) -> dict:
    experiment = get_experiment_with_relations(db, id)
    metric = get_metric(db, experiment.dataset_id, experiment.config_id)
    model = experiment.model
    return {
        "experiment_id": experiment.id,
        "dataset_id": experiment.dataset_id,
        "config_id": experiment.config_id,
        "user_id": experiment.user_id,
        "model_id": model.id if model else None,
        "start_time": experiment.start_time,
        "end_time": experiment.end_time,
        "status": experiment.status,
        "error_message": experiment.error_message,
        "batch_size": experiment.config.batch_size,
        "epochs_num": experiment.config.epochs_num,
        "loss_function": experiment.config.loss_function,
        "learning_rate": float(experiment.config.learning_rate),
        "optimizer": experiment.config.optimizer,
        "val_split": float(experiment.config.validation_split),
        "train_accuracy": metric.train_accuracy if metric else None,
        "train_loss": metric.train_loss if metric else None,
        "validation_accuracy": metric.validation_accuracy if metric else None,
        "validation_loss": metric.validation_loss if metric else None,
        "params_num": model.params_num if model else None,
    }


@router.get("/{id}/report")
def get_experiment_report(
    id: int,
    principal=Depends(get_current_principal),
    db: Session = Depends(get_database),
):
    experiment = ensure_experiment_access(get_experiment_with_relations(db, id), principal)
    if experiment.status != "COMPLETED":
        raise ApiException(status.HTTP_409_CONFLICT, "Report is available only after training is completed")
    if experiment.model is None or not experiment.model.weights_path:
        raise NotFoundException("Model not found")

    weights_path = MODEL_WEIGHTS_DIR / experiment.model.weights_path
    history = _load_history(weights_path)
    train_accuracy_history = list(history.get("train_accuracy_history", []))
    val_accuracy_history = list(history.get("val_accuracy_history", [])) or list(train_accuracy_history)
    train_loss_history = list(history.get("train_loss_history", []))
    val_loss_history = list(history.get("val_loss_history", [])) or list(train_loss_history)
    n = min(
        len(train_accuracy_history),
        len(val_accuracy_history),
        len(train_loss_history),
        len(val_loss_history),
    )
    if n < 1:
        raise BadRequestException("No report data available for experiment")

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.ticker import MaxNLocator

    epochs = np.arange(1, n + 1)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    ax1.plot(epochs, train_accuracy_history[:n], color="#3b82f6", linewidth=2, label="Train accuracy")
    ax1.plot(epochs, val_accuracy_history[:n], color="#22c55e", linewidth=2, linestyle="--", label="Validation accuracy")
    ax1.set_title(f"Accuracy on {n} epochs")
    ax1.set_xlabel("Epochs")
    ax1.set_ylabel("Accuracy")
    ax1.grid(True)
    ax1.legend()
    ax1.xaxis.set_major_locator(MaxNLocator(integer=True))

    ax2.plot(epochs, train_loss_history[:n], color="#ef4444", linewidth=2, label="Train loss")
    ax2.plot(epochs, val_loss_history[:n], color="#f97316", linewidth=2, linestyle="--", label="Validation loss")
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
    headers = {"Content-Disposition": f'inline; filename="experiment_{experiment.id}.png"'}
    return StreamingResponse(buffer, media_type="image/png", headers=headers)


@router.patch("/{id}/status", response_model=ExperimentResponse)
def update_status(
    id: int,
    request: ExperimentStatusUpdateRequest,
    _=Depends(require_admin),
    db: Session = Depends(get_database),
) -> ExperimentResponse:
    if request.status not in VALID_EXPERIMENT_STATUSES:
        raise BadRequestException("No enum constant for experiment status")
    experiment = get_experiment_with_relations(db, id)
    experiment.status = request.status
    if request.status in {"COMPLETED", "FAILED"}:
        experiment.end_time = datetime.now(timezone.utc)
    else:
        experiment.end_time = None
    if request.status != "FAILED":
        experiment.error_message = None
    db.commit()
    experiment = get_experiment_with_relations(db, id)
    metric = get_metric(db, experiment.dataset_id, experiment.config_id)
    return to_experiment_response(experiment, experiment.model, metric)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experiment(
    id: int,
    _=Depends(require_admin),
    db: Session = Depends(get_database),
) -> Response:
    experiment = get_experiment_with_relations(db, id)
    config_id = experiment.config_id

    if experiment.model is not None:
        model = experiment.model
        weights_path = str((MODEL_WEIGHTS_DIR / model.weights_path).resolve()) if model.weights_path else None
        delete_classifications_for_model(db, model.id)
        db.delete(model)
        db.commit()
        remove_path(weights_path)
        if weights_path:
            remove_path(str(Path(weights_path).with_suffix(".json")))

    db.query(Metric).filter(Metric.config_id == config_id).delete()
    db.delete(experiment)
    db.commit()

    remaining = db.scalar(select(func.count(Experiment.id)).where(Experiment.config_id == config_id))
    if not remaining:
        config = db.get(TrainingConfig, config_id)
        if config is not None:
            db.delete(config)
            db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/train", response_model=LegacyStartExperimentResponse, status_code=status.HTTP_202_ACCEPTED)
def start_experiment_legacy(
    request: LegacyStartExperimentRequest,
    db: Session = Depends(get_database),
) -> LegacyStartExperimentResponse:
    user_id = request.user_id or 1
    user = db.scalar(select(User).options(joinedload(User.role)).where(User.id == user_id))
    if user is None:
        raise NotFoundException("User not found")

    if request.experiment_id is not None:
        experiment = db.get(Experiment, request.experiment_id)
        if experiment is None:
            raise NotFoundException("Experiment not found")
        if experiment.user_id != user.id:
            raise BadRequestException("Experiment belongs to another user")

        experiment.status = "RUNNING"
        experiment.error_message = None
        experiment.external_experiment_id = experiment.id
        db.commit()

        thread = threading.Thread(target=_run_training_job, args=(experiment.id,), daemon=True)
        thread.start()
        return LegacyStartExperimentResponse(experiment_id=experiment.id, status=experiment.status)

    config_payload = None
    if request.config:
        config_payload = {
            "epochsNum": request.config.get("epochsNum", request.config.get("epochs_num")),
            "batchSize": request.config.get("batchSize", request.config.get("batch_size")),
            "learningRate": request.config.get("learningRate", request.config.get("learning_rate")),
            "optimizer": request.config.get("optimizer"),
            "lossFunction": request.config.get("lossFunction", request.config.get("loss_function")),
            "validationSplit": request.config.get("validationSplit", request.config.get("val_split")),
            "layersNum": request.config.get("layersNum", request.config.get("layers_num")),
            "neuronsNum": request.config.get("neuronsNum", request.config.get("neurons_num")),
        }

    experiment_request = ExperimentCreateRequest(
        datasetId=request.dataset_id,
        configId=request.config_id,
        config=config_payload,
    )
    experiment = _create_experiment_for_user(db, user, experiment_request)
    return LegacyStartExperimentResponse(experiment_id=experiment.id, status=experiment.status)
