# Model Unit Tests

Comprehensive unit tests for all SQLModel classes in the IAM Dashboard application.

## Overview

This directory contains unit tests that validate model behavior, validation rules, relationships, and factory patterns. Tests follow the project's testing strategy by focusing on model logic without mocking internal business behavior.

## Test Structure

### Test Files

- **`test_user.py`** - Tests for User model and UserRole enum
- **`test_client.py`** - Tests for Client model with CPF and birth date validation  
- **`test_permission.py`** - Tests for UserAgentPermission model and AgentName enum
- **`test_audit.py`** - Tests for AuditLog model and AuditAction enum
- **`conftest.py`** - Test configuration and fixtures
- **`README.md`** - This documentation file

### Test Categories

Each test file is organized into logical test classes:

#### User Model Tests (`test_user.py`)
- `TestUserModel` - Basic user creation and field validation
- `TestUserValidation` - Required fields and constraint validation
- `TestUserRoleEnum` - UserRole enumeration behavior

#### Client Model Tests (`test_client.py`)
- `TestClientModel` - Basic client creation and field validation
- `TestClientCPFValidation` - CPF number validation and formatting
- `TestClientBirthDateValidation` - Birth date range and age validation
- `TestClientNameValidation` - Name length and format validation
- `TestClientRequiredFields` - Required field enforcement

#### Permission Model Tests (`test_permission.py`)
- `TestUserAgentPermissionModel` - Permission creation and CRUD flags
- `TestUserAgentPermissionProperties` - Property methods (`has_any_permission`, `is_valid`, etc.)
- `TestUserAgentPermissionRepr` - String representation
- `TestAgentNameEnum` - AgentName enumeration behavior
- `TestUserAgentPermissionValidation` - Required fields and defaults

#### Audit Log Tests (`test_audit.py`)
- `TestAuditLogModel` - Basic audit log creation and tracking
- `TestAuditLogFactoryMethod` - Built-in factory method testing
- `TestAuditLogRepr` - String representation
- `TestAuditActionEnum` - AuditAction enumeration behavior
- `TestAuditLogValidation` - Required fields and JSON field handling

## Running Tests

### All Model Tests
```bash
# From API directory
cd apps/api
uv run pytest tests/test_models/ -v
```

### Specific Test Files
```bash
# User model tests
uv run pytest tests/test_models/test_user.py -v

# Client model tests  
uv run pytest tests/test_models/test_client.py -v

# Permission model tests
uv run pytest tests/test_models/test_permission.py -v

# Audit model tests
uv run pytest tests/test_models/test_audit.py -v
```

### Test Categories with Markers
```bash
# Unit tests only (fast)
uv run pytest tests/test_models/ -m unit -v

# Model validation tests
uv run pytest tests/test_models/ -m validation -v

# Factory-related tests
uv run pytest tests/test_models/ -m factory -v
```

### Coverage Report
```bash
# Generate coverage report for models
uv run pytest tests/test_models/ --cov=src.models --cov-report=html --cov-report=term-missing
```

## Test Patterns

### Factory Usage
All tests use factory classes for creating test data:

```python
def test_user_creation():
    # Use factory for realistic test data
    user = UserFactory.create_user(email="test@example.com")
    assert user.email == "test@example.com"
```

### Validation Testing
Tests thoroughly cover model validation:

```python
def test_cpf_validation():
    # Test valid CPF
    client = ClientFactory.create_client(cpf="11144477735")
    assert client.cpf == "11144477735"
    
    # Test invalid CPF
    with pytest.raises(ValidationError):
        ClientFactory.create_client(cpf="invalid")
```

### Enum Testing
Comprehensive enum behavior validation:

```python
def test_user_role_values():
    assert UserRole.SYSADMIN.value == "sysadmin"
    assert UserRole.ADMIN.value == "admin"
    assert UserRole.USER.value == "user"
```

### Property Testing
Model property methods are thoroughly tested:

```python
def test_permission_properties():
    permission = UserAgentPermissionFactory.create_full_access_permission()
    assert permission.has_full_access is True
    assert permission.has_any_permission is True
    assert permission.is_valid is True
```

## Test Data Management

### Factories vs Direct Creation
- **Use factories** for most tests to get realistic data
- **Use direct model creation** only when testing specific validation edge cases
- **Never mock** internal model behavior (per CLAUDE.md guidelines)

### Test Isolation
- Each test is independent and uses fresh data
- Factory-generated data includes randomization for uniqueness
- No shared state between tests

### Performance Considerations
- Unit tests focus on model logic and validation
- No database connections in pure unit tests
- Fast execution for developer feedback

## Coverage Requirements

Model tests must achieve:
- **100% line coverage** for model classes
- **100% branch coverage** for validation logic
- **Complete enum coverage** for all enum values
- **Property method coverage** for all custom properties

### Current Coverage Areas

#### User Model ✅
- ✅ User creation with all role types
- ✅ Authentication field validation
- ✅ 2FA support testing
- ✅ Account locking mechanisms
- ✅ UserRole enumeration behavior
- ✅ String representation

#### Client Model ✅
- ✅ Client creation with age distributions
- ✅ CPF validation (format, length, invalid patterns)
- ✅ Birth date validation (age ranges, future dates)
- ✅ Name length validation
- ✅ Brazilian data generation
- ✅ String representation with masked CPF

#### Permission Model ✅
- ✅ CRUD permission combinations
- ✅ Agent type coverage
- ✅ Permission expiration logic
- ✅ Property methods (has_any_permission, has_full_access, is_valid, is_expired)
- ✅ AgentName enumeration behavior
- ✅ Permission scenarios and matrices

#### Audit Log Model ✅
- ✅ All audit action types
- ✅ Resource tracking
- ✅ JSON field handling (old_values, new_values, additional_data)
- ✅ Session tracking (IP, user agent, session ID)
- ✅ Built-in factory method
- ✅ Security audit scenarios
- ✅ Complete user session trails

## Best Practices

### Test Naming
- Use descriptive test names that explain the scenario
- Group related tests in classes with clear names
- Use consistent naming patterns

### Assertions
- Test both positive and negative cases
- Verify all relevant fields, not just the primary field
- Use appropriate assertion methods

### Error Testing
- Test all validation scenarios that should raise exceptions
- Verify error messages are appropriate
- Test edge cases and boundary conditions

### Factory Integration
- Prefer factory methods over manual data creation
- Use factory scenarios for complex test setups
- Leverage factory randomization for uniqueness

## Debugging Tests

### Verbose Output
```bash
# Run with detailed output
uv run pytest tests/test_models/ -v -s
```

### Failed Test Details
```bash
# Show full diff on failures
uv run pytest tests/test_models/ --tb=long
```

### Specific Test Debugging
```bash
# Run single test with debugging
uv run pytest tests/test_models/test_user.py::TestUserModel::test_user_creation_with_defaults -v -s
```

---

These model tests provide comprehensive coverage of all SQLModel behavior while following the project's testing strategy and architectural guidelines.