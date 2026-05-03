from datetime import datetime
from pydantic import BaseModel, ConfigDict

class UserBase(BaseModel):
    username: str
    privilege_level: int = 1

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    privilege_level: int

class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str

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

class QuotaUpdate(BaseModel):
    max_tokens: int

class AuditLogResponse(BaseModel):
    id: int
    endpoint: str
    tokens_estimated: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class SystemStats(BaseModel):
    total_requests: int
    total_tokens_used: int
    unique_active_users: int

class QuotaForecast(BaseModel):
    average_daily_tokens: float
    days_until_exhaustion: float | None
    is_critical: bool
