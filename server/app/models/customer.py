# app/models/customer.py
import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(300), nullable=False)
    phone = Column(String(20))
    address = Column(Text, nullable=False)
    latitude = Column(DECIMAL(10, 8), nullable=False)
    longitude = Column(DECIMAL(11, 8), nullable=False)
    credit_balance = Column(DECIMAL(10, 2), default=0.00)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
