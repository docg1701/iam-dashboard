# Developer Quick Reference Guide

**Fast access to common development patterns, commands, and troubleshooting for the Multi-Agent IAM Dashboard**

> ๐ **Quick Links**: [Setup](#-quick-setup) | [Commands](#-common-commands) | [Patterns](#-code-patterns) | [Troubleshooting](#-troubleshooting) | [Testing](#-testing-quick-reference)

---

## ๐ Quick Setup

### ๐ฑ First-Time Setup (5 minutes)
```bash
# 1. Clone and install dependencies
npm install
cd apps/frontend && npm install && cd ../..
cd apps/backend && uv sync && cd ../..

# 2. Setup environment files
cp .env.example .env
cp apps/frontend/.env.local.example apps/frontend/.env.local
cp apps/backend/.env.example apps/backend/.env

# 3. Start services
docker-compose up -d postgres redis
npm run db:migrate
npm run dev
```

### ๐ Developer URLs
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Database**: localhost:5432 (postgres/postgres)
- **Redis**: localhost:6379

---

## โก Common Commands

### ๐ฆ Package Management
```bash
# Frontend dependencies
cd apps/frontend
npm install <package>
npm uninstall <package>

# Backend dependencies (NEVER edit pyproject.toml directly)
cd apps/backend
uv add <package>
uv add --dev <package>
uv remove <package>
uv sync  # Install from lock file
```

### ๐ณ Development Services
```bash
# Start all services
npm run dev

# Start individual services
npm run dev:frontend  # Frontend only
npm run dev:backend   # Backend only

# Docker services
docker-compose up -d postgres redis  # Background
docker-compose up postgres redis     # Foreground
docker-compose down                   # Stop all
docker-compose logs -f backend        # View logs
```

### ๐พ Database Operations
```bash
# Migrations
npm run db:migrate        # Run migrations
npm run db:migration      # Create new migration
npm run db:rollback       # Rollback last migration
npm run db:reset          # Reset database

# Backend-specific (from apps/backend)
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"
uv run alembic downgrade -1
```

### ๐งช Testing Commands
```bash
# All tests
npm run test

# Frontend tests
npm run test:frontend
npm run test:frontend:watch
npm run test:frontend:coverage
npm run test:e2e

# Backend tests
npm run test:backend
npm run test:backend:watch
npm run test:backend:coverage

# Specific test files
npm run test:frontend -- ClientForm.test.tsx
npm run test:backend -- test_client_service.py
```

### ๐ Code Quality
```bash
# Format code
npm run format            # All workspaces
npm run format:frontend   # Frontend only
npm run format:backend    # Backend only

# Lint code
npm run lint              # All workspaces
npm run lint:frontend     # Frontend only
npm run lint:backend      # Backend only

# Type checking
npm run type-check        # All workspaces
npm run type-check:frontend # Frontend only
```

---

## ๐จ Code Patterns

### ๐ Frontend Patterns

#### Component Creation Template
```typescript
// src/components/example/ExampleComponent.tsx
'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { PermissionGuard } from '@/components/common/PermissionGuard'
import { useUserPermissions } from '@/hooks/useUserPermissions'
import { cn } from '@/lib/utils'

interface ExampleComponentProps {
  className?: string
  // Add your props here
}

export const ExampleComponent: React.FC<ExampleComponentProps> = ({
  className,
  ...props
}) => {
  const [isLoading, setIsLoading] = useState(false)
  const { hasAgentPermission } = useUserPermissions()

  const handleAction = async () => {
    setIsLoading(true)
    try {
      // Your async logic here
    } catch (error) {
      console.error('Action failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader>
        <CardTitle>Example Component</CardTitle>
      </CardHeader>
      <CardContent>
        <PermissionGuard agent="client_management" operation="create">
          <Button onClick={handleAction} disabled={isLoading}>
            {isLoading ? 'Loading...' : 'Action'}
          </Button>
        </PermissionGuard>
      </CardContent>
    </Card>
  )
}
```

#### API Hook Template
```typescript
// src/hooks/useExample.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { exampleAPI } from '@/lib/api/example'
import { useToast } from '@/hooks/use-toast'

export const useExample = (id?: string) => {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  const { data, isLoading, error } = useQuery({
    queryKey: ['example', id],
    queryFn: () => exampleAPI.getById(id!),
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  const createMutation = useMutation({
    mutationFn: exampleAPI.create,
    onSuccess: () => {
      queryClient.invalidateQueries(['example'])
      toast({ title: 'Success', description: 'Created successfully' })
    },
    onError: (error) => {
      toast({ 
        title: 'Error', 
        description: error.message,
        variant: 'destructive'
      })
    }
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string, data: any }) => 
      exampleAPI.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['example'])
      toast({ title: 'Success', description: 'Updated successfully' })
    }
  })

  return {
    data,
    isLoading,
    error,
    create: createMutation.mutate,
    update: updateMutation.mutate,
    isCreating: createMutation.isLoading,
    isUpdating: updateMutation.isLoading
  }
}
```

#### Form Component Template
```typescript
// src/components/forms/ExampleForm.tsx
'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'

const exampleSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Invalid email format'),
  // Add your validation rules
})

type ExampleFormData = z.infer<typeof exampleSchema>

interface ExampleFormProps {
  onSubmit: (data: ExampleFormData) => Promise<void>
  initialData?: Partial<ExampleFormData>
  isLoading?: boolean
}

export const ExampleForm: React.FC<ExampleFormProps> = ({
  onSubmit,
  initialData,
  isLoading = false
}) => {
  const form = useForm<ExampleFormData>({
    resolver: zodResolver(exampleSchema),
    defaultValues: {
      name: '',
      email: '',
      ...initialData
    }
  })

  const handleSubmit = async (data: ExampleFormData) => {
    try {
      await onSubmit(data)
      form.reset()
    } catch (error) {
      // Error handling is done in the hook
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Nome</FormLabel>
              <FormControl>
                <Input placeholder="Digite o nome" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input type="email" placeholder="Digite o email" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button type="submit" disabled={isLoading}>
          {isLoading ? 'Salvando...' : 'Salvar'}
        </Button>
      </form>
    </Form>
  )
}
```

### ๐  Backend Patterns

#### API Endpoint Template
```python
# src/api/v1/example.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from src.core.database import get_db
from src.core.security import get_current_user
from src.core.middleware import require_agent_permission
from src.models.user import User
from src.schemas.example import ExampleCreate, ExampleUpdate, ExampleResponse
from src.services.example_service import ExampleService

router = APIRouter(prefix="/example", tags=["example"])

@router.get("/", response_model=List[ExampleResponse])
@require_agent_permission("example_agent", "read")
async def get_examples(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get examples with pagination and search"""
    service = ExampleService(db)
    return await service.get_examples(
        skip=skip, 
        limit=limit, 
        search=search,
        user_id=current_user.user_id
    )

@router.post("/", response_model=ExampleResponse)
@require_agent_permission("example_agent", "create")
async def create_example(
    example_data: ExampleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new example"""
    service = ExampleService(db)
    return await service.create_example(example_data, current_user.user_id)

@router.get("/{example_id}", response_model=ExampleResponse)
@require_agent_permission("example_agent", "read")
async def get_example(
    example_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get example by ID"""
    service = ExampleService(db)
    example = await service.get_example_by_id(example_id)
    
    if not example:
        raise HTTPException(status_code=404, detail="Example not found")
    
    return example

@router.put("/{example_id}", response_model=ExampleResponse)
@require_agent_permission("example_agent", "update")
async def update_example(
    example_id: UUID,
    example_data: ExampleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update example"""
    service = ExampleService(db)
    return await service.update_example(example_id, example_data, current_user.user_id)

@router.delete("/{example_id}")
@require_agent_permission("example_agent", "delete")
async def delete_example(
    example_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete example"""
    service = ExampleService(db)
    await service.delete_example(example_id, current_user.user_id)
    return {"message": "Example deleted successfully"}
```

#### Service Layer Template
```python
# src/services/example_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from src.models.example import Example
from src.schemas.example import ExampleCreate, ExampleUpdate
from src.core.exceptions import BusinessLogicError, PermissionDeniedError
from src.services.base_service import BaseService

class ExampleService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(db)
    
    async def create_example(self, example_data: ExampleCreate, user_id: UUID) -> Example:
        """Create new example with validation"""
        # Validate business rules
        await self._validate_create_rules(example_data)
        
        # Create model
        example = Example(
            **example_data.dict(),
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(example)
        await self.db.commit()
        await self.db.refresh(example)
        
        # Log action
        await self.audit_service.log_action(
            "example_created", 
            {"example_id": example.example_id}, 
            user_id
        )
        
        return example
    
    async def get_examples(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        user_id: UUID = None
    ) -> List[Example]:
        """Get examples with filtering"""
        query = select(Example).where(Example.is_active == True)
        
        # Add search filter
        if search:
            query = query.where(
                or_(
                    Example.name.ilike(f"%{search}%"),
                    Example.description.ilike(f"%{search}%")
                )
            )
        
        # Add pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_example_by_id(self, example_id: UUID) -> Optional[Example]:
        """Get example by ID"""
        query = select(Example).where(
            and_(
                Example.example_id == example_id,
                Example.is_active == True
            )
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_example(
        self, 
        example_id: UUID, 
        example_data: ExampleUpdate, 
        user_id: UUID
    ) -> Example:
        """Update example"""
        example = await self.get_example_by_id(example_id)
        if not example:
            raise BusinessLogicError("Example not found")
        
        # Apply updates
        update_data = example_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(example, field, value)
        
        example.updated_by = user_id
        example.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(example)
        
        return example
    
    async def delete_example(self, example_id: UUID, user_id: UUID) -> bool:
        """Soft delete example"""
        example = await self.get_example_by_id(example_id)
        if not example:
            raise BusinessLogicError("Example not found")
        
        # Check for dependencies
        dependencies = await self._check_dependencies(example_id)
        if dependencies:
            raise BusinessLogicError(f"Cannot delete example with dependencies: {dependencies}")
        
        # Soft delete
        example.is_active = False
        example.deleted_by = user_id
        example.deleted_at = datetime.utcnow()
        
        await self.db.commit()
        
        return True
    
    async def _validate_create_rules(self, example_data: ExampleCreate):
        """Validate business rules for creation"""
        # Check for duplicates
        existing = await self.db.execute(
            select(Example).where(Example.name == example_data.name)
        )
        if existing.scalar_one_or_none():
            raise BusinessLogicError("Example with this name already exists")
    
    async def _check_dependencies(self, example_id: UUID) -> List[str]:
        """Check for dependent records"""
        dependencies = []
        
        # Check related records
        # Add your dependency checks here
        
        return dependencies
```

#### Model Template
```python
# src/models/example.py
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from uuid import uuid4

class ExampleBase(SQLModel):
    """Base fields for Example"""
    name: str = Field(min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    is_active: bool = Field(default=True)

class Example(ExampleBase, table=True):
    """Example model"""
    __tablename__ = "examples"
    
    # Primary key
    example_id: UUID = Field(primary_key=True, default_factory=uuid4)
    
    # Audit fields
    created_by: UUID = Field(foreign_key="users.user_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[UUID] = Field(foreign_key="users.user_id", default=None)
    updated_at: Optional[datetime] = Field(default=None)
    deleted_by: Optional[UUID] = Field(foreign_key="users.user_id", default=None)
    deleted_at: Optional[datetime] = Field(default=None)
    
    # Relationships (if needed)
    # creator: "User" = Relationship(back_populates="created_examples")

class ExampleCreate(ExampleBase):
    """Schema for creating examples"""
    pass

class ExampleUpdate(SQLModel):
    """Schema for updating examples"""
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)

class ExampleResponse(ExampleBase):
    """Schema for example responses"""
    example_id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
```

---

## ๐ Troubleshooting

### ๐ Common Issues

#### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Reset database
docker-compose down
docker volume rm iam-dashboard_postgres_data
docker-compose up -d postgres
npm run db:migrate
```

#### Frontend Build Issues
```bash
# Clear Next.js cache
rm -rf apps/frontend/.next
rm -rf apps/frontend/node_modules/.cache

# Reinstall dependencies
cd apps/frontend
rm -rf node_modules package-lock.json
npm install

# Check TypeScript errors
npm run type-check:frontend
```

#### Backend Import Issues
```bash
# Activate virtual environment
cd apps/backend
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Sync dependencies
uv sync

# Check Python path
uv run python -c "import sys; print(sys.path)"
```

#### Permission System Issues
```typescript
// Debug permission hooks
const { permissions, hasAgentPermission } = useUserPermissions()
console.log('Current permissions:', permissions)
console.log('Can create clients:', hasAgentPermission('client_management', 'create'))

// Check user role
const { user } = useAuth()
console.log('User role:', user?.role)
```

```python
# Debug backend permissions
async def debug_permissions(user_id: UUID):
    permissions = await permission_service.get_user_permissions(user_id)
    print(f"User {user_id} permissions: {permissions}")
    
    # Test specific permission
    has_perm = await permission_service.has_agent_permission(
        user_id, "client_management", "create"
    )
    print(f"Can create clients: {has_perm}")
```

### ๐ Performance Issues

#### Slow Database Queries
```sql
-- Check slow queries
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE tablename = 'your_table';
```

#### Frontend Performance
```typescript
// Use React DevTools Profiler
// Check for unnecessary re-renders

// Optimize permission checks
const permissions = useMemo(() => {
  return getAgentPermissions('client_management')
}, [getAgentPermissions])

// Use virtualization for large lists
import { FixedSizeList as List } from 'react-window'
```

#### Redis Cache Issues
```bash
# Check Redis connection
docker-compose exec redis redis-cli ping

# View cached permissions
docker-compose exec redis redis-cli keys "permissions:*"

# Clear permission cache
docker-compose exec redis redis-cli flushall
```

---

## ๐งช Testing Quick Reference

### ๐ Frontend Testing

#### Component Testing
```typescript
// src/__tests__/components/ExampleComponent.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ExampleComponent } from '@/components/ExampleComponent'

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false }
  }
})

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  )
}

