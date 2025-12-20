from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    LargeBinary,
    Float,
    Interval
)
from sqlalchemy.orm import relationship
from sniffnet.database.db import Base

from datetime import datetime, timezone

class User(Base):
    __tablename__ = "user"

    user_id = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True, nullable=False)
    email = Column(String(20), unique=True)
    password = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    experiments = relationship("Experiment", back_populates="user")


class Experiment(Base):
    __tablename__ = "experiment"

    experiment_id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey("dataset.dataset_id"))
    config_id = Column(Integer, ForeignKey("training_config.config_id"))
    user_id = Column(Integer, ForeignKey("user.user_id"))
    model_id = Column(Integer, ForeignKey("model.model_id"))
    
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    status = Column(String(20), default="queued")
    error_message = Column(String(255))

    user = relationship("User", back_populates="experiments")
    dataset = relationship("Dataset", back_populates="experiments")
    config = relationship("TrainingConfig", back_populates="experiments")
    model = relationship("Model", back_populates="experiments")


class Dataset(Base):
    __tablename__ = "dataset"

    dataset_id = Column(Integer, primary_key=True)
    name = Column(String(20), nullable=False)
    classes_num = Column(Integer, nullable=False)
    source = Column(String(20))

    experiments = relationship("Experiment", back_populates="dataset")
    models = relationship("Model", back_populates="dataset")
    metrics = relationship("Metric", back_populates="dataset")


class TrainingConfig(Base):
    __tablename__ = "training_config"

    config_id = Column(Integer, primary_key=True)
    epochs_num = Column(Integer)
    batch_size = Column(Integer)
    loss_function = Column(String(20))
    learning_rate = Column(Float)
    optimizer = Column(String(20))
    layers_num = Column(Integer)
    neurons_num = Column(Integer)
    val_split = Column(Float, default=0.2)

    experiments = relationship("Experiment", back_populates="config")
    models = relationship("Model", back_populates="config")
    metrics = relationship("Metric", back_populates="config")


class Model(Base):
    __tablename__ = "model"

    model_id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey("dataset.dataset_id"))
    config_id = Column(Integer, ForeignKey("training_config.config_id"))

    params_num = Column(Integer)
    weights = Column(LargeBinary)
    weights_path = Column(String(255))
    name = Column(String(20))
    training_time = Column(Interval)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    dataset = relationship("Dataset", back_populates="models")
    config = relationship("TrainingConfig", back_populates="models")
    experiments = relationship("Experiment", back_populates="model")


class Metric(Base):
    __tablename__ = "metric"

    metric_id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey("dataset.dataset_id"))
    config_id = Column(Integer, ForeignKey("training_config.config_id"))

    train_accuracy = Column(Float)
    train_loss = Column(Float)

    dataset = relationship("Dataset", back_populates="metrics")
    config = relationship("TrainingConfig", back_populates="metrics")
