from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.services.user_service import (
    create_user, get_users, get_user_by_id, update_user, deactivate_user
)

router = APIRouter()

@router.post("/", response_model=UserOut)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user_in)

@router.get("/", response_model=list[UserOut])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_users(db, skip=skip, limit=limit)

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: str, db: Session = Depends(get_db)):
    return get_user_by_id(db, user_id)

@router.put("/{user_id}", response_model=UserOut)
def update_user_info(user_id: str, user_in: UserUpdate, db: Session = Depends(get_db)):
    return update_user(db, user_id, user_in)

@router.patch("/{user_id}/deactivate", response_model=UserOut)
def deactivate(user_id: str, db: Session = Depends(get_db)):
    return deactivate_user(db, user_id)
