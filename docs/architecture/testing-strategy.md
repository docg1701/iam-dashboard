# Testing Strategy

**The platform implements comprehensive testing following the testing pyramid approach to ensure 80% minimum code coverage and reliable functionality across all multi-agent interactions**

> ๐ **Quick Navigation**: [Testing Commands](./developer-reference.md#testing-quick-reference) | [Permission Testing](./permission-integration-guide.md#testing-integration-patterns) | [Development Workflow](./development-workflow.md) | [Coding Standards](./coding-standards.md)

---

### Testing Pyramid

```
                  E2E Tests
                 /        \
            Integration Tests
               /            \
          Frontend Unit  Backend Unit
```

The testing strategy emphasizes unit tests as the foundation while ensuring critical user workflows are validated through end-to-end testing across all agents.

### Test Organization

#### Frontend Tests

```
frontend/tests/
├── __tests__/                 # Unit tests co-located with components
│   ├── components/
│   │   ├── forms/
│   │   │   ├── ClientForm.test.tsx
│   │   │   └── UserForm.test.tsx
│   │   ├── common/
│   │   │   ├── Header.test.tsx
│   │   │   └── Sidebar.test.tsx
│   │   └── features/
│   │       ├── auth/
│   │       ├── clients/
│   │       └── branding/
│   ├── hooks/
│   │   ├── useAuth.test.ts
│   │   ├── useClients.test.ts
│   │   └── useBranding.test.ts
│   ├── stores/
│   │   ├── clientStore.test.ts
│   │   ├── authStore.test.ts
│   │   └── appStore.test.ts
│   └── utils/
│       ├── validation.test.ts
│       ├── formatting.test.ts
│       └── api-client.test.ts
├── integration/               # Integration tests
│   ├── auth-flow.test.tsx
│   ├── client-management.test.tsx
│   └── branding-system.test.tsx
└── setup/                     # Test configuration
    ├── test-utils.tsx
    ├── mocks/
    └── fixtures/
```

#### Backend Tests

```
backend/src/tests/
├── unit/                      # Unit tests
│   ├── agents/
│   │   ├── agent1/
│   │   │   ├── test_services.py
│   │   │   ├── test_models.py
│   │   │   └── test_schemas.py
│   │   ├── agent2/
│   │   ├── agent3/
│   │   └── agent4/
│   ├── core/
│   │   ├── test_auth.py
│   │   ├── test_database.py
│   │   └── test_config.py
│   └── shared/
│       ├── test_utils.py
│       └── test_validators.py
├── integration/               # Integration tests
│   ├── test_api_endpoints.py
│   ├── test_agent_communication.py
│   ├── test_database_operations.py
│   └── test_auth_flow.py
├── conftest.py               # Pytest configuration
├── factories.py              # Test data factories
└── fixtures/                 # Test fixtures
    ├── sample_clients.json
    ├── test_pdfs/
    └── audio_samples/
```

#### E2E Tests

```
tests/playwright/
├── auth/
│   ├── login.spec.ts
│   ├── two-factor.spec.ts
│   └── logout.spec.ts
├── clients/
│   ├── client-creation.spec.ts
│   ├── client-search.spec.ts
│   ├── client-editing.spec.ts
│   └── bulk-operations.spec.ts
├── agents/
│   ├── pdf-processing.spec.ts
│   ├── report-generation.spec.ts
│   └── audio-recording.spec.ts
├── branding/
│   ├── theme-customization.spec.ts
│   ├── asset-upload.spec.ts
│   └── branding-deployment.spec.ts
├── admin/
│   ├── user-management.spec.ts
│   └── system-configuration.spec.ts
├── fixtures/
│   ├── test-users.ts
│   ├── sample-data.ts
│   └── brand-assets/
└── utils/
    ├── auth-helpers.ts
    ├── data-helpers.ts
    └── page-objects/
```

### Test Examples

#### Frontend Component Test

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { ClientForm } from '@/components/forms/ClientForm';
import { ClientService } from '@/services/ClientService';

// Mock the service
vi.mock('@/services/ClientService');

describe('ClientForm', () => {
  const mockCreateClient = vi.fn();
  
  beforeEach(() => {
    vi.mocked(ClientService.createClient).mockImplementation(mockCreateClient);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should validate SSN format correctly', async () => {
    const user = userEvent.setup();
    
    render(<ClientForm onSuccess={vi.fn()} />);
    
    // Fill in form with invalid SSN
    await user.type(screen.getByLabelText(/name/i), 'John Doe');
    await user.type(screen.getByLabelText(/ssn/i), '123456789');
    await user.type(screen.getByLabelText(/birth date/i), '1990-01-01');
    
    // Submit form
    await user.click(screen.getByRole('button', { name: /create client/i }));
    
    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText(/invalid ssn format/i)).toBeInTheDocument();
    });
    
    // Service should not be called
    expect(mockCreateClient).not.toHaveBeenCalled();
  });

  it('should create client with valid data', async () => {
    const user = userEvent.setup();
    const mockClient = {
      client_id: '123',
      name: 'John Doe',
      ssn: '123-45-6789',
      birth_date: '1990-01-01'
    };
    
    mockCreateClient.mockResolvedValue(mockClient);
    const onSuccess = vi.fn();
    
    render(<ClientForm onSuccess={onSuccess} />);
    
    // Fill in form with valid data
    await user.type(screen.getByLabelText(/name/i), 'John Doe');
    await user.type(screen.getByLabelText(/ssn/i), '123-45-6789');
    await user.type(screen.getByLabelText(/birth date/i), '1990-01-01');
    
    // Submit form
    await user.click(screen.getByRole('button', { name: /create client/i }));
    
    // Should call service with correct data
    await waitFor(() => {
      expect(mockCreateClient).toHaveBeenCalledWith({
        name: 'John Doe',
        ssn: '123-45-6789',
        birth_date: '1990-01-01'
      });
    });
    
    // Should call success callback
    expect(onSuccess).toHaveBeenCalledWith(mockClient);
  });
});
```

#### Backend API Test

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4

from main import app
from core.database import get_db
from shared.models import User
from agents.agent1.models import Client
from tests.factories import UserFactory, ClientFactory

class TestClientAPI:
    """Test suite for client management API endpoints."""
    
    def test_create_client_success(self, test_client: TestClient, auth_headers: dict):
        """Test successful client creation."""
        client_data = {
            "name": "John Doe",
            "ssn": "123-45-6789",
            "birth_date": "1990-01-01"
        }
        
        response = test_client.post(
            "/api/v1/clients/",
            json=client_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == client_data["name"]
        assert data["ssn"] == client_data["ssn"]
        assert data["birth_date"] == client_data["birth_date"]
        assert "client_id" in data
        assert "created_at" in data
    
    def test_create_client_duplicate_ssn(self, test_client: TestClient, auth_headers: dict, db: Session):
        """Test client creation with duplicate SSN."""
        # Create existing client
        existing_client = ClientFactory(ssn="123-45-6789")
        db.add(existing_client)
        db.commit()
        
        client_data = {
            "name": "Jane Doe",
            "ssn": "123-45-6789",  # Same SSN
            "birth_date": "1985-05-15"
        }
        
        response = test_client.post(
            "/api/v1/clients/",
            json=client_data,
            headers=auth_headers
        )
        
        assert response.status_code == 409
        data = response.json()
        assert data["error"]["code"] == "DUPLICATE_CLIENT"
        assert "SSN already exists" in data["error"]["message"]
```

