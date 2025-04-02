from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class DocumentBase(BaseModel):
    name: Optional[str]
    tags: Optional[List[str]]

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: int
    user_id: int
    file_path: str
    file_type: str
    file_size: int
    processed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class DocumentShare(BaseModel):
    email: str
    permission_level: str = 'read'

class DocumentQuery(BaseModel):
    question: str
    model: Optional[str] = None
