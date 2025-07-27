"""Test configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.user import User, UserRole
from app.models.client import Client
from app.repositories.user_repository import UserRepository
from app.repositories.client_repository import ClientRepository
from app.services.user_service import UserService
from app.services.client_service import ClientService

# Test database URL (use PostgreSQL for tests to support JSONB and Vector types)
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/advocacia_test_db"
TEST_SYNC_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/advocacia_test_db"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Create an async database session for testing."""
    # Create async engine
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def user_repository(async_session: AsyncSession) -> UserRepository:
    """Create a user repository for testing."""
    return UserRepository(async_session)


@pytest_asyncio.fixture
async def user_service(user_repository: UserRepository) -> UserService:
    """Create a user service for testing."""
    return UserService(user_repository)


@pytest_asyncio.fixture
async def test_user(user_service: UserService) -> User:
    """Create a test user."""
    return await user_service.create_user(
        username="testuser",
        password="testpassword123",
        role=UserRole.COMMON_USER,
        enable_2fa=True
    )


@pytest_asyncio.fixture
async def test_user_no_2fa(user_service: UserService) -> User:
    """Create a test user without 2FA."""
    return await user_service.create_user(
        username="testuser_no2fa",
        password="testpassword123",
        role=UserRole.COMMON_USER,
        enable_2fa=False
    )


@pytest_asyncio.fixture
async def client_repository(async_session: AsyncSession) -> ClientRepository:
    """Create a client repository for testing."""
    return ClientRepository(async_session)


@pytest_asyncio.fixture
async def client_service(client_repository: ClientRepository) -> ClientService:
    """Create a client service for testing."""
    return ClientService(client_repository)


@pytest_asyncio.fixture
async def test_client(client_service: ClientService) -> Client:
    """Create a test client."""
    from datetime import date
    return await client_service.create_client(
        name="João da Silva",
        cpf="11144477735",  # Valid CPF
        birth_date=date(1980, 5, 15)
    )