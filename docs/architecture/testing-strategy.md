# Testing Strategy

> **BMAD Architecture Document** | Multi-Agent IAM Dashboard Testing Strategy  
> **Source Section**: [Architecture.md § 16. Testing Strategy](../architecture.md#16-testing-strategy)  
> **Last Updated**: January 2025 | **Version**: 1.2  
> **Owner**: Development Team | **Status**: Active Implementation

**Quick Navigation**: [Testing Commands](./developer-reference.md#testing-quick-reference) | [Development Workflow](./development-workflow.md) | [Coding Standards](./coding-standards.md) | [Permission Testing](./permission-integration-guide.md#testing-integration-patterns)

---

The platform implements **comprehensive testing** following the testing pyramid approach to ensure 80% minimum code coverage and reliable functionality across all multi-agent interactions.

**🚨 CRITICAL TESTING DIRECTIVE**: Following CLAUDE.md backend testing directives:
- **NEVER mock internal business logic** (PermissionService, UserService, authentication flows)
- **ONLY mock external dependencies** (APIs, file systems, Redis/cache, time/random)
- **Unit Tests**: Mock external APIs, file systems, Redis - Test real business logic
- **Integration Tests**: Use real database sessions, real services - Mock only external systems
- **Golden Rule**: "Mock the boundaries, not the behavior" - Mock system edges, test internal logic

## Testing Pyramid

```
                  E2E Tests (No Internal Mocks)
                 /        \
            Integration Tests (Real DB + Services)
               /            \
          Frontend Unit (Real Components)  Backend Unit (Real Logic)
```

The testing strategy emphasizes unit tests as the foundation while ensuring critical user workflows are validated through end-to-end testing across all agents.

**PROHIBITED MOCKING PATTERNS** (per CLAUDE.md):
- ❌ `vi.mock('@/services/ClientService')`
- ❌ `vi.mock('@/hooks/useAuth')`
- ❌ `patch('core.permissions.PermissionService')`
- ❌ `patch('services.UserService')`
- ❌ Database session mocking in integration tests

**APPROVED MOCKING PATTERNS**:
- ✅ `global.fetch = vi.fn()` (external API)
- ✅ `patch('external_services.notification_service')` (external service)
- ✅ `patch('time.time')` (time/random)
- ✅ `patch('external_services.redis_client')` (external cache)

## Test Organization

### Frontend Tests

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

### Backend Tests

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

### E2E Tests

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

## Test Examples

**CRITICAL**: Following CLAUDE.md testing directives - Mock only external dependencies, test real business logic

### Frontend Component Test

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { ClientForm } from '@/components/forms/ClientForm';
import { AuthProvider } from '@/contexts/AuthContext';

// Mock only external API calls - NEVER mock internal components/services
global.fetch = vi.fn();

describe('ClientForm', () => {
  const mockFetch = vi.mocked(fetch);
  
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should validate CPF format correctly using real validation logic', async () => {
    const user = userEvent.setup();
    
    render(
      <AuthProvider>
        <ClientForm onSuccess={vi.fn()} />
      </AuthProvider>
    );
    
    // Fill in form with invalid CPF
    await user.type(screen.getByLabelText(/name/i), 'John Doe');
    await user.type(screen.getByLabelText(/cpf/i), '12345678901');
    await user.type(screen.getByLabelText(/birth date/i), '1990-01-01');
    
    // Submit form
    await user.click(screen.getByRole('button', { name: /create client/i }));
    
    // Should show validation error from real Zod validation
    await waitFor(() => {
      expect(screen.getByText(/invalid cpf format/i)).toBeInTheDocument();
    });
    
    // No API call should be made for invalid data
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it('should create client with valid data using real form logic', async () => {
    const user = userEvent.setup();
    const mockClient = {
      client_id: '123',
      name: 'John Doe',
      cpf: '123.456.789-01',
      birth_date: '1990-01-01'
    };
    
    // Mock only the external API response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockClient
    } as Response);
    
    const onSuccess = vi.fn();
    
    render(
      <AuthProvider>
        <ClientForm onSuccess={onSuccess} />
      </AuthProvider>
    );
    
    // Fill in form with valid data
    await user.type(screen.getByLabelText(/name/i), 'John Doe');
    await user.type(screen.getByLabelText(/cpf/i), '123-45-6789');
    await user.type(screen.getByLabelText(/birth date/i), '1990-01-01');
    
    // Submit form
    await user.click(screen.getByRole('button', { name: /create client/i }));
    
    // Should call external API with correct data
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/v1/clients', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'John Doe',
          cpf: '123.456.789-01',
          birth_date: '1990-01-01'
        })
      });
    });
    
    // Should call success callback through real logic
    expect(onSuccess).toHaveBeenCalledWith(mockClient);
  });
});
```

### Backend Integration Test

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch
from uuid import uuid4

from main import app
from core.database import get_db
from shared.models import User
from agents.agent1.models import Client
from tests.factories import UserFactory, ClientFactory

class TestClientAPI:
    """Integration test suite - tests real business logic with mocked external dependencies only."""
    
    @patch('external_services.notification_service.send_email')  # Mock external service only
    @patch('time.time', return_value=1234567890)  # Mock time for consistent testing
    def test_create_client_success(self, mock_time, mock_email, test_client: TestClient, auth_headers: dict, db: Session):
        """Test successful client creation using real business logic and database."""
        client_data = {
            "name": "John Doe",
            "cpf": "123.456.789-01",
            "birth_date": "1990-01-01"
        }
        
        # Test real API endpoint with real validation and database operations
        response = test_client.post(
            "/api/v1/clients/",
            json=client_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == client_data["name"]
        assert data["cpf"] == client_data["cpf"]
        assert data["birth_date"] == client_data["birth_date"]
        assert "client_id" in data
        assert "created_at" in data
        
        # Verify client exists in real database
        created_client = db.query(Client).filter(Client.cpf == "123.456.789-01").first()
        assert created_client is not None
        assert created_client.full_name == "John Doe"
        
        # Verify external service was called (mocked)
        mock_email.assert_called_once()
    
    @patch('external_services.notification_service.send_email')
    def test_create_client_duplicate_cpf(self, mock_email, test_client: TestClient, auth_headers: dict, db: Session):
        """Test client creation with duplicate CPF using real validation logic."""
        # Create existing client in real database
        existing_client = ClientFactory(cpf="123.456.789-01")
        db.add(existing_client)
        db.commit()
        
        client_data = {
            "name": "Jane Doe",
            "cpf": "123.456.789-01",  # Same CPF
            "birth_date": "1985-05-15"
        }
        
        # Test real duplicate validation logic
        response = test_client.post(
            "/api/v1/clients/",
            json=client_data,
            headers=auth_headers
        )
        
        assert response.status_code == 409
        data = response.json()
        assert data["error"]["code"] == "DUPLICATE_CLIENT"
        assert "CPF already exists" in data["error"]["message"]
        
        # No email should be sent for failed creation
        mock_email.assert_not_called()
        
        # Verify real database state - should still have only one client
        clients_with_cpf = db.query(Client).filter(Client.cpf == "123.456.789-01").all()
        assert len(clients_with_cpf) == 1
```

