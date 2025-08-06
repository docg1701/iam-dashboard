"""Test data factories for creating realistic test data."""

from datetime import timedelta
from typing import Any, TypedDict
from uuid import UUID

import factory
from factory.faker import Faker
from faker import Faker as FakerInstance

from src.models.audit import AuditAction, AuditLog
from src.models.client import Client, ClientStatus
from src.models.permissions import (
    AgentName,
    PermissionAuditLog,
    PermissionTemplate,
    UserAgentPermission,
)
from src.models.user import User, UserRole

fake = FakerInstance()


class UserAuditValues(TypedDict):
    """Audit values structure for users table."""

    user_id: str
    email: str
    role: str
    is_active: bool
    totp_enabled: bool
    created_at: str


class ClientAuditValues(TypedDict):
    """Audit values structure for agent1_clients table."""

    client_id: str
    full_name: str
    ssn: str
    birth_date: str
    status: str
    created_by: str
    created_at: str


class GenericAuditValues(TypedDict):
    """Generic audit values structure for unknown tables."""

    id: str
    created_at: str


class UserFactory(factory.Factory):  # type: ignore[misc,name-defined]
    """Factory for creating User instances with realistic data."""

    class Meta:
        model = User

    # Basic user fields
    email = Faker("email")  # type: ignore[no-untyped-call]
    role = factory.Iterator([UserRole.USER, UserRole.ADMIN, UserRole.SYSADMIN])  # type: ignore[attr-defined,no-untyped-call]
    is_active = True
    totp_enabled = False
    last_login = None

    # Timestamps
    created_at = Faker("date_time_this_year")  # type: ignore[no-untyped-call]
    updated_at = factory.LazyAttribute(  # type: ignore[attr-defined,no-untyped-call]
        lambda obj: obj.created_at + timedelta(days=fake.random_int(0, 30))
    )

    # Authentication fields
    password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewfBNgCI.BZGV/Y6"  # "password"
    totp_secret = None

    @factory.post_generation  # type: ignore[attr-defined,misc]
    def enable_totp_for_admins(obj: Any, _create: bool, _extracted: Any, **_kwargs: Any) -> None:
        """Enable TOTP for admin and sysadmin users."""
        # Handle factory Iterator values safely
        role_val = obj.role.value if hasattr(obj.role, "value") else obj.role
        if role_val in [UserRole.ADMIN.value, UserRole.SYSADMIN.value]:
            obj.totp_enabled = True
            obj.totp_secret = fake.lexify(text="?" * 32, letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ234567")


class ClientFactory(factory.Factory):  # type: ignore[misc,name-defined]
    """Factory for creating Client instances with realistic data."""

    class Meta:
        model = Client

    # Client basic fields
    full_name = Faker("name")  # type: ignore[no-untyped-call]
    ssn = factory.LazyAttribute(lambda _: generate_valid_ssn())  # type: ignore[attr-defined,no-untyped-call]
    birth_date = Faker("date_of_birth", minimum_age=18, maximum_age=90)  # type: ignore[no-untyped-call]
    status = factory.Iterator([ClientStatus.ACTIVE, ClientStatus.INACTIVE])  # type: ignore[attr-defined,no-untyped-call]
    notes = Faker("text", max_nb_chars=200)  # type: ignore[no-untyped-call]

    # Timestamps
    created_at = Faker("date_time_this_year")  # type: ignore[no-untyped-call]
    updated_at = factory.LazyAttribute(  # type: ignore[attr-defined,no-untyped-call]
        lambda obj: obj.created_at + timedelta(days=fake.random_int(0, 15))
    )

    # Foreign key relationships (will be set via SubFactory when needed)
    created_by = factory.LazyFunction(lambda: UUID(fake.uuid4()))  # type: ignore[attr-defined,no-untyped-call]
    updated_by = factory.LazyAttribute(lambda obj: obj.created_by)  # type: ignore[attr-defined,no-untyped-call]

    @factory.post_generation  # type: ignore[attr-defined,misc]
    def set_notes_for_inactive(obj: Any, _create: bool, _extracted: Any, **_kwargs: Any) -> None:
        """Add explanatory notes for inactive clients."""
        # Cast to ClientStatus to avoid mypy iterator comparison issue
        status_val = obj.status.value if hasattr(obj.status, "value") else obj.status
        if status_val in {ClientStatus.INACTIVE.value, ClientStatus.INACTIVE}:
            current_notes = (
                obj.notes if hasattr(obj, "notes") and obj.notes else "No additional notes."
            )
            obj.notes = f"Client marked inactive. {current_notes}"


class AuditLogFactory(factory.Factory):  # type: ignore[misc,name-defined]
    """Factory for creating AuditLog instances with realistic data."""

    class Meta:
        model = AuditLog

    # Audit log fields
    table_name = factory.Iterator(["users", "agent1_clients"])  # type: ignore[attr-defined,no-untyped-call]
    record_id = factory.LazyFunction(lambda: str(fake.uuid4()))  # type: ignore[attr-defined,no-untyped-call]
    action = factory.Iterator([AuditAction.CREATE, AuditAction.UPDATE, AuditAction.VIEW])  # type: ignore[attr-defined,no-untyped-call]

    # Audit data
    old_values = None
    new_values = factory.LazyAttribute(  # type: ignore[attr-defined,no-untyped-call]
        lambda obj: generate_audit_values(obj.table_name, obj.action)
    )

    # User and session tracking
    user_id = factory.LazyFunction(lambda: UUID(fake.uuid4()))  # type: ignore[attr-defined,no-untyped-call]
    ip_address = Faker("ipv4")  # type: ignore[no-untyped-call]
    user_agent = Faker("user_agent")  # type: ignore[no-untyped-call]

    # Timestamps
    timestamp = Faker("date_time_this_year")  # type: ignore[no-untyped-call]
    created_at = factory.LazyAttribute(lambda obj: obj.timestamp)  # type: ignore[attr-defined,no-untyped-call]
    updated_at = None

    @factory.post_generation  # type: ignore[attr-defined,misc]
    def set_old_values_for_updates(
        obj: Any, _create: bool, _extracted: Any, **_kwargs: Any
    ) -> None:
        """Set old_values for UPDATE and DELETE actions."""
        # Convert factory Iterator to actual value for comparison
        action_val = obj.action.value if hasattr(obj.action, "value") else obj.action
        if action_val in [AuditAction.UPDATE.value, AuditAction.DELETE.value]:
            table_name = obj.table_name if isinstance(obj.table_name, str) else str(obj.table_name)
            obj.old_values = generate_audit_values(table_name, AuditAction.CREATE)


class AdminUserFactory(UserFactory):
    """Factory for creating admin users specifically."""

    role = factory.LazyFunction(lambda: UserRole.ADMIN)  # type: ignore[attr-defined,no-untyped-call,assignment]
    is_active = True
    totp_enabled = True
    totp_secret = factory.LazyFunction(  # type: ignore[attr-defined,no-untyped-call,assignment]
        lambda: fake.lexify(text="?" * 32, letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ234567")
    )
    last_login = factory.LazyFunction(lambda: fake.date_time_this_month())  # type: ignore[attr-defined,no-untyped-call,assignment]


class SysAdminUserFactory(UserFactory):
    """Factory for creating system administrator users."""

    role = factory.LazyFunction(lambda: UserRole.SYSADMIN)  # type: ignore[attr-defined,no-untyped-call,assignment]
    is_active = True
    totp_enabled = True
    totp_secret = factory.LazyFunction(  # type: ignore[attr-defined,no-untyped-call,assignment]
        lambda: fake.lexify(text="?" * 32, letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ234567")
    )
    last_login = factory.LazyFunction(lambda: fake.date_time_this_month())  # type: ignore[attr-defined,no-untyped-call,assignment]
    email = factory.LazyFunction(lambda: f"sysadmin.{fake.user_name()}@company.com")  # type: ignore[attr-defined,no-untyped-call,assignment]


class InactiveClientFactory(ClientFactory):
    """Factory for creating inactive clients."""

    status = factory.LazyFunction(lambda: ClientStatus.INACTIVE)  # type: ignore[attr-defined,no-untyped-call,assignment]
    notes = "Client account deactivated per client request"  # type: ignore[assignment]
    updated_at = Faker("date_time_this_month")  # type: ignore[no-untyped-call,assignment]


class RecentClientFactory(ClientFactory):
    """Factory for creating recently added clients."""

    created_at = Faker("date_time_this_month")  # type: ignore[no-untyped-call]
    updated_at = factory.LazyAttribute(  # type: ignore[attr-defined,no-untyped-call]
        lambda obj: obj.created_at + timedelta(hours=fake.random_int(1, 48))
    )
    status = ClientStatus.ACTIVE  # type: ignore[assignment]


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


def generate_audit_values(
    table_name: str, action: AuditAction
) -> UserAuditValues | ClientAuditValues | GenericAuditValues:
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


def create_test_user(role: UserRole = UserRole.USER, **kwargs: Any) -> User:
    """Create a test user with specified role."""
    factory_class = {
        UserRole.USER: UserFactory,
        UserRole.ADMIN: AdminUserFactory,
        UserRole.SYSADMIN: SysAdminUserFactory,
    }.get(role, UserFactory)

    return factory_class(**kwargs)


def create_test_client(status: ClientStatus = ClientStatus.ACTIVE, **kwargs: Any) -> Client:
    """Create a test client with specified status."""
    factory_class = {
        ClientStatus.ACTIVE: ClientFactory,
        ClientStatus.INACTIVE: InactiveClientFactory,
    }.get(status, ClientFactory)

    return factory_class(**kwargs)


def create_test_audit_log(
    table_name: str = "users", action: AuditAction = AuditAction.CREATE, **kwargs: Any
) -> AuditLog:
    """Create a test audit log for specified table and action."""
    return AuditLogFactory(table_name=table_name, action=action, **kwargs)


def create_user_with_clients(client_count: int = 3) -> tuple[User, list[Client]]:
    """Create a user and associated clients for testing relationships."""
    user = create_test_user(role=UserRole.ADMIN)
    clients = []

    for _ in range(client_count):
        client = create_test_client(created_by=user.user_id, updated_by=user.user_id)
        clients.append(client)

    return user, clients


def create_complete_audit_trail(
    table_name: str = "agent1_clients", record_id: str | None = None
) -> list[AuditLog]:
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
            old_values=None,
        ),
        # UPDATE action
        create_test_audit_log(
            table_name=table_name,
            record_id=record_id,
            action=AuditAction.UPDATE,
            user_id=user_id,
            timestamp=base_time + timedelta(days=1),
        ),
        # VIEW action
        create_test_audit_log(
            table_name=table_name,
            record_id=record_id,
            action=AuditAction.VIEW,
            user_id=user_id,
            timestamp=base_time + timedelta(days=2),
            old_values=None,
            new_values=None,
        ),
    ]

    return audit_logs


# Seed data functions for development environment


def create_seed_users() -> list[User]:
    """Create seed users for development environment."""
    users = [
        # System administrator
        create_test_user(
            role=UserRole.SYSADMIN, email="sysadmin@company.com", is_active=True, totp_enabled=True
        ),
        # Regular admin
        create_test_user(
            role=UserRole.ADMIN, email="admin@company.com", is_active=True, totp_enabled=True
        ),
        # Regular users
        create_test_user(role=UserRole.USER, email="user1@company.com", is_active=True),
        create_test_user(role=UserRole.USER, email="user2@company.com", is_active=True),
        # Inactive user
        create_test_user(role=UserRole.USER, email="inactive@company.com", is_active=False),
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
            notes="Initial client for testing",
        ),
        create_test_client(
            full_name="Jane Smith",
            status=ClientStatus.ACTIVE,
            created_by=admin_user_id,
            updated_by=admin_user_id,
        ),
        create_test_client(
            full_name="Bob Johnson",
            status=ClientStatus.ACTIVE,
            created_by=admin_user_id,
            updated_by=admin_user_id,
        ),
        # Inactive client
        create_test_client(
            full_name="Alice Brown",
            status=ClientStatus.INACTIVE,
            created_by=admin_user_id,
            updated_by=admin_user_id,
            notes="Client requested account deactivation",
        ),
    ]

    return clients


