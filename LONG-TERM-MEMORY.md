# Long-Term Memory - Critical Bug Fixes

This document contains critical bug fixes and solutions for issues caused by outdated training data in AI models. **ALWAYS consult this document before making changes to the areas listed below.**

## Bug #1: SQLModel-Alembic Enum Incompatibility 

### Problem
SQLModel's Alembic autogenerate feature creates enum types with **UPPERCASE enum names** while Python enums have **lowercase values**, causing database constraint violations and runtime errors.

**Example of the bug:**
```python
# Python enum (correct)
class UserRole(str, Enum):
    ADMIN = "admin"  # value is lowercase

# Generated migration (WRONG)
sa.Enum("ADMIN", "USER", name="userrole")  # names are uppercase

# Database stores: "ADMIN" but Python expects: "admin"
```

### Root Cause
- Claude's training data contains **outdated SQLModel patterns** from pre-2024
- Missing knowledge about the `sa_column` parameter for enum fields
- Incorrect enum rendering in Alembic's autogenerate process
- **Context7 MCP was required** to access current SQLModel documentation

### Symptoms
- Database constraint violations when saving enum values
- Enum values not matching between Python code and database
- Migration files with uppercase enum values
- Tests passing but production failing with PostgreSQL

### Solution

**Step 1: Use `sa_column` in enum fields (SQLModel + SQLAlchemy pattern)**
```python
from sqlalchemy import Column, Enum as SQLAEnum
from sqlmodel import SQLModel, Field

class UserRole(str, Enum):
    SYSADMIN = "sysadmin"
    ADMIN = "admin" 
    USER = "user"

class User(SQLModel, table=True):
    # CORRECT: sa_column with values_callable ensures enum VALUES are used
    role: UserRole = Field(
        default=UserRole.USER,
        sa_column=Column(
            SQLAEnum(UserRole, values_callable=lambda obj: [e.value for e in obj]),
            nullable=False,
            default=UserRole.USER.value
        )
    )
    
    # Apply same pattern to ALL enum fields
    # Example for AuditLog:
    # action: AuditAction = Field(
    #     sa_column=Column(
    #         SQLAEnum(AuditAction, values_callable=lambda obj: [e.value for e in obj]),
    #         nullable=False
    #     )
    # )
```

**Step 2: Add custom `render_item` to Alembic env.py (Alembic autogenerate fix)**
```python
from sqlalchemy import Enum as SQLAEnum

def render_item(type_, obj, autogen_context):
    """Custom rendering for Enums to use values not names.
    
    Critical fix for SQLModel-Alembic enum compatibility.
    Without this, Alembic generates enum names (UPPERCASE) 
    instead of enum values (lowercase).
    """
    if type_ == "type" and isinstance(obj, SQLAEnum):
        enum_class = obj.enum_class
        if enum_class:
            # Extract enum VALUES, not names
            values = [e.value for e in enum_class]
            return f"sa.Enum({', '.join(repr(v) for v in values)}, name='{obj.name}')"
    return False

# In both offline and online migration functions
def run_migrations_offline() -> None:
    context.configure(
        url=url,
        target_metadata=target_metadata,
        render_item=render_item,  # CRITICAL: Include this
        # ... other parameters
    )

def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_item=render_item,  # CRITICAL: Include this
        # ... other parameters  
    )
```

**Step 3: Generate new migration with correct enum values**
```bash
cd apps/api

# Remove any problematic migrations first
rm alembic/versions/*_initial_schema_*.py

# Generate new migration (will use render_item function)
alembic revision --autogenerate -m "initial_schema_fixed_enums"

# Verify migration contains lowercase values:
# sa.Enum('sysadmin', 'admin', 'user', name='userrole')
# NOT: sa.Enum('SYSADMIN', 'ADMIN', 'USER', name='userrole')
```

