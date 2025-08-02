"""
Pytest configuration and fixtures for testing.

This module provides shared fixtures and configuration for all tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from src.core.database import get_session
from src.main import app


@pytest.fixture(name="test_engine")
def test_engine():
    """Create test database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="test_session")
def test_session(test_engine):
    """Create test database session."""
    with Session(test_engine) as session:
        yield session


@pytest.fixture(name="client")
def client(test_session: Session):
    """Create test client with test database."""

    def get_test_session():
        return test_session

    app.dependency_overrides[get_session] = get_test_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
