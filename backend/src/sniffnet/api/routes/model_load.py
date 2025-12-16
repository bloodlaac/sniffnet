from fastapi import APIRouter

from sniffnet.api.config import MODEL_DEVICE, MODEL_WEIGHTS_PATH
from sniffnet.core import model_loader

router = APIRouter(tags=["model"])


@router.post("/api/model/load")
def load_model():
    if model_loader.is_loaded():
        return {"status": "already_loaded"}

    started = model_loader.start_load(str(MODEL_WEIGHTS_PATH), MODEL_DEVICE)

    if started or model_loader.is_loading():
        return {"status": "loading_started"}

    return {"status": "already_loaded"}
