# 🔧 Mock Refactoring Guide - Agent 6 Results

**Created**: 2025-08-07  
**Author**: Agent 6 - Mock Refactoring Specialist  
**Mission**: Convert internal mocks to boundary mocks following CLAUDE.md directives  

## 🎯 Key Findings

### ❌ **Prohibited Internal Mocks Found**

**Location 1**: `src/tests/unit/test_users_api.py`  
**Pattern**: 17 test methods mocking `UserService` (internal business logic)  
**Violation**: Direct contradiction of CLAUDE.md "Mock the boundaries, not the behavior"  

**Location 2**: `src/tests/unit/test_core_permissions.py`  
**Pattern**: 5 test methods mocking `PermissionService` (internal business logic)  
**Violation**: Mocking internal permission logic instead of external dependencies  

### 📊 **Audit Results Summary**
- **Files with Internal Service Mocks**: 2 files
- **Total Prohibited Mocks**: 20+ internal service mocks  
- **Test Methods Affected**: 22+ test methods
- **Mock Types Found**: 
  - `@patch("src.api.v1.users.UserService")` (HIGH PRIORITY - 17 occurrences)
  - `@patch("src.core.permissions.PermissionService")` (HIGH PRIORITY - 5 occurrences)
  - Various service method mocks (MEDIUM PRIORITY)
  
### ✅ **GOOD Examples Found**
- **`test_permission_service.py`**: Uses real PermissionService with Redis boundaries mocked ✅
- **`test_client_service.py`**: Uses real ClientService throughout ✅  
- **Integration tests**: All use real services with boundary mocks only ✅

---

## 🚫 **BEFORE: Prohibited Pattern**

```python
# ❌ WRONG - Mocking internal business logic
@pytest.mark.asyncio
async def test_list_users_success_with_pagination(self) -> None:
    """BAD: Mocking UserService business logic."""
    # This mocks INTERNAL business logic
    with patch("src.api.v1.users.UserService") as mock_user_service_class:
        mock_service = Mock()
        mock_user_service_class.return_value = mock_service
        mock_service.list_users = AsyncMock(return_value=(mock_users, total_count))
        
        # Test passes but doesn't test real behavior!
        result = await list_users(...)
        
        # Only tests mock behavior, not real business logic
        assert result.success is True
```

**Problems with this approach**:
- ❌ No real business logic tested
- ❌ No real validation tested  
- ❌ No real error handling tested
- ❌ Tests pass with completely fake behavior
- ❌ Changes to UserService won't break tests (bad!)

---

## ✅ **AFTER: Correct Boundary Mocking**

```python
# ✅ CORRECT - Mock boundaries, test real behavior  
@pytest.mark.asyncio
@patch('src.core.security.redis')  # Mock external Redis dependency
@patch('datetime.datetime')  # Mock external time dependency  
async def test_list_users_success_with_pagination(self, mock_datetime, mock_redis) -> None:
    """GOOD: Tests real UserService with boundary mocks."""
    
    # Mock only external boundaries
    mock_redis.from_url.return_value.get = AsyncMock(return_value=None)
    mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
    
    # Create real test data using factories
    from src.tests.factories import create_test_user
    test_users = [
        create_test_user(email="john@example.com", role=UserRole.USER),
        create_test_user(email="jane@example.com", role=UserRole.ADMIN),
    ]
    
    # Mock database queries (boundary, not behavior)
    mock_session = Mock(spec=Session)
    
    def mock_exec_side_effect(query):
        query_str = str(query)
        if 'COUNT' in query_str.upper():
            mock_count_result = Mock()
            mock_count_result.one.return_value = 25
            return mock_count_result
        else:
            mock_user_result = Mock() 
            mock_user_result.all.return_value = test_users
            return mock_user_result
    
    mock_session.exec.side_effect = mock_exec_side_effect
    
    # Execute with REAL UserService (no service mocking!)
    result = await list_users(
        request=mock_request,
        params=mock_params,
        page=2,
        per_page=10,
        token_data=mock_token_data,
        session=mock_session,
    )
    
    # Test REAL business logic results
    assert isinstance(result, PaginatedResponse)  # Real response structure
    assert result.success is True  # Real success logic
    assert len(result.data) == len(test_users)  # Real data processing
    
    # Test REAL pagination calculation
    expected_total_pages = math.ceil(25 / 10)  # Real math
    assert result.pagination.page == 2
    assert result.pagination.total_pages == expected_total_pages
    assert result.pagination.has_next is True  # Real next/prev logic
    assert result.pagination.has_prev is True
```

**Benefits of this approach**:
- ✅ Tests real business logic
- ✅ Tests real validation  
- ✅ Tests real error handling
- ✅ Tests real pagination calculations
- ✅ Changes to UserService WILL break tests (good!)
- ✅ Only external dependencies mocked

---

## 📋 **Boundary Mock Categories**

