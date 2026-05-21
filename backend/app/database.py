from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager
from app.config import settings

DATABASE_URL = settings.DATABASE_URL or "sqlite:///./test.db"

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
    # Add real tenant logic later if needed
    pass
