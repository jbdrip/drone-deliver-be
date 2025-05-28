# app/models/distribution_center.py
import uuid
import enum
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, Enum, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class CenterTypeEnum(str, enum.Enum):
    main_warehouse = "main_warehouse"
    distribution_point = "distribution_point"

class DistributionCenter(Base):
    __tablename__ = "distribution_centers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    address = Column(Text, nullable=False)
    latitude = Column(DECIMAL(10, 8), nullable=False)
    longitude = Column(DECIMAL(11, 8), nullable=False)
    max_drone_range = Column(Integer, nullable=False)
    center_type = Column(Enum(CenterTypeEnum), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

