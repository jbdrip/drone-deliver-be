# app/models/delivery_route.py
import uuid
import enum
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class RouteTypeEnum(str, enum.Enum):
    pickup = "pickup"
    delivery = "delivery"
    transfer = "transfer"

class DeliveryRoute(Base):
    __tablename__ = "delivery_routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    route_type = Column(Enum(RouteTypeEnum), nullable=False)
    origin_center_id = Column(UUID(as_uuid=True), ForeignKey("distribution_centers.id"), nullable=False)
    destination_center_id = Column(UUID(as_uuid=True), ForeignKey("distribution_centers.id"))
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"))
    distance = Column(Integer, nullable=False)
    sequence_order = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
