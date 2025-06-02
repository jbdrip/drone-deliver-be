from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class TransactionCreate(BaseModel):
    customer_id: UUID
    credited_by_user_id: UUID
    amount: float
    transaction_type: str  # Should match TransactionTypeEnum in the model
    description: str | None = None
    order_id: UUID | None = None

class TransactionOut(BaseModel):
    id: UUID
    customer_id: UUID
    credited_by_user_id: UUID
    amount: float
    transaction_type: str  # Should match TransactionTypeEnum in the model
    description: str | None = None
    order_id: UUID | None = None
    balance_before: float
    balance_after: float
    created_at: datetime

    class Config:
        from_attributes = True