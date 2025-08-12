# Frontend Authentication System

This document describes the complete frontend authentication system implemented for the IAM Dashboard project, based on Story 1.3 requirements.

## Overview

The authentication system provides:
- JWT-based authentication with automatic token refresh
- Two-factor authentication (2FA) support
- Secure token storage (httpOnly cookies in production, encrypted localStorage in development)
- React Context API integration with Zustand for state management
- Protected routes and permission-based guards
- Comprehensive TypeScript type safety

## Architecture

### Core Components

1. **Authentication Context** (`src/contexts/AuthContext.tsx`)
   - React Context provider for auth state
   - Hooks: `useAuth()`, `usePermissions()`, `useAuthStatus()`
   - Higher-order components for auth integration

2. **Zustand Store** (`src/stores/authStore.ts`)
   - Client-side state management
   - Background token refresh
   - Authentication actions (login, logout, refresh)

3. **HTTP Client** (`src/services/httpClient.ts`)
   - Axios-based client with automatic token refresh
   - Request/response interceptors
   - Authentication failure handling

4. **Authentication Service** (`src/services/authService.ts`)
   - API calls for authentication operations
   - Login, logout, 2FA, profile management
   - Session management

5. **Token Storage** (`src/utils/tokenStorage.ts`)
   - Production: httpOnly cookies (secure)
   - Development: encrypted localStorage
   - Token expiration checking

## File Structure

```
src/
├── contexts/
│   └── AuthContext.tsx          # React Context and hooks
├── stores/
│   └── authStore.ts            # Zustand store
├── services/
│   ├── httpClient.ts           # HTTP client with auth
│   └── authService.ts          # Authentication API calls
├── utils/
│   └── tokenStorage.ts         # Secure token storage
├── types/
│   └── auth.ts                 # TypeScript interfaces
├── lib/
│   ├── config.ts               # App configuration
│   └── validations/
│       └── auth.ts             # Zod validation schemas
└── components/
    ├── auth/
    │   └── ProtectedRoute.tsx  # Route protection
    └── forms/
        └── LoginForm.tsx       # Login form component
```

## Usage Examples

### Basic Authentication

```tsx
import { useAuth } from '@/contexts/AuthContext'

function LoginPage() {
  const { login, isLoading, error } = useAuth()
  
  const handleLogin = async (credentials) => {
    try {
      await login(credentials)
      // Redirect to dashboard
    } catch (err) {
      // Handle error
    }
  }
  
  return <LoginForm onSubmit={handleLogin} />
}
```

### Protected Routes

```tsx
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'

function AdminPage() {
  return (
    <ProtectedRoute
      requireAuth={true}
      requiredRoles={['admin', 'sysadmin']}
    >
      <AdminDashboard />
    </ProtectedRoute>
  )
}
```

### Permission Guards

```tsx
import { PermissionGuard } from '@/components/auth/ProtectedRoute'

function UserList() {
  return (
    <div>
      <h1>Users</h1>
      <PermissionGuard
        agentName="user-management"
        actions={['create']}
      >
        <CreateUserButton />
      </PermissionGuard>
    </div>
  )
}
```

### Using Permissions Hook

```tsx
import { usePermissions } from '@/contexts/AuthContext'

function UserActions() {
  const { hasPermission, isAdmin } = usePermissions()
  
  const canCreateUser = hasPermission('user-management', 'create')
  const canDeleteUser = hasPermission('user-management', 'delete')
  
  return (
    <div>
      {canCreateUser && <button>Create User</button>}
      {canDeleteUser && <button>Delete User</button>}
      {isAdmin() && <button>Admin Actions</button>}
    </div>
  )
}
```

## Configuration

### Environment Variables

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_BASE_URL=http://localhost:3000

# Feature Flags
NEXT_PUBLIC_ENABLE_2FA=true
NEXT_PUBLIC_ENABLE_REMEMBER_ME=true
NEXT_PUBLIC_ENABLE_PASSWORD_RESET=true

# Development Only
NEXT_PUBLIC_DEBUG_AUTH=true
NEXT_PUBLIC_BYPASS_2FA=false  # NEVER set to true in production
```

### App Configuration

The system uses a centralized configuration in `src/lib/config.ts`:

```typescript
import { API_CONFIG, AUTH_CONFIG, FEATURES } from '@/lib/config'

