from sniffnet.schemas.datasets import DatasetRequest
from typing import Annotated
from sqlalchemy.orm import Session
from sniffnet.database.db_models import Dataset
from sniffnet.api.deps import get_database

from fastapi import APIRouter, HTTPException, Depends


router = APIRouter(tags=["datasets"])

@router.get("/datasets")
def get_datasets(db: Annotated[Session, Depends(get_database)]):
    return db.query(Dataset).all()


@router.get("/datasets/{id}")
def get_dataset(id, db: Annotated[Session, Depends(get_database)]):
    dataset = db.query(Dataset).filter(Dataset.dataset_id == id).first()

    if dataset is None:
        raise HTTPException(status_code=404, detail="Датасет не найден")
    
    return dataset


@router.post("/datasets")
def post_dataset(dataset: DatasetRequest, db: Annotated[Session, Depends(get_database)]) -> DatasetRequest:
    db_dataset = Dataset(**dataset.model_dump())
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)

    return db_dataset

@router.put("/datasets")
def update_dataset(input_dataset: DatasetRequest, db: Annotated[Session, Depends(get_database)]) -> DatasetRequest:
    db_dataset = db.query(Dataset).filter(Dataset.dataset_id == input_dataset["dataset_id"]).first()

    if db_dataset is None:
        raise HTTPException(status_code=404, detail="Датасет не найден")
    
    db_dataset.name = input_dataset["name"]
    db_dataset.classes_num = input_dataset["classes_num"]
    db_dataset.source = input_dataset["source"]

    db.commit()
    db.refresh(db_dataset)

    return db_dataset