**Example of CORRECT migration output:**
```python
# Generated migration with render_item fix
def upgrade() -> None:
    # PostgreSQL extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')
    
    # Tables with CORRECT lowercase enum values
    op.create_table('users',
        sa.Column('role', sa.Enum('sysadmin', 'admin', 'user', name='userrole'), nullable=False),
        # ... other columns
    )
    op.create_table('audit_logs',
        sa.Column('action', sa.Enum('create', 'read', 'update', 'delete', 'login', 'logout', 'permission_change', name='auditaction'), nullable=False),
        # ... other columns
    )
```

### Prevention Checklist
- [ ] **NEVER remove `sa_column` from enum fields**
- [ ] **NEVER modify `render_item` in alembic/env.py**
- [ ] **ALWAYS use `values_callable=lambda obj: [e.value for e in obj]`**
- [ ] **Test enum storage with actual PostgreSQL**, not just SQLite
- [ ] **Verify migration files have lowercase enum values before applying**
- [ ] **Check migration preview**: `alembic upgrade --sql head` to see SQL before running

### Test Commands
```bash
# 1. Verify enum values are stored correctly in database
docker compose exec -T postgres psql -U postgres -d iam_dashboard -c \
"SELECT enumlabel FROM pg_enum WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userrole') ORDER BY enumlabel;"
# Expected output: admin, sysadmin, user (lowercase)

# 2. Test enum insertion works
cd apps/api
.venv/bin/python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlmodel import select
from src.models.user import User, UserRole

async def test():
    engine = create_async_engine('postgresql+asyncpg://postgres:password@localhost:5432/iam_dashboard')
    async with AsyncSession(engine) as session:
        user = User(email='test@example.com', password_hash='hash', role=UserRole.ADMIN)
        session.add(user)
        await session.commit()
        print('✅ Enum insertion successful')
    await engine.dispose()

asyncio.run(test())
"
```

### References
- **Context7 Query**: SQLModel enum sa_column + Alembic render_item documentation (August 2025)
- **Working Migration**: `bf6164bca6c6_initial_schema_fixed_enums.py`
- **Fixed Files**: `apps/api/src/models/*.py`, `apps/api/alembic/env.py`
- **Production Status**: ✅ Validated with PostgreSQL in production

---

## Bug #2: DateTime Timezone PostgreSQL Incompatibility

### Problem
SQLModel models using timezone-aware datetime objects (`datetime.now(UTC)`) cause PostgreSQL to reject inserts with "can't subtract offset-naive and offset-aware datetimes" errors.

**Example of the bug:**
```python
# This FAILS with PostgreSQL
created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

# PostgreSQL expects naive datetime for TIMESTAMP WITHOUT TIME ZONE
```

### Root Cause
- Claude's training data suggests using timezone-aware datetime
- **PostgreSQL's TIMESTAMP WITHOUT TIME ZONE** requires naive datetime
- SQLModel documentation doesn't clearly specify this requirement
- **Claude often suggests `datetime.utcnow()` which is DEPRECATED in Python 3.12+**

### Symptoms
- `asyncpg.exceptions.DataError: can't subtract offset-naive and offset-aware datetimes`
- Database insert/update operations failing
- Tests passing with SQLite but failing with PostgreSQL

### Solution

**Use naive datetime with UTC semantics (PostgreSQL TIMESTAMP WITHOUT TIME ZONE):**
```python
from datetime import UTC, datetime
from sqlmodel import SQLModel, Field

# CORRECT pattern for ALL datetime fields
class User(SQLModel, table=True):
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )
    last_login_at: datetime | None = Field(default=None)
    locked_until: datetime | None = Field(default=None)

class AuditLog(SQLModel, table=True):
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )

class UserAgentPermission(SQLModel, table=True):
    granted_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )
    expires_at: datetime | None = Field(default=None)

# For comparison operations in methods
class UserAgentPermission(SQLModel, table=True):
    # ... fields ...
    
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        # ALWAYS use .replace(tzinfo=None) for consistency
        return datetime.now(UTC).replace(tzinfo=None) > self.expires_at
    
    def expires_soon(self, hours: int = 24) -> bool:
        if self.expires_at is None:
            return False
        threshold = datetime.now(UTC).replace(tzinfo=None) + timedelta(hours=hours)
        return self.expires_at <= threshold
```

