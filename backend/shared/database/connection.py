"""
Database connection management
Provides session handling and connection pooling
"""
import os
from contextlib import contextmanager
from typing import Generator

from loguru import logger
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

# Database configuration from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:password@localhost:5432/healthtech"
)

# Environment
ENV = os.getenv("ENV", "development")
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"

# Connection pool settings
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))

# Create engine with appropriate settings
if ENV == "test":
    # Use NullPool for testing to avoid connection issues
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        echo=SQL_ECHO,
    )
else:
    # Use QueuePool for production/development
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_timeout=POOL_TIMEOUT,
        pool_recycle=POOL_RECYCLE,
        pool_pre_ping=True,  # Enable connection health checks
        echo=SQL_ECHO,
    )


# SQLAlchemy event listeners for logging
@event.listens_for(Engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log when a new connection is created"""
    logger.debug("New database connection established")


@event.listens_for(Engine, "close")
def receive_close(dbapi_conn, connection_record):
    """Log when a connection is closed"""
    logger.debug("Database connection closed")


# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,  # Prevent expired object errors
)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions

    Usage:
        with get_db_session() as db:
            user = db.query(User).first()
            db.commit()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes

    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Database error in request: {e}")
        raise
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables"""
    from .models import Base

    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")


def drop_db():
    """Drop all database tables - USE WITH CAUTION!"""
    from .models import Base

    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.warning("All tables dropped")


def check_db_connection() -> bool:
    """
    Check if database connection is working

    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Database connection check: SUCCESS")
        return True
    except Exception as e:
        logger.error(f"Database connection check: FAILED - {e}")
        return False


def get_db_info() -> dict:
    """
    Get database connection information

    Returns:
        dict: Database connection details
    """
    return {
        "url": DATABASE_URL.split("@")[-1],  # Hide credentials
        "pool_size": POOL_SIZE,
        "max_overflow": MAX_OVERFLOW,
        "pool_timeout": POOL_TIMEOUT,
        "pool_recycle": POOL_RECYCLE,
        "dialect": engine.dialect.name,
        "driver": engine.driver,
    }
