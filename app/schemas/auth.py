from pydantic import BaseModel, EmailStr, field_validator, constr
from datetime import datetime
from enum import Enum
from typing import Optional

class UserRole(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"

class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None

class UserCreate(UserBase):
    password: constr(min_length=8, max_length=64)
    password_confirm: str
    role: UserRole = UserRole.VIEWER

    @field_validator('password_confirm')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('passwords do not match')
        return v

    @field_validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('password must contain at least one digit')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?`~' for c in v):
            raise ValueError('password must contain at least one special character')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserInDB(UserBase):
    id: int
    is_active: bool
    role: UserRole
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str | None = None

class TokenData(BaseModel):
    email: str | None = None
    scopes: list[str] = []