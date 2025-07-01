from pydantic import BaseModel, ConfigDict


class ConfigRequest(BaseModel):
    epochs_num: int
    batch_size: int
    loss_function: str
    learning_rate: float
    optimizer: str
    layers_num: int
    neurons_num: int

    model_config = ConfigDict(from_attributes=True)