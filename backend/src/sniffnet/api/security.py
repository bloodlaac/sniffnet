from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from sniffnet.api.config import JWT_ALGORITHM, JWT_EXPIRATION_HOURS, JWT_SECRET
from sniffnet.api.deps import get_database
from sniffnet.api.errors import ApiException, NotFoundException
from sniffnet.database.db_models import User


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class UserPrincipal:
    id: int
    username: str
    role_code: str


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_context.verify(plain_password, hashed_password)


def create_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.username,
        "userId": user.id,
        "role": user.role.code,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=JWT_EXPIRATION_HOURS)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_database),
) -> UserPrincipal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise ApiException(401, "Not authenticated")

    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise ApiException(401, "Not authenticated") from exc

    user_id = payload.get("userId")
    if user_id is None:
        raise ApiException(401, "Not authenticated")

    user = db.get(User, int(user_id))
    if user is None:
        raise NotFoundException("User not found")

    return UserPrincipal(id=user.id, username=user.username, role_code=user.role.code)


def require_admin(principal: UserPrincipal = Depends(get_current_principal)) -> UserPrincipal:
    if principal.role_code != "ROLE_ADMIN":
        raise ApiException(403, "Access denied")
    return principal