# Permission factories


class UserAgentPermissionFactory(factory.Factory):  # type: ignore[misc,name-defined]
    """Factory for creating UserAgentPermission instances."""

    class Meta:
        model = UserAgentPermission

    # Core fields
    user_id = factory.LazyFunction(lambda: UUID(fake.uuid4()))  # type: ignore[attr-defined,no-untyped-call]
    agent_name = factory.Iterator(  # type: ignore[attr-defined,no-untyped-call]
        [
            AgentName.CLIENT_MANAGEMENT,
            AgentName.PDF_PROCESSING,
            AgentName.REPORTS_ANALYSIS,
            AgentName.AUDIO_RECORDING,
        ]
    )
    permissions = factory.LazyAttribute(  # type: ignore[attr-defined,no-untyped-call]
        lambda obj: generate_agent_permissions(obj.agent_name)
    )

    # Audit fields
    created_by_user_id = factory.LazyFunction(lambda: UUID(fake.uuid4()))  # type: ignore[attr-defined,no-untyped-call]
    created_at = Faker("date_time_this_year")  # type: ignore[no-untyped-call]
    updated_at = None


class PermissionTemplateFactory(factory.Factory):  # type: ignore[misc,name-defined]
    """Factory for creating PermissionTemplate instances."""

    class Meta:
        model = PermissionTemplate

    # Core fields
    template_name = factory.LazyAttribute(lambda _: f"{fake.word().title()} Template")  # type: ignore[attr-defined,no-untyped-call]
    description = Faker("sentence")  # type: ignore[no-untyped-call]
    permissions = factory.LazyFunction(lambda: generate_template_permissions())  # type: ignore[attr-defined,no-untyped-call]

    # Metadata
    is_system_template = False
    created_by_user_id = factory.LazyFunction(lambda: UUID(fake.uuid4()))  # type: ignore[attr-defined,no-untyped-call]
    created_at = Faker("date_time_this_year")  # type: ignore[no-untyped-call]
    updated_at = None


