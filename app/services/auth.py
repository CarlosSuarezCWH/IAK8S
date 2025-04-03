import logging
from datetime import datetime, timedelta
from typing import Optional, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db_session
from app.models.user import User
from app.schemas.auth import Token, TokenData, UserCreate, UserInDB
from app.utils.security import generate_password_reset_token, verify_password_reset_token

logger = logging.getLogger(__name__)

# Security configurations
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login",
    scopes={
        "me": "Read your own user data",
        "docs:read": "Read documents",
        "docs:write": "Create and update documents",
        "admin": "Admin operations"
    }
)

class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    async def get_user(db: AsyncSession, email: str) -> Optional[UserInDB]:
        result = await db.execute(User.select().where(User.email == email))
        user = result.scalars().first()
        if user:
            return UserInDB.from_orm(user)
        return None

    @staticmethod
    async def authenticate_user(
        db: AsyncSession, 
        email: str, 
        password: str
    ) -> Optional[UserInDB]:
        user = await AuthService.get_user(db, email)
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def create_access_token(
        data: dict, 
        expires_delta: Optional[timedelta] = None,
        scopes: list[str] = []
    ) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({
            "exp": expire,
            "scopes": scopes
        })
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        db: Annotated[AsyncSession, Depends(get_db_session)]
    ) -> UserInDB:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
            token_scopes = payload.get("scopes", [])
            token_data = TokenData(email=email, scopes=token_scopes)
        except JWTError:
            raise credentials_exception
        
        user = await AuthService.get_user(db, email=token_data.email)
        if user is None:
            raise credentials_exception
        return user

    @staticmethod
    async def create_user(db: AsyncSession, user_create: UserCreate) -> UserInDB:
        existing_user = await AuthService.get_user(db, user_create.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        hashed_password = AuthService.get_password_hash(user_create.password)
        db_user = User(
            email=user_create.email,
            hashed_password=hashed_password,
            full_name=user_create.full_name
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return UserInDB.from_orm(db_user)

    @staticmethod
    async def reset_password(
        db: AsyncSession,
        token: str,
        new_password: str
    ) -> UserInDB:
        email = verify_password_reset_token(token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token"
            )
        
        user = await AuthService.get_user(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        hashed_password = AuthService.get_password_hash(new_password)
        user.hashed_password = hashed_password
        await db.commit()
        return UserInDB.from_orm(user)