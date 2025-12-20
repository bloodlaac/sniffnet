from io import BytesIO

import torch
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Form, Depends
from PIL import Image

from sniffnet.api.config import MODEL_DEVICE, MODEL_WEIGHTS_DIR
from sniffnet.core.model_loader import load_model_for_weights, get_model_health
from sniffnet.api.deps import get_database
from sniffnet.database.db_models import Model
from sqlalchemy.orm import Session

router = APIRouter(tags=["predict"])


@router.post("/predict")
async def predict(
    file: UploadFile = File(...),
    model_id: int = Form(...),
    db: Session = Depends(get_database),
):
    model_row = db.query(Model).filter(Model.model_id == model_id).first()
    if model_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Модель не найдена")
    if not model_row.weights_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Файл весов не указан")

    weights_path = MODEL_WEIGHTS_DIR / model_row.weights_path
    if not weights_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл весов не найден")

    try:
        image_bytes = await file.read()
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file")

    try:
        model, transform, classes = load_model_for_weights(str(weights_path), MODEL_DEVICE)
    except RuntimeError as exc:
        message = str(exc)
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


@router.get("/model/health")
async def model_health():
    try:
        health = get_model_health()
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    return health