class PermissionAuditLogFactory(factory.Factory):  # type: ignore[misc,name-defined]
    """Factory for creating PermissionAuditLog instances."""

    class Meta:
        model = PermissionAuditLog

    # Core fields
    user_id = factory.LazyFunction(lambda: UUID(fake.uuid4()))  # type: ignore[attr-defined,no-untyped-call]
    agent_name = factory.Iterator(  # type: ignore[attr-defined,no-untyped-call]
        [
            AgentName.CLIENT_MANAGEMENT,
            AgentName.PDF_PROCESSING,
            AgentName.REPORTS_ANALYSIS,
            AgentName.AUDIO_RECORDING,
        ]
    )
    action = factory.Iterator(["CREATE", "UPDATE", "DELETE", "BULK_CREATE", "BULK_UPDATE"])  # type: ignore[attr-defined,no-untyped-call]

    # Permission data
    old_permissions = None
    new_permissions = factory.LazyAttribute(  # type: ignore[attr-defined,no-untyped-call]
        lambda obj: generate_agent_permissions(obj.agent_name)
    )

    # Audit metadata
    changed_by_user_id = factory.LazyFunction(lambda: UUID(fake.uuid4()))  # type: ignore[attr-defined,no-untyped-call]
    change_reason = factory.Iterator(  # type: ignore[attr-defined,no-untyped-call]
        [
            "Initial permission assignment",
            "Role change update",
            "Security audit adjustment",
            "User request modification",
            None,
        ]
    )

    # Timestamps
    created_at = Faker("date_time_this_year")  # type: ignore[no-untyped-call]

    @factory.post_generation  # type: ignore[attr-defined,misc]
    def set_old_permissions_for_updates(
        obj: Any, _create: bool, _extracted: Any, **_kwargs: Any
    ) -> None:
        """Set old_permissions for UPDATE and DELETE actions if not explicitly provided."""
        action_val = obj.action if isinstance(obj.action, str) else obj.action
        if action_val in ["UPDATE", "DELETE", "BULK_UPDATE"] and obj.old_permissions is None:
            obj.old_permissions = generate_agent_permissions(obj.agent_name, minimal=True)


