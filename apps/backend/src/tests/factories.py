"""Test data factories for creating realistic test data."""

from datetime import timedelta
from typing import Any
from uuid import UUID

import factory
from factory import Faker, LazyAttribute
from faker import Faker as FakerInstance

from ..models.audit import AuditAction, AuditLog
from ..models.client import Client, ClientStatus
from ..models.user import User, UserRole

fake = FakerInstance()


class UserFactory(factory.Factory):
    """Factory for creating User instances with realistic data."""

    class Meta:
        model = User

    # Basic user fields
    email = Faker("email")
    role = factory.Iterator([UserRole.USER, UserRole.ADMIN, UserRole.SYSADMIN])
    is_active = True
    totp_enabled = False
    last_login = None

    # Timestamps
    created_at = Faker("date_time_this_year")
    updated_at = LazyAttribute(lambda obj: obj.created_at + timedelta(days=fake.random_int(0, 30)))

    # Authentication fields
    password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewfBNgCI.BZGV/Y6"  # "password"
    totp_secret = None

    @factory.post_generation
    def enable_totp_for_admins(obj, _create, _extracted, **_kwargs):
        """Enable TOTP for admin and sysadmin users."""
        if obj.role in [UserRole.ADMIN, UserRole.SYSADMIN]:
            obj.totp_enabled = True
            obj.totp_secret = fake.lexify(text="?" * 32, letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ234567")


class ClientFactory(factory.Factory):
    """Factory for creating Client instances with realistic data."""

    class Meta:
        model = Client

    # Client basic fields
    full_name = Faker("name")
    ssn = LazyAttribute(lambda _: generate_valid_ssn())
    birth_date = Faker("date_of_birth", minimum_age=18, maximum_age=90)
    status = factory.Iterator([ClientStatus.ACTIVE, ClientStatus.INACTIVE])
    notes = Faker("text", max_nb_chars=200)

    # Timestamps
    created_at = Faker("date_time_this_year")
    updated_at = LazyAttribute(lambda obj: obj.created_at + timedelta(days=fake.random_int(0, 15)))

    # Foreign key relationships (will be set via SubFactory when needed)
    created_by = factory.LazyFunction(lambda: UUID(fake.uuid4()))
    updated_by = LazyAttribute(lambda obj: obj.created_by)

    @factory.post_generation
    def set_notes_for_inactive(obj, _create, _extracted, **_kwargs):
        """Add explanatory notes for inactive clients."""
        if obj.status == ClientStatus.INACTIVE:
            obj.notes = f"Client marked inactive. {obj.notes or 'No additional notes.'}"


class AuditLogFactory(factory.Factory):
    """Factory for creating AuditLog instances with realistic data."""

    class Meta:
        model = AuditLog

    # Audit log fields
    table_name = factory.Iterator(["users", "agent1_clients"])
    record_id = factory.LazyFunction(lambda: str(fake.uuid4()))
    action = factory.Iterator([AuditAction.CREATE, AuditAction.UPDATE, AuditAction.VIEW])

    # Audit data
    old_values = None
    new_values = LazyAttribute(lambda obj: generate_audit_values(obj.table_name, obj.action))

    # User and session tracking
    user_id = factory.LazyFunction(lambda: UUID(fake.uuid4()))
    ip_address = Faker("ipv4")
    user_agent = Faker("user_agent")

    # Timestamps
    timestamp = Faker("date_time_this_year")
    created_at = LazyAttribute(lambda obj: obj.timestamp)
    updated_at = None

    @factory.post_generation
    def set_old_values_for_updates(obj, _create, _extracted, **_kwargs):
        """Set old_values for UPDATE and DELETE actions."""
        if obj.action in [AuditAction.UPDATE, AuditAction.DELETE]:
            obj.old_values = generate_audit_values(obj.table_name, AuditAction.CREATE)


class AdminUserFactory(UserFactory):
    """Factory for creating admin users specifically."""

    role = UserRole.ADMIN
    is_active = True
    totp_enabled = True
    totp_secret = factory.LazyFunction(
        lambda: fake.lexify(text="?" * 32, letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ234567")
    )
    last_login = Faker("date_time_this_month")


class SysAdminUserFactory(UserFactory):
    """Factory for creating system administrator users."""

    role = UserRole.SYSADMIN
    is_active = True
    totp_enabled = True
    totp_secret = factory.LazyFunction(
        lambda: fake.lexify(text="?" * 32, letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ234567")
    )
    last_login = Faker("date_time_this_month")
    email = factory.LazyFunction(lambda: f"sysadmin.{fake.user_name()}@company.com")


class InactiveClientFactory(ClientFactory):
    """Factory for creating inactive clients."""

    status = ClientStatus.INACTIVE
    notes = "Client account deactivated per client request"
    updated_at = Faker("date_time_this_month")


class RecentClientFactory(ClientFactory):
    """Factory for creating recently added clients."""

    created_at = Faker("date_time_this_month")
    updated_at = LazyAttribute(lambda obj: obj.created_at + timedelta(hours=fake.random_int(1, 48)))
    status = ClientStatus.ACTIVE


def generate_valid_ssn() -> str:
    """Generate a valid SSN format that passes validation."""
    # Generate valid area number (001-899, excluding 666)
    area = fake.random_int(1, 899)
    if area == 666:
        area = 667

    # Generate valid group number (01-99)
    group = fake.random_int(1, 99)

    # Generate valid serial number (0001-9999)
    serial = fake.random_int(1, 9999)

    return f"{area:03d}-{group:02d}-{serial:04d}"


def generate_audit_values(table_name: str, action: AuditAction) -> dict[str, Any]:
    """Generate realistic audit values based on table and action."""
    if table_name == "users":
        return {
            "user_id": str(fake.uuid4()),
            "email": fake.email(),
            "role": fake.random_element(["USER", "ADMIN", "SYSADMIN"]),
            "is_active": fake.boolean(),
            "totp_enabled": fake.boolean(),
            "created_at": fake.date_time_this_year().isoformat(),
        }
    elif table_name == "agent1_clients":
        return {
            "client_id": str(fake.uuid4()),
            "full_name": fake.name(),
            "ssn": generate_valid_ssn(),
            "birth_date": fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat(),
            "status": fake.random_element(["ACTIVE", "INACTIVE", "ARCHIVED"]),
            "created_by": str(fake.uuid4()),
            "created_at": fake.date_time_this_year().isoformat(),
        }
    else:
        return {
            "id": str(fake.uuid4()),
            "created_at": fake.date_time_this_year().isoformat(),
        }


# Convenience functions for creating test data

def create_test_user(role: UserRole = UserRole.USER, **kwargs) -> User:
    """Create a test user with specified role."""
    factory_class = {
        UserRole.USER: UserFactory,
        UserRole.ADMIN: AdminUserFactory,
        UserRole.SYSADMIN: SysAdminUserFactory,
    }.get(role, UserFactory)

    return factory_class(**kwargs)


def create_test_client(status: ClientStatus = ClientStatus.ACTIVE, **kwargs) -> Client:
    """Create a test client with specified status."""
    factory_class = {
        ClientStatus.ACTIVE: ClientFactory,
        ClientStatus.INACTIVE: InactiveClientFactory,
    }.get(status, ClientFactory)

    return factory_class(**kwargs)


def create_test_audit_log(table_name: str = "users", action: AuditAction = AuditAction.CREATE, **kwargs) -> AuditLog:
    """Create a test audit log for specified table and action."""
    return AuditLogFactory(table_name=table_name, action=action, **kwargs)


def create_user_with_clients(client_count: int = 3) -> tuple[User, list[Client]]:
    """Create a user and associated clients for testing relationships."""
    user = create_test_user(role=UserRole.ADMIN)
    clients = []

    for _ in range(client_count):
        client = create_test_client(
            created_by=user.user_id,
            updated_by=user.user_id
        )
        clients.append(client)

    return user, clients


def create_complete_audit_trail(table_name: str = "agent1_clients", record_id: str = None) -> list[AuditLog]:
    """Create a complete audit trail for a record (CREATE -> UPDATE -> VIEW)."""
    if not record_id:
        record_id = str(fake.uuid4())

    user_id = UUID(fake.uuid4())
    base_time = fake.date_time_this_month()

    audit_logs = [
        # CREATE action
        create_test_audit_log(
            table_name=table_name,
            record_id=record_id,
            action=AuditAction.CREATE,
            user_id=user_id,
            timestamp=base_time,
            old_values=None
        ),
        # UPDATE action
        create_test_audit_log(
            table_name=table_name,
            record_id=record_id,
            action=AuditAction.UPDATE,
            user_id=user_id,
            timestamp=base_time + timedelta(days=1)
        ),
        # VIEW action
        create_test_audit_log(
            table_name=table_name,
            record_id=record_id,
            action=AuditAction.VIEW,
            user_id=user_id,
            timestamp=base_time + timedelta(days=2),
            old_values=None,
            new_values=None
        ),
    ]

    return audit_logs


# Seed data functions for development environment

def create_seed_users() -> list[User]:
    """Create seed users for development environment."""
    users = [
        # System administrator
        create_test_user(
            role=UserRole.SYSADMIN,
            email="sysadmin@company.com",
            is_active=True,
            totp_enabled=True
        ),
        # Regular admin
        create_test_user(
            role=UserRole.ADMIN,
            email="admin@company.com",
            is_active=True,
            totp_enabled=True
        ),
        # Regular users
        create_test_user(
            role=UserRole.USER,
            email="user1@company.com",
            is_active=True
        ),
        create_test_user(
            role=UserRole.USER,
            email="user2@company.com",
            is_active=True
        ),
        # Inactive user
        create_test_user(
            role=UserRole.USER,
            email="inactive@company.com",
            is_active=False
        ),
    ]

    return users


def create_seed_clients(admin_user_id: UUID) -> list[Client]:
    """Create seed clients for development environment."""
    clients = [
        # Active clients
        create_test_client(
            full_name="John Doe",
            status=ClientStatus.ACTIVE,
            created_by=admin_user_id,
            updated_by=admin_user_id,
            notes="Initial client for testing"
        ),
        create_test_client(
            full_name="Jane Smith",
            status=ClientStatus.ACTIVE,
            created_by=admin_user_id,
            updated_by=admin_user_id
        ),
        create_test_client(
            full_name="Bob Johnson",
            status=ClientStatus.ACTIVE,
            created_by=admin_user_id,
            updated_by=admin_user_id
        ),
        # Inactive client
        create_test_client(
            full_name="Alice Brown",
            status=ClientStatus.INACTIVE,
            created_by=admin_user_id,
            updated_by=admin_user_id,
            notes="Client requested account deactivation"
        ),
    ]

    return clients
