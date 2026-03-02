from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    APP_NAME: str = "DocuMind AI"
    DEBUG: bool = False
    
    ANTHROPIC_API_KEY: str
    
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    UPLOAD_DIR: str = "uploads"
    CHROMA_DIR: str = "chroma_db"
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./documind.db"
    
    class Config:
        env_file = ".env"

settings = Settings()

# Ensure directories exist
Path(settings.UPLOAD_DIR).mkdir(exist_ok=True)
Path(settings.CHROMA_DIR).mkdir(exist_ok=True)