from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from sniffnet.api.deps import get_database
from sniffnet.api.errors import BadRequestException, NotFoundException
from sniffnet.api.helpers import get_accessible_model, get_metric, is_admin
from sniffnet.api.mappers import (
    to_dataset_response,
    to_metric_response,
    to_model_response,
    to_training_config_response,
)
from sniffnet.api.security import get_current_principal
from sniffnet.database.db_models import Dataset, Experiment, Model, TrainingConfig
from sniffnet.schemas.contracts import (
    DatasetResponse,
    MetricResponse,
    ModelResponse,
    TrainingConfigRequest,
    TrainingConfigResponse,
)


router = APIRouter(tags=["catalog"])


@router.get("/datasets", response_model=list[DatasetResponse], dependencies=[Depends(get_current_principal)])
def get_datasets(db: Session = Depends(get_database)) -> list[DatasetResponse]:
    datasets = db.scalars(select(Dataset).order_by(Dataset.id.asc())).all()
    return [to_dataset_response(dataset) for dataset in datasets]


@router.get("/datasets/{id}", response_model=DatasetResponse, dependencies=[Depends(get_current_principal)])
def get_dataset(id: int, db: Session = Depends(get_database)) -> DatasetResponse:
    dataset = db.get(Dataset, id)
    if dataset is None:
        raise NotFoundException("Dataset not found")
    return to_dataset_response(dataset)


@router.get("/configs", response_model=list[TrainingConfigResponse], dependencies=[Depends(get_current_principal)])
def get_configs(db: Session = Depends(get_database)) -> list[TrainingConfigResponse]:
    configs = db.scalars(select(TrainingConfig).order_by(TrainingConfig.id.asc())).all()
    return [to_training_config_response(config) for config in configs]


@router.post("/configs", response_model=TrainingConfigResponse, status_code=status.HTTP_201_CREATED)
def create_config(
    request: TrainingConfigRequest,
    db: Session = Depends(get_database),
    _=Depends(get_current_principal),
) -> TrainingConfigResponse:
    config = TrainingConfig(
        epochs_num=request.epochsNum,
        batch_size=request.batchSize,
        learning_rate=request.learningRate,
        optimizer=request.optimizer,
        loss_function=request.lossFunction,
        validation_split=request.validationSplit,
        layers_num=request.layersNum,
        neurons_num=request.neuronsNum,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return to_training_config_response(config)


@router.get("/configs/{id}", response_model=TrainingConfigResponse, dependencies=[Depends(get_current_principal)])
def get_config(id: int, db: Session = Depends(get_database)) -> TrainingConfigResponse:
    config = db.get(TrainingConfig, id)
    if config is None:
        raise NotFoundException("Training config not found")
    return to_training_config_response(config)


@router.put("/configs/{id}", response_model=TrainingConfigResponse, dependencies=[Depends(get_current_principal)])
def update_config(id: int, request: TrainingConfigRequest, db: Session = Depends(get_database)) -> TrainingConfigResponse:
    config = db.get(TrainingConfig, id)
    if config is None:
        raise NotFoundException("Training config not found")
    config.epochs_num = request.epochsNum
    config.batch_size = request.batchSize
    config.learning_rate = request.learningRate
    config.optimizer = request.optimizer
    config.loss_function = request.lossFunction
    config.validation_split = request.validationSplit
    config.layers_num = request.layersNum
    config.neurons_num = request.neuronsNum
    db.commit()
    db.refresh(config)
    return to_training_config_response(config)


@router.delete("/configs/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_principal)])
def delete_config(id: int, db: Session = Depends(get_database)) -> Response:
    config = db.get(TrainingConfig, id)
    if config is None:
        raise NotFoundException("Training config not found")
    is_used = db.scalar(select(func.count(Experiment.id)).where(Experiment.config_id == id))
    if is_used:
        raise BadRequestException("Training config is already used by an experiment")
    db.delete(config)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/models", response_model=list[ModelResponse])
def get_models(
    datasetId: int | None = None,
    principal=Depends(get_current_principal),
    db: Session = Depends(get_database),
) -> list[ModelResponse]:
    stmt = (
        select(Model)
        .options(
            joinedload(Model.dataset),
            joinedload(Model.config),
            joinedload(Model.experiment).joinedload(Experiment.user),
        )
        .order_by(Model.created_at.desc())
    )
    if datasetId is not None:
        stmt = stmt.where(Model.dataset_id == datasetId)
    if not is_admin(principal):
        stmt = stmt.join(Model.experiment).where(Experiment.user_id == principal.id)
    models = db.scalars(stmt).unique().all()
    result: list[ModelResponse] = []
    for model in models:
        metric = get_metric(db, model.dataset_id, model.config_id)
        result.append(to_model_response(model, metric))
    return result


@router.get("/models/{id}", response_model=ModelResponse)
def get_model(id: int, principal=Depends(get_current_principal), db: Session = Depends(get_database)) -> ModelResponse:
    model = get_accessible_model(db, id, principal)
    metric = get_metric(db, model.dataset_id, model.config_id)
    return to_model_response(model, metric)


@router.get("/models/{id}/metrics", response_model=MetricResponse)
def get_model_metrics(
    id: int,
    principal=Depends(get_current_principal),
    db: Session = Depends(get_database),
) -> MetricResponse:
    model = get_accessible_model(db, id, principal)
    metric = get_metric(db, model.dataset_id, model.config_id)
    if metric is None:
        raise NotFoundException("Metrics not found for model")
    return to_metric_response(metric)
