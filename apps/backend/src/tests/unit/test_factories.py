"""Tests for the test data factories."""

import json
from datetime import date, datetime
from uuid import UUID, uuid4

from src.models.audit import AuditAction, AuditLog
from src.models.client import Client, ClientStatus
from src.models.user import User, UserRole
from src.tests.factories import (
    AdminUserFactory,
    AuditLogFactory,
    ClientFactory,
    InactiveClientFactory,
    RecentClientFactory,
    SysAdminUserFactory,
    UserFactory,
    create_complete_audit_trail,
    create_seed_clients,
    create_seed_users,
    create_test_client,
    create_test_user,
    create_user_with_clients,
    generate_audit_values,
    generate_valid_cpf,
)


class TestUserFactory:
    """Test the User factory."""

    def test_creates_valid_user(self) -> None:
        """Test that UserFactory creates a valid User instance."""
        user = UserFactory.build()

        assert isinstance(user, User)
        assert isinstance(user.user_id, UUID)
        assert "@" in user.email
        assert user.role in [UserRole.USER, UserRole.ADMIN, UserRole.SYSADMIN]
        assert isinstance(user.is_active, bool)
        assert isinstance(user.totp_enabled, bool)
        assert isinstance(user.created_at, datetime)
        assert user.password_hash.startswith("$2b$")
        assert len(user.password_hash) >= 60

    def test_admin_users_have_totp_enabled(self) -> None:
        """Test that admin users automatically get TOTP enabled."""
        admin_user = AdminUserFactory.build()
        sysadmin_user = SysAdminUserFactory.build()

        assert admin_user.role == UserRole.ADMIN
        assert admin_user.totp_enabled is True
        assert admin_user.totp_secret is not None
        assert len(admin_user.totp_secret) == 32

        assert sysadmin_user.role == UserRole.SYSADMIN
        assert sysadmin_user.totp_enabled is True
        assert sysadmin_user.totp_secret is not None

    def test_creates_multiple_unique_users(self) -> None:
        """Test that multiple users have unique data."""
        users = [UserFactory.build() for _ in range(5)]

        emails = [user.email for user in users]
        user_ids = [user.user_id for user in users]

        assert len(set(emails)) == 5  # All emails unique
        assert len(set(user_ids)) == 5  # All IDs unique


class TestClientFactory:
    """Test the Client factory."""

    def test_creates_valid_client(self) -> None:
        """Test that ClientFactory creates a valid Client instance."""
        client = ClientFactory.build()

        assert isinstance(client, Client)
        assert isinstance(client.client_id, UUID)
        assert len(client.full_name) >= 2
        assert len(client.cpf) == 14  # XXX.XXX.XXX-XX format
        assert "." in client.cpf
        assert "-" in client.cpf
        assert isinstance(client.birth_date, date)
        assert client.status in [ClientStatus.ACTIVE, ClientStatus.INACTIVE, ClientStatus.ARCHIVED]
        assert isinstance(client.created_by, UUID)
        assert isinstance(client.updated_by, UUID)

    def test_cpf_format_is_valid(self) -> None:
        """Test that generated CPFs follow the correct format."""
        for _ in range(10):
            client = ClientFactory.build()
            # CPF format: XXX.XXX.XXX-XX
            assert len(client.cpf) == 14
            assert client.cpf[3] == "."
            assert client.cpf[7] == "."
            assert client.cpf[11] == "-"

            # Extract parts for validation
            digits = client.cpf.replace(".", "").replace("-", "")
            assert len(digits) == 11
            assert digits.isdigit()

            # Should not be all same digits (basic invalid CPF check)
            assert not all(d == digits[0] for d in digits)

    def test_inactive_client_has_notes(self) -> None:
        """Test that inactive clients get explanatory notes."""
        inactive_client = InactiveClientFactory.build()

        assert inactive_client.status == ClientStatus.INACTIVE
        assert inactive_client.notes
        assert "inactive" in inactive_client.notes.lower()

    def test_birth_date_is_reasonable(self) -> None:
        """Test that birth dates are within reasonable range."""
        client = ClientFactory.build()
        today = date.today()

        # Calculate more accurate age
        age = today.year - client.birth_date.year
        if today.month < client.birth_date.month or (
            today.month == client.birth_date.month and today.day < client.birth_date.day
        ):
            age -= 1

        assert 18 <= age <= 95  # Allow slightly wider range


