import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    # MongoDB Configuration
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://admin:123456@localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "app_db")
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Email Configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@supnum.mr")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    FRONTEND_VITE_URL: str = os.getenv("FRONTEND_VITE_URL", "http://localhost:5173")
    
    # Cookie Configuration
    REFRESH_TOKEN_COOKIE_NAME: str = os.getenv("REFRESH_TOKEN_COOKIE_NAME", "refresh_token")
    REFRESH_TOKEN_COOKIE_HTTP_ONLY: bool = os.getenv("REFRESH_TOKEN_COOKIE_HTTP_ONLY", "True").lower() == "true"
    REFRESH_TOKEN_COOKIE_SECURE: bool = os.getenv("REFRESH_TOKEN_COOKIE_SECURE", "False").lower() == "true"
    REFRESH_TOKEN_COOKIE_SAME_SITE: str = os.getenv("REFRESH_TOKEN_COOKIE_SAME_SITE", "lax")
    
    # Storage Configuration
    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "local")
    
    # AWS S3 Configuration (only needed if STORAGE_TYPE="s3")
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_S3_BUCKET_NAME: Optional[str] = os.getenv("AWS_S3_BUCKET_NAME")


settings = Settings()

