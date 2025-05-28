# app/models/order.py
import uuid
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    status_id = Column(Integer, ForeignKey("order_statuses.id"), nullable=False)
    assigned_distribution_center_id = Column(UUID(as_uuid=True), ForeignKey("distribution_centers.id"))
    total_distance = Column(Integer)
    service_cost = Column(DECIMAL(10, 2))
    product_cost = Column(DECIMAL(10, 2))
    total_cost = Column(DECIMAL(10, 2))
    estimated_delivery_time = Column(Integer)
    cancellation_reason = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
