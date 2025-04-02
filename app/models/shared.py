from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime
from sqlalchemy.sql import func
from app.database.mysql import Base

class SharedDocument(Base):
    __tablename__ = "shared_documents"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    shared_with_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    permission_level = Column(Enum('read', 'write'), default='read')
    created_at = Column(DateTime, server_default=func.now())
