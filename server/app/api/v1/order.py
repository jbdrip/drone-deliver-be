from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.api import ApiResponse
from app.models.user import User
from app.core.security import get_current_user
from app.schemas.order import OrderCreate, OrderUpdate
from app.services.order_service import (
    create_order, get_orders, update_order, confirm_order
)

router = APIRouter()

@router.post("/", response_model=ApiResponse)
def register_order(
        order_in: OrderCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
    return create_order(db, current_user, order_in)

@router.get("/", response_model=ApiResponse)
def list_orders(
    page: int = 1,
    limit: int = 10,
    search: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    skip = (page - 1) * limit
    if skip < 0: raise HTTPException(status_code=400, detail="Page number must be greater than 0")
    return get_orders(db, current_user, skip=skip, limit=limit, search=search)

@router.put("/{order_id}/edit", response_model=ApiResponse)
def update_order_info(
        order_id: str,
        order_in: OrderUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
    return update_order(db, current_user, order_id, order_in)

# Confirm endpoint
@router.patch("/{order_id}/confirm", response_model=ApiResponse)
def confirm_order_info(
        order_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
    return confirm_order(db, current_user, order_id)
