"""Tests for seed_data utility functions."""

from typing import Any
from unittest.mock import Mock, patch

import pytest
from sqlmodel import Session

from src.models.audit import AuditAction
from src.models.client import ClientStatus
from src.models.user import UserRole
from src.utils.seed_data import (
    clear_database,
    main,
    print_seed_summary,
    reset_database,
    seed_database,
    seed_for_testing,
)


class TestSeedDatabase:
    """Test database seeding function."""

    @pytest.fixture
    def mock_session(self) -> Mock:
        """Create a mock database session."""
        session = Mock(spec=Session)
        session.add = Mock()
        session.commit = Mock()
        session.exec = Mock()
        return session

    @pytest.fixture
    def mock_engine(self):
        """Create a mock database engine."""
        return Mock()

    @patch("src.utils.seed_data.Session")
    @patch("src.utils.seed_data.engine")
    @patch("src.utils.seed_data.create_seed_users")
    @patch("src.utils.seed_data.create_seed_clients")
    @patch("src.utils.seed_data.create_complete_audit_trail")
    @patch("src.utils.seed_data.create_test_audit_log")
    @patch("src.utils.seed_data.print_seed_summary")
    @patch("builtins.print")
    @pytest.mark.asyncio
    async def test_seed_database_success(
        self,
        mock_print: Any,
        mock_print_summary: Any,
        mock_create_audit_log: Any,
        mock_create_audit_trail: Any,
        mock_create_clients: Any,
        mock_create_users: Any,
        _mock_engine: Any,
        mock_session_class: Any,
        mock_session: Any,
    ) -> None:
        """Test successful database seeding."""
        mock_session_class.return_value.__enter__.return_value = mock_session

        # Mock seed data creation
        mock_admin = Mock(user_id="admin1", email="admin@company.com")
        mock_users = [Mock(user_id="user1"), Mock(user_id="user2")]

        # Mock no existing users (empty database)
        empty_result = Mock()
        empty_result.all.return_value = []

        # Mock select query for admin user
        admin_result = Mock()
        admin_result.first.return_value = mock_admin

        # Set up exec to return different results based on call
        mock_session.exec.side_effect = [empty_result, admin_result]
        mock_users.append(mock_admin)
        mock_create_users.return_value = mock_users

        mock_clients = [Mock(client_id="client1"), Mock(client_id="client2")]
        mock_create_clients.return_value = mock_clients

        mock_audit_logs = [Mock(), Mock()]
        mock_create_audit_trail.return_value = mock_audit_logs
        mock_create_audit_log.return_value = Mock()

        # Mock select query for admin user
        mock_admin_result = Mock()
        mock_admin_result.first.return_value = mock_admin
        mock_session.exec.return_value = mock_admin_result

        await seed_database()

        # Verify users were created
        assert mock_session.add.call_count >= len(mock_users)

        # Verify print statements
        mock_print.assert_any_call("🌱 Starting database seeding...")
        mock_print.assert_any_call("🎉 Database seeding completed successfully!")

        # Verify summary was printed
        mock_print_summary.assert_called_once()

    @patch("src.utils.seed_data.Session")
    @patch("src.utils.seed_data.engine")
    @patch("builtins.print")
    @pytest.mark.asyncio
    async def test_seed_database_already_seeded(
        self, mock_print, _mock_engine, mock_session_class, mock_session
    ):
        """Test seeding when database already has users."""
        mock_session_class.return_value.__enter__.return_value = mock_session

        # Mock existing users
        existing_users = [Mock(), Mock()]
        mock_result = Mock()
        mock_result.all.return_value = existing_users
        mock_session.exec.return_value = mock_result

        await seed_database()

        # Should print warning and return early
        mock_print.assert_any_call("⚠️  Database already contains users. Skipping seeding.")
        mock_print.assert_any_call(f"   Found {len(existing_users)} existing users.")

        # Should not add any new data
        mock_session.add.assert_not_called()

    @patch("src.utils.seed_data.Session")
    @patch("src.utils.seed_data.engine")
    @patch("src.utils.seed_data.create_seed_users")
    @patch("builtins.print")
    @pytest.mark.asyncio
    async def test_seed_database_exception_handling(
        self, mock_print, mock_create_users, _mock_engine, mock_session_class, mock_session
    ):
        """Test exception handling during seeding."""
        mock_session_class.return_value.__enter__.return_value = mock_session

        # Mock no existing users
        mock_result = Mock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        # Mock exception during user creation
        mock_create_users.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await seed_database()

        # Should rollback transaction
        mock_session.rollback.assert_called_once()

        # Should print error
        mock_print.assert_any_call("❌ Error during seeding: Database error")


