from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings."""
    
    # Database settings
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/invoice_db"
    
    # API settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Invoice App"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000"]
    
    class Config:
        case_sensitive = True
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings() 