#### E2E Test

```typescript
import { test, expect } from '@playwright/test';
import { AuthHelper } from '../utils/auth-helpers';
import { DataHelper } from '../utils/data-helpers';

test.describe('Client Management Workflow', () => {
  let authHelper: AuthHelper;
  let dataHelper: DataHelper;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthHelper(page);
    dataHelper = new DataHelper(page);
    
    // Login as admin user
    await authHelper.loginAsAdmin();
  });

  test('should create, edit, and delete client successfully', async ({ page }) => {
    // Navigate to clients page
    await page.goto('/clients');
    await expect(page.getByRole('heading', { name: 'Clients' })).toBeVisible();

    // Create new client
    await page.getByRole('button', { name: 'Add Client' }).click();
    await expect(page.getByRole('dialog')).toBeVisible();

    // Fill client form
    await page.getByLabel('Name').fill('John Doe');
    await page.getByLabel('SSN').fill('123-45-6789');
    await page.getByLabel('Birth Date').fill('1990-01-01');

    // Submit form
    await page.getByRole('button', { name: 'Create Client' }).click();

    // Verify client was created
    await expect(page.getByText('Client created successfully')).toBeVisible();
    await expect(page.getByText('John Doe')).toBeVisible();

    // Edit client
    await page.getByRole('row', { name: /John Doe/ }).getByRole('button', { name: 'Edit' }).click();
    await page.getByLabel('Name').fill('John Smith');
    await page.getByRole('button', { name: 'Save Changes' }).click();

    // Verify client was updated
    await expect(page.getByText('Client updated successfully')).toBeVisible();
    await expect(page.getByText('John Smith')).toBeVisible();

    // Delete client
    await page.getByRole('row', { name: /John Smith/ }).getByRole('button', { name: 'Delete' }).click();
    await page.getByRole('button', { name: 'Confirm Delete' }).click();

    // Verify client was deleted
    await expect(page.getByText('Client deleted successfully')).toBeVisible();
    await expect(page.getByText('John Smith')).not.toBeVisible();
  });
});
```

