from typing import Annotated
from sqlalchemy.orm import Session
from sniffnet.schemas.training_configs import ConfigRequest
from sniffnet.api.deps import get_database
from sniffnet.database.db_models import TrainingConfig

from fastapi import APIRouter, HTTPException, Depends


router = APIRouter(tags=["training_configs"])

@router.get("/configurations")
def get_configs(db: Annotated[Session, Depends(get_database)]):
    return db.query(TrainingConfig).all()


@router.get("/configurations/{id}")
def get_config(id, db: Annotated[Session, Depends(get_database)]):
    config =  db.query(TrainingConfig).filter(TrainingConfig.config_id == id).first()

    if config is None:
        raise HTTPException(status_code=404, detail="Конфигурация модели не найдена")
    
    return config


@router.post("/configurations", response_model=ConfigRequest)
def post_config(
    config: ConfigRequest,
    db: Annotated[Session, Depends(get_database)]
):
    db_config = TrainingConfig(**config.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config