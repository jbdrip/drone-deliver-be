from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password

def create_user(db: Session, user_in: UserCreate):
    exists = db.query(User).filter(User.email == user_in.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        password_hash=hash_password(user_in.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_id(db: Session, user_id: str):
    return db.query(User).filter(User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

def update_user(db: Session, user_id: str, user_in: UserUpdate):
    user = db.query(User).filter(User.id == user_id).first()
    if user_in.full_name:
        user.full_name = user_in.full_name
    if user_in.password:
        user.password_hash = hash_password(user_in.password)
    db.commit()
    db.refresh(user)
    return user

def deactivate_user(db: Session, user_id: str):
    user = db.query(User).filter(User.id == user_id).first()
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user