## Permission System Testing Strategy

### Permission Testing Requirements

The permission system requires comprehensive testing to ensure security boundaries are maintained while providing the required functionality. Testing must cover all permission scenarios, role inheritance, and edge cases.

#### Permission Test Categories

1. **Unit Tests**: Individual permission methods and validation logic
2. **Integration Tests**: Permission middleware and API protection
3. **Component Tests**: Frontend permission guards and UI visibility
4. **E2E Tests**: Complete permission workflows and user scenarios

### Permission Unit Tests

#### Backend Permission Service Tests

```python
import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from core.permissions import PermissionService
from models.user import User
from models.permissions import UserAgentPermission

class TestPermissionService:
    """Test suite for permission validation and management."""
    
    @pytest.fixture
    def permission_service(self, mock_db, mock_redis):
        return PermissionService(mock_db, mock_redis)
    
    @pytest.fixture
    def sysadmin_user(self):
        return User(user_id=uuid4(), role="sysadmin", email="admin@test.com")
    
    @pytest.fixture  
    def admin_user(self):
        return User(user_id=uuid4(), role="admin", email="admin@test.com")
    
    @pytest.fixture
    def regular_user(self):
        return User(user_id=uuid4(), role="user", email="user@test.com")

    async def test_sysadmin_has_all_permissions(self, permission_service, sysadmin_user):
        """Test that sysadmin bypasses all permission checks."""
        with patch.object(permission_service, 'get_user', return_value=sysadmin_user):
            result = await permission_service.has_agent_permission(
                sysadmin_user.user_id, "client_management", "delete"
            )
            assert result is True
            
            # Test all agents and operations
            agents = ["client_management", "pdf_processing", "reports_analysis", "audio_recording"]
            operations = ["create", "read", "update", "delete"]
            
            for agent in agents:
                for operation in operations:
                    result = await permission_service.has_agent_permission(
                        sysadmin_user.user_id, agent, operation
                    )
                    assert result is True, f"Sysadmin should have {agent}:{operation}"

    async def test_admin_role_inheritance(self, permission_service, admin_user):
        """Test admin role inheritance for specific agents."""
        with patch.object(permission_service, 'get_user', return_value=admin_user):
            # Admin should have access to client_management
            result = await permission_service.has_agent_permission(
                admin_user.user_id, "client_management", "create"
            )
            assert result is True
            
            # Admin should have access to reports_analysis
            result = await permission_service.has_agent_permission(
                admin_user.user_id, "reports_analysis", "read"
            )
            assert result is True
            
            # Admin should NOT have access to pdf_processing by default
            result = await permission_service.has_agent_permission(
                admin_user.user_id, "pdf_processing", "create"
            )
            assert result is False

    async def test_user_explicit_permissions(self, permission_service, regular_user, mock_db):
        """Test explicit permission grants for regular users."""
        # Mock database permission record
        permission_record = UserAgentPermission(
            user_id=regular_user.user_id,
            agent_name="client_management",
            permissions={"create": True, "read": True, "update": False, "delete": False}
        )
        
        with patch.object(permission_service, 'get_user', return_value=regular_user):
            with patch.object(mock_db, 'get', return_value=permission_record):
                # Should have create permission
                result = await permission_service.has_agent_permission(
                    regular_user.user_id, "client_management", "create"
                )
                assert result is True
                
                # Should have read permission
                result = await permission_service.has_agent_permission(
                    regular_user.user_id, "client_management", "read"
                )
                assert result is True
                
                # Should NOT have update permission
                result = await permission_service.has_agent_permission(
                    regular_user.user_id, "client_management", "update"
                )
                assert result is False
                
                # Should NOT have delete permission
                result = await permission_service.has_agent_permission(
                    regular_user.user_id, "client_management", "delete"
                )
                assert result is False

    async def test_permission_caching(self, permission_service, regular_user, mock_redis):
        """Test Redis caching for permission checks."""
        # Mock cached permissions
        cached_permissions = '{"create": true, "read": true, "update": false, "delete": false}'
        mock_redis.get.return_value = cached_permissions
        
        with patch.object(permission_service, 'get_user', return_value=regular_user):
            result = await permission_service.has_agent_permission(
                regular_user.user_id, "client_management", "create"
            )
            assert result is True
            
            # Verify Redis was called
            mock_redis.get.assert_called_with(f"permissions:{regular_user.user_id}:client_management")

    async def test_bulk_permission_assignment(self, permission_service, admin_user):
        """Test bulk permission assignment functionality."""
        user_ids = [uuid4() for _ in range(3)]
        permissions = {
            "client_management": {"create": True, "read": True, "update": True, "delete": False}
        }
        
        with patch.object(permission_service, 'assign_agent_permissions') as mock_assign:
            mock_assign.return_value = AsyncMock()
            
            results = await permission_service.bulk_assign_permissions(
                user_ids=user_ids,
                permissions=permissions,
                assigned_by=admin_user.user_id
            )
            
            # Should call assign_agent_permissions for each user
            assert mock_assign.call_count == len(user_ids)
            assert len(results) == len(user_ids)
            
            # All results should be successful
            for result in results:
                assert result["status"] == "success"

    async def test_permission_template_application(self, permission_service, admin_user):
        """Test applying permission templates to users."""
        template = {
            "template_id": uuid4(),
            "permissions": {
                "client_management": {"create": True, "read": True, "update": True, "delete": False},
                "reports_analysis": {"create": False, "read": True, "update": False, "delete": False}
            }
        }
        user_id = uuid4()
        
        with patch.object(permission_service, 'get_permission_template', return_value=template):
            with patch.object(permission_service, 'assign_agent_permissions') as mock_assign:
                await permission_service.apply_permission_template(
                    user_id=user_id,
                    template_id=template["template_id"],
                    applied_by=admin_user.user_id
                )
                
                # Should assign permissions for each agent in template
                assert mock_assign.call_count == 2
                mock_assign.assert_any_call(
                    user_id=user_id,
                    agent_name="client_management",
                    permissions=template["permissions"]["client_management"],
                    assigned_by=admin_user.user_id
                )
```

