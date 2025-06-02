from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException
from app.models.user import User, RoleEnum
from app.schemas.api import ApiResponse
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.core.security import hash_password

def create_user(db: Session, user_in: UserCreate) -> ApiResponse:
    exists = db.query(User).filter(User.email == user_in.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    if user_in.role not in [e.value for e in RoleEnum]:
        raise HTTPException(status_code=400, detail="Rol de usuario no válido")

    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        password_hash=hash_password(user_in.password),
        role=user_in.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return ApiResponse(
        status="success",
        message="Usuario creado exitosamente",
        data=UserOut.from_orm(user)
    )

def get_users(db: Session, skip: int = 0, limit: int = 100, search: str = "") -> ApiResponse:
    query = db.query(User)
     
    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            or_(
                User.email.ilike(search_term),
                User.full_name.ilike(search_term)
            )
        )
    
    # Obtener el total ANTES de aplicar paginación
    total = query.count()
    
    # Aplicar paginación DESPUÉS de obtener el conteo
    users = query.offset(skip).limit(limit).all()
    user_list = [UserOut.from_orm(user) for user in users]
         
    return ApiResponse(
        status="success",
        message="Lista de usuarios obtenida",
        data={
            "users": user_list,
            "total": total
        }   
    )

def update_user(db: Session, user_id: str, user_in: UserUpdate) -> ApiResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if user_in.full_name:
        user.full_name = user_in.full_name
    if user_in.password:
        user.password_hash = hash_password(user_in.password)
    db.commit()
    db.refresh(user)
    return ApiResponse(
        status="success",
        message="Usuario actualizado exitosamente",
        data=UserOut.from_orm(user)
    )

def deactivate_user(db: Session, user_id: str) -> ApiResponse:
    user = db.query(User).filter(User.id == user_id).first()
    user.is_active = False
    db.commit()
    db.refresh(user)
    return ApiResponse(
        status="success",
        message="Usuario desactivado exitosamente",
        data=UserOut.from_orm(user)
    )
