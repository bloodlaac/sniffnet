from sniffnet.schemas.models import ModelResponse
from typing import Annotated
from sqlalchemy.orm import Session
from sniffnet.database.db_models import Model
from sniffnet.api.deps import get_database

from fastapi import APIRouter, HTTPException, Depends


router = APIRouter(tags=["models"])

def serialize_model(model: Model) -> dict:
    return {
        "model_id": model.model_id,
        "dataset_id": model.dataset_id,
        "config_id": model.config_id,
        "name": model.name,
        "weights_path": model.weights_path,
        "created_at": model.created_at,
    }


@router.get("/models", response_model=list[ModelResponse])
def get_models(db: Session = Depends(get_database)):
    models = (
        db.query(Model)
        .filter(Model.weights_path.isnot(None))
        .order_by(Model.model_id.desc())
        .all()
    )
    return [serialize_model(model) for model in models]


@router.get("/models/{id}", response_model=ModelResponse)
def get_model(id, db: Annotated[Session, Depends(get_database)]):
    model =  db.query(Model).filter(Model.model_id == id).first()

    if model is None:
        raise HTTPException(status_code=404, detail="Модель не найдена")
    
    return serialize_model(model)
