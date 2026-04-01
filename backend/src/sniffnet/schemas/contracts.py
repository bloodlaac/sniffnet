from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class ApiErrorResponse(BaseModel):
    timestamp: str
    status: int
    error: str
    message: str
    path: str
    validationErrors: dict[str, str] | None = None


class AuthResponse(BaseModel):
    token: str
    userId: int
    username: str
    email: str
    role: str


class CurrentUserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    createdAt: datetime


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str
    password: str = Field(min_length=6, max_length=100)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    createdAt: datetime


class UserUpdateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str
    role: str


class DatasetResponse(BaseModel):
    id: int
    name: str
    classesNum: int
    source: str


class TrainingConfigRequest(BaseModel):
    epochsNum: int = Field(gt=0)
    batchSize: int = Field(gt=0)
    learningRate: float = Field(gt=0)
    optimizer: str
    lossFunction: str
    validationSplit: float = Field(gt=0.0, lt=1.0)
    layersNum: int | None = Field(default=None, gt=0)
    neuronsNum: int | None = Field(default=None, gt=0)


class TrainingConfigResponse(TrainingConfigRequest):
    id: int


class MetricResponse(BaseModel):
    id: int
    trainAccuracy: float
    trainLoss: float
    validationAccuracy: float | None = None
    validationLoss: float | None = None
    detailsJson: str | None = None


class ModelResponse(BaseModel):
    id: int
    name: str
    datasetId: int
    datasetName: str
    configId: int
    experimentId: int
    paramsNum: int | None = None
    trainingTimeSeconds: int
    availableForInference: bool
    weightsPath: str | None = None
    createdAt: datetime
    metrics: MetricResponse | None = None


class ExperimentResponse(BaseModel):
    id: int
    status: str
    startTime: datetime
    endTime: datetime | None = None
    reportPath: str | None = None
    errorMessage: str | None = None
    datasetId: int
    datasetName: str
    userId: int
    username: str
    config: TrainingConfigResponse
    model: ModelResponse | None = None
    metrics: MetricResponse | None = None


class ExperimentCreateRequest(BaseModel):
    datasetId: int
    configId: int | None = None
    config: TrainingConfigRequest | None = None

    @model_validator(mode="after")
    def validate_config_choice(self) -> "ExperimentCreateRequest":
        if self.configId is None and self.config is None:
            raise ValueError("configId or config payload is required")
        return self


class ExperimentStatusUpdateRequest(BaseModel):
    status: str


class UploadedImageResponse(BaseModel):
    id: int
    userId: int
    originalFilename: str
    storedFilename: str
    contentType: str
    sizeBytes: int
    storagePath: str
    uploadedAt: datetime


class ClassificationResponse(BaseModel):
    id: int
    status: str
    createdAt: datetime
    completedAt: datetime | None = None
    predictedClass: str | None = None
    confidence: float | None = None
    modelId: int
    modelName: str
    imageId: int
    imagePath: str
    probabilities: dict[str, float]


class ClassificationQuery(BaseModel):
    userId: int | None = None
    from_: date | None = Field(default=None, alias="from")
    to: date | None = None


class PredictResponse(BaseModel):
    class_name: str = Field(alias="class")
    confidence: float
    probs: dict[str, float]

    model_config = {"populate_by_name": True}


class LegacyStartExperimentRequest(BaseModel):
    experiment_id: int | None = None
    user_id: int | None = None
    dataset_id: int
    config_id: int | None = None
    config: dict[str, Any] | None = None


class LegacyStartExperimentResponse(BaseModel):
    experiment_id: int
    status: str


class ClassificationFilters(BaseModel):
    user_id: int | None = None
    from_date: date | None = None
    to_date: date | None = None

    @field_validator("to_date")
    @classmethod
    def validate_dates(cls, value: date | None, info):
        from_date = info.data.get("from_date")
        if value is not None and from_date is not None and value < from_date:
            raise ValueError("to must be greater than or equal to from")
        return value