### ✅ **ALWAYS Mock (External Boundaries)**
```python
# External services and infrastructure
@patch('src.core.security.redis')           # Redis cache  
@patch('httpx.AsyncClient')                  # HTTP requests
@patch('smtplib.SMTP')                       # Email sending
@patch('builtins.open')                      # File I/O
@patch('os.makedirs')                        # File system
@patch('datetime.datetime')                  # Time functions
@patch('uuid.uuid4')                         # UUID generation
@patch('secrets.token_urlsafe')              # Random generation
```

### 🚫 **NEVER Mock (Internal Business Logic)**
```python
# Internal services and business logic - DO NOT MOCK
# @patch('src.services.user_service.UserService')        ❌
# @patch('src.services.permission_service.PermissionService') ❌  
# @patch('src.services.client_service.ClientService')    ❌
# @patch('src.core.database.*')  # In integration tests   ❌
# @patch('src.utils.validation.*')                        ❌
# @patch('src.models.*')                                  ❌
```

### 🤔 **Database Mocking Strategy**
```python
# Unit Tests: Mock database queries (boundary)
mock_session = Mock(spec=Session)
mock_session.exec.return_value = mock_query_result  # Mock query response

# Integration Tests: Use real database 
# No database mocking - real transactions, real data

# E2E Tests: Use real database
# No database mocking - full end-to-end testing
```

---

## 🔄 **Step-by-Step Refactoring Process**

### **Step 1: Identify External Dependencies**
```python
# Analyze the service to identify what needs mocking
# UserService uses:
# - SecureAuthService (uses Redis) ← Mock Redis
# - datetime.utcnow() ← Mock datetime  
# - Database session ← Mock query responses
# - NO HTTP, SMTP, files ← Nothing else to mock
```

### **Step 2: Replace Service Mock with Boundary Mocks**
```python
# BEFORE: Mock the service
with patch("src.api.v1.users.UserService") as mock_service:

# AFTER: Mock the boundaries  
@patch('src.core.security.redis')
@patch('datetime.datetime')
async def test_method(self, mock_datetime, mock_redis):
```

### **Step 3: Configure Boundary Mocks**
```python
# Configure external dependency mocks
mock_redis.from_url.return_value.get = AsyncMock(return_value=None)
mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
```

### **Step 4: Mock Database Queries (Not Service)**
```python
# Mock database responses, not service behavior
def mock_exec_side_effect(query):
    # Return appropriate mock results based on query type
    if 'COUNT' in str(query).upper():
        return mock_count_result
    else:  
        return mock_data_result
        
mock_session.exec.side_effect = mock_exec_side_effect
```

### **Step 5: Test Real Business Logic**
```python
# Call the endpoint - UserService will be real
result = await list_users(...)

# Verify REAL behavior, not mock behavior
assert result.success is True  # Real success logic
assert len(result.data) == expected_count  # Real data processing
```

---

## 📊 **Refactoring Priority Matrix**

### **HIGH Priority - Security & Core Logic**
- [ ] `test_users_api.py` - 17 UserService mocks
- [ ] `test_permission_service.py` - Permission logic mocks  
- [ ] `test_client_service.py` - Client business logic mocks
- [ ] `test_auth_*.py` - Authentication flow mocks

### **MEDIUM Priority - API Layer**  
- [ ] API endpoint tests with service mocks
- [ ] Validation logic mocks
- [ ] Error handling mocks

### **LOW Priority - Utilities**
- [ ] Utility function mocks that might be internal
- [ ] Helper function mocks

---

## 🧪 **Testing Strategy by Layer**

### **Unit Tests (60-75%)**
```python
# Mock: External APIs, Redis, file I/O, time, HTTP
# Real: Business logic, validation, calculations, data processing
@patch('src.core.security.redis')
@patch('datetime.datetime')  
async def test_business_logic(self, mock_datetime, mock_redis):
    # Use REAL services with mocked external dependencies
    service = UserService(mock_session)  # Real service
    result = await service.create_user(...)  # Real business logic
    assert result.email == expected_email  # Real validation tested
```

### **Integration Tests (20-30%)**  
```python
# Mock: Only external services (HTTP, SMTP, file I/O)
# Real: Database, Redis, business services, auth flows
async def test_full_workflow(self, test_session):
    # Real database, real services, real auth
    user_service = UserService(test_session)  # Real with real DB
    result = await user_service.create_user(...)
    
    # Verify in database
    db_user = test_session.get(User, result.user_id)
    assert db_user.email == result.email
```

### **E2E Tests (5-10%)**
```python  
# Mock: Nothing internal, maybe external HTTP APIs
# Real: Complete system, database, Redis, auth, all services
async def test_complete_user_creation_flow(client):
    # Real HTTP requests, real database, real everything
    response = client.post("/api/v1/users", json=user_data)
    assert response.status_code == 201
    
    # Verify persisted correctly
    user = client.get(f"/api/v1/users/{user_id}")
    assert user.json()["email"] == user_data["email"]
```

---

## 📚 **Templates for Common Patterns**

