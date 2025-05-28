from fastapi import APIRouter, Depends
from app.api.v1 import auth, user
from app.core.security import get_current_user

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(user.router, prefix="/users", tags=["users"], dependencies=[Depends(get_current_user)])