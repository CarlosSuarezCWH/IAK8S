from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean  # Añade Boolean aquí
from sqlalchemy.sql import func
from app.database.mysql import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255))
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer)
    processed = Column(Boolean, default=False)
    tags = Column(String(512))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())