# BACKEND_DEVELOPER_GUIDE.md

This file provides comprehensive guidance when working with the Python/FastAPI backend in this repository.

## Core Development Philosophy

### KISS (Keep It Simple, Stupid)

Simplicity should be a key goal in design. Choose straightforward solutions over complex ones whenever possible. Simple solutions are easier to understand, maintain, and debug.

### YAGNI (You Aren't Gonna Need It)

Avoid building functionality on speculation. Implement features only when they are needed, not when you anticipate they might be useful in the future.

### Design Principles

- **Dependency Inversion**: High-level modules should not depend on low-level modules. Both should depend on abstractions.
- **Open/Closed Principle**: Software entities should be open for extension but closed for modification.
- **Single Responsibility**: Each function, class, and module should have one clear purpose.
- **Fail Fast**: Check for potential errors early and raise exceptions immediately when issues occur.

## 🧱 Code Structure & Modularity

### File and Function Limits

- **Never create a file longer than 500 lines of code**. If approaching this limit, refactor by splitting into modules.
- **Functions should be under 50 lines** with a single, clear responsibility.
- **Classes should be under 100 lines** and represent a single concept or entity.
- **Organize code into clearly separated modules**, grouped by feature or responsibility.
- **Line length should be max 100 characters** (enforced by Ruff).

### Project Architecture

Follow a strict vertical slice architecture adapted for our monorepo:

```
apps/backend/app/
    __init__.py
    main.py
    tests/
        test_main.py
    conftest.py

    # Core modules
    core/
        __init__.py
        database.py
        dal.py # Data Access Layer for Tenant Isolation
        tests/
            test_dal.py

    # Feature slices
    features/
        user_management/
            __init__.py
            router.py
            service.py
            schemas.py # Pydantic Schemas
            tests/
                test_router.py
                test_service.py
```

## 🛠️ Development Environment

### UV Package Management

This project uses UV for blazing-fast Python package and environment management within the backend application.

```bash
# Navigate to the backend directory
cd apps/backend

# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv

# Sync dependencies from pyproject.toml
uv sync

# Add a package ***NEVER UPDATE A DEPENDENCY DIRECTLY IN PYPROJECT.toml***
# ALWAYS USE UV ADD
uv add requests

# Add development dependency
uv add --dev pytest ruff mypy

# Remove a package
uv remove requests

# Run commands in the environment
uv run python script.py
uv run pytest
uv run ruff check .
```

### Development Commands

```bash
# From within apps/backend/

# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app --cov-report=html

# Format code
uv run ruff format .

# Check linting
uv run ruff check .

# Fix linting issues automatically
uv run ruff check --fix .

# Type checking
uv run mypy app/```

## 📋 Style & Conventions

### Python Style Guide

- **Follow PEP8** with Ruff's enforcement.
- **Line length: 100 characters** (set in `pyproject.toml`).
- **Use double quotes** for strings.
- **Use trailing commas** in multi-line structures.
- **Always use type hints** for function signatures and class attributes.
- **Format with `ruff format`**.
- **Use `pydantic` v2** for data validation and settings management.

### Docstring Standards

Use Google-style docstrings for all public functions, classes, and modules:

```python
from decimal import Decimal

def calculate_discount(
    price: Decimal,
    discount_percent: float,
    min_amount: Decimal = Decimal("0.01")
) -> Decimal:
    """Calculate the discounted price for a product.

    Args:
        price: Original price of the product.
        discount_percent: Discount percentage (0-100).
        min_amount: Minimum allowed final price.

    Returns:
        Final price after applying discount.

    Raises:
        ValueError: If discount_percent is not between 0 and 100.
        ValueError: If final price would be below min_amount.
    """
```

### Naming Conventions

- **Variables and functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private attributes/methods**: `_leading_underscore`

## 🧪 Testing Strategy

### Test-Driven Development (TDD)

1.  **Write the test first** - Define expected behavior before implementation.
2.  **Watch it fail** - Ensure the test actually tests something.
3.  **Write minimal code** - Just enough to make the test pass.
4.  **Refactor** - Improve code while keeping tests green.
5.  **Repeat** - One test at a time.

### Testing Best Practices

- **Always use `pytest` fixtures** for setup (`conftest.py` for shared fixtures).
- Use descriptive test names (e.g., `test_user_can_update_email_when_valid`).
- Test edge cases and error conditions, not just the "happy path".
- Keep test files next to the code they test.
- Aim for 80%+ code coverage, but focus on critical paths.

## 🚨 Error Handling

### Exception Best Practices

- Create custom, domain-specific exceptions (e.g., `class DocumentProcessingError(Exception):`).
- Use specific `except` blocks rather than catching generic `Exception`.
- Use context managers (`with` statements) for resource management.

### Logging Strategy

- Use **structured logging** (e.g., with `structlog`).
- Include a **`correlationId`** in all logs to trace a request end-to-end.
- Log with context (e.g., `user_id`, `tenant_id`, `document_id`).

## 🔧 Configuration Management

### Environment Variables and Settings

- All configuration **MUST** be managed via a Pydantic `BaseSettings` class.
- This class will load variables from a `.env` file.
- This provides automatic validation and type-casting for all environment variables.

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with validation."""
    APP_NAME: str = "IA.M Backend"
    DEBUG: bool = False
    DATABASE_URL: str
    # ... other settings

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

## 🏗️ Data Models and Validation

- All data models (API request/response bodies, etc.) **MUST** be defined using Pydantic V2.
- This ensures strict data validation at the boundaries of the API.
- Use specific types like `EmailStr`, `UUID`, etc., where appropriate.

## 🔄 Git Workflow

### Branch Strategy

- `main` - Production-ready code.
- `develop` - Integration branch for features.
- `feature/*` - New features.
- `fix/*` - Bug fixes.

### Commit Message Format

Use the Conventional Commits specification.

```
<type>(<scope>): <subject>

<body>

<footer>
```
**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.

## 🗄️ Database Naming Standards

### Entity-Specific Primary Keys
All database tables **MUST** use entity-specific primary keys for clarity.

```sql
-- ✅ STANDARDIZED:
users.user_id UUID PRIMARY KEY
tenants.tenant_id UUID PRIMARY KEY
documents.document_id UUID PRIMARY KEY
```

### Field Naming Conventions

- **Primary keys**: `{entity}_id`
- **Foreign keys**: `{referenced_entity}_id`
- **Timestamps**: `{action}_at` (e.g., `created_at`, `updated_at`)
- **Booleans**: `is_{state}` (e.g., `is_active`)

## 🛡️ Security Best Practices

- **Never commit secrets** - use environment variables and a secrets manager.
- **Validate all user input** with Pydantic.
- **Use parameterized queries** (handled automatically by SQLAlchemy ORM) to prevent SQL injection.
- **Implement rate limiting** for public-facing APIs.
- **Keep dependencies updated** with `uv sync`.
- **Implement proper authentication and authorization** on all endpoints.

## 🔍 Search Command Requirements

**CRITICAL**: Always use `rg` (ripgrep) instead of `grep` and `find`.

```bash
# ✅ Use rg
rg "pattern"

# ✅ Use rg with file filtering
rg --files -g "*.py"
```