from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
class Settings(BaseSettings):
    # Configuración de MySQL (Docker)
    MYSQL_HOST: str = "db"
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "rootpassword"
    MYSQL_DB: str = "document_ai"
    MYSQL_PORT: int = 3306
    
    # Configuración de MongoDB (Docker)
    MONGO_URI: str = "mongodb://mongo:27017"
    MONGO_DB_NAME: str = "document_ai"
    MONGO_VECTOR_COLLECTION: str = "document_vectors"
    
    # Autenticación JWT
    SECRET_KEY: str = "tu_clave_secreta_compleja_aqui"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Configuración de archivos
    UPLOAD_FOLDER: str = "./uploads"
    ALLOWED_EXTENSIONS: set = {'pdf', 'csv', 'doc', 'docx'}
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Ollama (Docker)
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    DEFAULT_MODEL: str = "llama3"
    OLLAMA_TIMEOUT: int = 300  # 5 minutos
    
    # Configuración de embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-mpnet-base-v2"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # Configuración del sistema
    DEBUG: bool = False
    CORS_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "ignore"  # Ignora variables extras no definidas

# Instancia de configuración
settings = Settings()

# Crear directorio de uploads si no existe
Path(settings.UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)