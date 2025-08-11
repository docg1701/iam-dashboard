# Test Data Factories

This directory contains factory classes for generating realistic test data for all models in the IAM Dashboard application.

## Overview

The factories follow the Factory Pattern to create test instances with sensible defaults while allowing customization of specific fields. This ensures consistent, realistic test data generation across unit tests, integration tests, and development seeding.

## Factory Classes

### BaseFactory (`base_factory.py`)
Common utilities and helper methods used by all factories:
- UUID generation
- Email generation  
- Brazilian name generation
- Valid CPF generation
- Date/time generation
- IP address and user agent generation
- Random data generation utilities

### UserFactory (`user_factory.py`)
Creates User model instances with authentication support:

```python
from factories import UserFactory

# Basic user creation
user = UserFactory.create_user()

# Specific role users
sysadmin = UserFactory.create_sysadmin()
admin = UserFactory.create_admin() 
regular_user = UserFactory.create_regular_user()

# Users with special features
user_with_2fa = UserFactory.create_user_with_2fa()
locked_user = UserFactory.create_locked_user()
inactive_user = UserFactory.create_inactive_user()

# Multiple users with distribution
users = UserFactory.create_multiple_users(
    count=10,
    role_distribution={
        UserRole.SYSADMIN: 0.1,
        UserRole.ADMIN: 0.2, 
        UserRole.USER: 0.7
    }
)
```

### ClientFactory (`client_factory.py`)
Creates Client model instances with valid CPF numbers:

```python
from factories import ClientFactory

# Basic client creation
client = ClientFactory.create_client()

# Age-specific clients
young_client = ClientFactory.create_young_adult_client()
middle_aged_client = ClientFactory.create_middle_aged_client()
senior_client = ClientFactory.create_senior_client()

# Batch creation with age distribution
clients = ClientFactory.create_client_batch(
    count=20,
    created_by=admin_user_id,
    age_distribution={
        'young': 0.3,
        'middle': 0.5, 
        'senior': 0.2
    }
)

# Clients for specific user
user_clients = ClientFactory.create_clients_for_user(
    user_id=user.id,
    count=5
)
```

### UserAgentPermissionFactory (`permission_factory.py`)
Creates permission instances for testing access control:

```python
from factories import UserAgentPermissionFactory
from models.permission import AgentName

# Basic permission creation
permission = UserAgentPermissionFactory.create_permission()

# Specific permission types
full_access = UserAgentPermissionFactory.create_full_access_permission(
    user_id=user.id,
    agent_name=AgentName.CLIENT_MANAGEMENT
)

read_only = UserAgentPermissionFactory.create_read_only_permission(
    user_id=user.id,
    agent_name=AgentName.PDF_PROCESSING
)

# All agents for a user
permissions = UserAgentPermissionFactory.create_agent_permissions_for_user(
    user_id=user.id,
    permission_type="full"  # "full", "read_write", "read_only"
)

# Permission scenarios for testing
scenarios = UserAgentPermissionFactory.create_permission_scenarios()
```

### AuditLogFactory (`audit_factory.py`)
Creates audit log instances for compliance testing:

```python
from factories import AuditLogFactory
from models.audit import AuditAction

# Basic audit log
audit_log = AuditLogFactory.create_audit_log()

# Specific audit types
user_creation_audit = AuditLogFactory.create_user_creation_audit(
    actor_id=admin.id,
    user_id=new_user.id,
    user_email=new_user.email,
    user_role=new_user.role.value
)

login_audit = AuditLogFactory.create_login_audit(
    user_id=user.id,
    ip_address="192.168.1.100"
)

# Complete user session audit trail
session_logs = AuditLogFactory.create_audit_trail_for_user_session(
    user_id=user.id,
    session_duration_hours=2,
    actions_count=10
)

# Security-related audit logs
security_logs = AuditLogFactory.create_security_audit_logs()
```

## Usage in Tests

### Unit Tests
Use factories to create isolated test instances:

```python
def test_user_creation():
    user = UserFactory.create_user(email="test@example.com")
    assert user.email == "test@example.com"
    assert user.is_active is True

def test_client_cpf_validation():
    # Test with valid CPF
    client = ClientFactory.create_client(cpf="11144477735")
    assert client.cpf == "11144477735"
    
    # Test with invalid CPF
    with pytest.raises(ValueError):
        ClientFactory.create_client(cpf="invalid")
```

### Integration Tests
Create realistic data scenarios:

```python
def test_permission_system():
    # Create users
    admin = UserFactory.create_admin()
    user = UserFactory.create_regular_user()
    
    # Create permissions
    permission = UserAgentPermissionFactory.create_full_access_permission(
        user_id=user.id,
        agent_name=AgentName.CLIENT_MANAGEMENT,
        granted_by=admin.id
    )
    
    # Create clients
    clients = ClientFactory.create_clients_for_user(
        user_id=user.id,
        count=3
    )
    
    # Test business logic
    assert permission.has_full_access
    assert len(clients) == 3
```

## Seeding Development Data

The `seed_data.py` script uses all factories to create a complete development dataset:

```bash
# Run the seeding script
cd apps/api
uv run python scripts/seed_data.py

# Or use the convenience script
./scripts/run_seed.sh
```

This creates:
- System users (sysadmin, admin, regular users)
- Sample clients with realistic data
- Permission scenarios for all agent types
- Audit logs for compliance testing

## Best Practices

1. **Use Default Values**: Factories provide sensible defaults, only override what's specific to your test
2. **Realistic Data**: Use factory-generated data instead of hardcoded values for more realistic tests
3. **Consistent Patterns**: Follow the same patterns when extending factories
4. **Mock External Dependencies**: Factories create data, but don't mock business logic (per CLAUDE.md guidelines)

## Extending Factories

When adding new models, create corresponding factories:

1. Create a new factory file in this directory
2. Inherit from `BaseFactory`
3. Implement `create_*` class methods
4. Add factory to `__init__.py`
5. Update documentation

Example:
```python
class NewModelFactory(BaseFactory):
    @classmethod
    def create_new_model(cls, **kwargs):
        # Implementation
        pass
```

## Testing Factory Classes

Factory classes themselves should be tested to ensure they generate valid data:

```python
def test_user_factory_creates_valid_users():
    user = UserFactory.create_user()
    assert user.id is not None
    assert "@" in user.email
    assert user.password_hash
    assert user.role in UserRole
```

---

These factories provide a solid foundation for test data generation while following the project's testing strategy and architectural guidelines.