from fastapi import HTTPException
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import timedelta
from app.models import User
from app.schemas.api import ApiResponse
from app.schemas.auth import Token
from app.core.security import (
    verify_password, create_access_token, create_refresh_token
)
from app.core.config import settings

def authenticate_user(db: Session, email: str, password: str) -> ApiResponse:
    user = db.query(User).filter(User.email == email, User.is_active == True).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    token: Token = {
        "access_token": access_token,
        "refresh_token": refresh_token
    }
    return ApiResponse(status="success", message="Usuario autenticado", data=token)

def refresh_access_token(db: Session, refresh_token: str) -> Token:
    try:
        payload = jwt.decode(refresh_token, settings.JWT_REFRESH_SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token inválido")

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return Token(access_token=access_token, refresh_token=refresh_token)
