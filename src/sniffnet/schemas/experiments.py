from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ExperimentBase(BaseModel):
    start_time: datetime
    end_time: datetime

    model_config = ConfigDict(from_attributes=True)

class ExperimentRequest(BaseModel):
    dataset_id: int
    user_id: int
    start_time: datetime
    end_time: datetime

    epochs_num: int
    batch_size: int
    loss_function: str
    learning_rate: float
    optimizer: str
    layers_num: int
    neurons_num: int

    model_config = ConfigDict(from_attributes=True)

class ExperimentJoined(BaseModel):
    experiment_id: int
    dataset_id: int
    config_id: int
    user_id: int

    start_time: datetime
    end_time: datetime

    # поля из TrainingConfig
    batch_size: int
    epochs_num: int
    loss_function: str
    learning_rate: float
    optimizer: str
    layers_num: int
    neurons_num: int

    model_config = ConfigDict(from_attributes=True)