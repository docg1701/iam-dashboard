"""
Tests for database module.

This module tests database configuration, session management, and utilities.
"""

from contextlib import suppress
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.core.database import (
    close_db_connections,
    create_database_engine,
    create_test_session,
    get_session,
    health_check,
    init_db,
)


def test_create_database_engine_success() -> None:
    """Test successful database engine creation."""
    with patch("src.core.database.create_engine") as mock_create_engine:
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        result = create_database_engine()

        assert result == mock_engine
        mock_create_engine.assert_called_once()


def test_create_database_engine_failure() -> None:
    """Test database engine creation failure."""
    with patch("src.core.database.create_engine") as mock_create_engine:
        mock_create_engine.side_effect = Exception("Connection failed")

        result = create_database_engine()

        assert result is None


def test_get_session_no_session_local() -> None:
    """Test get_session when SessionLocal is None."""
    with patch("src.core.database.SessionLocal", None):
        session_gen = get_session()

        with pytest.raises(Exception, match="Database not available"):
            next(session_gen)


def test_get_session_success(test_session: Any) -> None:
    """Test successful session creation."""
    with patch("src.core.database.SessionLocal") as mock_session_local:
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        session_gen = get_session()
        session = next(session_gen)

        assert session == mock_session

        # Test cleanup
        with suppress(StopIteration):
            next(session_gen)

        mock_session.close.assert_called_once()


def test_create_test_session_no_session_local() -> None:
    """Test create_test_session when SessionLocal is None."""
    with (
        patch("src.core.database.SessionLocal", None),
        pytest.raises(Exception, match="Database not available"),
    ):
        create_test_session()


def test_create_test_session_success() -> None:
    """Test successful test session creation."""
    with patch("src.core.database.SessionLocal") as mock_session_local:
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        result = create_test_session()

        assert result == mock_session
        mock_session_local.assert_called_once()


@pytest.mark.asyncio
async def test_health_check_no_engine() -> None:
    """Test health check when engine is None."""
    with patch("src.core.database.engine", None):
        result = await health_check()
        assert result is False


@pytest.mark.asyncio
async def test_health_check_success() -> None:
    """Test successful health check."""
    mock_engine = MagicMock()
    mock_connection = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_connection

    with patch("src.core.database.engine", mock_engine):
        result = await health_check()

        assert result is True
        mock_connection.execute.assert_called_once()


@pytest.mark.asyncio
async def test_health_check_failure() -> None:
    """Test health check failure."""
    mock_engine = MagicMock()
    mock_engine.connect.side_effect = Exception("Connection failed")

    with patch("src.core.database.engine", mock_engine):
        result = await health_check()

        assert result is False


def test_close_db_connections_no_engine() -> None:
    """Test close_db_connections when engine is None."""
    with patch("src.core.database.engine", None):
        # Should not raise exception
        close_db_connections()


def test_close_db_connections_success() -> None:
    """Test successful connection closing."""
    mock_engine = MagicMock()

    with patch("src.core.database.engine", mock_engine):
        close_db_connections()

        mock_engine.dispose.assert_called_once()


@pytest.mark.asyncio
async def test_init_db_no_engine() -> None:
    """Test init_db when engine is None."""
    with patch("src.core.database.engine", None):
        # Should not raise exception
        await init_db()


@pytest.mark.asyncio
async def test_init_db_success() -> None:
    """Test successful database initialization."""
    mock_engine = MagicMock()
    mock_connection = MagicMock()
    mock_result = MagicMock()
    mock_result.fetchone.return_value = True  # pgvector available

    mock_connection.execute.return_value = mock_result
    mock_engine.connect.return_value.__enter__.return_value = mock_connection

    with (
        patch("src.core.database.engine", mock_engine),
        patch("src.core.database.SQLModel") as mock_sqlmodel,
    ):
        await init_db()

        # Check pgvector extension query
        assert mock_connection.execute.call_count >= 1
        mock_sqlmodel.metadata.create_all.assert_called_once_with(bind=mock_engine)


@pytest.mark.asyncio
async def test_init_db_failure() -> None:
    """Test database initialization failure."""
    mock_engine = MagicMock()
    mock_engine.connect.side_effect = Exception("Connection failed")

    with (
        patch("src.core.database.engine", mock_engine),
        pytest.raises(Exception, match="Connection failed"),
    ):
        await init_db()
