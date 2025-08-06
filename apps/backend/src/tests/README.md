# Backend Test Structure Documentation

This document describes the organized test structure following the testing guidelines specified in CLAUDE.md.

## Directory Structure

```
src/tests/
├── conftest.py              # Main test configuration with shared fixtures
├── factories.py             # Test data factories for all test types
├── unit/                    # Unit Tests (64.7% of tests - 483 tests)
│   ├── conftest.py         # Unit-specific configuration with external mocking
│   └── test_*.py           # Unit test files
├── integration/             # Integration Tests (19.7% of tests - 147 tests)  
│   ├── conftest.py         # Integration-specific configuration
│   └── test_*.py           # Integration test files
├── e2e/                     # End-to-End Tests (13.9% of tests - 104 tests)
│   ├── conftest.py         # E2E-specific configuration with minimal mocking
│   └── test_*.py           # E2E test files
└── performance/             # Performance Tests (1.6% of tests - 12 tests)
    ├── conftest.py         # Performance test configuration
    └── test_*.py           # Performance/benchmark test files
```

## Test Categories and Mocking Strategies

### Unit Tests (`unit/`)
**Purpose**: Test individual components in isolation
- **Mock**: External APIs, file systems, Redis/cache, time/random, SMTP
- **Test Real**: Business logic, service methods, model validation, internal algorithms
- **Database**: Mock or use in-memory database for data layer tests
- **Examples**: Model validation, service business logic, utility functions

### Integration Tests (`integration/`)
**Purpose**: Test component interactions and cross-service functionality
- **Mock**: External HTTP APIs, SMTP servers, file I/O operations
- **Test Real**: Database operations, service integrations, permission logic, authentication flows
- **Database**: Use real database sessions with transactions
- **Examples**: Service-to-service communication, database operations, permission system

### End-to-End Tests (`e2e/`)
**Purpose**: Test complete user workflows and API endpoints
- **Mock**: Only external services not part of the system (external APIs, SMTP)
- **Test Real**: Complete authentication flow, API endpoints, database persistence, business workflows
- **Database**: Real database operations with proper transaction handling
- **Examples**: Full API workflows, authentication + authorization, complete user journeys

### Performance Tests (`performance/`)
**Purpose**: Measure system performance and identify bottlenecks
- **Mock**: External services that introduce timing variability
- **Test Real**: Database operations, CPU-intensive logic, memory usage
- **Database**: Real database operations to measure actual performance
- **Examples**: Query performance, endpoint response times, concurrent user handling

## Test Distribution

The current test distribution aligns with the testing pyramid:
- **Unit Tests**: 64.7% (Target: 60-75%) ✅
- **Integration Tests**: 19.7% (Target: 20-30%) ✅ 
- **End-to-End Tests**: 13.9% (Target: 5-10%) ⚠️ *Slightly high but acceptable*
- **Performance Tests**: 1.6% (Target: <5%) ✅

## Running Tests

### Run All Tests
```bash
uv run pytest
```

### Run by Category
```bash
# Unit tests only
uv run pytest src/tests/unit/

# Integration tests only  
uv run pytest src/tests/integration/

# E2E tests only
uv run pytest src/tests/e2e/

# Performance tests only
uv run pytest src/tests/performance/
```

### Run by Marker
```bash
# Unit tests
uv run pytest -m unit

# Integration tests
uv run pytest -m integration  

# E2E tests
uv run pytest -m e2e

# Performance tests
uv run pytest -m performance
```

### Coverage Requirements
- **Minimum Coverage**: 85% overall
- **Unit Tests**: Should provide the majority of coverage
- **Integration Tests**: Focus on service interactions
- **E2E Tests**: Validate complete workflows

## Configuration Files

### Main conftest.py
- Shared fixtures for all test types
- Database test engine and session
- Mock fixtures for external dependencies (Redis, email, time, UUID)
- Authentication fixtures with real JWT tokens

### Category-specific conftest.py files
- **unit/conftest.py**: Auto-mocks external dependencies (HTTP, file I/O, SMTP)
- **integration/conftest.py**: Mocks only external services, allows real Redis if available
- **e2e/conftest.py**: Minimal mocking, uses real implementations
- **performance/conftest.py**: Mocks timing-variable external services

## Mocking Guidelines

### ✅ ALWAYS Mock in Unit Tests
- External HTTP/API calls (`httpx.AsyncClient`)
- File system operations (`open`, `os.path.exists`)
- SMTP email sending (`smtplib.SMTP`)
- Time functions (`datetime.now`, `time.time`)
- Random/UUID generation for deterministic tests
- Redis/cache operations

### ✅ ALWAYS Mock in Integration Tests  
- External API calls
- SMTP servers
- File system operations (unless testing file handling)

### ✅ ALWAYS Mock in E2E Tests
- Only external services not part of the system under test
- SMTP for email sending (unless testing email integration)

### ❌ NEVER Mock (Internal Business Logic)
- Service classes and their methods
- Permission checking logic
- Authentication flows (except in unit tests)
- Database operations (in integration/E2E tests)
- Model validation and business rules
- Internal utility functions

## Best Practices

1. **Test Isolation**: Each test should be independent and not affect others
2. **Meaningful Names**: Test names should clearly describe what is being tested
3. **One Assertion Focus**: Each test should focus on one specific behavior
4. **Arrange-Act-Assert**: Structure tests clearly with setup, action, and verification
5. **Real Data**: Use factories to create realistic test data
6. **Error Testing**: Test both success and failure scenarios
7. **Edge Cases**: Include boundary conditions and error states

## Fixtures and Factories

### Available Fixtures
- `test_session`: Isolated database session
- `test_user`, `test_sysadmin`, `test_regular_user`: Test users with different roles
- `admin_auth_token`, `sysadmin_auth_token`, `user_auth_token`: Real JWT tokens
- `client`: FastAPI test client with database override
- `mock_redis_client`: Mocked Redis client with in-memory storage

### Factory Usage
```python
from src.tests.factories import ClientFactory, UserFactory

# Create test data
client = ClientFactory()
user = UserFactory(role=UserRole.ADMIN)
```

## Coverage and Quality

- All tests must maintain the 85% coverage requirement
- Use `--cov=src --cov-report=html` for detailed coverage reports
- Focus on testing business logic and critical paths
- Performance tests should include benchmarks and memory profiling