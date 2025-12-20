from pydantic import BaseModel, ConfigDict, Field


class TrainingConfigCreate(BaseModel):
    epochs_num: int
    batch_size: int
    loss_function: str
    learning_rate: float
    optimizer: str
    val_split: float = Field(default=0.2, gt=0, lt=1)


class TrainingConfigResponse(TrainingConfigCreate):
    training_config_id: int

    model_config = ConfigDict(from_attributes=True)
