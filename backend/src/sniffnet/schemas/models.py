from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class ModelResponse(BaseModel):
    model_id: int
    dataset_id: Optional[int] = None
    config_id: Optional[int] = None
    name: Optional[str] = None
    weights_path: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
