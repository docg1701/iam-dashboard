"""Debug test to examine error response."""

import asyncio

from httpx import ASGITransport, AsyncClient

from src.core.config import Settings, get_settings
from src.main import create_app


async def debug_health():
    # Override settings for testing
    test_settings = Settings(
        SECRET_KEY="test-secret-key-change-in-production",
        DB_PASSWORD="test-password",
        DEBUG=True,
        ALLOWED_HOSTS=["test", "localhost", "127.0.0.1", "testserver"],
    )

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        print(f"Headers: {response.headers}")


if __name__ == "__main__":
    asyncio.run(debug_health())
