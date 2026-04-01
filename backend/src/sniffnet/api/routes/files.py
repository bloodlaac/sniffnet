from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from sniffnet.api.deps import get_database
from sniffnet.api.helpers import get_accessible_image, get_user_entity, store_uploaded_image
from sniffnet.api.mappers import to_uploaded_image_response
from sniffnet.api.security import get_current_principal
from sniffnet.schemas.contracts import UploadedImageResponse


router = APIRouter(prefix="/files/images", tags=["files"])


@router.post("", response_model=UploadedImageResponse)
async def upload_image(
    file: UploadFile = File(...),
    principal=Depends(get_current_principal),
    db: Session = Depends(get_database),
) -> UploadedImageResponse:
    user = get_user_entity(db, principal)
    image = await store_uploaded_image(db, file, user)
    image = get_accessible_image(db, image.id, principal)
    return to_uploaded_image_response(image)


@router.get("/{id}", response_model=UploadedImageResponse)
def get_image_metadata(
    id: int,
    principal=Depends(get_current_principal),
    db: Session = Depends(get_database),
) -> UploadedImageResponse:
    image = get_accessible_image(db, id, principal)
    return to_uploaded_image_response(image)


@router.get("/{id}/content")
def get_image_content(
    id: int,
    principal=Depends(get_current_principal),
    db: Session = Depends(get_database),
):
    image = get_accessible_image(db, id, principal)
    return FileResponse(image.storage_path, media_type=image.content_type, filename=image.original_filename)
