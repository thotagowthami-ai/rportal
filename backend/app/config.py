from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path
 
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    # App Metadata
    APP_NAME: str = "Recruiting Platform API"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security
    JWT_SECRET_KEY: str = "dev-secret-key-CHANGE-IN-PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database / Infra
     # Database / Infra
    DATABASE_URL: Optional[str] = None
    REDIS_URL: Optional[str] = None
    
    @property
    def REDIS_KEY_PREFIX(self) -> str:
        return f"recruit:{self.ENVIRONMENT}:"

    UPSTASH_REDIS_REST_URL: Optional[str] = None
    UPSTASH_REDIS_REST_TOKEN: Optional[str] = None
    AUTO_CREATE_TABLES: bool = False

    # Storage (Cloudflare R2)
    R2_ACCOUNT_ID: Optional[str] = None
    R2_ACCESS_KEY_ID: Optional[str] = None
    R2_SECRET_ACCESS_KEY: Optional[str] = None
    R2_BUCKET_NAME: Optional[str] = None
    R2_PUBLIC_URL: Optional[str] = None

    # Email (SendGrid - keeping for backcompat if needed, but primary is SMTP)
    SENDGRID_API_KEY: Optional[str] = None
    
    # SMTP Configuration
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    FROM_EMAIL: str = "noreply@yourapp.com"

    # CORS
    ALLOWED_ORIGINS: str = ""
    ALLOWED_ORIGIN_REGEX: str = ""

    # Observability
    SENTRY_DSN: Optional[str] = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    # AI / LLM
    CLAUDE_API_KEY: Optional[str] = None
    CLAUDE_MODEL: str = "claude-3-haiku-20240307"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "deepseek/deepseek-chat"
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    LINKEDIN_REDIRECT_URI: Optional[str] = None
    LINKEDIN_SCOPES: str = "openid profile email w_member_social"
    FRONTEND_URL: str = ""

    # Candidate Portal integration
    CANDIDATE_PORTAL_URL: Optional[str] = None
    CANDIDATE_PORTAL_TENANT_ID: Optional[str] = None
    # Back-compat: some deployments may still use this name
    RECRUITING_TENANT_ID: Optional[str] = None

    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    BACKEND_URL: str = "http://127.0.0.1:8000"
    FRONTEND_URL: str = "http://127.0.0.1:3000"

    class Config:
        env_file = str(ENV_FILE)
        case_sensitive = True

    @property
    def async_database_url(self) -> str:
        if not self.DATABASE_URL:
            return "sqlite+aiosqlite:///./test.db"
        db_url = self.DATABASE_URL
        db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
        return db_url


settings = Settings()
