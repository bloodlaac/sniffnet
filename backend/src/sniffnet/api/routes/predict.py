from io import BytesIO

import torch
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from PIL import Image

from sniffnet.api.config import MODEL_DEVICE, MODEL_WEIGHTS_PATH
from sniffnet.core.model_loader import start_load, get_model_blocking, get_model_health

router = APIRouter(tags=["predict"])


@router.post("/api/predict")
async def predict(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file")

    start_load(str(MODEL_WEIGHTS_PATH), MODEL_DEVICE)

    try:
        model, transform, classes = get_model_blocking(timeout=30)
    except RuntimeError as exc:
        message = str(exc)
        if "loading in progress" in message:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Model is loading, try again",
            )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)

    tensor = transform(image).unsqueeze(0)
    device = next(model.parameters()).device
    tensor = tensor.to(device)

    with torch.no_grad():
        logits = model(tensor)
        probs_tensor = torch.softmax(logits, dim=1)[0]

    probs = probs_tensor.cpu().tolist()
    pred_idx = int(probs_tensor.argmax().item())

    probs_by_class = {classes[i]: float(probs[i]) for i in range(min(len(classes), len(probs)))}

    return {
        "class": classes[pred_idx] if pred_idx < len(classes) else str(pred_idx),
        "confidence": float(probs[pred_idx]),
        "probs": probs_by_class,
    }


@router.get("/api/model/health")
async def model_health():
    if not start_load(str(MODEL_WEIGHTS_PATH), MODEL_DEVICE):
        # load already triggered or in progress; continue
        pass

    try:
        model, _, _ = get_model_blocking(timeout=30)
        device = str(next(model.parameters()).device)
    except RuntimeError as exc:
        message = str(exc)
        if "loading in progress" in message:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Model is loading, try again",
            )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)

    try:
        health = get_model_health()
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    health["device"] = device
    return health
