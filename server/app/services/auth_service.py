from fastapi import HTTPException
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.models import User
from app.schemas.api import ApiResponse
from app.schemas.auth import Token
from app.schemas.user import UserOut
from app.core.security import (
    verify_password, create_access_token, create_refresh_token, hash_password
)
from app.core.config import settings

def authenticate_user(db: Session, email: str, password: str) -> ApiResponse:
    user = db.query(User).filter(User.email == email, User.is_active == True).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token({"sub": str(user.id), "role": user.role})
    token: dict = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user_data": UserOut.from_orm(user)
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

def request_password_reset(db: Session, email: str) -> ApiResponse:
    """
    Solicitar restablecimiento de contraseña
    """
    user = db.query(User).filter(User.email == email, User.is_active == True).first()
    
    # Por seguridad, siempre devolvemos la misma respuesta aunque el usuario no exista
    if not user:
        return ApiResponse(
            status="success", 
            message="Si el email existe, recibirás instrucciones para restablecer tu contraseña",
            data=None
        )
    
    # Crear token de restablecimiento (válido por 30 minutos)
    reset_token_data = {
        "sub": str(user.id),
        "type": "password_reset",
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    reset_token = jwt.encode(reset_token_data, settings.JWT_SECRET_KEY, algorithm="HS256")
    
    # Aquí normalmente enviarías un email con el token
    # Por simplicidad, lo devolvemos en la respuesta (en producción NO hacer esto)
    
    return ApiResponse(
        status="success",
        message="Si el email existe, recibirás instrucciones para restablecer tu contraseña",
        data={"reset_token": reset_token}
    )

def reset_password(db: Session, token: str, new_password: str) -> ApiResponse:
    """
    Restablecer contraseña usando el token
    """
    try:
        # Decodificar y validar el token
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        token_type = payload.get("type")
        
        if token_type != "password_reset":
            raise JWTError("Token type invalid")
            
    except JWTError:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")
    
    # Buscar el usuario
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Validar que la nueva contraseña tenga al menos 6 caracteres
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")
    
    # Actualizar la contraseña
    user.password_hash = hash_password(new_password)
    db.commit()
    
    return ApiResponse(
        status="success",
        message="Contraseña restablecida exitosamente",
        data=None
    )
