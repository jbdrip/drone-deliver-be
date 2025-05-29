from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.api import ApiResponse
from app.schemas.distribution_center import DistributionCenterCreate, DistributionCenterUpdate
from app.services.distribution_center_service import (
    create_distribution_center, get_distribution_centers, update_distribution_center, deactivate_distribution_center
)

router = APIRouter()

@router.post("/", response_model=ApiResponse)
def register_distribution_center(distribution_center_in: DistributionCenterCreate, db: Session = Depends(get_db)):
    return create_distribution_center(db, distribution_center_in)

@router.get("/", response_model=ApiResponse)
def list_distribution_centers(
    page: int = 1,
    limit: int = 10,
    search: str = "",
    db: Session = Depends(get_db)
):
    skip = (page - 1) * limit
    if skip < 0: raise HTTPException(status_code=400, detail="Page number must be greater than 0")
    return get_distribution_centers(db, skip=skip, limit=limit, search=search)

@router.put("/{distribution_center_id}", response_model=ApiResponse)
def update_distribution_center_info(distribution_center_id: str, distribution_center_in: DistributionCenterUpdate, db: Session = Depends(get_db)):
    return update_distribution_center(db, distribution_center_id, distribution_center_in)

@router.patch("/{distribution_center_id}/deactivate", response_model=ApiResponse)
def deactivate(distribution_center_id: str, db: Session = Depends(get_db)):
    return deactivate_distribution_center(db, distribution_center_id)