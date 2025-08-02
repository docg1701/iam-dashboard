"""
Database configuration and session management using SQLModel.

This module provides database connection, session management, and initialization.
All database operations should use the session dependency from this module.
"""

from collections.abc import AsyncGenerator, Generator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel

from .config import settings


# Create database engine with proper driver
def create_database_engine() -> Engine | None:
    """Create database engine with proper configuration."""
    try:
        return create_engine(
            str(settings.DATABASE_URL),
            pool_pre_ping=True,
            pool_recycle=300,
            echo=settings.DEBUG,
            # Connection pool settings for production
            pool_size=20,
            max_overflow=30,
        )
    except Exception as e:
        print(f"Warning: Database engine creation failed: {e}")
        # Return a dummy engine for import purposes
        return None


engine = create_database_engine()

# Create session factory
SessionLocal = (
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        class_=Session,
    )
    if engine
    else None
)


async def init_db() -> None:
    """
    Initialize database and create tables.

    This function is called during application startup to ensure
    all database tables are created and ready for use.
    """
    if not engine:
        print("⚠️ Warning: Database engine not available, skipping initialization")
        return

    try:
        # Test database connection
        with engine.connect() as connection:
            # Check if pgvector extension is available
            result = connection.execute(
                text("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'")
            )
            if not result.fetchone():
                print("⚠️ Warning: pgvector extension not available")
            else:
                # Enable pgvector extension if available
                connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                connection.commit()
                print("✅ pgvector extension enabled")

        # Create all tables
        SQLModel.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")

    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise


def get_session() -> Generator[Session]:
    """
    Dependency function to get database session.

    Use this function as a FastAPI dependency to inject database sessions
    into your route handlers. The session will be automatically closed
    after the request completes.

    Example:
        @app.get("/users")
        def get_users(session: Session = Depends(get_session)):
            return session.exec(select(User)).all()
    """
    if not SessionLocal:
        raise Exception("Database not available")

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


async def get_async_session() -> AsyncGenerator[Session]:
    """
    Async dependency function to get database session.

    Use this for async route handlers that need database access.
    """
    if not SessionLocal:
        raise Exception("Database not available")

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_test_session() -> Session:
    """
    Create a database session for testing.

    This function creates a session that can be used in tests.
    The session should be manually closed after use.
    """
    if not SessionLocal:
        raise Exception("Database not available")
    return SessionLocal()


# Database utilities
async def health_check() -> bool:
    """
    Check database connectivity for health endpoints.

    Returns:
        bool: True if database is accessible, False otherwise
    """
    if not engine:
        return False

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def close_db_connections() -> None:
    """
    Close all database connections.

    This function should be called during application shutdown
    to ensure all database connections are properly closed.
    """
    if engine:
        engine.dispose()