**CRITICAL: Why .replace(tzinfo=None) is required:**
```python
# PostgreSQL column type: TIMESTAMP WITHOUT TIME ZONE
# This means PostgreSQL expects naive datetime objects

# WRONG (causes asyncpg.exceptions.DataError)
datetime.now(UTC)  # Returns: 2025-08-15 10:30:00+00:00 (timezone-aware)

# CORRECT (PostgreSQL compatible)
datetime.now(UTC).replace(tzinfo=None)  # Returns: 2025-08-15 10:30:00 (naive)

# Alternative using timezone.utc (same result)
from datetime import timezone
datetime.now(timezone.utc).replace(tzinfo=None)
```

### Prevention Checklist
- [ ] **NEVER use `datetime.now(UTC)` directly in Field defaults**
- [ ] **NEVER use `datetime.utcnow()` (deprecated in Python 3.12+)**
- [ ] **ALWAYS use `.replace(tzinfo=None)` for PostgreSQL compatibility**
- [ ] **Test with actual PostgreSQL**, not just SQLite
- [ ] **Use UTC semantics but naive storage**

### Test Commands
```bash
# 1. Test datetime insertion works without errors
cd apps/api
.venv/bin/python -c "
import sys
sys.path.append('src')
import asyncio
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlmodel import select
from src.models.user import User, UserRole
from src.models.audit import AuditLog, AuditAction

async def test():
    engine = create_async_engine('postgresql+asyncpg://postgres:password@localhost:5432/iam_dashboard')
    async with AsyncSession(engine) as session:
        # Test User model datetime fields
        user = User(email='test@example.com', password_hash='hash', role=UserRole.USER)
        session.add(user)
        await session.commit()
        print('✅ User datetime insertion successful')
        
        # Test AuditLog model datetime fields
        audit = AuditLog(
            actor_id=user.id,
            action=AuditAction.CREATE,
            resource_type='test',
            ip_address='127.0.0.1'
        )
        session.add(audit)
        await session.commit()
        print('✅ AuditLog datetime insertion successful')
        
        # Test datetime comparison (should not error)
        now = datetime.now(UTC).replace(tzinfo=None)
        if user.created_at <= now:
            print('✅ DateTime comparison successful')
    
    await engine.dispose()

asyncio.run(test())
"

# 2. Verify PostgreSQL column types are TIMESTAMP WITHOUT TIME ZONE
docker compose exec -T postgres psql -U postgres -d iam_dashboard -c "
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'users' AND column_name LIKE '%_at'
ORDER BY column_name;
"
# Expected: All datetime columns should show 'timestamp without time zone'

# 3. Check for any timezone-aware datetime usage in codebase
cd apps/api
rg "datetime\.now\(UTC\)(?!\.replace)" src/
# Should return NO matches (all should have .replace(tzinfo=None))
```

### References
- **Root Cause**: PostgreSQL TIMESTAMP WITHOUT TIME ZONE vs timezone-aware datetime mismatch
- **Fixed Migration**: `bf6164bca6c6_initial_schema_fixed_enums.py`
- **Fixed Files**: `apps/api/src/models/user.py`, `apps/api/src/models/audit.py`, `apps/api/src/models/permission.py`
- **Production Status**: ✅ Validated with PostgreSQL in production

---

## Bug #3: Missing PostgreSQL Extensions

### Problem
Projects requiring PostgreSQL extensions (pgvector, uuid-ossp, pgcrypto) may not have them created during migrations, causing feature failures in production.

### Root Cause
- Alembic doesn't automatically create PostgreSQL extensions
- Docker images may have extensions installed but not activated
- Migrations need explicit extension creation commands

### Solution
**Add extension creation to migration:**
```python
def upgrade() -> None:
    # Create PostgreSQL extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')
    
    # Continue with table creation...
```

