"""
Database configuration and connection management.
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel
import structlog

from .config import get_settings
# Note: Models will be imported explicitly where needed to avoid circular imports

logger = structlog.get_logger(__name__)

settings = get_settings()

# Create async engine with proper connection pooling
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# Create async session maker
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_database() -> None:
    """Initialize database tables."""
    try:
        async with engine.begin() as conn:
            # Create all tables (models already imported at module level)
            await conn.run_sync(SQLModel.metadata.create_all)
            
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function that yields database sessions.
    
    Usage:
        @app.get("/users/")
        async def get_users(session: AsyncSession = Depends(get_async_session)):
            result = await session.exec(select(User))
            return result.all()
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()