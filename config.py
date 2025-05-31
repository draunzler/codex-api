from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # MongoDB Configuration
    mongodb_url: str = "mongodb+srv://draunzler:<db_password>@test.nmxzjdn.mongodb.net/"
    mongodb_password: str = ""  # Set this in .env file
    database_name: str = "genshin_assistant"
    
    # Google Gemini API
    google_api_key: str
    
    # Google Custom Search Engine
    google_cse_id: str
    google_cse_api_key: str
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Genshin Data Update Interval (in hours)
    update_interval: int = 4
    
    # Environment and Logging
    environment: str = "development"
    log_level: str = "info"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings() 