#### Frontend Permission Hook Tests

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { useUserPermissions } from '@/hooks/useUserPermissions';
import { useAuth } from '@/hooks/useAuth';
import * as permissionsAPI from '@/lib/api/permissions';

// Mock dependencies
vi.mock('@/hooks/useAuth');
vi.mock('@/lib/api/permissions');

describe('useUserPermissions', () => {
  const mockUseAuth = vi.mocked(useAuth);
  const mockPermissionsAPI = vi.mocked(permissionsAPI);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should return true for sysadmin user on all permissions', () => {
    mockUseAuth.mockReturnValue({
      user: { user_id: '123', role: 'sysadmin', email: 'admin@test.com' }
    });

    const { result } = renderHook(() => useUserPermissions());

    // Sysadmin should have all permissions
    expect(result.current.hasAgentPermission('client_management', 'create')).toBe(true);
    expect(result.current.hasAgentPermission('pdf_processing', 'delete')).toBe(true);
    expect(result.current.hasAgentPermission('reports_analysis', 'update')).toBe(true);
    expect(result.current.hasAgentPermission('audio_recording', 'read')).toBe(true);
  });

  it('should return correct permissions for admin user', () => {
    mockUseAuth.mockReturnValue({
      user: { user_id: '123', role: 'admin', email: 'admin@test.com' }
    });

    const { result } = renderHook(() => useUserPermissions());

    // Admin should have access to client_management and reports_analysis
    expect(result.current.hasAgentPermission('client_management', 'create')).toBe(true);
    expect(result.current.hasAgentPermission('reports_analysis', 'read')).toBe(true);
    
    // Admin should NOT have access to pdf_processing and audio_recording
    expect(result.current.hasAgentPermission('pdf_processing', 'create')).toBe(false);
    expect(result.current.hasAgentPermission('audio_recording', 'read')).toBe(false);
  });

  it('should check explicit permissions for regular user', async () => {
    const mockPermissions = {
      client_management: { create: true, read: true, update: false, delete: false },
      pdf_processing: { create: false, read: true, update: false, delete: false }
    };

    mockUseAuth.mockReturnValue({
      user: { user_id: '123', role: 'user', email: 'user@test.com' }
    });
    
    mockPermissionsAPI.getUserPermissions.mockResolvedValue(mockPermissions);

    const { result } = renderHook(() => useUserPermissions());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Should have explicit permissions
    expect(result.current.hasAgentPermission('client_management', 'create')).toBe(true);
    expect(result.current.hasAgentPermission('client_management', 'read')).toBe(true);
    expect(result.current.hasAgentPermission('client_management', 'update')).toBe(false);
    expect(result.current.hasAgentPermission('client_management', 'delete')).toBe(false);
    
    expect(result.current.hasAgentPermission('pdf_processing', 'read')).toBe(true);
    expect(result.current.hasAgentPermission('pdf_processing', 'create')).toBe(false);
    
    // Should not have permissions for ungranted agents
    expect(result.current.hasAgentPermission('reports_analysis', 'read')).toBe(false);
    expect(result.current.hasAgentPermission('audio_recording', 'create')).toBe(false);
  });
});
```

#### Permission Guard Component Tests

```typescript
import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import { PermissionGuard } from '@/components/common/PermissionGuard';
import { useUserPermissions } from '@/hooks/useUserPermissions';

