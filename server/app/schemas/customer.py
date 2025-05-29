from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

class CustomerCreate(BaseModel):
    email: EmailStr
    full_name: str
    phone: str | None = None
    address: str
    latitude: float
    longitude: float

class CustomerOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    phone: str | None = None
    address: str
    latitude: float
    longitude: float
    credit_balance: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class CustomerUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    credit_balance: float | None = None