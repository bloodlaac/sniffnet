from sniffnet.schemas.users import UserRequest
from typing import Annotated
from sqlalchemy.orm import Session
from sniffnet.database.db_models import User
from sniffnet.api.deps import get_database

from fastapi import APIRouter, HTTPException, Depends, Body


router = APIRouter(tags=["users"])

@router.get("/users")
def get_users(db: Annotated[Session, Depends(get_database)]):
    return db.query(User).all()


@router.get("/users/{id}")
def get_user(id, db: Annotated[Session, Depends(get_database)]):
    user =  db.query(User).filter(User.user_id == id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return user


@router.delete("/users/{id}")
def delete_user(id, db: Annotated[Session, Depends(get_database)]):
    user = db.query(User).filter(User.user_id == id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    db.delete(user)
    db.commit()

    return user


@router.post("/users")
def post_user(user: UserRequest, db: Annotated[Session, Depends(get_database)]):
    db_user = User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.put("/users")
def update_user(input_user: UserRequest, db: Annotated[Session, Depends(get_database)]):
    db_user = db.query(User).filter(User.user_id == input_user["user_id"]).first()

    if db_user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    db_user.username = input_user["username"]
    db_user.email = input_user["email"]

    db.commit()
    db.refresh(db_user)

    return db_user