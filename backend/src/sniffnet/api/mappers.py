from __future__ import annotations

import json

from sniffnet.database.db_models import (
    ClassificationRequest,
    Dataset,
    Experiment,
    Metric,
    Model,
    TrainingConfig,
    UploadedImage,
    User,
)
from sniffnet.schemas.contracts import (
    ClassificationResponse,
    CurrentUserResponse,
    DatasetResponse,
    ExperimentResponse,
    MetricResponse,
    ModelResponse,
    TrainingConfigResponse,
    UploadedImageResponse,
    UserResponse,
)


def to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.code,
        createdAt=user.created_at,
    )


def to_current_user_response(user: User) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.code,
        createdAt=user.created_at,
    )


def to_dataset_response(dataset: Dataset) -> DatasetResponse:
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        classesNum=dataset.classes_num,
        source=dataset.source,
    )


def to_training_config_response(config: TrainingConfig) -> TrainingConfigResponse:
    return TrainingConfigResponse(
        id=config.id,
        epochsNum=config.epochs_num,
        batchSize=config.batch_size,
        learningRate=float(config.learning_rate),
        optimizer=config.optimizer,
        lossFunction=config.loss_function,
        validationSplit=float(config.validation_split),
        layersNum=config.layers_num,
        neuronsNum=config.neurons_num,
    )


def to_metric_response(metric: Metric | None) -> MetricResponse | None:
    if metric is None:
        return None
    return MetricResponse(
        id=metric.id,
        trainAccuracy=metric.train_accuracy,
        trainLoss=metric.train_loss,
        validationAccuracy=metric.validation_accuracy,
        validationLoss=metric.validation_loss,
        detailsJson=metric.details_json,
    )


def to_model_response(model: Model, metric: Metric | None = None) -> ModelResponse:
    return ModelResponse(
        id=model.id,
        name=model.name,
        datasetId=model.dataset.id,
        datasetName=model.dataset.name,
        configId=model.config.id,
        experimentId=model.experiment.id,
        paramsNum=model.params_num,
        trainingTimeSeconds=model.training_time_seconds,
        availableForInference=model.available_for_inference,
        weightsPath=model.weights_path,
        createdAt=model.created_at,
        metrics=to_metric_response(metric),
    )


def to_experiment_response(
    experiment: Experiment,
    model: Model | None = None,
    metric: Metric | None = None,
) -> ExperimentResponse:
    return ExperimentResponse(
        id=experiment.id,
        status=experiment.status,
        startTime=experiment.start_time,
        endTime=experiment.end_time,
        reportPath=experiment.report_path,
        errorMessage=experiment.error_message,
        datasetId=experiment.dataset.id,
        datasetName=experiment.dataset.name,
        userId=experiment.user.id,
        username=experiment.user.username,
        config=to_training_config_response(experiment.config),
        model=to_model_response(model, metric) if model else None,
        metrics=to_metric_response(metric),
    )


def to_uploaded_image_response(image: UploadedImage) -> UploadedImageResponse:
    return UploadedImageResponse(
        id=image.id,
        userId=image.user.id,
        originalFilename=image.original_filename,
        storedFilename=image.stored_filename,
        contentType=image.content_type,
        sizeBytes=image.size_bytes,
        storagePath=image.storage_path,
        uploadedAt=image.uploaded_at,
    )


def to_classification_response(request: ClassificationRequest) -> ClassificationResponse:
    probabilities = json.loads(request.probabilities_json) if request.probabilities_json else {}
    return ClassificationResponse(
        id=request.id,
        status=request.status,
        createdAt=request.created_at,
        completedAt=request.completed_at,
        predictedClass=request.predicted_class,
        confidence=request.confidence,
        modelId=request.model.id,
        modelName=request.model.name,
        imageId=request.image.id,
        imagePath=request.image.storage_path,
        probabilities={str(key): float(value) for key, value in probabilities.items()},
    )
