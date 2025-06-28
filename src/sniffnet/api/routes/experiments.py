from typing import Annotated
from sniffnet.schemas.experiments import ExperimentRequest
from sqlalchemy.orm import Session
from sniffnet.database.db_models import Experiment
from sniffnet.api.deps import get_database

from fastapi import APIRouter, HTTPException, Depends


router = APIRouter(tags=["experiments"])

@router.get("/experiments")
def get_experiments(db: Annotated[Session, Depends(get_database)]):
    return db.query(Experiment).all()


@router.get("/experiments/{id}")
def get_experiment(id, db: Annotated[Session, Depends(get_database)]):
    experiment = db.query(Experiment).filter(Experiment.experiment_id == id).first()

    if experiment is None:
        raise HTTPException(status_code=404, detail="Эксперимент не найден")
    
    return experiment


@router.post("/experiments")
def post_experiment(experiment: ExperimentRequest, db: Annotated[Session, Depends(get_database)]) -> ExperimentRequest:
    db_experiment = Experiment(**experiment.model_dump())
    db.add(db_experiment)
    db.commit()
    db.refresh(db_experiment)

    return db_experiment