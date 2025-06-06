from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.api import ApiResponse
from app.models.user import User
from app.core.security import get_current_user
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.services.customer_service import (
    create_customer, get_customer_by_email, get_customers, update_customer, deactivate_customer
)

router = APIRouter()

@router.post("/", response_model=ApiResponse)
def register_customer(customer_in: CustomerCreate, db: Session = Depends(get_db)):
    return create_customer(db, customer_in)

@router.get("/get/current", response_model=ApiResponse)
def get_customer_by_email_(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_customer_by_email(db, current_user.email)

@router.get("/get/all", response_model=ApiResponse)
def list_customers(
    page: int = 1,
    limit: int = 10,
    search: str = "",
    db: Session = Depends(get_db)
):
    skip = (page - 1) * limit
    if skip < 0: raise HTTPException(status_code=400, detail="Page number must be greater than 0")
    return get_customers(db, skip=skip, limit=limit, search=search)

@router.put("/{customer_id}", response_model=ApiResponse)
def update_customer_info(customer_id: str, customer_in: CustomerUpdate, db: Session = Depends(get_db)):
    return update_customer(db, customer_id, customer_in)

@router.patch("/{customer_id}/deactivate", response_model=ApiResponse)
def deactivate(customer_id: str, db: Session = Depends(get_db)):
    return deactivate_customer(db, customer_id)