describe('ExampleComponent', () => {
  it('should render correctly', () => {
    renderWithProviders(<ExampleComponent />)
    expect(screen.getByText('Example Component')).toBeInTheDocument()
  })
  
  it('should handle user interaction', async () => {
    const mockFn = jest.fn()
    renderWithProviders(<ExampleComponent onAction={mockFn} />)
    
    fireEvent.click(screen.getByText('Action'))
    await waitFor(() => {
      expect(mockFn).toHaveBeenCalled()
    })
  })
})
```

#### Permission Testing
```typescript
import { createMockPermissionHooks } from '@/test/utils/permission-test-utils'

jest.mock('@/hooks/useUserPermissions', () => 
  createMockPermissionHooks({
    client_management: { create: true, read: true, update: false, delete: false }
  })
)
```

### ๐  Backend Testing

#### API Testing
```python
# src/tests/test_example_api.py
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_create_example():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/example/",
            json={"name": "Test Example", "description": "Test description"},
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Example"

@pytest.mark.asyncio 
async def test_get_examples_requires_permission(mock_permission_service):
    # User without permission
    mock_permission_service.set_user_permissions("user123", {})
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/example/",
            headers={"Authorization": "Bearer user123_token"}
        )
        
        assert response.status_code == 403
```

#### Service Testing
```python
# src/tests/test_example_service.py
import pytest
from src.services.example_service import ExampleService
from src.schemas.example import ExampleCreate

