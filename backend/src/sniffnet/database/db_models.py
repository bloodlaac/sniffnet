from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sniffnet.database.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="role")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column("createdAt", DateTime(timezone=True), default=utcnow, nullable=False)

    role: Mapped[Role] = relationship(back_populates="users")
    experiments: Mapped[list["Experiment"]] = relationship(back_populates="user")
    uploaded_images: Mapped[list["UploadedImage"]] = relationship(back_populates="user")
    classifications: Mapped[list["ClassificationRequest"]] = relationship(back_populates="user")


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    classes_num: Mapped[int] = mapped_column("classesNum", Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)

    experiments: Mapped[list["Experiment"]] = relationship(back_populates="dataset")
    models: Mapped[list["Model"]] = relationship(back_populates="dataset")
    metrics: Mapped[list["Metric"]] = relationship(back_populates="dataset")


class TrainingConfig(Base):
    __tablename__ = "training_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    epochs_num: Mapped[int] = mapped_column("epochsNum", Integer, nullable=False)
    batch_size: Mapped[int] = mapped_column("batchSize", Integer, nullable=False)
    learning_rate: Mapped[float] = mapped_column("learningRate", Numeric(10, 6), nullable=False)
    optimizer: Mapped[str] = mapped_column(String(100), nullable=False)
    loss_function: Mapped[str] = mapped_column("lossFunction", String(100), nullable=False)
    validation_split: Mapped[float] = mapped_column("validationSplit", Numeric(4, 2), nullable=False)
    layers_num: Mapped[int | None] = mapped_column("layersNum", Integer)
    neurons_num: Mapped[int | None] = mapped_column("neuronsNum", Integer)

    experiments: Mapped[list["Experiment"]] = relationship(back_populates="config")
    models: Mapped[list["Model"]] = relationship(back_populates="config")
    metrics: Mapped[list["Metric"]] = relationship(back_populates="config")


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    config_id: Mapped[int] = mapped_column(ForeignKey("training_configs.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="CREATED")
    start_time: Mapped[datetime] = mapped_column("startTime", DateTime(timezone=True), default=utcnow, nullable=False)
    end_time: Mapped[datetime | None] = mapped_column("endTime", DateTime(timezone=True))
    report_path: Mapped[str | None] = mapped_column("reportPath", String(255))
    error_message: Mapped[str | None] = mapped_column("errorMessage", String(255))
    external_experiment_id: Mapped[int | None] = mapped_column("externalExperimentId", Integer, unique=True)

    dataset: Mapped[Dataset] = relationship(back_populates="experiments")
    config: Mapped[TrainingConfig] = relationship(back_populates="experiments")
    user: Mapped[User] = relationship(back_populates="experiments")
    model: Mapped["Model | None"] = relationship(back_populates="experiment", uselist=False)


class Model(Base):
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    config_id: Mapped[int] = mapped_column(ForeignKey("training_configs.id"), nullable=False)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"), nullable=False, unique=True)
    params_num: Mapped[int | None] = mapped_column("paramsNum", Integer)
    training_time_seconds: Mapped[int] = mapped_column("trainingTimeSeconds", Integer, nullable=False, default=0)
    available_for_inference: Mapped[bool] = mapped_column(
        "availableForInference",
        Boolean,
        nullable=False,
        default=False,
    )
    weights_path: Mapped[str | None] = mapped_column("weightsPath", String(255))
    external_model_id: Mapped[int | None] = mapped_column("externalModelId", Integer, unique=True)
    created_at: Mapped[datetime] = mapped_column("createdAt", DateTime(timezone=True), default=utcnow, nullable=False)

    dataset: Mapped[Dataset] = relationship(back_populates="models")
    config: Mapped[TrainingConfig] = relationship(back_populates="models")
    experiment: Mapped[Experiment] = relationship(back_populates="model")
    classifications: Mapped[list["ClassificationRequest"]] = relationship(back_populates="model")


class Metric(Base):
    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    config_id: Mapped[int] = mapped_column(ForeignKey("training_configs.id"), nullable=False)
    train_accuracy: Mapped[float] = mapped_column("trainAccuracy", Float, nullable=False)
    train_loss: Mapped[float] = mapped_column("trainLoss", Float, nullable=False)
    validation_accuracy: Mapped[float | None] = mapped_column("validationAccuracy", Float)
    validation_loss: Mapped[float | None] = mapped_column("validationLoss", Float)
    details_json: Mapped[str | None] = mapped_column("detailsJson", Text)

    dataset: Mapped[Dataset] = relationship(back_populates="metrics")
    config: Mapped[TrainingConfig] = relationship(back_populates="metrics")


class UploadedImage(Base):
    __tablename__ = "uploaded_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    original_filename: Mapped[str] = mapped_column("originalFilename", String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column("storedFilename", String(255), unique=True, nullable=False)
    content_type: Mapped[str] = mapped_column("contentType", String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column("sizeBytes", Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column("storagePath", String(500), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column("uploadedAt", DateTime(timezone=True), default=utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="uploaded_images")
    classifications: Mapped[list["ClassificationRequest"]] = relationship(back_populates="image")


class ClassificationRequest(Base):
    __tablename__ = "classification_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    model_id: Mapped[int] = mapped_column(ForeignKey("models.id"), nullable=False)
    image_id: Mapped[int] = mapped_column(ForeignKey("uploaded_images.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="CREATED")
    created_at: Mapped[datetime] = mapped_column("createdAt", DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column("completedAt", DateTime(timezone=True))
    predicted_class: Mapped[str | None] = mapped_column("predictedClass", String(100))
    confidence: Mapped[float | None] = mapped_column(Float)
    probabilities_json: Mapped[str | None] = mapped_column("probabilitiesJson", Text)

    user: Mapped[User] = relationship(back_populates="classifications")
    model: Mapped[Model] = relationship(back_populates="classifications")
    image: Mapped[UploadedImage] = relationship(back_populates="classifications")
