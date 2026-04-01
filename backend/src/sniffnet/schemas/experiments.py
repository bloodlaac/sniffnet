from typing import Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from sniffnet.schemas.training_configs import TrainingConfigCreate


class ExperimentBase(BaseModel):
    start_time: datetime
    end_time: datetime

    model_config = ConfigDict(from_attributes=True)


class StartExperimentRequest(BaseModel):
    experiment_id: Optional[int] = None
    user_id: Optional[int] = None
    dataset_id: int
    config_id: Optional[int] = None
    config: TrainingConfigCreate


class StartExperimentResponse(BaseModel):
    experiment_id: int
    status: str

class ExperimentJoined(BaseModel):
    experiment_id: int
    dataset_id: int
    config_id: int
    user_id: Optional[int]
    model_id: Optional[int]
    start_time: datetime
    end_time: Optional[datetime]
    status: Optional[str] = None
    error_message: Optional[str] = None

    batch_size: int
    epochs_num: int
    loss_function: str
    learning_rate: float
    optimizer: str
    val_split: float

    train_accuracy: Optional[float] = None
    train_loss: Optional[float] = None
    validation_accuracy: Optional[float] = None
    validation_loss: Optional[float] = None
    params_num: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
