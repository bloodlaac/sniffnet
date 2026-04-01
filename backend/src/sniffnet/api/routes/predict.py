from __future__ import annotations

from io import BytesIO

import torch
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from PIL import Image
from sqlalchemy.orm import Session

from sniffnet.api.config import MODEL_DEVICE, MODEL_WEIGHTS_DIR
from sniffnet.api.deps import get_database
from sniffnet.core.model_loader import load_model_for_weights
from sniffnet.database.db_models import Model


router = APIRouter(tags=["predict"])


@router.post("/predict")
async def predict(
    file: UploadFile = File(...),
    model_id: int = Form(...),
    db: Session = Depends(get_database),
):
    model_row = db.get(Model, model_id)
    if model_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    if not model_row.weights_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Model is not available for inference")

    weights_path = MODEL_WEIGHTS_DIR / model_row.weights_path
    if not weights_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model weights file not found")

    image_bytes = await file.read()
    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        model, transform, classes = load_model_for_weights(str(weights_path), MODEL_DEVICE)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

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
