from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

class DistributionCenterCreate(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    max_drone_range: int
    center_type: str  # Should match CenterTypeEnum in the model

class DistributionCenterOut(BaseModel):
    id: UUID
    name: str
    address: str
    latitude: float
    longitude: float
    max_drone_range: int
    center_type: str  # Should match CenterTypeEnum in the model
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class DistributionCenterUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    max_drone_range: int | None = None
    center_type: str | None = None  # Should match CenterTypeEnum in the model