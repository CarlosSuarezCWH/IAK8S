import logging
from datetime import datetime, timedelta
from typing import Optional, List
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.database import get_db_session

logger = logging.getLogger(__name__)

class PasswordHistory(BaseModel):
    password_hash: str
    changed_at: datetime

class SecurityUtils:
    pwd_context = CryptContext(
        schemes=["bcrypt", "argon2"],
        deprecated="auto",
        bcrypt__rounds=12,
        argon2__time_cost=3,
        argon2__memory_cost=65536,
        argon2__parallelism=4,
        argon2__hash_len=32
    )

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return SecurityUtils.pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return SecurityUtils.pwd_context.hash(password)

    @staticmethod
    async def validate_password_complexity(password: str) -> bool:
        """Valida complejidad de contraseña"""
        if len(password) < 8:
            return False
        if not any(c.isupper() for c in password):
            return False
        if not any(c.isdigit() for c in password):
            return False
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?`~' for c in password):
            return False
        return True

    @staticmethod
    async def check_password_history(
        db: AsyncSession,
        user_id: int,
        new_password: str,
        history_depth: int = 5
    ) -> bool:
        """Verifica si la contraseña fue usada recientemente"""
        result = await db.execute(
            select(User.password_history)
            .where(User.id == user_id)
        )
        user = result.scalars().first()
        
        if not user or not user.password_history:
            return False
            
        # Verificar contra las últimas N contraseñas
        recent_history = user.password_history[-history_depth:]
        for old_password in recent_history:
            if SecurityUtils.verify_password(new_password, old_password.password_hash):
                return True
        return False

    @staticmethod
    def create_access_token(
        data: dict,
        expires_delta: Optional[timedelta] = None,
        secret: Optional[str] = None,
        algorithm: Optional[str] = None
    ) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        return jwt.encode(
            to_encode,
            secret or settings.SECRET_KEY,
            algorithm=algorithm or settings.ALGORITHM
        )

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        try:
            return jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
        except JWTError as e:
            logger.warning(f"Token verification failed: {str(e)}")
            return None

    @staticmethod
    async def rotate_password(
        db: AsyncSession,
        user_id: int,
        new_password: str
    ) -> None:
        """Actualiza contraseña con historial"""
        if not await SecurityUtils.validate_password_complexity(new_password):
            raise ValueError("Password does not meet complexity requirements")
            
        if await SecurityUtils.check_password_history(db, user_id, new_password):
            raise ValueError("Password was used recently")
        
        new_hash = SecurityUtils.get_password_hash(new_password)
        new_history = PasswordHistory(
            password_hash=new_hash,
            changed_at=datetime.utcnow()
        )
        
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                hashed_password=new_hash,
                password_history=User.password_history + [new_history]
            )
        )
        await db.commit()

    @staticmethod
    def generate_secure_random(length: int = 32) -> str:
        """Genera cadena aleatoria segura"""
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))