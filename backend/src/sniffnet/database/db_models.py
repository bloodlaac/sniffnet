from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from sniffnet.database.db import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)

    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    user_id = Column("id", Integer, primary_key=True)
    username = Column(String(20), unique=True, nullable=False)
    email = Column(String(20), unique=True)
    password = Column(String(128), nullable=False)
    role_id = Column("role_id", Integer, ForeignKey("roles.id"), nullable=False)
    created_at = Column("createdAt", DateTime, default=datetime.now(timezone.utc))

    role = relationship("Role", back_populates="users")
    experiments = relationship("Experiment", back_populates="user")


class Experiment(Base):
    __tablename__ = "experiments"

    experiment_id = Column("id", Integer, primary_key=True)
    dataset_id = Column("dataset_id", Integer, ForeignKey("datasets.id"))
    config_id = Column("config_id", Integer, ForeignKey("training_configs.id"))
    user_id = Column("user_id", Integer, ForeignKey("users.id"))

    start_time = Column("startTime", DateTime(timezone=True))
    end_time = Column("endTime", DateTime(timezone=True))
    status = Column(String(20), default="CREATED")
    error_message = Column("errorMessage", String(255))
    report_path = Column("reportPath", String(255))
    external_experiment_id = Column("externalExperimentId", Integer, unique=True)

    user = relationship("User", back_populates="experiments")
    dataset = relationship("Dataset", back_populates="experiments")
    config = relationship("TrainingConfig", back_populates="experiments")
    model = relationship("Model", back_populates="experiment", uselist=False)


class Dataset(Base):
    __tablename__ = "datasets"

    dataset_id = Column("id", Integer, primary_key=True)
    name = Column(String(20), nullable=False)
    classes_num = Column("classesNum", Integer, nullable=False)
    source = Column(String(20))

    experiments = relationship("Experiment", back_populates="dataset")
    models = relationship("Model", back_populates="dataset")
    metrics = relationship("Metric", back_populates="dataset")


class TrainingConfig(Base):
    __tablename__ = "training_configs"

    config_id = Column("id", Integer, primary_key=True)
    epochs_num = Column("epochsNum", Integer)
    batch_size = Column("batchSize", Integer)
    loss_function = Column("lossFunction", String(20))
    learning_rate = Column("learningRate", Float)
    optimizer = Column(String(20))
    layers_num = Column("layersNum", Integer)
    neurons_num = Column("neuronsNum", Integer)
    val_split = Column("validationSplit", Float, default=0.2)

    experiments = relationship("Experiment", back_populates="config")
    models = relationship("Model", back_populates="config")
    metrics = relationship("Metric", back_populates="config")


class Model(Base):
    __tablename__ = "models"

    model_id = Column("id", Integer, primary_key=True)
    dataset_id = Column("dataset_id", Integer, ForeignKey("datasets.id"))
    config_id = Column("config_id", Integer, ForeignKey("training_configs.id"))
    experiment_id = Column("experiment_id", Integer, ForeignKey("experiments.id"))

    params_num = Column("paramsNum", Integer)
    weights_path = Column("weightsPath", String(255))
    name = Column(String(120), nullable=False, unique=True)
    training_time_seconds = Column("trainingTimeSeconds", Integer, nullable=False, default=0)
    available_for_inference = Column("availableForInference", Boolean, nullable=False, default=False)
    external_model_id = Column("externalModelId", Integer, unique=True)
    created_at = Column("createdAt", DateTime, default=datetime.now(timezone.utc))

    dataset = relationship("Dataset", back_populates="models")
    config = relationship("TrainingConfig", back_populates="models")
    experiment = relationship("Experiment", back_populates="model")


class Metric(Base):
    __tablename__ = "metrics"

    metric_id = Column("id", Integer, primary_key=True)
    dataset_id = Column("dataset_id", Integer, ForeignKey("datasets.id"))
    config_id = Column("config_id", Integer, ForeignKey("training_configs.id"))

    train_accuracy = Column("trainAccuracy", Float)
    train_loss = Column("trainLoss", Float)
    validation_accuracy = Column("validationAccuracy", Float)
    validation_loss = Column("validationLoss", Float)
    details_json = Column("detailsJson", String)

    dataset = relationship("Dataset", back_populates="metrics")
    config = relationship("TrainingConfig", back_populates="metrics")
