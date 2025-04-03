import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, RedisDsn, validator, MySQLDsn
from typing import Optional, Dict, Any

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=True
    )

    # Entorno
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")

    # MySQL
    MYSQL_HOST: str = Field(default="db")
    MYSQL_PORT: int = Field(default=3306)
    MYSQL_USER: str = Field(default="root")
    MYSQL_PASSWORD: str = Field(default="rootpassword")
    MYSQL_DB: str = Field(default="document_ai")
    MYSQL_POOL_SIZE: int = Field(default=10)
    MYSQL_MAX_OVERFLOW: int = Field(default=20)
    
    # MongoDB
    MONGO_URI: str = Field(default="mongodb://mongo:27017")
    MONGO_DB_NAME: str = Field(default="document_ai")
    MONGO_MAX_POOL_SIZE: int = Field(default=100)
    MONGO_TIMEOUT_MS: int = Field(default=5000)

    # Auth
    SECRET_KEY: str = Field(default="your-secret-key")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    # Files
    UPLOAD_FOLDER: str = Field(default="/app/uploads")
    MAX_FILE_SIZE_MB: int = Field(default=10)
    ALLOWED_EXTENSIONS: set = Field(default={'pdf', 'docx', 'csv', 'txt'})

    # Ollama
    OLLAMA_BASE_URL: str = Field(default="http://ollama:11434")
    DEFAULT_MODEL: str = Field(default="llama3")
    OLLAMA_TIMEOUT: int = Field(default=300)

    # URLs completas
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"

    @validator('UPLOAD_FOLDER')
    def create_upload_folder(cls, v):
        Path(v).mkdir(parents=True, exist_ok=True)
        return v

    @validator('ALLOWED_EXTENSIONS')
    def normalize_extensions(cls, v):
        return {ext.lower() for ext in v}

# Singleton de configuración
settings = Settings()

# Configuración de logging
LOGGING_CONFIG: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        },
    },
    "loggers": {
        "app": {
            "handlers": ["console"],
            "level": settings.LOG_LEVEL,
            "propagate": False
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING"
    }
}