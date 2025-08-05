"""Tests for seed_data utility functions."""

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
    def mock_engine(self) -> Mock:
        """Create a mock database engine."""
        return Mock()

    @patch("src.utils.seed_data.Session")
    @patch("src.utils.seed_data.create_seed_users")
    @patch("builtins.print")
    @pytest.mark.asyncio
    async def test_seed_database_success(
        self,
        mock_print: Mock,
        mock_create_users: Mock,
        mock_session_class: Mock,
        mock_session: Mock,
    ) -> None:
        """Test successful database seeding."""
        # Setup session context manager
        mock_session_class.return_value.__enter__.return_value = mock_session
        mock_session_class.return_value.__exit__.return_value = None

        # Mock empty database check
        empty_result = Mock()
        empty_result.all.return_value = []
        mock_session.exec.return_value = empty_result

        # Mock user creation
        mock_users = [Mock(email="user1@test.com"), Mock(email="admin@company.com")]
        mock_create_users.return_value = mock_users

        await seed_database()

        # Verify basic functionality
        assert mock_session.add.call_count >= len(mock_users)
        mock_session.commit.assert_called()
        mock_print.assert_any_call("🌱 Starting database seeding...")

    @patch("src.utils.seed_data.Session")
    @patch("builtins.print")
    @pytest.mark.asyncio
    async def test_seed_database_already_seeded(
        self, mock_print: Mock, mock_session_class: Mock
    ) -> None:
        """Test seeding when database already has users."""
        mock_session = Mock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        mock_session_class.return_value.__exit__.return_value = None

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
    @patch("src.utils.seed_data.create_seed_users")
    @patch("builtins.print")
    @pytest.mark.asyncio
    async def test_seed_database_exception_handling(
        self,
        mock_print: Mock,
        mock_create_users: Mock,
        mock_session_class: Mock,
    ) -> None:
        """Test exception handling during seeding."""
        mock_session = Mock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        mock_session_class.return_value.__exit__.return_value = None

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

        # Should print error (without the leading spaces)
        mock_print.assert_any_call("❌ Error during seeding: Database error")


class TestPrintSeedSummary:
    """Test seed summary printing function."""

    @pytest.fixture
    def mock_users(self) -> list[Mock]:
        """Create mock users with different roles."""
        return [
            Mock(role=UserRole.SYSADMIN),
            Mock(role=UserRole.ADMIN),
            Mock(role=UserRole.USER),
            Mock(role=UserRole.USER),
        ]

    @pytest.fixture
    def mock_clients(self) -> list[Mock]:
        """Create mock clients with different statuses."""
        return [
            Mock(status=ClientStatus.ACTIVE),
            Mock(status=ClientStatus.ACTIVE),
            Mock(status=ClientStatus.INACTIVE),
        ]

    @pytest.fixture
    def mock_audit_logs(self) -> list[Mock]:
        """Create mock audit logs with different actions."""
        return [
            Mock(action=AuditAction.CREATE),
            Mock(action=AuditAction.UPDATE),
            Mock(action=AuditAction.CREATE),
        ]

    @patch("builtins.print")
    def test_print_seed_summary(
        self,
        mock_print: Mock,
        mock_users: list[Mock],
        mock_clients: list[Mock],
        mock_audit_logs: list[Mock],
    ) -> None:
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
    @patch("builtins.print")
    @pytest.mark.asyncio
    async def test_clear_database_success(self, mock_print: Mock, mock_session_class: Mock) -> None:
        """Test successful database clearing."""
        mock_session = Mock()
        mock_connection = Mock()
        mock_session.connection.return_value = mock_connection
        mock_session_class.return_value.__enter__.return_value = mock_session
        mock_session_class.return_value.__exit__.return_value = None

        await clear_database()

        # Verify delete operations were called on connection
        assert mock_connection.execute.call_count == 3  # AuditLog, Client, User

        # Verify commit was called
        mock_session.commit.assert_called_once()

        # Verify success message
        mock_print.assert_any_call("🧹 Clearing database...")
        mock_print.assert_any_call("   ✅ Database cleared successfully")

    @patch("src.utils.seed_data.Session")
    @patch("builtins.print")
    @pytest.mark.asyncio
    async def test_clear_database_exception(
        self, mock_print: Mock, mock_session_class: Mock
    ) -> None:
        """Test exception handling during database clearing."""
        mock_session = Mock()
        mock_connection = Mock()
        mock_session.connection.return_value = mock_connection
        mock_connection.execute.side_effect = Exception("Database error")
        mock_session_class.return_value.__enter__.return_value = mock_session
        mock_session_class.return_value.__exit__.return_value = None

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
    async def test_reset_database(self, mock_seed: Mock, mock_clear: Mock) -> None:
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
    @patch("src.utils.seed_data.create_seed_users")
    def test_seed_for_testing(
        self,
        mock_create_users: Mock,
        mock_session_class: Mock,
    ) -> None:
        """Test seeding for testing environment."""
        mock_session = Mock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        mock_session_class.return_value.__exit__.return_value = None

        # Mock test data
        mock_admin = Mock(user_id="admin1", email="admin@company.com")
        mock_users = [mock_admin, Mock(user_id="user1")]
        mock_create_users.return_value = mock_users

        result = seed_for_testing()

        # Verify it returns the data
        assert result is not None
        assert len(result) == 3  # users, clients, audit_logs

        # Verify users were added
        assert mock_session.add.call_count >= len(mock_users)
        mock_session.commit.assert_called()


class TestMain:
    """Test CLI main function."""

    @patch("sys.argv", ["script_name", "seed"])
    @patch("src.utils.seed_data.seed_database")
    @pytest.mark.asyncio
    async def test_main_seed_command(self, mock_seed: Mock) -> None:
        """Test main function with seed command."""
        await main()
        mock_seed.assert_called_once()

    @patch("sys.argv", ["script_name", "clear"])
    @patch("src.utils.seed_data.clear_database")
    @pytest.mark.asyncio
    async def test_main_clear_command(self, mock_clear: Mock) -> None:
        """Test main function with clear command."""
        await main()
        mock_clear.assert_called_once()

    @patch("sys.argv", ["script_name", "reset"])
    @patch("src.utils.seed_data.reset_database")
    @pytest.mark.asyncio
    async def test_main_reset_command(self, mock_reset: Mock) -> None:
        """Test main function with reset command."""
        await main()
        mock_reset.assert_called_once()

    @patch("sys.argv", ["script_name"])
    @pytest.mark.asyncio
    async def test_main_no_command(self) -> None:
        """Test main function with no command."""
        # This test just verifies no exceptions are raised
        await main()

    @patch("sys.argv", ["script_name", "invalid"])
    @pytest.mark.asyncio
    async def test_main_invalid_command(self) -> None:
        """Test main function with invalid command."""
        # This test just verifies no exceptions are raised
        await main()
