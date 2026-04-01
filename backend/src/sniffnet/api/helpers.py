from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, joinedload

from sniffnet.api.config import IMAGE_STORAGE_DIR, MAX_IMAGE_SIZE_BYTES
from sniffnet.api.errors import BadRequestException, NotFoundException
from sniffnet.api.security import UserPrincipal
from sniffnet.database.db_models import (
    ClassificationRequest,
    Experiment,
    Metric,
    Model,
    Role,
    UploadedImage,
    User,
)


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def is_admin(principal: UserPrincipal) -> bool:
    return principal.role_code == "ROLE_ADMIN"


def get_user_entity(db: Session, principal: UserPrincipal) -> User:
    user = db.get(User, principal.id)
    if user is None:
        raise NotFoundException("User not found")
    return user


def get_role_entity(db: Session, role_code: str) -> Role:
    role = db.scalar(select(Role).where(Role.code == role_code))
    if role is None:
        raise NotFoundException("Role not found")
    return role


def get_metric(db: Session, dataset_id: int, config_id: int) -> Metric | None:
    return db.scalar(
        select(Metric)
        .where(Metric.dataset_id == dataset_id, Metric.config_id == config_id)
        .order_by(Metric.id.desc())
    )


def get_experiment_with_relations(db: Session, experiment_id: int) -> Experiment:
    experiment = db.scalar(
        select(Experiment)
        .options(
            joinedload(Experiment.dataset),
            joinedload(Experiment.config),
            joinedload(Experiment.user).joinedload(User.role),
            joinedload(Experiment.model).joinedload(Model.dataset),
            joinedload(Experiment.model).joinedload(Model.config),
        )
        .where(Experiment.id == experiment_id)
    )
    if experiment is None:
        raise NotFoundException("Experiment not found")
    return experiment


def ensure_experiment_access(experiment: Experiment, principal: UserPrincipal) -> Experiment:
    if not is_admin(principal) and experiment.user_id != principal.id:
        raise NotFoundException("Experiment not found")
    return experiment


def get_accessible_model(db: Session, model_id: int, principal: UserPrincipal) -> Model:
    model = db.scalar(
        select(Model)
        .options(
            joinedload(Model.dataset),
            joinedload(Model.config),
            joinedload(Model.experiment).joinedload(Experiment.user).joinedload(User.role),
        )
        .where(Model.id == model_id)
    )
    if model is None:
        raise NotFoundException("Model not found")
    if not is_admin(principal) and model.experiment.user_id != principal.id:
        raise NotFoundException("Model not found")
    return model


def get_accessible_image(db: Session, image_id: int, principal: UserPrincipal) -> UploadedImage:
    image = db.scalar(
        select(UploadedImage)
        .options(joinedload(UploadedImage.user).joinedload(User.role))
        .where(UploadedImage.id == image_id)
    )
    if image is None:
        raise NotFoundException("Image not found")
    if not is_admin(principal) and image.user_id != principal.id:
        raise NotFoundException("Image not found")
    return image


def get_accessible_classification(db: Session, classification_id: int, principal: UserPrincipal) -> ClassificationRequest:
    request = db.scalar(
        select(ClassificationRequest)
        .options(
            joinedload(ClassificationRequest.user).joinedload(User.role),
            joinedload(ClassificationRequest.model),
            joinedload(ClassificationRequest.image),
        )
        .where(ClassificationRequest.id == classification_id)
    )
    if request is None:
        raise NotFoundException("Classification request not found")
    if not is_admin(principal) and request.user_id != principal.id:
        raise NotFoundException("Classification request not found")
    return request


async def store_uploaded_image(db: Session, file: UploadFile, user: User) -> UploadedImage:
    validate_upload(file)

    IMAGE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    extension = Path(file.filename or "").suffix.lower()
    stored_filename = f"{uuid4()}{extension}"
    destination = IMAGE_STORAGE_DIR / stored_filename
    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE_BYTES:
        raise BadRequestException("Image file is too large")
    destination.write_bytes(contents)

    image = UploadedImage(
        user_id=user.id,
        original_filename=file.filename or stored_filename,
        stored_filename=stored_filename,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(contents),
        storage_path=str(destination.resolve()),
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


def validate_upload(file: UploadFile) -> None:
    if file is None or not file.filename:
        raise BadRequestException("Image file is required")
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise BadRequestException("Unsupported image content type")
    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise BadRequestException("Unsupported image extension")
    size = getattr(file, "size", None)
    if size is not None and size > MAX_IMAGE_SIZE_BYTES:
        raise BadRequestException("Image file is too large")


def remove_path(path: str | None) -> None:
    if not path:
        return
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def delete_orphan_images(db: Session, image_ids: list[int]) -> None:
    for image_id in image_ids:
        remaining = db.scalar(
            select(func.count(ClassificationRequest.id)).where(ClassificationRequest.image_id == image_id)
        )
        if remaining:
            continue
        image = db.get(UploadedImage, image_id)
        if image is None:
            continue
        remove_path(image.storage_path)
        db.delete(image)


def delete_classifications_for_model(db: Session, model_id: int) -> None:
    image_ids = list(
        db.scalars(select(ClassificationRequest.image_id).where(ClassificationRequest.model_id == model_id)).all()
    )
    db.execute(delete(ClassificationRequest).where(ClassificationRequest.model_id == model_id))
    db.commit()
    delete_orphan_images(db, image_ids)
    db.commit()
