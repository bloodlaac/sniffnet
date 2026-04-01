from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta, timezone

import torch
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from sniffnet.api.config import MODEL_DEVICE, MODEL_WEIGHTS_DIR
from sniffnet.api.deps import get_database
from sniffnet.api.errors import BadRequestException, NotFoundException
from sniffnet.api.helpers import (
    get_accessible_classification,
    get_accessible_image,
    get_accessible_model,
    get_user_entity,
    is_admin,
    store_uploaded_image,
)
from sniffnet.api.mappers import to_classification_response
from sniffnet.api.security import get_current_principal
from sniffnet.core.model_loader import load_model_for_weights
from sniffnet.database.db_models import ClassificationRequest, Model, UploadedImage, User
from sniffnet.schemas.contracts import ClassificationResponse


router = APIRouter(prefix="/classifications", tags=["classifications"])


def _predict_image(model_row: Model, image_path: str) -> tuple[str, float, dict[str, float]]:
    if not model_row.weights_path:
        raise BadRequestException("Model is not available for inference")
    weights_path = MODEL_WEIGHTS_DIR / model_row.weights_path
    if not weights_path.exists():
        raise NotFoundException("Model weights file not found")

    try:
        model, transform, classes = load_model_for_weights(str(weights_path), MODEL_DEVICE)
        image = Image.open(image_path).convert("RGB")
    except NotFoundException:
        raise
    except Exception as exc:
        raise BadRequestException(str(exc)) from exc

    tensor = transform(image).unsqueeze(0)
    device = next(model.parameters()).device
    tensor = tensor.to(device)
    with torch.no_grad():
        logits = model(tensor)
        probs_tensor = torch.softmax(logits, dim=1)[0]

    probs = probs_tensor.cpu().tolist()
    pred_idx = int(probs_tensor.argmax().item())
    probabilities = {classes[i]: float(probs[i]) for i in range(min(len(classes), len(probs)))}
    predicted_class = classes[pred_idx] if pred_idx < len(classes) else str(pred_idx)
    return predicted_class, float(probs[pred_idx]), probabilities


@router.post("", response_model=ClassificationResponse, status_code=status.HTTP_201_CREATED)
async def classify(
    modelId: int = Form(...),
    imageId: int | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    principal=Depends(get_current_principal),
    db: Session = Depends(get_database),
) -> ClassificationResponse:
    model = get_accessible_model(db, modelId, principal)
    if not model.available_for_inference:
        raise BadRequestException("Model is not available for inference")

    user = get_user_entity(db, principal)
    image: UploadedImage
    if imageId is not None:
        image = get_accessible_image(db, imageId, principal)
    elif file is not None:
        image = await store_uploaded_image(db, file, user)
        image = get_accessible_image(db, image.id, principal)
    else:
        raise BadRequestException("Either imageId or file must be provided")

    request = ClassificationRequest(
        user_id=user.id,
        model_id=model.id,
        image_id=image.id,
        status="CREATED",
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    try:
        predicted_class, confidence, probabilities = _predict_image(model, image.storage_path)
        request.status = "COMPLETED"
        request.completed_at = datetime.now(timezone.utc)
        request.predicted_class = predicted_class
        request.confidence = confidence
        request.probabilities_json = json.dumps(probabilities)
        db.commit()
    except Exception:
        request.status = "FAILED"
        request.completed_at = datetime.now(timezone.utc)
        db.commit()
        raise

    request = get_accessible_classification(db, request.id, principal)
    return to_classification_response(request)


@router.get("", response_model=list[ClassificationResponse])
def get_classifications(
    userId: int | None = None,
    from_: date | None = Query(default=None, alias="from"),
    to: date | None = None,
    principal=Depends(get_current_principal),
    db: Session = Depends(get_database),
) -> list[ClassificationResponse]:
    stmt = (
        select(ClassificationRequest)
        .options(
            joinedload(ClassificationRequest.user).joinedload(User.role),
            joinedload(ClassificationRequest.model),
            joinedload(ClassificationRequest.image),
        )
        .order_by(ClassificationRequest.created_at.desc())
    )

    effective_user_id = userId if is_admin(principal) else principal.id
    if effective_user_id is not None:
        stmt = stmt.where(ClassificationRequest.user_id == effective_user_id)
    if from_:
        from_date = datetime.combine(from_, time.min, tzinfo=timezone.utc)
        stmt = stmt.where(ClassificationRequest.created_at >= from_date)
    if to:
        to_date = datetime.combine(to + timedelta(days=1), time.min, tzinfo=timezone.utc)
        stmt = stmt.where(ClassificationRequest.created_at < to_date)

    requests = db.scalars(stmt).all()
    return [to_classification_response(item) for item in requests]


@router.get("/{id}", response_model=ClassificationResponse)
def get_classification(
    id: int,
    principal=Depends(get_current_principal),
    db: Session = Depends(get_database),
) -> ClassificationResponse:
    request = get_accessible_classification(db, id, principal)
    return to_classification_response(request)
