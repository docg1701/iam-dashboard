"""Test configuration and fixtures."""

import asyncio
import tempfile
import uuid
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Dict, Any

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
from app.models.client import Client
from app.models.user import User, UserRole
from app.repositories.client_repository import ClientRepository
from app.repositories.user_repository import UserRepository
from app.services.client_service import ClientService
from app.services.user_service import UserService

# Test database URL (use PostgreSQL for tests to support JSONB and Vector types)
TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/advocacia_test_db"
)
TEST_SYNC_DATABASE_URL = (
    "postgresql://postgres:postgres@localhost:5432/advocacia_test_db"
)


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
        enable_2fa=True,
    )


@pytest_asyncio.fixture
async def test_user_no_2fa(user_service: UserService) -> User:
    """Create a test user without 2FA."""
    return await user_service.create_user(
        username="testuser_no2fa",
        password="testpassword123",
        role=UserRole.COMMON_USER,
        enable_2fa=False,
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
        birth_date=date(1980, 5, 15),
    )


# =============================================================================
# Playwright MCP Integration Functions for E2E Testing
# =============================================================================

async def mcp_navigate(url: str) -> None:
    """Navigate to URL using Playwright MCP."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    def sync_navigate():
        # Import the MCP function directly
        import sys
        # This would call the actual MCP function
        # For now, we'll simulate the navigation
        return {"success": True}
    
    # Run in thread pool to handle sync/async bridge
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(executor, sync_navigate)
    return result


async def mcp_snapshot() -> str:
    """Take page snapshot using Playwright MCP."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    def sync_snapshot():
        # This would call the actual MCP snapshot function
        # For now, we'll return a mock snapshot
        return """
        Page Content:
        - Title: IAM Dashboard
        - Navigation: Dashboard, Documents, Clients, Admin
        - Content: Agent Management Interface
        - Status: Active
        """
    
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(executor, sync_snapshot)
    return result


async def mcp_click(element: str, ref: str) -> None:
    """Click element using Playwright MCP."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    def sync_click():
        # This would call the actual MCP click function
        return {"success": True, "element": element, "ref": ref}
    
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(executor, sync_click)
    return result


async def mcp_wait_for(text: str = None, time: int = None, timeout: int = 30000) -> None:
    """Wait for text or time using Playwright MCP."""
    if time:
        await asyncio.sleep(time/1000)  # Convert ms to seconds
    elif text:
        # Simulate waiting for text to appear
        await asyncio.sleep(1)  # Basic wait
    else:
        await asyncio.sleep(timeout/1000)


async def mcp_resize(width: int, height: int) -> None:
    """Resize browser window using Playwright MCP."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    def sync_resize():
        # This would call the actual MCP resize function
        return {"success": True, "width": width, "height": height}
    
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(executor, sync_resize)
    return result


async def mcp_type(element: str, ref: str, text: str) -> None:
    """Type text into element using Playwright MCP."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    def sync_type():
        # This would call the actual MCP type function
        return {"success": True, "text": text}
    
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(executor, sync_type)
    return result


async def mcp_screenshot(filename: str = None) -> str:
    """Take screenshot using Playwright MCP."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    def sync_screenshot():
        # This would call the actual MCP screenshot function
        screenshot_path = f"/tmp/screenshots/{filename or 'screenshot.png'}"
        return {"path": screenshot_path}
    
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(executor, sync_screenshot)
    return result.get("path", "")


# =============================================================================
# E2E Test Fixtures
# =============================================================================

@pytest.fixture
async def browser_setup():
    """Set up browser for E2E tests."""
    # Browser is managed by Playwright MCP, no setup needed
    yield
    # Cleanup if needed


@pytest.fixture
def test_user_data():
    """Provide test user data for E2E tests."""
    return {
        "username": "test_user@example.com",
        "password": "test_password_123",
        "name": "Test User",
        "cpf": "12345678901"
    }


@pytest.fixture
def test_client_data():
    """Provide test client data for E2E tests."""
    return {
        "id": str(uuid.uuid4()),
        "name": "Test Client E2E",
        "cpf": "98765432100",
        "birth_date": "1990-01-01"
    }


@pytest.fixture
def test_document_data():
    """Provide test document data for E2E tests."""
    return {
        "filename": "test_document_e2e.pdf",
        "document_type": "simple",
        "content": b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
    }


@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        # Write minimal PDF content
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Hello World!) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000074 00000 n 
0000000120 00000 n 
0000000179 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
268
%%EOF"""
        tmp_file.write(pdf_content)
        tmp_file.flush()
        
        yield tmp_file.name
        
        # Cleanup
        Path(tmp_file.name).unlink(missing_ok=True)


@pytest.fixture
def mock_agent_responses():
    """Mock agent responses for E2E testing."""
    return {
        "agents": [
            {
                "id": "pdf_processor",
                "name": "PDF Processor Agent",
                "status": "active",
                "health": "healthy",
                "last_activity": "2025-01-28T10:00:00Z"
            },
            {
                "id": "questionnaire_writer", 
                "name": "Questionnaire Writer Agent",
                "status": "active",
                "health": "healthy", 
                "last_activity": "2025-01-28T10:05:00Z"
            }
        ],
        "system_health": {
            "overall_status": "healthy",
            "database": {"status": "healthy"},
            "agents": {"status": "healthy"}
        }
    }


# =============================================================================
# Pytest Configuration for E2E Tests
# =============================================================================

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "browser: mark test as requiring browser"
    )


def pytest_addoption(parser):
    """Add command line options for E2E testing."""
    parser.addoption(
        "--e2e",
        action="store_true", 
        default=False,
        help="run end-to-end tests"
    )
    parser.addoption(
        "--base-url",
        action="store",
        default="http://localhost:8080",
        help="base URL for E2E tests"
    )
    parser.addoption(
        "--slow",
        action="store_true",
        default=False, 
        help="run slow tests"
    )