// API endpoints
console.log(API_CONFIG.API_URL) // http://localhost:8000/api/v1

// Token refresh interval
console.log(AUTH_CONFIG.TOKEN_REFRESH_INTERVAL) // 45 minutes

// Feature checks
if (FEATURES.TWO_FACTOR_AUTH) {
  // Enable 2FA UI
}
```

## Security Features

### Token Management
- **Production**: httpOnly cookies with secure, sameSite flags
- **Development**: AES-encrypted localStorage with session keys
- **Automatic refresh**: 15 minutes before token expiry
- **Token rotation**: New refresh token on each renewal

### Password Security
- Minimum 12 characters
- Mixed case + numbers + symbols required
- bcrypt hashing with 12 rounds (backend)
- Secure transmission over HTTPS

### Two-Factor Authentication
- TOTP-based (Google Authenticator compatible)
- QR code generation for setup
- Backup codes for account recovery
- 30-second time window tolerance

### Rate Limiting
- Tiered limits by user role:
  - Users: 100 req/min
  - Admins: 500 req/min
  - Sysadmins: 1000 req/min

## Error Handling

The system provides comprehensive error handling:

```typescript
try {
  await login(credentials)
} catch (error) {
  switch (error.code) {
    case 'INVALID_CREDENTIALS':
      // Show invalid login message
      break
    case 'ACCOUNT_LOCKED':
      // Show account locked message
      break
    case '2FA_REQUIRED':
      // Show 2FA input
      break
    case 'RATE_LIMITED':
      // Show rate limit message
      break
    default:
      // Show generic error
  }
}
```

## Testing

### Mock External Dependencies Only
Following CLAUDE.md guidelines:

✅ **Mock these (external boundaries)**:
- HTTP API calls to backend
- Time/date functions for token expiry
- Browser storage (localStorage, cookies)
- UUID generation

❌ **Never mock these (internal logic)**:
- AuthContext logic
- Permission checking functions
- Token validation logic
- Form validation

### Example Test

```typescript
import { render, screen, waitFor } from '@testing-library/react'
import { useAuth } from '@/contexts/AuthContext'

// Mock only external API calls
vi.mock('@/services/httpClient', () => ({
  httpClient: {
    post: vi.fn(),
    get: vi.fn(),
  }
}))

test('login flow works correctly', async () => {
  // Test actual auth logic, not mocked implementations
  const { result } = renderHook(() => useAuth())
  
  await act(async () => {
    await result.current.login({ email: 'test@example.com', password: 'password123' })
  })
  
  expect(result.current.isAuthenticated).toBe(true)
})
```

## Deployment Considerations

### Production Checklist
- [ ] Set secure environment variables
- [ ] Enable httpOnly cookie storage
- [ ] Configure CORS properly
- [ ] Set up SSL/TLS certificates
- [ ] Configure CSP headers
- [ ] Enable rate limiting
- [ ] Set up monitoring and alerts

### Performance
- Token refresh happens in background (no UI blocking)
- Automatic cleanup of expired tokens
- Optimized re-renders with React.memo where appropriate
- Debounced API calls for form validation

## Monitoring and Observability

The system provides logging for:
- Authentication attempts (success/failure)
- Token refresh operations
- Permission checks
- Security events (account lockouts, etc.)

Use the browser console in development to see auth-related logs.

## Contributing

When adding new authentication features:

1. Add TypeScript types to `src/types/auth.ts`
2. Add validation schemas to `src/lib/validations/auth.ts`
3. Update the AuthService for new API endpoints
4. Add React hooks or context methods as needed
5. Update this README with usage examples
6. Add tests (mock external dependencies only)

## Troubleshooting

### Common Issues

**Tokens not persisting:**
- Check browser developer tools → Application → Storage
- Verify environment variables are set correctly
- Check for JavaScript errors in console

**2FA not working:**
- Verify system time is synchronized
- Check TOTP secret is properly generated
- Ensure 6-digit codes are entered correctly

**Permissions not working:**
- Check user role in the user object
- Verify permissions are loaded from API
- Check permission guard configuration

**Auto-refresh failing:**
- Check network connectivity
- Verify refresh token is still valid
- Check for CORS issues in browser console

For more detailed troubleshooting, enable debug mode:
```bash
NEXT_PUBLIC_DEBUG_AUTH=true
```

This will provide detailed console logging for all authentication operations.