from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import secrets

class Settings(BaseSettings):
    """Application configuration with environment variable support."""
    
    # Application
    APP_NAME: str = "Recruiting Platform API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Security
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)  # Override in production!
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/recruitingdb"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Claude API
    CLAUDE_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"
    CLAUDE_MAX_TOKENS: int = 4096
    
    # Cloudflare R2
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "recruiting-resumes"
    R2_PUBLIC_URL: str = ""
    
    # SendGrid
    SENDGRID_API_KEY: str = ""
    FROM_EMAIL: str = "noreply@yourapp.com"
    
    # Rate Limiting
    RATE_LIMIT_FREE: int = 100
    RATE_LIMIT_PRO: int = 1000
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".doc", ".docx"]
    
    # Monitoring
    SENTRY_DSN: str = ""
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    def get_r2_endpoint(self) -> str:
        """Construct R2 endpoint URL."""
        return f"https://{self.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    
    @property
    def async_database_url(self) -> str:
        """Convert sync database URL to async."""
        return self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg://")

# Global settings instance
settings = Settings()