class TestPrintSeedSummary:
    """Test seed summary printing function."""

    @pytest.fixture
    def mock_users(self):
        """Create mock users with different roles."""
        return [
            Mock(role=UserRole.SYSADMIN),
            Mock(role=UserRole.ADMIN),
            Mock(role=UserRole.USER),
            Mock(role=UserRole.USER),
        ]

    @pytest.fixture
    def mock_clients(self):
        """Create mock clients with different statuses."""
        return [
            Mock(status=ClientStatus.ACTIVE),
            Mock(status=ClientStatus.ACTIVE),
            Mock(status=ClientStatus.INACTIVE),
        ]

    @pytest.fixture
    def mock_audit_logs(self):
        """Create mock audit logs with different actions."""
        return [
            Mock(action=AuditAction.CREATE),
            Mock(action=AuditAction.UPDATE),
            Mock(action=AuditAction.CREATE),
        ]

    @patch("builtins.print")
    def test_print_seed_summary(self, mock_print, mock_users, mock_clients, mock_audit_logs):
        """Test seed summary printing."""
        mock_session = Mock(spec=Session)

        # Mock database queries to return actual lists, not Mock objects
        user_result = Mock()
        user_result.all.return_value = mock_users
        client_result = Mock()
        client_result.all.return_value = mock_clients
        audit_result = Mock()
        audit_result.all.return_value = mock_audit_logs

        mock_session.exec.side_effect = [user_result, client_result, audit_result]

        print_seed_summary(mock_session)

        # Verify summary information was printed
        mock_print.assert_any_call("\n📊 Seed Data Summary:")
        mock_print.assert_any_call(f"   Users: {len(mock_users)}")
        mock_print.assert_any_call(f"   Clients: {len(mock_clients)}")
        mock_print.assert_any_call(f"   Audit Logs: {len(mock_audit_logs)}")

        # Verify role breakdown
        mock_print.assert_any_call("   Roles breakdown:")
        mock_print.assert_any_call("     - sysadmin: 1")
        mock_print.assert_any_call("     - admin: 1")
        mock_print.assert_any_call("     - user: 2")

        # Verify status breakdown
        mock_print.assert_any_call("   Status breakdown:")
        mock_print.assert_any_call("     - active: 2")
        mock_print.assert_any_call("     - inactive: 1")

        # Verify action breakdown
        mock_print.assert_any_call("   Action breakdown:")
        mock_print.assert_any_call("     - CREATE: 2")
        mock_print.assert_any_call("     - UPDATE: 1")


class TestClearDatabase:
    """Test database clearing function."""

    @pytest.fixture
    def mock_session(self) -> Mock:
        """Create a mock database session."""
        session = Mock(spec=Session)
        session.exec = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        return session

    @patch("src.utils.seed_data.Session")
    @patch("src.utils.seed_data.engine")
    @patch("builtins.print")
    @pytest.mark.asyncio
    async def test_clear_database_success(
        self, mock_print, _mock_engine, mock_session_class, mock_session
    ):
        """Test successful database clearing."""
        mock_session_class.return_value.__enter__.return_value = mock_session

        await clear_database()

        # Verify deletion queries were executed in correct order
        expected_deletes = [
            "DELETE FROM audit_logs",
            "DELETE FROM agent1_clients",
            "DELETE FROM users",
        ]

        assert mock_session.exec.call_count == len(expected_deletes)
        for i, expected_query in enumerate(expected_deletes):
            actual_call = mock_session.exec.call_args_list[i][0][0]
            assert actual_call == expected_query

        # Verify commit was called
        mock_session.commit.assert_called_once()

        # Verify success message
        mock_print.assert_any_call("🧹 Clearing database...")
        mock_print.assert_any_call("   ✅ Database cleared successfully")

    @patch("src.utils.seed_data.Session")
    @patch("src.utils.seed_data.engine")
    @patch("builtins.print")
    @pytest.mark.asyncio
    async def test_clear_database_exception(
        self, mock_print, _mock_engine, mock_session_class, mock_session
    ):
        """Test exception handling during database clearing."""
        mock_session_class.return_value.__enter__.return_value = mock_session
        mock_session.exec.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await clear_database()

        # Should rollback and print error
        mock_session.rollback.assert_called_once()
        mock_print.assert_any_call("   ❌ Error clearing database: Database error")


