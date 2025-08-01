#!/usr/bin/env python3
"""Debug script for admin API test."""

from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.admin import router as admin_router
from app.containers import Container


def test_admin_endpoint():
    """Test admin endpoint directly."""
    # Mock the agent manager
    mock_agent_manager = MagicMock()
    mock_agent_manager.enable_agent = AsyncMock(return_value=True)

    # Create container and override
    container = Container()
    container.agent_manager.override(mock_agent_manager)

    # Create a clean FastAPI app
    app = FastAPI()
    app.include_router(admin_router)

    # Wire the container
    container.wire(modules=["app.api.admin"])

    # Create test client
    with TestClient(app) as client:
        try:
            response = client.post("/v1/admin/agents/test_agent/start")
            print(f"Status code: {response.status_code}")
            print(f"Response: {response.text}")
            print(f"Headers: {response.headers}")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_admin_endpoint()
