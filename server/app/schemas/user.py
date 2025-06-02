from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str # Should match RoleEnum in the model

class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: str  # Should match RoleEnum in the model
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: str | None = None
    password: str | None = None
