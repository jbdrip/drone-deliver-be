from pydantic import BaseModel

class LoginReq(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str

class TokenPayload(BaseModel):
    sub: str  # normalmente el user_id o email
    exp: int

class RefreshTokenRequest(BaseModel):
    refresh_token: str