@pytest.mark.asyncio
async def test_create_example_success(db_session, regular_user):
    service = ExampleService(db_session)
    
    example_data = ExampleCreate(
        name="Test Example",
        description="Test description"
    )
    
    example = await service.create_example(example_data, regular_user.user_id)
    
    assert example.name == "Test Example"
    assert example.created_by == regular_user.user_id

@pytest.mark.asyncio
async def test_create_example_duplicate_name(db_session, regular_user):
    service = ExampleService(db_session)
    
    # Create first example
    await service.create_example(
        ExampleCreate(name="Duplicate", description="First"),
        regular_user.user_id
    )
    
    # Try to create duplicate
    with pytest.raises(BusinessLogicError, match="already exists"):
        await service.create_example(
            ExampleCreate(name="Duplicate", description="Second"),
            regular_user.user_id
        )
```

### ๐งช Test Fixtures
```python
# src/tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from src.core.database import get_db
from src.models.user import User

@pytest.fixture
async def db_session():
    """Provide test database session"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with AsyncSession(engine) as session:
        yield session

@pytest.fixture
async def regular_user(db_session):
    """Create test user"""
    user = User(
        email="test@example.com",
        full_name="Test User",
        role="user"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
```

---

## ๐ Performance Monitoring

### ๐ Key Metrics to Watch
- **API Response Time**: <200ms for simple endpoints
- **Database Query Time**: <50ms for indexed queries
- **Permission Check Time**: <10ms with Redis cache
- **Frontend Bundle Size**: <1MB initial load
- **Memory Usage**: <512MB for backend, <100MB for frontend

### ๐ Monitoring Commands
```bash
# Backend performance
uv run python -m cProfile -o profile.stats src/main.py
uv run python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('time').print_stats(10)"

# Database performance
docker-compose exec postgres psql -U postgres -d dashboard -c "
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 5;"

# Frontend bundle analysis
cd apps/frontend
npm run build
npm run analyze

# Memory usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

---

## ๐ VS Code Setup

### ๐งฉ Recommended Extensions
```json
// .vscode/extensions.json
{
  "recommendations": [
    "ms-python.python",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "ms-vscode.vscode-json",
    "charliermarsh.ruff",
    "ms-python.mypy-type-checker"
  ]
}
```

### โ๏ธ Workspace Settings
```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "./apps/backend/.venv/bin/python",
  "python.formatting.provider": "none",
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": true
    }
  },
  "[typescript]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "typescript.preferences.includePackageJsonAutoImports": "auto",
  "tailwindCSS.includeLanguages": {
    "typescript": "javascript",
    "typescriptreact": "javascript"
  }
}
```

---

## ๐ Security Checklist

### ๐ก๏ธ Before Deployment
- [ ] All API endpoints have permission decorators
- [ ] Input validation with Zod/Pydantic on all forms
- [ ] SQL injection prevention (using SQLModel/SQLAlchemy)
- [ ] XSS prevention (React automatically escapes)
- [ ] CSRF protection enabled
- [ ] Environment variables for secrets (never hardcode)
- [ ] HTTPS enforced in production
- [ ] Rate limiting on authentication endpoints
- [ ] Audit logging for permission changes
- [ ] Database connection strings secured

### ๐ Security Commands
```bash
# Check for secrets in code
rg -i "password|secret|key|token" --type py --type ts

# Audit npm packages
cd apps/frontend && npm audit
cd apps/backend && uv pip-audit

# Check environment files
grep -r "password\|secret" .env* || echo "No hardcoded secrets found"
```

---

*This developer reference provides quick access to the most common development tasks. For detailed architecture information, see the [Architecture Index](./index.md) and [Integration Guide](./permission-integration-guide.md).*