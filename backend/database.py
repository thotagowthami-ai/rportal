from sqlalchemy import create_engine, event, pool, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Sync engine for migrations
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    poolclass=pool.QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    pool_pre_ping=True,
)

# Async engine for API
async_engine = create_async_engine(
    settings.async_database_url,
    echo=settings.DATABASE_ECHO,
    poolclass=pool.AsyncAdaptedQueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    pool_pre_ping=True,
)

# Session factories
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
    expire_on_commit=False
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()

def init_db():
    """Initialize database and create helper functions."""
    try:
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✓ Database connection successful")
        
        # Create RLS helper function
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE OR REPLACE FUNCTION current_tenant_id() RETURNS UUID AS $$
                BEGIN
                    RETURN NULLIF(current_setting('app.current_tenant_id', TRUE), '')::UUID;
                END;
                $$ LANGUAGE plpgsql STABLE;
            """))
        logger.info("✓ Created current_tenant_id() function for RLS")
        
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        raise
