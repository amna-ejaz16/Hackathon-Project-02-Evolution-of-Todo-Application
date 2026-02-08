"""Database connection module using SQLModel + PostgreSQL."""

import logging
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from fastapi import HTTPException, status
from .config import get_settings

logger = logging.getLogger(__name__)

# Create engine with connection pool settings for Neon PostgreSQL
_engine = None


class DatabaseConnectionError(Exception):
    """Raised when database connection fails."""
    pass


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        try:
            settings = get_settings()
            _engine = create_engine(
                settings.database_url,
                echo=settings.debug,
                pool_pre_ping=True,  # Verify connections before use
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,  # Wait up to 30 seconds for a connection
                pool_recycle=1800,  # Recycle connections after 30 minutes
            )
            logger.info("Database engine created successfully")
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            raise DatabaseConnectionError(f"Database connection failed: {e}")
    return _engine


def create_db_and_tables():
    """Create tables defined by SQLModel models.

    Note: Only creates the 'tasks' table. The 'user' table is managed by
    Better Auth on the frontend and should already exist.
    """
    try:
        engine = get_engine()

        # Import models to ensure they're registered
        from ..models.task import Task
        from ..models.chat import Conversation, Message

        # Only create tables that don't exist yet
        # This avoids conflicts with Better Auth's user table
        SQLModel.metadata.create_all(engine, checkfirst=True)
        logger.info("Database tables created/verified successfully")
    except OperationalError as e:
        logger.error(f"Database connection error during table creation: {e}")
        raise DatabaseConnectionError(f"Could not connect to database: {e}")
    except SQLAlchemyError as e:
        logger.error(f"Database error during table creation: {type(e).__name__}: {e}")
        raise DatabaseConnectionError(f"Database error: {e}")


def get_session():
    """
    Dependency to get a database session.

    Handles connection errors gracefully and returns appropriate HTTP errors.
    """
    try:
        engine = get_engine()
        with Session(engine) as session:
            yield session
    except OperationalError as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable. Please try again later.",
        )
    except SQLAlchemyError as e:
        # Log full error details for debugging
        logger.error(f"Database error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {type(e).__name__}: {str(e)[:200]}",
        )
