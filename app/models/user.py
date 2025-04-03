from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Enum
from sqlalchemy.sql import func, expression
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.dialects.postgresql import ARRAY
from enum import Enum as PyEnum
from typing import List, Dict, Any

from app.database.mysql import Base

class UserRole(str, PyEnum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"
    GUEST = "guest"

class UserPermission(str, PyEnum):
    DOCUMENTS_READ = "docs:read"
    DOCUMENTS_WRITE = "docs:write"
    DOCUMENTS_SHARE = "docs:share"
    USERS_MANAGE = "users:manage"
    SYSTEM_ADMIN = "system:admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, server_default=expression.true(), default=True)
    is_verified = Column(Boolean, server_default=expression.false(), default=False)
    
    # Roles y permisos
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    permissions = Column(MutableList.as_mutable(ARRAY(String)), default=[], nullable=False)
    
    # Seguridad
    last_login = Column(DateTime)
    password_changed_at = Column(DateTime)
    password_history = Column(JSON, default=[])  # Almacena hash anteriores
    
    # Auditoría
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def has_permission(self, permission: UserPermission) -> bool:
        """Verifica si el usuario tiene un permiso específico"""
        if UserPermission.SYSTEM_ADMIN in self.permissions:
            return True
        
        # Permisos basados en rol
        role_permissions = {
            UserRole.ADMIN: [
                UserPermission.DOCUMENTS_READ,
                UserPermission.DOCUMENTS_WRITE,
                UserPermission.DOCUMENTS_SHARE,
                UserPermission.USERS_MANAGE
            ],
            UserRole.EDITOR: [
                UserPermission.DOCUMENTS_READ,
                UserPermission.DOCUMENTS_WRITE
            ],
            UserRole.VIEWER: [
                UserPermission.DOCUMENTS_READ
            ]
        }
        
        return (permission in self.permissions or 
                permission in role_permissions.get(self.role, []))

    def set_password(self, password: str):
        """Actualiza contraseña con historial"""
        from app.utils.security import SecurityUtils
        self.hashed_password = SecurityUtils.get_password_hash(password)
        self.password_changed_at = func.now()
        
        # Mantener historial de las últimas 5 contraseñas
        history_entry = {
            "hash": self.hashed_password,
            "changed_at": str(self.password_changed_at)
        }
        self.password_history = [history_entry] + self.password_history[:4]

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"