from __future__ import annotations

from datetime import datetime, timezone

import pytest
from jose import jwt

from sniffnet.api.config import JWT_ALGORITHM, JWT_EXPIRATION_HOURS, JWT_SECRET
from sniffnet.api.errors import ApiException
from sniffnet.api.security import UserPrincipal, create_access_token, hash_password, require_admin, verify_password
from sniffnet.database.db_models import Role, User


def test_hash_password_and_verify_password_roundtrip() -> None:
    hashed = hash_password("secret123")

    assert hashed != "secret123"
    assert verify_password("secret123", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_access_token_embeds_expected_claims() -> None:
    user = User(id=7, username="demo", email="demo@sniffnet.local", password="hash", role=Role(code="ROLE_USER", name="User"))

    token = create_access_token(user)
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

    assert payload["sub"] == "demo"
    assert payload["userId"] == 7
    assert payload["role"] == "ROLE_USER"
    assert payload["exp"] - payload["iat"] == JWT_EXPIRATION_HOURS * 3600
    assert payload["iat"] <= int(datetime.now(timezone.utc).timestamp())


def test_require_admin_allows_admin_and_rejects_regular_user() -> None:
    admin = UserPrincipal(id=1, username="admin", role_code="ROLE_ADMIN")
    demo = UserPrincipal(id=2, username="demo", role_code="ROLE_USER")

    assert require_admin(admin) is admin

    with pytest.raises(ApiException, match="Access denied"):
        require_admin(demo)
