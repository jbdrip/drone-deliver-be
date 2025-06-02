from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.api import ApiResponse
from app.schemas.credit_transaction import TransactionCreate
from app.services.credit_transaction_service import (
    create_transaction, get_transactions
)

router = APIRouter()

@router.post("/", response_model=ApiResponse)
def register_transaction(transaction_in: TransactionCreate, db: Session = Depends(get_db)):
    return create_transaction(db, transaction_in)

@router.get("/", response_model=ApiResponse)
def list_transactions(
    page: int = 1,
    limit: int = 10,
    search: str = "",
    db: Session = Depends(get_db)
):
    skip = (page - 1) * limit
    if skip < 0: raise HTTPException(status_code=400, detail="Page number must be greater than 0")
    return get_transactions(db, skip=skip, limit=limit, search=search)