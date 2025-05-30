from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    price: float
    stock_quantity: int | None = 0

class ProductOut(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    price: float
    stock_quantity: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    stock_quantity: int | None = None