vi.mock('@/hooks/useUserPermissions');

describe('PermissionGuard', () => {
  const mockUseUserPermissions = vi.mocked(useUserPermissions);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render children when user has permission', () => {
    mockUseUserPermissions.mockReturnValue({
      hasAgentPermission: vi.fn().mockReturnValue(true),
      permissions: {},
      isLoading: false,
      error: null
    });

    render(
      <PermissionGuard agent="client_management" operation="create">
        <button>Create Client</button>
      </PermissionGuard>
    );

    expect(screen.getByText('Create Client')).toBeInTheDocument();
    expect(mockUseUserPermissions().hasAgentPermission).toHaveBeenCalledWith('client_management', 'create');
  });

  it('should render fallback when user lacks permission', () => {
    mockUseUserPermissions.mockReturnValue({
      hasAgentPermission: vi.fn().mockReturnValue(false),
      permissions: {},
      isLoading: false,
      error: null
    });

    render(
      <PermissionGuard 
        agent="client_management" 
        operation="create"
        fallback={<div>Access Denied</div>}
      >
        <button>Create Client</button>
      </PermissionGuard>
    );

    expect(screen.getByText('Access Denied')).toBeInTheDocument();
    expect(screen.queryByText('Create Client')).not.toBeInTheDocument();
  });

  it('should render nothing when user lacks permission and no fallback provided', () => {
    mockUseUserPermissions.mockReturnValue({
      hasAgentPermission: vi.fn().mockReturnValue(false),
      permissions: {},
      isLoading: false,
      error: null
    });

    const { container } = render(
      <PermissionGuard agent="client_management" operation="create">
        <button>Create Client</button>
      </PermissionGuard>
    );

    expect(container.firstChild).toBeNull();
    expect(screen.queryByText('Create Client')).not.toBeInTheDocument();
  });
});
```

### Permission Integration Tests

#### API Permission Middleware Tests

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app
from core.auth import get_current_user
from models.user import User

class TestPermissionMiddleware:
    """Test API endpoint permission protection."""
    
    def test_client_creation_requires_permission(self, test_client: TestClient):
        """Test that client creation requires client_management:create permission."""
        # Mock user without permission
        user = User(user_id=uuid4(), role="user", email="user@test.com")
        
        with patch('core.auth.get_current_user', return_value=user):
            with patch('core.permissions.PermissionService.has_agent_permission', return_value=False):
                response = test_client.post("/api/v1/clients/", json={
                    "name": "John Doe",
                    "ssn": "123-45-6789",
                    "birth_date": "1990-01-01"
                })
                
                assert response.status_code == 403
                data = response.json()
                assert data["error"] == "Insufficient permissions"
                assert data["required_permission"] == "client_management:create"
                assert data["user_role"] == "user"

    def test_client_creation_with_permission(self, test_client: TestClient):
        """Test successful client creation with proper permissions."""
        user = User(user_id=uuid4(), role="user", email="user@test.com")
        
        with patch('core.auth.get_current_user', return_value=user):
            with patch('core.permissions.PermissionService.has_agent_permission', return_value=True):
                response = test_client.post("/api/v1/clients/", json={
                    "name": "John Doe", 
                    "ssn": "123-45-6789",
                    "birth_date": "1990-01-01"
                })
                
                assert response.status_code == 201
                data = response.json()
                assert data["name"] == "John Doe"

    def test_sysadmin_bypasses_permission_checks(self, test_client: TestClient):
        """Test that sysadmin bypasses all permission checks."""
        sysadmin = User(user_id=uuid4(), role="sysadmin", email="admin@test.com")
        
        with patch('core.auth.get_current_user', return_value=sysadmin):
            # Should not even check permissions for sysadmin
            with patch('core.permissions.PermissionService.has_agent_permission') as mock_check:
                response = test_client.post("/api/v1/clients/", json={
                    "name": "John Doe",
                    "ssn": "123-45-6789", 
                    "birth_date": "1990-01-01"
                })
                
                assert response.status_code == 201
                # Permission service should not be called for sysadmin
                mock_check.assert_not_called()

    def test_admin_permission_inheritance(self, test_client: TestClient):
        """Test admin role inheritance for specific agents."""
        admin = User(user_id=uuid4(), role="admin", email="admin@test.com")
        
        with patch('core.auth.get_current_user', return_value=admin):
            # Admin should have access to client_management without explicit permission check
            response = test_client.post("/api/v1/clients/", json={
                "name": "John Doe",
                "ssn": "123-45-6789",
                "birth_date": "1990-01-01"
            })
            
            assert response.status_code == 201

    def test_permission_audit_logging(self, test_client: TestClient):
        """Test that permission checks are properly audited."""
        user = User(user_id=uuid4(), role="user", email="user@test.com")
        
        with patch('core.auth.get_current_user', return_value=user):
            with patch('core.permissions.PermissionService.has_agent_permission', return_value=False):
                with patch('core.audit.log_security_event') as mock_audit:
                    response = test_client.post("/api/v1/clients/", json={
                        "name": "John Doe",
                        "ssn": "123-45-6789",
                        "birth_date": "1990-01-01"
                    })
                    
                    assert response.status_code == 403
                    
                    # Should log security event for denied access
                    mock_audit.assert_called_once()
                    call_args = mock_audit.call_args
                    assert call_args[0][0] == "ACCESS_DENIED"
                    assert "required_permission" in call_args[0][1]
```

