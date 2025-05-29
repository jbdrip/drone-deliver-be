from pydantic import BaseModel
from typing import Any

class ApiResponse(BaseModel):
    status: str
    message: str
    data: Any = None