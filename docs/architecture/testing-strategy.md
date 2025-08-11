# Testing Strategy

The testing strategy ensures comprehensive coverage of the revolutionary agent-based permission system and multi-client deployment model with automated validation across all system components, following strict CLAUDE.md compliance.

## CRITICAL Testing Directives Compliance

**Backend Testing Rules (CLAUDE.md Compliance):**
- ✅ **NEVER mock**: PermissionService logic, authentication flows, database operations (in integration), business rules
- ✅ **ALWAYS mock**: External HTTP calls, SMTP servers, file I/O, third-party libraries, time/UUID generation
- ✅ **Golden Rule**: "Mock the boundaries, not the behavior"

**Frontend Testing Rules (CLAUDE.md Compliance):**
- ✅ **NEVER mock**: Internal frontend code, components, hooks, or utilities  
- ✅ **ONLY mock**: External APIs (fetch calls, third-party services, etc.)
- ✅ **Test actual behavior**, not implementation details

## Test Organization

### Frontend Tests
```
apps/web/tests/
├── __tests__/                    # Unit tests co-located with components
│   ├── components/
│   │   ├── PermissionGuard.test.tsx
│   │   ├── ClientForm.test.tsx
│   │   └── UserManagement.test.tsx
│   ├── hooks/
│   │   ├── useAuth.test.ts
│   │   ├── usePermissions.test.ts
│   │   └── useClients.test.ts
│   ├── services/
│   │   ├── auth.service.test.ts
│   │   └── clients.service.test.ts
│   └── utils/
│       ├── validation.test.ts
│       └── permissions.test.ts
├── integration/                  # Integration tests
│   ├── auth-flow.test.tsx
│   ├── permission-system.test.tsx
│   ├── client-management.test.tsx
│   └── custom-branding.test.tsx
└── e2e/                         # MCP Playwright E2E tests
    ├── auth/
    │   ├── login.spec.ts
    │   ├── 2fa-flow.spec.ts
    │   └── logout.spec.ts
    ├── permissions/
    │   ├── admin-permission-management.spec.ts
    │   ├── user-access-validation.spec.ts
    │   └── permission-template-system.spec.ts
    └── clients/
        ├── client-crud-operations.spec.ts
        ├── client-search-filtering.spec.ts
        └── bulk-operations.spec.ts
```

## MCP Playwright E2E Testing

**CRITICAL**: Using MCP Playwright instead of local installation, following CLAUDE.md guidelines:

```typescript
// E2E Testing Implementation using MCP Playwright
// NO local Playwright installation required

describe('MCP Playwright E2E Tests', () => {
  async function setupE2ETest() {
    // Navigate to application
    await mcp__playwright__browser_navigate({ url: 'http://localhost:3000' });
    
    // Take initial screenshot
    await mcp__playwright__browser_take_screenshot({ 
      filename: 'e2e-test-start.png' 
    });
    
    // Get page structure
    const pageSnapshot = await mcp__playwright__browser_snapshot();
    return pageSnapshot;
  }
  
  async function testUserAuthenticationFlow() {
    // Navigate to login
    await mcp__playwright__browser_navigate({ url: 'http://localhost:3000/auth/login' });
    
    // Fill login form
    await mcp__playwright__browser_type({
      element: 'Email Input',
      ref: 'input[name="email"]',
      text: 'admin@empresa.com.br'
    });
    
    await mcp__playwright__browser_type({
      element: 'Password Input',
      ref: 'input[name="password"]',
      text: 'SecurePassword123!'
    });
    
    // Submit login
    await mcp__playwright__browser_click({
      element: 'Login Button',
      ref: 'button[type="submit"]'
    });
    
    // Verify successful login
    await mcp__playwright__browser_take_screenshot({ 
      filename: 'login-success.png' 
    });
    
    return await mcp__playwright__browser_snapshot();
  }
});
```

---
