# app/models/credit_transaction.py
import uuid
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, DECIMAL, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class TransactionTypeEnum(str, enum.Enum):
    credit = "credit"
    debit = "debit"

class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    credited_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    transaction_type = Column(Enum(TransactionTypeEnum), nullable=False)
    description = Column(String(255))
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    balance_before = Column(DECIMAL(10, 2), nullable=False)
    balance_after = Column(DECIMAL(10, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
