from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ModelRequest(BaseModel):
    model_id: int
    dataset_id: int
    config_id: int
    params_num: int
    weights: bytes  # TODO: think of forms
    name: str
    training_time: datetime
    
    model_config = ConfigDict(from_attributes=True)