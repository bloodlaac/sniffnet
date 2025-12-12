from pydantic import BaseModel, ConfigDict


class DatasetRequest(BaseModel):
    dataset_id: int
    name: str
    classes_num: int
    source: str

    model_config = ConfigDict(from_attributes=True)