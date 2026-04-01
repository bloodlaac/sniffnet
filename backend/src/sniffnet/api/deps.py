from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from sniffnet.database.db import SessionLocal


def get_database() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