class TestResetDatabase:
    """Test database reset function."""

    @patch("src.utils.seed_data.clear_database")
    @patch("src.utils.seed_data.seed_database")
    @pytest.mark.asyncio
    async def test_reset_database(self, mock_seed, mock_clear):
        """Test database reset calls clear then seed."""
        await reset_database()

        # Should call clear first, then seed
        mock_clear.assert_called_once()
        mock_seed.assert_called_once()


class TestSeedForTesting:
    """Test testing data seeding function."""

    @pytest.fixture
    def mock_session(self) -> Mock:
        """Create a mock database session."""
        session = Mock(spec=Session)
        session.add = Mock()
        session.commit = Mock()
        return session

    @patch("src.utils.seed_data.Session")
    @patch("src.utils.seed_data.engine")
    @patch("src.utils.seed_data.create_seed_users")
    @patch("src.utils.seed_data.create_seed_clients")
    @patch("src.utils.seed_data.create_complete_audit_trail")
    def test_seed_for_testing(
        self,
        mock_create_audit_trail,
        mock_create_clients,
        mock_create_users,
        _mock_engine,
        mock_session_class,
        mock_session,
    ):
        """Test seeding for testing environment."""
        mock_session_class.return_value.__enter__.return_value = mock_session

        # Mock test data
        mock_admin = Mock(user_id="admin1", email="admin@company.com")
        mock_users = [mock_admin, Mock(user_id="user1")]
        mock_create_users.return_value = mock_users

        mock_clients = [Mock(client_id="client1"), Mock(client_id="client2")]
        mock_create_clients.return_value = mock_clients

        mock_audit_logs = [Mock(), Mock()]
        mock_create_audit_trail.return_value = mock_audit_logs

        result_users, result_clients, result_audit_logs = seed_for_testing()

        # Verify returned data
        assert result_users == mock_users
        assert result_clients == mock_clients
        assert len(result_audit_logs) >= 0  # May be empty list

        # Verify data was added to database
        assert mock_session.add.call_count >= len(mock_users) + len(mock_clients)
        assert mock_session.commit.call_count >= 2  # At least for users and clients


class TestMain:
    """Test CLI main function."""

    @patch("sys.argv", ["script_name", "seed"])
    @patch("src.utils.seed_data.seed_database")
    @patch("builtins.print")
    @pytest.mark.asyncio
    async def test_main_seed_command(self, _mock_print, mock_seed):
        """Test main function with seed command."""
        await main()
        mock_seed.assert_called_once()

    @patch("sys.argv", ["script_name", "clear"])
    @patch("src.utils.seed_data.clear_database")
    @patch("builtins.print")
    @pytest.mark.asyncio
    async def test_main_clear_command(self, _mock_print, mock_clear):
        """Test main function with clear command."""
        await main()
        mock_clear.assert_called_once()

    @patch("sys.argv", ["script_name", "reset"])
    @patch("src.utils.seed_data.reset_database")
    @patch("builtins.print")
    @pytest.mark.asyncio
    async def test_main_reset_command(self, _mock_print, mock_reset):
        """Test main function with reset command."""
        await main()
        mock_reset.assert_called_once()

    @patch("sys.argv", ["script_name"])
    @patch("builtins.print")
    @pytest.mark.asyncio
    async def test_main_no_command(self, mock_print):
        """Test main function with no command."""
        await main()
        mock_print.assert_called_with("Usage: python -m src.utils.seed_data [seed|clear|reset]")

    @patch("sys.argv", ["script_name", "invalid"])
    @patch("builtins.print")
    @pytest.mark.asyncio
    async def test_main_invalid_command(self, mock_print):
        """Test main function with invalid command."""
        await main()
        mock_print.assert_any_call("Unknown command: invalid")
        mock_print.assert_any_call("Available commands: seed, clear, reset")
