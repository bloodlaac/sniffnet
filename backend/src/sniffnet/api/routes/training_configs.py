from typing import Annotated
from sqlalchemy.orm import Session
from sniffnet.schemas.training_configs import TrainingConfigCreate, TrainingConfigResponse
from sniffnet.api.deps import get_database
from sniffnet.database.db_models import TrainingConfig

from fastapi import APIRouter, HTTPException, Depends


router = APIRouter(tags=["training_configs"])

def serialize_training_config(config: TrainingConfig) -> dict:
    return {
        "training_config_id": config.config_id,
        "epochs_num": config.epochs_num,
        "batch_size": config.batch_size,
        "loss_function": config.loss_function,
        "learning_rate": config.learning_rate,
        "optimizer": config.optimizer,
        "val_split": config.val_split if config.val_split is not None else 0.2,
    }

@router.get("/training-configs", response_model=list[TrainingConfigResponse])
@router.get("/configurations", response_model=list[TrainingConfigResponse])
def get_configs(db: Annotated[Session, Depends(get_database)]):
    configs = db.query(TrainingConfig).all()
    return [serialize_training_config(cfg) for cfg in configs]

@router.get("/training-configs/{id}", response_model=TrainingConfigResponse)
@router.get("/configurations/{id}", response_model=TrainingConfigResponse)
def get_config(id, db: Annotated[Session, Depends(get_database)]):
    config = db.query(TrainingConfig).filter(TrainingConfig.config_id == id).first()

    if config is None:
        raise HTTPException(status_code=404, detail="Конфигурация модели не найдена")
    
    return serialize_training_config(config)


@router.post("/training-configs", response_model=TrainingConfigResponse)
@router.post("/configurations", response_model=TrainingConfigResponse)
def post_config(
    config: TrainingConfigCreate,
    db: Annotated[Session, Depends(get_database)]
):
    db_config = TrainingConfig(**config.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return serialize_training_config(db_config)
