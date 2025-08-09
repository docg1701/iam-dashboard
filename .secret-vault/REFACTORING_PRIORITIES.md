# Phase 4 Refactoring Priorities - Service Mock Elimination

## Quick Reference for Refactoring Teams

### 🚨 IMMEDIATE ACTION REQUIRED (This Sprint)

#### Priority 1: Security Critical Violations
**File**: `src/tests/unit/test_core_permissions.py`  
**Issue**: PermissionService completely mocked (5 violations)  
**Risk**: CRITICAL SECURITY - Authorization logic bypassed  
**Agent**: Agent 7 - Security Mock Auditor

**Specific violations to fix**:
- Line 292: `patch('src.core.permissions.PermissionService')`
- Line 327: `patch('src.core.permissions.PermissionService')`  
- Line 365: `patch('src.core.permissions.PermissionService')`
- Line 400: `patch('src.core.permissions.PermissionService')`
- Line 447: `patch('src.core.permissions.PermissionService')`

### 🔥 HIGH PRIORITY (Next Sprint)

#### Priority 2: Business Logic Violations  
**File**: `src/tests/unit/test_users_api.py`  
**Issue**: UserService completely mocked (15 violations)  
**Risk**: HIGH - Business validation not tested  
**Agent**: Agent 6 - Service Mock Eliminator  

**Pattern to eliminate**:
```python
# ❌ REMOVE THIS PATTERN
with patch("src.api.v1.users.UserService") as mock_user_service_class:
    mock_service = Mock()
    mock_user_service_class.return_value = mock_service
```

### ⚠️ MEDIUM PRIORITY (Following Sprint)

#### Priority 3: Database Session Patterns
**Files**: `src/tests/unit/test_users_api.py`, `src/tests/unit/test_seed_data.py`  
**Issue**: Database sessions mocked in unit tests (6 violations)  
**Risk**: MEDIUM - Database interaction not tested  
**Agent**: Agent 8 - Integration Test Converter

---

## Refactoring Rules

### ✅ KEEP (Compliant Boundary Mocks)
- Redis external dependency mocking: `mock_redis_client`
- Time/DateTime mocking: `@patch('datetime.datetime')`
- File system mocking: `@patch('os.path.exists')`
- External HTTP API mocking

### 🚫 REMOVE (Prohibited Internal Mocks)
- Any `patch("*.Service")` patterns
- Any `mock.*Service` patterns  
- Internal business logic mocking
- Authentication/Permission service mocking

### 🔄 CONVERT TO
- Integration tests using real services with test database
- Real business logic validation
- External boundary mocking only

---

## Success Criteria

- [ ] 0 PermissionService mocks (Currently 5)
- [ ] 0 UserService mocks (Currently 15) 
- [ ] All security tests use real permission validation
- [ ] Maintain 85%+ test coverage
- [ ] All external boundary mocks preserved

---

## Contact for Questions
- **Audit Report**: See `MOCK_AUDIT_REPORT.md` for full details
- **Testing Strategy**: See `docs/architecture/testing-strategy.md` 
- **CLAUDE.md Guidelines**: Backend Testing Directives section