### **Template: API Endpoint Test**
```python
@pytest.mark.asyncio
@patch('src.core.security.redis')
@patch('datetime.datetime')
async def test_api_endpoint(self, mock_datetime, mock_redis) -> None:
    """Test API endpoint with real service logic."""
    
    # 1. Mock external boundaries
    mock_redis.from_url.return_value.get = AsyncMock(return_value=None)
    mock_datetime.utcnow.return_value = datetime(2024, 1, 1)
    
    # 2. Create real test data
    test_data = create_test_user(email="test@example.com")
    
    # 3. Mock database queries (boundary)
    mock_session = Mock(spec=Session)
    mock_session.exec.return_value.all.return_value = [test_data]
    
    # 4. Call endpoint (real service logic)
    result = await endpoint_function(
        session=mock_session,
        # ... other real parameters
    )
    
    # 5. Verify real business logic
    assert result.success is True
    assert len(result.data) == 1
    assert result.data[0].email == test_data.email
```

### **Template: Service Test with Complex Logic**
```python
@pytest.mark.asyncio  
@patch('src.core.security.redis')
@patch('httpx.AsyncClient')
@patch('datetime.datetime')
async def test_service_complex_logic(self, mock_datetime, mock_http, mock_redis):
    """Test service with multiple external dependencies."""
    
    # Mock all external boundaries
    mock_redis.from_url.return_value.get = AsyncMock(return_value=None)
    mock_http.return_value.__aenter__.return_value.post = AsyncMock()
    mock_datetime.utcnow.return_value = datetime(2024, 1, 1)
    
    # Real service with real logic
    service = UserService(mock_session)
    
    # Test real validation, real error handling, real business rules
    result = await service.complex_operation(...)
    
    # Verify real behavior
    assert result.success is True
    assert result.validation_passed is True  # Real validation logic
    assert result.business_rule_applied is True  # Real business logic
```

### **Template: Permission Decorator Test**
```python
@pytest.mark.asyncio
@patch('src.core.security.redis')  # Mock external Redis dependency
async def test_permission_decorator_real_logic(self, mock_redis, test_session):
    """Test permission decorator with real PermissionService logic.
    
    BEFORE (❌ WRONG):
    with patch('src.core.permissions.PermissionService') as MockPermissionService:
        mock_service_instance = AsyncMock()
        mock_service_instance.check_user_permission = mock_check_permission
        
    AFTER (✅ CORRECT):
    Use real PermissionService with real permission logic.
    """
    
    # Mock external Redis boundary
    mock_redis.from_url.return_value.get = AsyncMock(return_value=None)
    
    # Create real test data
    admin_user = create_test_user(role=UserRole.ADMIN)
    test_session.add(admin_user)
    test_session.commit()
    
    # Define function with real permission decorator
    @require_permission_async('agent1', 'create')
    async def test_function(user_id: UUID, data: str) -> str:
        return f"Success: {data}"
    
    # Execute with real PermissionService logic (no mocking!)
    result = await test_function(user_id=admin_user.user_id, data="test")
    
    # Verify real permission logic was executed
    assert result == "Success: test"  # Admin should have create permissions
    
    # Test real authorization failure
    user = create_test_user(role=UserRole.USER)  # Regular user
    test_session.add(user)
    test_session.commit()
    
    with pytest.raises(HTTPException) as exc_info:
        await test_function(user_id=user.user_id, data="test")
    
    # Verify real authorization error
    assert exc_info.value.status_code == 403
    assert "Insufficient permissions" in str(exc_info.value.detail)
```

---

## 🚀 **Next Steps for Implementation**

### **Immediate Actions (Agent 7+)**
1. **Refactor `test_users_api.py`** - Replace all 17 UserService mocks
2. **Create boundary mock fixtures** - Reusable mock setups  
3. **Update test documentation** - Add examples to README
4. **Run test suite validation** - Ensure all tests pass
5. **Measure coverage impact** - Verify coverage maintains/improves

### **Long-term Strategy**
1. **Create mock audit tool** - Automated detection of internal mocks
2. **Add lint rules** - Prevent internal mocks in CI/CD
3. **Training documentation** - Guidelines for new developers  
4. **Template generation** - Auto-generate proper test templates

---

## 🎯 **Success Metrics**

### **Quantitative Goals**
- [ ] **Zero internal service mocks** in unit tests
- [ ] **80%+ test coverage** maintained after refactoring
- [ ] **All tests pass** with real business logic  
- [ ] **Boundary mocks only** for external dependencies

### **Qualitative Goals** 
- [ ] **Tests reflect real behavior** - Changes to services break tests
- [ ] **Faster debugging** - Test failures point to real issues
- [ ] **Better integration confidence** - Unit tests catch real bugs
- [ ] **Clearer test intent** - What's being tested is obvious

---

**Remember**: *"Mock the boundaries, not the behavior"* - Focus on testing real business logic while isolating external dependencies.

---

## 🔗 **References**
- **CLAUDE.md**: Backend Testing Directives (lines 299-315)
- **backend-test-strategy.md**: Phase 3 mock restructuring (lines 280-320)  
- **Golden Rule**: "Mock system edges, test internal logic"