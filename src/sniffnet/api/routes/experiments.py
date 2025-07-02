from typing import Annotated
from sniffnet.schemas.experiments import CreateExperimentRequest, ExperimentJoined
from sniffnet.schemas.training_configs import ConfigRequest
from sqlalchemy.orm import Session
from sniffnet.database.db_models import Experiment, TrainingConfig, Metric
from sniffnet.api.deps import get_database
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends


router = APIRouter(tags=["experiments"])

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
        start_time=experiment.start_time,
        end_time=experiment.end_time,
        batch_size=cfg.batch_size,
        epochs_num=cfg.epochs_num,
        loss_function=cfg.loss_function,
        learning_rate=cfg.learning_rate,
        optimizer=cfg.optimizer,
        layers_num=cfg.layers_num,
        neurons_num=cfg.neurons_num,
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
