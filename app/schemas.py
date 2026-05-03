from datetime import datetime
from pydantic import BaseModel, ConfigDict

class UserBase(BaseModel):
    username: str
    privilege_level: int = 1

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class QuotaResponse(BaseModel):
    max_tokens: int
    used_tokens: int
    model_config = ConfigDict(from_attributes=True)

class AuditLogResponse(BaseModel):
    id: int
    endpoint: str
    tokens_estimated: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)