class TestAuditLogFactory:
    """Test the AuditLog factory."""

    def test_creates_valid_audit_log(self) -> None:
        """Test that AuditLogFactory creates a valid AuditLog instance."""
        audit_log = AuditLogFactory.build()

        assert isinstance(audit_log, AuditLog)
        assert isinstance(audit_log.audit_id, UUID)
        assert audit_log.table_name in ["users", "agent1_clients"]
        assert isinstance(audit_log.record_id, str)
        assert audit_log.action in [
            AuditAction.CREATE,
            AuditAction.UPDATE,
            AuditAction.DELETE,
            AuditAction.VIEW,
        ]
        assert isinstance(audit_log.user_id, UUID)
        assert "." in audit_log.ip_address  # Basic IP format check
        assert len(audit_log.user_agent) > 0
        assert isinstance(audit_log.timestamp, datetime)

    def test_update_actions_have_old_values(self) -> None:
        """Test that UPDATE and DELETE actions get old_values set."""
        update_log = AuditLogFactory.build(action=AuditAction.UPDATE)
        delete_log = AuditLogFactory.build(action=AuditAction.DELETE)

        assert update_log.old_values is not None
        assert delete_log.old_values is not None
        assert isinstance(update_log.old_values, dict)
        assert isinstance(delete_log.old_values, dict)

    def test_audit_values_match_table(self) -> None:
        """Test that audit values are appropriate for the table."""
        user_audit = AuditLogFactory.build(table_name="users")
        client_audit = AuditLogFactory.build(table_name="agent1_clients")

        if user_audit.new_values:
            assert "email" in user_audit.new_values
            assert "role" in user_audit.new_values

        if client_audit.new_values:
            assert "full_name" in client_audit.new_values
            assert "cpf" in client_audit.new_values


class TestUtilityFunctions:
    """Test utility functions."""

    def test_generate_valid_cpf(self) -> None:
        """Test CPF generation utility."""
        for _ in range(20):
            cpf = generate_valid_cpf()

            # Check CPF format XXX.XXX.XXX-XX
            assert len(cpf) == 14
            assert cpf[3] == "."
            assert cpf[7] == "."
            assert cpf[11] == "-"

            # Extract digits and validate
            digits = cpf.replace(".", "").replace("-", "")
            assert len(digits) == 11
            assert digits.isdigit()

            # Should not be all same digits
            assert not all(d == digits[0] for d in digits)

    def test_generate_audit_values(self) -> None:
        """Test audit values generation."""
        user_values = generate_audit_values("users", AuditAction.CREATE)
        client_values = generate_audit_values("agent1_clients", AuditAction.CREATE)

        assert "user_id" in user_values
        assert "email" in user_values
        assert "role" in user_values

        assert "client_id" in client_values
        assert "full_name" in client_values
        assert "cpf" in client_values

    def test_create_test_user_with_role(self) -> None:
        """Test create_test_user function."""
        admin = create_test_user(role=UserRole.ADMIN)
        user = create_test_user(role=UserRole.USER)
        sysadmin = create_test_user(role=UserRole.SYSADMIN)

        assert admin.role == UserRole.ADMIN
        assert admin.totp_enabled is True

        assert user.role == UserRole.USER

        assert sysadmin.role == UserRole.SYSADMIN
        assert sysadmin.totp_enabled is True

    def test_create_test_client_with_status(self) -> None:
        """Test create_test_client function."""
        active_client = create_test_client(status=ClientStatus.ACTIVE)
        inactive_client = create_test_client(status=ClientStatus.INACTIVE)

        assert active_client.status == ClientStatus.ACTIVE
        assert inactive_client.status == ClientStatus.INACTIVE
        assert inactive_client.notes
        assert "inactive" in inactive_client.notes.lower()

    def test_create_user_with_clients(self) -> None:
        """Test creating user with associated clients."""
        user, clients = create_user_with_clients(client_count=3)

        assert isinstance(user, User)
        assert user.role == UserRole.ADMIN
        assert len(clients) == 3

        for client in clients:
            assert isinstance(client, Client)
            assert client.created_by == user.user_id
            assert client.updated_by == user.user_id

    def test_create_complete_audit_trail(self) -> None:
        """Test creating complete audit trail."""
        record_id = "test-record-123"
        audit_logs = create_complete_audit_trail(record_id=record_id)

        assert len(audit_logs) == 3

        create_log, update_log, view_log = audit_logs

        assert create_log.action == AuditAction.CREATE
        assert create_log.record_id == record_id
        assert create_log.old_values is None

        assert update_log.action == AuditAction.UPDATE
        assert update_log.record_id == record_id
        assert update_log.old_values is not None

        assert view_log.action == AuditAction.VIEW
        assert view_log.record_id == record_id
        assert view_log.old_values is None
        assert view_log.new_values is None

        # Check timestamps are in order
        assert create_log.timestamp <= update_log.timestamp <= view_log.timestamp


