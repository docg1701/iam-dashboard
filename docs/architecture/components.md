# Components

Based on the architectural patterns, tech stack, and data models, here are the major logical components across the fullstack system:

## Frontend Components

### **AuthenticationManager**
**Responsibility:** Complete authentication lifecycle including login, 2FA, token management, and session persistence

**Key Interfaces:**
- `AuthProvider` - React context for authentication state
- `useAuth()` - Hook for accessing auth state and actions
- `ProtectedRoute` - Route wrapper for authentication requirements
- `PermissionGuard` - Component-level permission enforcement

**Dependencies:** JWT token service, TOTP validation, secure storage
**Technology Stack:** React 19 context, Zustand for auth state, secure localStorage with encryption

### **PermissionEngine**
**Responsibility:** Revolutionary agent-based permission validation and UI adaptation enabling 90% employee access

**Key Interfaces:**
- `usePermissions(agentName, operation)` - Hook for permission checks
- `PermissionProvider` - Context provider for user permissions
- `ConditionalRender` - Component for permission-based UI rendering
- `PermissionMatrix` - Admin interface for managing user permissions

**Dependencies:** User permissions API, Redis cache integration, real-time updates
**Technology Stack:** React context with TanStack Query, WebSocket for live updates, Redis for <10ms validation

### **ClientManagementInterface**
**Responsibility:** Complete client lifecycle management with advanced search, bulk operations, and audit trails

**Key Interfaces:**
- `ClientList` - Paginated client listing with search and filters
- `ClientForm` - Create/edit client with comprehensive validation
- `ClientDetail` - Individual client view with edit capabilities
- `BulkOperations` - Multi-client selection and mass actions
- `AuditTimeline` - Visual history of client changes

**Dependencies:** Client API, permission validation, audit logging
**Technology Stack:** Next.js pages, shadcn/ui forms, TanStack Query for caching, React Hook Form for validation

## Backend Components

### **AuthenticationService**
**Responsibility:** Secure authentication with OAuth2 + JWT + TOTP, session management, and security enforcement

**Key Interfaces:**
- `/auth/login` - Primary authentication endpoint with 2FA support
- `/auth/refresh` - JWT token refresh functionality
- `/auth/logout` - Secure session termination
- `AuthMiddleware` - Request authentication and permission validation

**Dependencies:** PostgreSQL user storage, Redis session cache, TOTP libraries
**Technology Stack:** FastAPI with OAuth2, bcrypt for passwords, pyotp for 2FA, Redis for session management

### **PermissionService**
**Responsibility:** Core permission engine with Redis caching delivering <10ms validation performance

**Key Interfaces:**
- `validate_permission(user_id, agent, operation)` - Primary permission check
- `grant_permission()` - Admin permission assignment
- `revoke_permission()` - Permission removal with audit
- `get_user_permissions()` - User permission retrieval with caching

**Dependencies:** PostgreSQL permissions storage, Redis caching, audit logging
**Technology Stack:** SQLModel for data access, Redis-py for caching, dependency injection for middleware

## Agent Components

### **Agent1_ClientManagement**
**Responsibility:** Core client CRUD operations with advanced search, validation, and bulk processing capabilities

**Key Interfaces:**
- `process_client_operation()` - Primary client management interface
- `validate_cpf()` - Brazilian CPF validation service using cnpj-cpf-validator
- `bulk_client_operations()` - Mass client processing
- `client_search_engine()` - Advanced search and filtering

**Dependencies:** Shared client data service, permission validation, audit logging
**Technology Stack:** Agno agent framework, shared PostgreSQL access, cnpj-cpf-validator for Brazilian document validation

### **CPF/CNPJ Validation Implementation**

The system uses the `cnpj-cpf-validator` library for robust Brazilian document validation with support for both current and future alphanumeric formats.

**Installation:**
```bash
pip install cnpj-cpf-validator
```

**CPF Validation Examples:**
```python
from cnpj_cpf_validator import CPF
