from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import auth_service, user_service, customer_service
from app.schemas.auth import LoginReq, RegisterReq, Token
from app.schemas import ApiResponse, CustomerCreate, UserCreate

router = APIRouter()

@router.post("/login", response_model=ApiResponse)
def login(req: LoginReq, db: Session = Depends(get_db)):
    return auth_service.authenticate_user(db, req.username, req.password)

@router.post("/register", response_model=ApiResponse)
def register(user_in: RegisterReq, db: Session = Depends(get_db)):
    
    # Create user in the database
    user_result = user_service.create_user(
        db,
        UserCreate(
            email=user_in.email,
            password=user_in.password,
            full_name=user_in.full_name,
            role="customer"
        )
    )
    # If user creation fails, return the error
    if not(user_result.status != None and user_result.status == 'success'):
        return user_result
    
    # If user is created successfully, create a customer
    customer_result = customer_service.create_customer(
        db,
        CustomerCreate(
            email=user_in.email,
            full_name=user_in.full_name,
            phone=user_in.phone,
            address=user_in.address,
            latitude=user_in.latitude,
            longitude=user_in.longitude
        )
    )
    # If customer creation fails, return the error
    if not(customer_result.status != None and customer_result.status == 'success'):
        return customer_result
    
    # If both user and customer are created successfully, return success response
    return ApiResponse(
        status="success",
        message="Usuario y cliente creados exitosamente",
        data={
            "user": user_result.data,
            "customer": customer_result.data
        }
    )

@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    return auth_service.refresh_access_token(db, refresh_token)