class TestSeededData:
    """Test seeded data functions."""

    def test_seed_users_creates_all_roles(self) -> None:
        """Test that seed users include all roles."""
        seed_users = create_seed_users()
        roles = [user.role for user in seed_users]

        assert UserRole.SYSADMIN in roles
        assert UserRole.ADMIN in roles
        assert UserRole.USER in roles

        # Check specific seed users
        sysadmin = next(user for user in seed_users if user.email == "sysadmin@company.com")
        admin = next(user for user in seed_users if user.email == "admin@company.com")

        assert sysadmin.role == UserRole.SYSADMIN
        assert sysadmin.totp_enabled is True

        assert admin.role == UserRole.ADMIN
        assert admin.totp_enabled is True

    def test_seed_clients_creates_various_statuses(self) -> None:
        """Test that seed clients include different statuses."""
        admin_id = uuid4()
        seed_clients = create_seed_clients(admin_id)
        statuses = [client.status for client in seed_clients]

        assert ClientStatus.ACTIVE in statuses
        assert ClientStatus.INACTIVE in statuses

        # All clients should be created by the admin
        for client in seed_clients:
            assert client.created_by == admin_id
            assert client.updated_by == admin_id


# Integration tests that verify factory data passes model validation


class TestFactoryDataValidation:
    """Test that factory-generated data passes model validation."""

    def test_user_factory_data_is_valid(self) -> None:
        """Test that User factory data passes all validators."""
        # Test different user types
        regular_user = UserFactory.build()
        admin_user = AdminUserFactory.build()
        sysadmin_user = SysAdminUserFactory.build()

        # These should not raise validation errors when the models validate them
        users = [regular_user, admin_user, sysadmin_user]

        for user in users:
            # Validate email format
            assert "@" in user.email
            assert "." in user.email

            # Validate password hash format
            assert user.password_hash.startswith("$2b$")

            # Validate TOTP secret format for enabled users
            if user.totp_enabled and user.totp_secret:
                assert len(user.totp_secret) == 32
                assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567" for c in user.totp_secret)

    def test_client_factory_data_is_valid(self) -> None:
        """Test that Client factory data passes all validators."""
        # Test different client types
        active_client = ClientFactory.build()
        inactive_client = InactiveClientFactory.build()
        recent_client = RecentClientFactory.build()

        clients = [active_client, inactive_client, recent_client]

        for client in clients:
            # Validate full name
            assert len(client.full_name.strip()) >= 2

            # Validate CPF format
            assert len(client.cpf) == 14  # XXX.XXX.XXX-XX
            assert client.cpf[3] == "."
            assert client.cpf[7] == "."
            assert client.cpf[11] == "-"

            # Extract digits
            digits = client.cpf.replace(".", "").replace("-", "")
            assert len(digits) == 11
            assert digits.isdigit()
            assert not all(d == digits[0] for d in digits)  # Not all same digits

            # Validate birth date
            today = date.today()
            min_date = date(1900, 1, 1)
            max_date = date(today.year - 13, today.month, today.day)
            assert min_date <= client.birth_date <= max_date

    def test_audit_log_factory_data_is_valid(self) -> None:
        """Test that AuditLog factory data passes all validators."""
        # Test different audit log types
        create_audit = AuditLogFactory.build(action=AuditAction.CREATE)
        update_audit = AuditLogFactory.build(action=AuditAction.UPDATE)
        view_audit = AuditLogFactory.build(action=AuditAction.VIEW)

        audit_logs = [create_audit, update_audit, view_audit]

        for audit_log in audit_logs:
            # Validate table name format
            assert audit_log.table_name.islower()
            assert (
                "_" not in audit_log.table_name
                or audit_log.table_name.replace("_", "").replace("1", "").isalpha()
            )

            # Validate IP address format
            ip_parts = audit_log.ip_address.split(".")
            assert len(ip_parts) == 4
            for part in ip_parts:
                assert 0 <= int(part) <= 255

            # Validate JSON serializable values
            if audit_log.old_values:
                json.dumps(audit_log.old_values)  # Should not raise exception

            if audit_log.new_values:
                json.dumps(audit_log.new_values)  # Should not raise exception