**And in alembic/env.py:**
```python
def do_run_migrations(connection: Connection) -> None:
    with context.begin_transaction():
        # Create PostgreSQL extensions
        connection.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        connection.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))
        connection.execute(text('CREATE EXTENSION IF NOT EXISTS "vector"'))
        
        context.run_migrations()
```

### Test Command
```bash
# Verify all extensions are installed
docker compose exec -T postgres psql -U postgres -d iam_dashboard -c "\dx"
```

### References
- **Commit**: `40d092d` - feat: add pgvector extension to initial migration
- **Story**: 1.2 Task 5 - PostgreSQL extensions requirement

---

## How to Use This Document

### For Claude/AI Models:
1. **Before modifying enum fields** → Read Bug #1 and run validation tests
2. **Before changing datetime fields** → Read Bug #2 and run compatibility tests
3. **Before updating migrations** → Read Bug #3 and verify extensions
4. **When in doubt** → Use Context7 MCP to get current documentation

### For Developers:
1. **When reviewing PRs** → Check against prevention checklists
2. **When debugging similar issues** → Run test commands
3. **When onboarding** → Read all bugs to understand pitfalls

### Update Process:
1. **New critical bugs** → Add new section with same structure
2. **Bug resolution** → Update with additional context
3. **Pattern discovery** → Document in appropriate section

---

## 🧪 COMPREHENSIVE VALIDATION SUITE

### Memory System Health Check
```bash
# Run full validation of all documented fixes
cd /home/galvani/dev/iam-dashboard

# 1. Verify LONG-TERM-MEMORY.md is accessible
cat LONG-TERM-MEMORY.md | head -5

# 2. Check CLAUDE.md references memory system
grep -n "LONG-TERM-MEMORY" CLAUDE.md

# 3. Validate all bug fixes are working in production
./scripts/validate-memory-system.sh
```

### Memory System Validation Script
Create this as `./scripts/validate-memory-system.sh`:
```bash
#!/bin/bash
set -e

echo "🧠 Long-Term Memory System Validation"
echo "======================================="

# Bug #1: SQLModel-Alembic Enum Validation
echo "🔍 Bug #1: Testing SQLModel-Alembic Enum Compatibility..."
cd apps/api

# Check all enum fields have sa_column
echo "  - Checking enum fields have sa_column..."
if rg "Field\(\s*default.*Enum" src/models/ | grep -v "sa_column"; then
    echo "  ❌ Found enum fields without sa_column"
    exit 1
else
    echo "  ✅ All enum fields have sa_column"
fi

# Check render_item function exists
if grep -q "render_item" alembic/env.py; then
    echo "  ✅ render_item function found in alembic/env.py"
else
    echo "  ❌ render_item function missing from alembic/env.py"
    exit 1
fi

# Bug #2: DateTime PostgreSQL Compatibility
echo "🔍 Bug #2: Testing DateTime PostgreSQL Compatibility..."

# Check no direct datetime.now(UTC) usage
if rg "datetime\.now\(UTC\)(?!\.replace)" src/; then
    echo "  ❌ Found timezone-aware datetime usage"
    exit 1
else
    echo "  ✅ No timezone-aware datetime found"
fi

# Bug #3: PostgreSQL Extensions
echo "🔍 Bug #3: Testing PostgreSQL Extensions..."

# Check extensions in migration
if grep -q "vector" alembic/versions/*.py; then
    echo "  ✅ pgvector extension found in migration"
else
    echo "  ❌ pgvector extension missing from migration"
    exit 1
fi

echo "🎉 All memory system validations passed!"
```

### Production Deployment with Memory System
```bash
# Full production validation sequence
./scripts/deploy-production.sh
./scripts/validate-memory-system.sh
./scripts/run-backend-tests.sh fast
./scripts/run-database-tests.sh fast

# If all pass, system is production-ready
echo "✅ Memory system validated in production environment"
```

---

**Last Updated**: August 15, 2025  
**Next Review**: When new compatibility issues arise or major dependency updates