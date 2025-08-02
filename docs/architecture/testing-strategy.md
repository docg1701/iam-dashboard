# Testing Strategy

The platform implements **comprehensive testing** following the testing pyramid approach to ensure 80% minimum code coverage and reliable functionality across all multi-agent interactions.

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
