from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    # MongoDB Configuration
    mongodb_url: str = os.getenv("MONGODB_URL", "")
    mongodb_password: str = os.getenv("MONGODB_PASSWORD", "")
    database_name: str = "genshin_assistant"
    
    # Google Gemini API
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Google Custom Search Engine
    google_cse_id: str = os.getenv("GOOGLE_CSE_ID", "")
    google_cse_api_key: str = os.getenv("GOOGLE_CSE_API_KEY", "")
    
    # Redis Configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = int(os.getenv("PORT", "8000"))
    
    # CORS Configuration (FastAPI equivalent of ALLOWED_HOSTS)
    allowed_origins: str = os.getenv("ALLOWED_HOSTS", "*")
    
    # Genshin Data Update Interval (in hours)
    update_interval: int = 4
    
    # Environment and Logging
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = "info"
    
    @property
    def cors_origins(self) -> List[str]:
        """Convert ALLOWED_ORIGINS string to list for CORS middleware."""
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings() 