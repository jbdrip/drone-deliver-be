from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.api import ApiResponse
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.services.user_service import (
    create_user, get_users, get_user_by_id, update_user, deactivate_user
)

router = APIRouter()

@router.post("/", response_model=ApiResponse)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user_in)

@router.get("/", response_model=ApiResponse)
def list_users(
    page: int = 1,
    limit: int = 10,
    search: str = "",
    db: Session = Depends(get_db)
):
    skip = (page - 1) * limit
    if skip < 0: raise HTTPException(status_code=400, detail="Page number must be greater than 0")
    return get_users(db, skip=skip, limit=limit, search=search)

@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: str, db: Session = Depends(get_db)):
    return get_user_by_id(db, user_id)

@router.put("/{user_id}", response_model=ApiResponse)
def update_user_info(user_id: str, user_in: UserUpdate, db: Session = Depends(get_db)):
    return update_user(db, user_id, user_in)

@router.patch("/{user_id}/deactivate", response_model=ApiResponse)
def deactivate(user_id: str, db: Session = Depends(get_db)):
    return deactivate_user(db, user_id)