### Permission E2E Tests

#### Complete Permission Workflow Tests

```typescript
import { test, expect } from '@playwright/test';
import { AuthHelper } from '../utils/auth-helpers';

test.describe('Permission System E2E', () => {
  let authHelper: AuthHelper;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthHelper(page);
  });

  test('should enforce permission-based UI visibility', async ({ page }) => {
    // Login as regular user with limited permissions
    await authHelper.loginAsUser('user@test.com', {
      client_management: { create: false, read: true, update: false, delete: false }
    });

    // Navigate to clients page
    await page.goto('/clients');

    // Should see clients list (read permission)
    await expect(page.getByRole('heading', { name: 'Clients' })).toBeVisible();
    await expect(page.getByRole('table')).toBeVisible();

    // Should NOT see create button (no create permission)
    await expect(page.getByRole('button', { name: 'Add Client' })).not.toBeVisible();

    // Should NOT see edit/delete buttons in table rows (no update/delete permissions)
    const firstRow = page.getByRole('row').first();
    await expect(firstRow.getByRole('button', { name: 'Edit' })).not.toBeVisible();
    await expect(firstRow.getByRole('button', { name: 'Delete' })).not.toBeVisible();
  });

  test('should show all features for admin users', async ({ page }) => {
    // Login as admin user
    await authHelper.loginAsAdmin();

    // Navigate to clients page
    await page.goto('/clients');

    // Should see all client management features
    await expect(page.getByRole('button', { name: 'Add Client' })).toBeVisible();
    
    // Should see admin-only features
    await expect(page.getByRole('link', { name: 'User Management' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Permissions' })).toBeVisible();
  });

  test('should handle permission changes in real-time', async ({ page, context }) => {
    // Start with limited user
    await authHelper.loginAsUser('user@test.com', {
      client_management: { create: false, read: true, update: false, delete: false }
    });

    await page.goto('/clients');
    
    // Verify limited access
    await expect(page.getByRole('button', { name: 'Add Client' })).not.toBeVisible();

    // Simulate admin granting create permission in another tab
    const adminPage = await context.newPage();
    await authHelper.loginAsAdmin(adminPage);
    await adminPage.goto('/admin/permissions');
    
    // Find user and grant create permission
    await adminPage.getByText('user@test.com').click();
    await adminPage.getByLabel('Client Management - Create').check();
    await adminPage.getByRole('button', { name: 'Save Changes' }).click();

    // Return to user page and verify permission update
    await page.bringToFront();
    
    // Should receive real-time update and show create button
    await expect(page.getByText('Suas permissões foram atualizadas')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Add Client' })).toBeVisible();
  });

  test('should prevent unauthorized access to protected pages', async ({ page }) => {
    // Login as regular user without admin permissions
    await authHelper.loginAsUser('user@test.com', {});

    // Try to access admin pages directly
    await page.goto('/admin/permissions');
    
    // Should be redirected to dashboard or show access denied
    await expect(page.getByText('Access denied')).toBeVisible();
    // OR should be redirected
    // await expect(page).toHaveURL('/dashboard');
  });

  test('should handle bulk permission operations correctly', async ({ page }) => {
    // Login as admin
    await authHelper.loginAsAdmin();

    // Navigate to permissions management
    await page.goto('/admin/permissions');

    // Select multiple users
    await page.getByRole('checkbox', { name: 'Select user1@test.com' }).check();
    await page.getByRole('checkbox', { name: 'Select user2@test.com' }).check();
    await page.getByRole('checkbox', { name: 'Select user3@test.com' }).check();

    // Open bulk operations dialog
    await page.getByRole('button', { name: 'Bulk Operations' }).click();

    // Grant client management permissions to all selected users
    await page.getByLabel('Client Management - Create').check();
    await page.getByLabel('Client Management - Read').check();
    await page.getByLabel('Client Management - Update').check();

    // Apply changes
    await page.getByRole('button', { name: 'Apply to 3 users' }).click();

    // Verify success
    await expect(page.getByText('Bulk permissions updated successfully')).toBeVisible();

    // Verify permissions were applied to all users
    for (const email of ['user1@test.com', 'user2@test.com', 'user3@test.com']) {
      await page.getByText(email).click();
      await expect(page.getByLabel('Client Management - Create')).toBeChecked();
      await expect(page.getByLabel('Client Management - Read')).toBeChecked();
      await expect(page.getByLabel('Client Management - Update')).toBeChecked();
    }
  });

  test('should maintain permission audit trail', async ({ page }) => {
    // Login as admin
    await authHelper.loginAsAdmin();

    // Make permission changes
    await page.goto('/admin/permissions');
    await page.getByText('user@test.com').click();
    await page.getByLabel('Client Management - Create').check();
    await page.getByRole('button', { name: 'Save Changes' }).click();

    // Navigate to audit log
    await page.goto('/admin/audit');

    // Verify permission change was logged
    await expect(page.getByText('Permission Grant')).toBeVisible();
    await expect(page.getByText('user@test.com')).toBeVisible();
    await expect(page.getByText('client_management:create')).toBeVisible();
    await expect(page.getByText('admin@test.com')).toBeVisible(); // Changed by
  });
});
```