def generate_agent_permissions(agent_name: AgentName, minimal: bool = False) -> dict[str, bool]:
    """Generate realistic permission structure based on agent and role."""
    if minimal:
        # Minimal permissions for testing old_permissions
        return {
            "create": False,
            "read": True,
            "update": False,
            "delete": False,
        }

    # Generate varied permissions based on agent type
    if agent_name == AgentName.CLIENT_MANAGEMENT:
        return {
            "create": fake.boolean(chance_of_getting_true=80),
            "read": True,  # Almost always true for client management
            "update": fake.boolean(chance_of_getting_true=70),
            "delete": fake.boolean(chance_of_getting_true=30),
        }
    elif agent_name == AgentName.PDF_PROCESSING:
        return {
            "create": fake.boolean(chance_of_getting_true=60),
            "read": fake.boolean(chance_of_getting_true=90),
            "update": fake.boolean(chance_of_getting_true=40),
            "delete": fake.boolean(chance_of_getting_true=20),
        }
    elif agent_name == AgentName.REPORTS_ANALYSIS:
        return {
            "create": fake.boolean(chance_of_getting_true=70),
            "read": fake.boolean(chance_of_getting_true=95),
            "update": fake.boolean(chance_of_getting_true=50),
            "delete": fake.boolean(chance_of_getting_true=25),
        }
    else:  # AUDIO_RECORDING
        return {
            "create": fake.boolean(chance_of_getting_true=50),
            "read": fake.boolean(chance_of_getting_true=85),
            "update": fake.boolean(chance_of_getting_true=35),
            "delete": fake.boolean(chance_of_getting_true=15),
        }


def generate_template_permissions() -> dict[str, dict[str, bool]]:
    """Generate complete template permissions for all agents."""
    return {agent.value: generate_agent_permissions(agent) for agent in AgentName}


# System template factories


