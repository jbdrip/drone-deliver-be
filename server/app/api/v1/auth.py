from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import auth_service
from app.schemas.auth import LoginReq, Token
from app.schemas.api import ApiResponse

router = APIRouter()

@router.post("/login", response_model=ApiResponse)
def login(req: LoginReq, db: Session = Depends(get_db)):
    return auth_service.authenticate_user(db, req.username, req.password)

@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    return auth_service.refresh_access_token(db, refresh_token)
