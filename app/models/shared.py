from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum

from app.database.mysql import Base
from app.models.user import User
from app.models.document import Document

class SharePermission(str, PyEnum):
    READ = "read"
    WRITE = "write"
    COMMENT = "comment"
    SHARE = "share"

class SharedDocument(Base):
    __tablename__ = "shared_documents"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    shared_with_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Permisos
    permission_level = Column(Enum(SharePermission), default=SharePermission.READ)
    can_download = Column(Boolean, default=True)
    can_print = Column(Boolean, default=False)
    
    # Metadata de compartición
    shared_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime)
    reason = Column(String(255))  # Propósito del compartimiento
    
    # Notificaciones
    notified_at = Column(DateTime)
    notification_message = Column(String(512))
    
    # Relaciones
    document = relationship("Document", back_populates="shared_with")
    owner = relationship("User", foreign_keys=[owner_id], back_populates="shared_by_me")
    shared_with_user = relationship("User", foreign_keys=[shared_with_id], back_populates="shared_with_me")
    
    # Auditoría
    revoked_at = Column(DateTime)
    revoked_by = Column(Integer, ForeignKey("users.id"))
    
    def is_active(self) -> bool:
        """Verifica si el compartimiento está activo"""
        if self.revoked_at:
            return False
        if self.expires_at and self.expires_at < datetime.now():
            return False
        return True

    def has_permission(self, permission: SharePermission) -> bool:
        """Verifica permisos"""
        permission_hierarchy = {
            SharePermission.READ: [SharePermission.READ],
            SharePermission.COMMENT: [SharePermission.READ, SharePermission.COMMENT],
            SharePermission.WRITE: [
                SharePermission.READ, 
                SharePermission.COMMENT, 
                SharePermission.WRITE
            ],
            SharePermission.SHARE: [
                SharePermission.READ,
                SharePermission.COMMENT,
                SharePermission.WRITE,
                SharePermission.SHARE
            ]
        }
        return permission in permission_hierarchy.get(self.permission_level, [])

    def __repr__(self):
        return f"<SharedDocument(document={self.document_id}, user={self.shared_with_id}, permission={self.permission_level})>"