class SystemPermissionTemplateFactory(PermissionTemplateFactory):
    """Factory for system permission templates."""

    is_system_template = True
    template_name = factory.Iterator(  # type: ignore[attr-defined,assignment,no-untyped-call]
        [
            "Administrator Template",
            "Manager Template",
            "User Template",
            "Read-Only Template",
            "Agent Specialist Template",
        ]
    )
    description = factory.LazyAttribute(  # type: ignore[attr-defined,no-untyped-call,assignment]
        lambda obj: f"System template for {obj.template_name.lower()}"
    )


class FullAccessPermissionFactory(UserAgentPermissionFactory):
    """Factory for full access permissions."""

    permissions = {  # type: ignore[assignment]
        "create": True,
        "read": True,
        "update": True,
        "delete": True,
    }


class ReadOnlyPermissionFactory(UserAgentPermissionFactory):
    """Factory for read-only permissions."""

    permissions = {  # type: ignore[assignment]
        "create": False,
        "read": True,
        "update": False,
        "delete": False,
    }


class NoAccessPermissionFactory(UserAgentPermissionFactory):
    """Factory for no access permissions."""

    permissions = {  # type: ignore[assignment]
        "create": False,
        "read": False,
        "update": False,
        "delete": False,
    }


# Convenience functions for permission testing


def create_test_permission(
    user_id: UUID | None = None,
    agent_name: AgentName = AgentName.CLIENT_MANAGEMENT,
    permissions: dict[str, bool] | None = None,
    **kwargs: Any,
) -> UserAgentPermission:
    """Create a test permission with specified parameters."""
    data = {"agent_name": agent_name, **kwargs}

    if user_id:
        data["user_id"] = user_id
    if permissions:
        data["permissions"] = permissions

    return UserAgentPermissionFactory(**data)


def create_test_template(
    template_name: str | None = None,
    permissions: dict[str, dict[str, bool]] | None = None,
    is_system: bool = False,
    **kwargs: Any,
) -> PermissionTemplate:
    """Create a test permission template."""
    factory_class = SystemPermissionTemplateFactory if is_system else PermissionTemplateFactory
    data = kwargs

    if template_name:
        data["template_name"] = template_name
    if permissions:
        data["permissions"] = permissions

    return factory_class(**data)


def create_test_permission_audit_log(
    user_id: UUID | None = None,
    agent_name: AgentName = AgentName.CLIENT_MANAGEMENT,
    action: str = "CREATE",
    **kwargs: Any,
) -> PermissionAuditLog:
    """Create a test permission audit log."""
    data = {"agent_name": agent_name, "action": action, **kwargs}

    if user_id:
        data["user_id"] = user_id

    return PermissionAuditLogFactory(**data)


def create_user_with_permissions(
    user_role: UserRole = UserRole.ADMIN,
    agent_permissions: dict[AgentName, dict[str, bool]] | None = None,
) -> tuple[User, list[UserAgentPermission]]:
    """Create a user with specific agent permissions."""
    user = create_test_user(role=user_role)
    permissions = []

    if agent_permissions:
        for agent_name, perms in agent_permissions.items():
            permission = create_test_permission(
                user_id=user.user_id,
                agent_name=agent_name,
                permissions=perms,
                created_by_user_id=user.user_id,
            )
            permissions.append(permission)
    else:
        # Create default permissions for all agents
        for agent_name in AgentName:
            permission = create_test_permission(
                user_id=user.user_id,
                agent_name=agent_name,
                created_by_user_id=user.user_id,
            )
            permissions.append(permission)

    return user, permissions


def create_permission_audit_trail(
    user_id: UUID, agent_name: AgentName, changed_by_user_id: UUID | None = None
) -> list[PermissionAuditLog]:
    """Create a complete permission audit trail."""
    if not changed_by_user_id:
        changed_by_user_id = UUID(fake.uuid4())

    base_time = fake.date_time_this_month()

    logs = [
        # CREATE
        create_test_permission_audit_log(
            user_id=user_id,
            agent_name=agent_name,
            action="CREATE",
            changed_by_user_id=changed_by_user_id,
            created_at=base_time,
            old_permissions=None,
        ),
        # UPDATE
        create_test_permission_audit_log(
            user_id=user_id,
            agent_name=agent_name,
            action="UPDATE",
            changed_by_user_id=changed_by_user_id,
            created_at=base_time + timedelta(days=1),
        ),
        # DELETE
        create_test_permission_audit_log(
            user_id=user_id,
            agent_name=agent_name,
            action="DELETE",
            changed_by_user_id=changed_by_user_id,
            created_at=base_time + timedelta(days=2),
            new_permissions=None,
        ),
    ]

    return logs
