from pydantic import BaseModel, EmailStr

class LoginReq(BaseModel):
    username: str
    password: str

class RegisterReq(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: str | None = None
    address: str
    latitude: float
    longitude: float

class Token(BaseModel):
    access_token: str
    refresh_token: str

class TokenPayload(BaseModel):
    sub: str  # normalmente el user_id o email
    exp: int

class RefreshTokenRequest(BaseModel):
    refresh_token: str