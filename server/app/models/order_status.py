# app/models/order_status.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base

class OrderStatus(Base):
    __tablename__ = "order_statuses"

    id = Column(Integer, primary_key=True)
    status_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
