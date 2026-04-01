from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from sniffnet.api.deps import get_database
from sniffnet.api.errors import ConflictException, NotFoundException
from sniffnet.api.helpers import get_role_entity
from sniffnet.api.mappers import to_user_response
from sniffnet.api.security import require_admin
from sniffnet.database.db_models import User
from sniffnet.schemas.contracts import UserResponse, UserUpdateRequest


router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponse], dependencies=[Depends(require_admin)])
def get_users(search: str | None = None, db: Session = Depends(get_database)) -> list[UserResponse]:
    stmt = select(User).options(joinedload(User.role))
    if search:
        stmt = stmt.where(User.username.ilike(f"%{search}%"))
    users = db.scalars(stmt.order_by(User.created_at.desc())).all()
    return [to_user_response(user) for user in users]


@router.get("/{id}", response_model=UserResponse, dependencies=[Depends(require_admin)])
def get_user(id: int, db: Session = Depends(get_database)) -> UserResponse:
    user = db.scalar(select(User).options(joinedload(User.role)).where(User.id == id))
    if user is None:
        raise NotFoundException("User not found")
    return to_user_response(user)


@router.put("/{id}", response_model=UserResponse, dependencies=[Depends(require_admin)])
def update_user(id: int, request: UserUpdateRequest, db: Session = Depends(get_database)) -> UserResponse:
    user = db.scalar(select(User).options(joinedload(User.role)).where(User.id == id))
    if user is None:
        raise NotFoundException("User not found")

    username_exists = db.scalar(
        select(User.id)
        .where(func.lower(User.username) == request.username.lower(), User.id != id)
    )
    if username_exists:
        raise ConflictException("Username already exists")

    email_exists = db.scalar(
        select(User.id)
        .where(func.lower(User.email) == request.email.lower(), User.id != id)
    )
    if email_exists:
        raise ConflictException("Email already exists")

    role = get_role_entity(db, request.role)
    user.username = request.username
    user.email = request.email
    user.role_id = role.id
    db.commit()
    user = db.scalar(select(User).options(joinedload(User.role)).where(User.id == id))
    assert user is not None
    return to_user_response(user)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_user(id: int, db: Session = Depends(get_database)) -> Response:
    user = db.get(User, id)
    if user is None:
        raise NotFoundException("User not found")
    try:
        db.delete(user)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictException("Operation violates related data constraints") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
