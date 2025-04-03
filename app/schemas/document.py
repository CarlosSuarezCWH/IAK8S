from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List
from enum import Enum
import re

class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"

class DocumentBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    tags: Optional[List[str]] = Field(None, max_items=10)

class DocumentCreate(DocumentBase):
    @field_validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[\w\s\-\.]+$', v):
            raise ValueError('Name contains invalid characters')
        return v.strip()

class DocumentUpdate(DocumentBase):
    name: Optional[str] = Field(None, min_length=3, max_length=255)

class DocumentInDB(DocumentBase):
    id: int
    user_id: int
    file_type: str
    file_size: int
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentShare(BaseModel):
    email: str
    permission_level: str = "read"
    expires_at: Optional[datetime] = None
    can_download: bool = True
    message: Optional[str] = Field(None, max_length=500)

    @field_validator('permission_level')
    def validate_permission(cls, v):
        if v not in ["read", "write", "comment", "share"]:
            raise ValueError('Invalid permission level')
        return v