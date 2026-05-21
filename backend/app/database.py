from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager
from app.config import settings

if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required but not configured in settings")
DATABASE_URL = settings.DATABASE_URL

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Avoid stale SSL pooled connections (common with managed Postgres).
    engine_kwargs.update(
        {
            "pool_pre_ping": True,
            "pool_recycle": 300,
            "pool_size": 5,
            "max_overflow": 10,
            "connect_args": {
                "connect_timeout": 10,
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5,
            },
        }
    )

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    # Import models so SQLAlchemy relationships are registered before mapper configuration.
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)


# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Dummy tenant context (since your project expects it)
def set_tenant_context(db, tenant_id=None):
    """
    Enforce tenant context on the database session.
    
    If tenant_id is missing or falsy, it raises a ValueError (fail-closed).
    Otherwise, it stores the tenant_id in the SQLAlchemy session's info dictionary
    so subsequent hooks, interceptors, or queries can query it for tenant scoping.
    """
    if not tenant_id:
        raise ValueError("Tenant ID is required to set the database context")
    
    # Store tenant context in the session's info dictionary (standard SQLAlchemy state)
    db.info["tenant_id"] = str(tenant_id)

