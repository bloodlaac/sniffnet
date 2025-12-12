from pydantic import BaseModel, ConfigDict


class MetricRequest(BaseModel):
    metric_id: int
    dataset_id: int
    config_id: int
    train_accuracy: float
    train_loss: float

    model_config = ConfigDict(from_attributes=True)