from sniffnet.schemas.metrics import MetricRequest
from typing import Annotated
from sqlalchemy.orm import Session
from sniffnet.database.db_models import Metric
from sniffnet.api.deps import get_database

from fastapi import APIRouter, HTTPException, Depends, Body


router = APIRouter(tags=["metrics"])

@router.get("/metrics")
def get_metrics(db: Annotated[Session, Depends(get_database)]):
    return db.query(Metric).all()


@router.get("/metrics/{id}")
def get_metric(id, db: Annotated[Session, Depends(get_database)]):
    metric = db.query(Metric).filter(Metric.metric_id == id).first()

    if metric is None:
        raise HTTPException(status_code=404, detail="Метрики не найдены")
    
    return metric


@router.post("/metrics")
def post_metric(metric: MetricRequest, db: Annotated[Session, Depends(get_database)]) -> MetricRequest:
    db_metric = Metric(**metric.model_dump())
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)

    return db_metric