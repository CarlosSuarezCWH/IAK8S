from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from typing import Optional, List

from app.database.mysql import Base
from app.models.user import User

class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Metadata del documento
    name = Column(String(255), nullable=False)
    description = Column(Text)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    checksum = Column(String(64))  # SHA-256 del archivo
    
    # Procesamiento
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED)
    processed_at = Column(DateTime)
    processing_errors = Column(Text)
    
    # Organización
    tags = Column(JSONB)  # Almacena tags como array JSON
    metadata = Column(JSONB)  # Metadata adicional personalizable
    
    # Relaciones
    owner = relationship("User", back_populates="documents")
    shared_with = relationship(
        "SharedDocument", 
        back_populates="document",
        cascade="all, delete-orphan"
    )
    
    # Auditoría
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    @validates('file_type')
    def validate_file_type(self, key, file_type):
        allowed_types = ['pdf', 'docx', 'csv', 'txt', 'pptx', 'xlsx']
        if file_type.split('/')[-1] not in allowed_types:
            raise ValueError(f"Invalid file type: {file_type}")
        return file_type

    def get_metadata(self) -> dict:
        """Obtiene metadata combinada"""
        base_meta = {
            "id": self.id,
            "name": self.name,
            "type": self.file_type,
            "size": self.file_size,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        
        if self.metadata:
            base_meta.update(self.metadata)
            
        return base_meta

    def __repr__(self):
        return f"<Document(id={self.id}, name={self.name}, status={self.status})>"