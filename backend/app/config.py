import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "ReqProof"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "reqproof-super-secret-key-development-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./reqproof.db")
    
    # Upload storage
    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")), "uploads"))
    MAX_UPLOAD_SIZE_MB: int = 50
    
    # AI integration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

settings = Settings()
