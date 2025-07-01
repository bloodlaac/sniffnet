from typing import Annotated
from sniffnet.schemas.experiments import ExperimentRequest, ExperimentJoined
from sniffnet.schemas.training_configs import ConfigRequest
from sqlalchemy.orm import Session
from sqlalchemy import select
from sniffnet.database.db_models import Experiment, TrainingConfig
from sniffnet.api.deps import get_database

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
    )


@router.post("/experiments", response_model=ExperimentJoined)
def post_experiment(
    payload: ExperimentRequest,
    db: Annotated[Session, Depends(get_database)]
) -> ExperimentJoined:
    config_data = ConfigRequest(
        epochs_num=payload.epochs_num,
        batch_size=payload.batch_size,
        loss_function=payload.loss_function,
        learning_rate=payload.learning_rate,
        optimizer=payload.optimizer,
        layers_num=payload.layers_num,
        neurons_num=payload.neurons_num,
    )
    db_config = TrainingConfig(**config_data.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)

    exp_data = payload.model_dump(exclude={
        "epochs_num", "batch_size", "loss_function",
        "learning_rate", "optimizer", "layers_num", "neurons_num",
    })
    db_experiment = Experiment(
        **exp_data,
        config_id=db_config.config_id
    )
    db.add(db_experiment)
    db.commit()
    db.refresh(db_experiment)

    return ExperimentJoined(
        experiment_id=db_experiment.experiment_id,
        dataset_id=db_experiment.dataset_id,
        config_id=db_config.config_id,
        user_id=db_experiment.user_id,
        start_time=db_experiment.start_time,
        end_time=db_experiment.end_time,
        batch_size=db_config.batch_size,
        epochs_num=db_config.epochs_num,
        loss_function=db_config.loss_function,
        learning_rate=db_config.learning_rate,
        optimizer=db_config.optimizer,
        layers_num=db_config.layers_num,
        neurons_num=db_config.neurons_num,
    )