### Permission Test Data and Factories

#### Permission Test Factories

```python
import factory
from models.user import User
from models.permissions import UserAgentPermission, PermissionTemplate

class UserPermissionFactory(factory.Factory):
    class Meta:
        model = UserAgentPermission
    
    permission_id = factory.Faker('uuid4')
    user_id = factory.Faker('uuid4')
    agent_name = factory.Faker('random_element', elements=('client_management', 'pdf_processing', 'reports_analysis', 'audio_recording'))
    permissions = factory.LazyFunction(lambda: {
        "create": factory.Faker('boolean').generate(),
        "read": True,
        "update": factory.Faker('boolean').generate(),
        "delete": False
    })
    created_by_user_id = factory.Faker('uuid4')

class PermissionTemplateFactory(factory.Factory):
    class Meta:
        model = PermissionTemplate
    
    template_id = factory.Faker('uuid4')
    template_name = factory.Faker('word')
    description = factory.Faker('sentence')
    permissions = factory.LazyFunction(lambda: {
        "client_management": {
            "create": True,
            "read": True,
            "update": True,
            "delete": False
        },
        "reports_analysis": {
            "create": False,
            "read": True,
            "update": False,
            "delete": False
        }
    })
    is_system_template = False
    created_by_user_id = factory.Faker('uuid4')

# Specific permission scenarios
class ClientSpecialistPermissionFactory(UserPermissionFactory):
    agent_name = "client_management"
    permissions = {
        "create": True,
        "read": True,
        "update": True,
        "delete": False
    }

class ReportAnalystPermissionFactory(UserPermissionFactory):
    agent_name = "reports_analysis"
    permissions = {
        "create": True,
        "read": True,
        "update": True,
        "delete": False
    }

class ReadOnlyPermissionFactory(UserPermissionFactory):
    permissions = {
        "create": False,
        "read": True,
        "update": False,
        "delete": False
    }
```

