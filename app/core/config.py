from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # MongoDB Configuration
    MONGODB_URL: str = "mongodb://admin:123456@localhost:27017"
    DATABASE_NAME: str = "app_db"
    
    # JWT Configuration
    JWT_SECRET_KEY: str = "your-secret-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Email Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "ahmedouvallmohamedlemine@gmail.com"
    SMTP_PASSWORD: str = "irzx jqdr yjqu yjzj"
    EMAIL_FROM: str = "noreply@supnum.mr"
    FRONTEND_URL: str = "http://localhost:3000"
    FRONTEND_VITE_URL: str = "http://localhost:5173"  # Vite default port
    
    # Cookie Configuration
    REFRESH_TOKEN_COOKIE_NAME: str = "refresh_token"
    REFRESH_TOKEN_COOKIE_HTTP_ONLY: bool = True
    REFRESH_TOKEN_COOKIE_SECURE: bool = False  # Set to False in development (HTTP), True in production (HTTPS)
    REFRESH_TOKEN_COOKIE_SAME_SITE: str = "lax"  # "lax", "strict", or "none"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

