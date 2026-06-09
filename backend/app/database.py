"""
NyayaShastra - Database Connection and Session Management
Configured for Neon PostgreSQL with connection pooling.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator

from app.config import settings
from app.models import Base


# Create database engine with connection pooling for Neon PostgreSQL
engine_args = {
    "echo": settings.database_echo,
}

# PostgreSQL-specific settings
if "postgresql" in settings.database_url:
    engine_args.update({
        "pool_size": 10,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,  # Recycle connections every 30 minutes
        "pool_pre_ping": True,  # Check connection viability before using
    })
else:
    # SQLite settings
    engine_args["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.database_url, **engine_args)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for database session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
