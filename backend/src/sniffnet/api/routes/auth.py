from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sniffnet.api.deps import get_database
from sniffnet.database.db_models import User
from sniffnet.schemas.auth import LoginRequest, LoginResponse

router = APIRouter()

@router.post("/auth/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_database)):
    user = (
        db.query(User)
        .filter(User.username == data.username)
        .first()
    )
    if user is None or user.password != data.password:
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    
    return LoginResponse(user_id=user.user_id, username=user.username)