### E2E Test

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
    
    // Real login flow - no mocks
    await authHelper.loginAsAdmin();
  });

  test('should create, edit, and delete client successfully', async ({ page }) => {
    // Navigate to clients page
    await page.goto('/clients');
    await expect(page.getByRole('heading', { name: 'Clients' })).toBeVisible();

    // Create new client - tests real form validation and API calls
    await page.getByRole('button', { name: 'Add Client' }).click();
    await expect(page.getByRole('dialog')).toBeVisible();

    // Fill client form - validates real client creation flow
    await page.getByLabel('Name').fill('John Doe');
    await page.getByLabel('CPF').fill('123.456.789-01');
    await page.getByLabel('Birth Date').fill('1990-01-01');

    // Submit form - tests complete client creation workflow
    await page.getByRole('button', { name: 'Create Client' }).click();

    // Verify client was created - validates database integration
    await expect(page.getByText('Client created successfully')).toBeVisible();
    await expect(page.getByText('John Doe')).toBeVisible();

    // Edit client - tests real edit functionality
    await page.getByRole('row', { name: /John Doe/ }).getByRole('button', { name: 'Edit' }).click();
    await page.getByLabel('Name').fill('John Smith');
    await page.getByRole('button', { name: 'Save Changes' }).click();

    // Verify client was updated - validates real update logic
    await expect(page.getByText('Client updated successfully')).toBeVisible();
    await expect(page.getByText('John Smith')).toBeVisible();

    // Delete client - tests real deletion with confirmation
    await page.getByRole('row', { name: /John Smith/ }).getByRole('button', { name: 'Delete' }).click();
    await page.getByRole('button', { name: 'Confirm Delete' }).click();

    // Verify client was deleted - validates complete deletion workflow
    await expect(page.getByText('Client deleted successfully')).toBeVisible();
    await expect(page.getByText('John Smith')).not.toBeVisible();
  });
});
```