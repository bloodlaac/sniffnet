from sniffnet.schemas.models import ModelRequest
from typing import Annotated
from sqlalchemy.orm import Session
from sniffnet.database.db_models import Model
from sniffnet.api.deps import get_database

from fastapi import APIRouter, HTTPException, Depends, Body, Form


router = APIRouter(tags=["models"])

@router.get("/models")
def get_models(db: Session = Depends(get_database)):
    return db.query(Model).all()


@router.get("/models/{id}")
def get_model(id, db: Annotated[Session, Depends(get_database)]):
    model =  db.query(Model).filter(Model.model_id == id).first()

    if model is None:
        raise HTTPException(status_code=404, detail="Модель не найдена")
    
    return model


@router.post("/models")
def post_model(
    model: ModelRequest,
    db: Annotated[Session, Depends(get_database)],
    #weights: Annotated[bytes, Form()]  # TODO: how to send weights through api
) -> ModelRequest:
    db_model = Model(**model.model_dump())
    db.add(db_model)
    db.commit()
    db.refresh(db_model)

    return db_model