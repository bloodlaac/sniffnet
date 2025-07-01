from typing import Annotated
from sniffnet.schemas.experiments import ExperimentRequest, ExperimentJoined
from sqlalchemy.orm import Session
from sqlalchemy import select
from sniffnet.database.db_models import Experiment, TrainingConfig
from sniffnet.api.deps import get_database

from fastapi import APIRouter, HTTPException, Depends


router = APIRouter(tags=["experiments"])

@router.get("/experiments")
def get_experiments(db: Annotated[Session, Depends(get_database)]):
    return db.query(Experiment).all()


@router.get("/experiments/{id}")
def get_experiment(id, db: Annotated[Session, Depends(get_database)]):
    experiment = db.query(Experiment).join(TrainingConfig).filter(Experiment.experiment_id == id).first()

    if experiment is None:
        raise HTTPException(status_code=404, detail="Эксперимент не найден")
    
    config: TrainingConfig = experiment.config

    return ExperimentJoined(
        experiment_id=experiment.experiment_id,
        dataset_id=experiment.dataset_id,
        config_id=experiment.config_id,
        user_id=experiment.user_id,
        start_time=experiment.start_time,
        end_time=experiment.end_time,
        batch_size=config.batch_size,
        epochs_num=config.epochs_num,
        loss_function=config.loss_function,
        learning_rate=config.learning_rate,
        optimizer=config.optimizer,
        layers_num=config.layers_num,
        neurons_num=config.neurons_num
    )


@router.post("/experiments")
def post_experiment(experiment: ExperimentRequest, db: Annotated[Session, Depends(get_database)]) -> ExperimentRequest:
    db_experiment = Experiment(**experiment.model_dump())
    db.add(db_experiment)
    db.commit()
    db.refresh(db_experiment)

    return db_experiment