### Permission Test Coverage Requirements

#### Required Test Scenarios

1. **Role Hierarchy Tests**
   - Sysadmin bypass for all permissions
   - Admin inheritance for client_management and reports_analysis
   - User explicit permission requirements

2. **Permission Validation Tests**
   - Valid permission operations (create, read, update, delete)
   - Invalid permission operations should fail
   - Permission boundary testing (edge cases)

3. **Cache Performance Tests**
   - Redis cache hit/miss scenarios
   - Cache invalidation on permission changes
   - Cache performance under load

4. **UI Permission Tests**
   - Component visibility based on permissions
   - Navigation menu filtering
   - Action button conditional rendering

5. **Real-time Update Tests**
   - WebSocket permission broadcasts
   - UI updates without page refresh
   - Multiple user scenarios

6. **Audit Trail Tests**
   - All permission changes logged
   - Audit log filtering and search
   - Audit data integrity

7. **Bulk Operation Tests**
   - Multiple user permission updates
   - Error handling in bulk operations
   - Rollback scenarios

8. **Template System Tests**
   - Template creation and application
   - System vs custom templates
   - Template validation

#### Performance Testing Requirements

```python
import pytest
import asyncio
from concurrent.futures import ThreadPoolExecutor

class TestPermissionPerformance:
    """Performance tests for permission system."""
    
    @pytest.mark.asyncio
    async def test_permission_check_performance(self, permission_service):
        """Test that permission checks are fast enough."""
        user_id = uuid4()
        
        # Warm up cache
        await permission_service.has_agent_permission(user_id, "client_management", "read")
        
        # Time 100 cached permission checks
        start_time = time.time()
        tasks = []
        for _ in range(100):
            task = permission_service.has_agent_permission(user_id, "client_management", "read")
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Should complete in less than 100ms (1ms per check average)
        assert (end_time - start_time) < 0.1, "Permission checks are too slow"
    
    @pytest.mark.asyncio
    async def test_bulk_operation_performance(self, permission_service):
        """Test bulk permission operations complete in reasonable time."""
        user_ids = [uuid4() for _ in range(50)]
        permissions = {
            "client_management": {"create": True, "read": True, "update": True, "delete": False}
        }
        
        start_time = time.time()
        results = await permission_service.bulk_assign_permissions(
            user_ids=user_ids,
            permissions=permissions,
            assigned_by=uuid4()
        )
        end_time = time.time()
        
        # Should complete 50 users in less than 5 seconds
        assert (end_time - start_time) < 5.0, "Bulk operations are too slow"
        assert len(results) == 50
        assert all(r["status"] == "success" for r in results)
```

This comprehensive permission testing strategy ensures that the enhanced role system maintains security while providing the required functionality and performance.
