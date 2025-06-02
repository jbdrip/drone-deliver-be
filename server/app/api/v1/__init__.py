from fastapi import APIRouter, Depends
from app.api.v1 import auth, user, customer, distribution_center, product, credit_transaction
from app.core.security import get_current_user

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(user.router, prefix="/users", tags=["users"], dependencies=[Depends(get_current_user)])
api_router.include_router(customer.router, prefix="/customers", tags=["customers"], dependencies=[Depends(get_current_user)])
api_router.include_router(distribution_center.router, prefix="/distribution-centers", tags=["distribution-centers"], dependencies=[Depends(get_current_user)])
api_router.include_router(product.router, prefix="/products", tags=["products"], dependencies=[Depends(get_current_user)])
api_router.include_router(credit_transaction.router, prefix="/credit-transactions", tags=["credit-transactions"], dependencies=[Depends(get_current_user)])