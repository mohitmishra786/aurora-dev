"""
PostgreSQL database connection management for AURORA-DEV.

This module provides SQLAlchemy engine and session management with
connection pooling and health checks.
"""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from aurora_dev.core.config import get_settings
from aurora_dev.core.logging import get_logger

logger = get_logger("database")

# Global engine instance
_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """
    Get or create the SQLAlchemy engine.

    Returns:
        The SQLAlchemy engine instance.
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database.url,
            poolclass=QueuePool,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            pool_recycle=settings.database.pool_recycle,
            echo=settings.database.echo,
        )
        logger.info(
            "Database engine created",
            extra={"pool_size": settings.database.pool_size},
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """
    Get or create the session factory.

    Returns:
        The SQLAlchemy session factory.
    """
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _session_factory


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Yields:
        A database session.

    Example:
        with get_session() as session:
            session.execute(text("SELECT 1"))
    """
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_health() -> bool:
    """
    Check database connectivity.

    Returns:
        True if database is accessible, False otherwise.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()
        logger.debug("Database health check passed")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def close_engine() -> None:
    """Close the database engine and release connections."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database engine closed")
