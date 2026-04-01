from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from sniffnet.api.deps import get_database
from sniffnet.api.errors import ApiException, ConflictException, NotFoundException
from sniffnet.api.helpers import get_role_entity, get_user_entity
from sniffnet.api.mappers import to_current_user_response
from sniffnet.api.security import create_access_token, get_current_principal, hash_password, verify_password
from sniffnet.database.db_models import User
from sniffnet.schemas.contracts import AuthResponse, CurrentUserResponse, LoginRequest, RegisterRequest


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_database),
) -> AuthResponse:
    username_exists = db.scalar(
        select(User.id).where(func.lower(User.username) == request.username.lower())
    )
    if username_exists:
        raise ConflictException("Username already exists")

    email_exists = db.scalar(select(User.id).where(func.lower(User.email) == request.email.lower()))
    if email_exists:
        raise ConflictException("Email already exists")

    role = get_role_entity(db, "ROLE_USER")
    user = User(
        username=request.username,
        email=request.email,
        password=hash_password(request.password),
        role_id=role.id,
    )
    db.add(user)
    db.commit()
    user = db.scalar(select(User).options(joinedload(User.role)).where(User.id == user.id))
    assert user is not None
    return AuthResponse(
        token=create_access_token(user),
        userId=user.id,
        username=user.username,
        email=user.email,
        role=user.role.code,
    )


@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_database)) -> AuthResponse:
    user = db.scalar(
        select(User).options(joinedload(User.role)).where(func.lower(User.username) == request.username.lower())
    )
    if user is None or not verify_password(request.password, user.password):
        raise ApiException(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")

    return AuthResponse(
        token=create_access_token(user),
        userId=user.id,
        username=user.username,
        email=user.email,
        role=user.role.code,
    )


@router.get("/me", response_model=CurrentUserResponse)
def me(principal=Depends(get_current_principal), db: Session = Depends(get_database)) -> CurrentUserResponse:
    user = get_user_entity(db, principal)
    user = db.scalar(select(User).options(joinedload(User.role)).where(User.id == user.id))
    if user is None:
        raise NotFoundException("User not found")
    return to_current_user_response(user)
