from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class OrderCreate(BaseModel):
    product_id: UUID
    quantity: int = 1

class OrderOut(BaseModel):
    id: UUID
    customer_id: UUID
    customer_name: str
    product_id: UUID
    product_name: str
    quantity: int
    status_id: int
    status_name: str
    assigned_distribution_center_id: UUID | None = None
    assigned_distribution_center_name: str | None = None
    total_distance: int | None = None
    service_cost: float | None = None
    product_cost: float | None = None
    total_cost: float | None = None
    estimated_delivery_time: int | None = None
    cancellation_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OrderUpdate(BaseModel):
    product_id: UUID | None = None
    status_id: int | None = None
    cancellation_reason: str | None = None