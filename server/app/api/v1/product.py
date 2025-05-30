from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.api import ApiResponse
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.product_service import (
    create_product, get_products, update_product, deactivate_product
)

router = APIRouter()

@router.post("/", response_model=ApiResponse)
def register_product(product_in: ProductCreate, db: Session = Depends(get_db)):
    return create_product(db, product_in)

@router.get("/", response_model=ApiResponse)
def list_products(
    page: int = 1,
    limit: int = 10,
    search: str = "",
    db: Session = Depends(get_db)
):
    skip = (page - 1) * limit
    if skip < 0: raise HTTPException(status_code=400, detail="Page number must be greater than 0")
    return get_products(db, skip=skip, limit=limit, search=search)

@router.put("/{product_id}", response_model=ApiResponse)
def update_product_info(product_id: str, product_in: ProductUpdate, db: Session = Depends(get_db)):
    return update_product(db, product_id, product_in)

@router.patch("/{product_id}/deactivate", response_model=ApiResponse)
def deactivate(product_id: str, db: Session = Depends(get_db)):
    return deactivate_product(db, product_id)