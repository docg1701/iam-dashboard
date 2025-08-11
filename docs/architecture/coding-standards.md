# Coding Standards

Define MINIMAL but CRITICAL standards for AI agents, focusing only on project-specific rules that prevent common mistakes and ensure consistency across the revolutionary agent-based permission system.

## Critical Fullstack Rules

- **Type Sharing:** Always define types in packages/shared and import from there - prevents API/frontend type mismatches in permission system
- **Permission Validation:** All protected routes and components must use centralized permission checking - never implement custom permission logic
- **API Error Handling:** All API routes must use the standard error handler with audit logging - ensures compliance and troubleshooting capability
- **Environment Variables:** Access only through config objects, never process.env directly - prevents configuration errors across client deployments
- **CPF Validation:** Always use shared cnpj-cpf-validator utility - prevents inconsistent validation between frontend and backend
- **Database Transactions:** All multi-table operations must use transactions with proper rollback - critical for data consistency in permission changes
- **Cache Invalidation:** Permission changes must immediately invalidate related cache keys - ensures <10ms performance without stale permissions
- **Audit Logging:** All state-changing operations must include audit trail within the same transaction - required for compliance
- **Brazilian Portuguese UI:** All user-facing text must be in Portuguese (Brazil) while code remains in English
- **Agent Boundaries:** Agents can read from other agent tables but only modify their own tables - maintains data consistency
- **JWT Token Storage:** Production uses httpOnly cookies, development uses encrypted localStorage - never store tokens in plain localStorage
- **Input Sanitization:** All user input must be validated with Pydantic/Zod schemas before processing - prevents injection attacks

## Naming Conventions

| Element | Frontend | Backend | Example |
|---------|----------|---------|---------|
| Components | PascalCase | - | `ClientManagementForm.tsx` |
| Hooks | camelCase with 'use' | - | `usePermissions.ts`, `useClientData.ts` |
| API Routes | - | kebab-case | `/api/v1/client-management`, `/api/v1/user-permissions` |
| Database Tables | - | snake_case | `user_agent_permissions`, `client_metadata` |
| CSS Classes | kebab-case | - | `permission-guard`, `client-form-container` |
| Environment Variables | SCREAMING_SNAKE_CASE | SCREAMING_SNAKE_CASE | `REDIS_CACHE_TTL`, `PERMISSION_CHECK_TIMEOUT` |
| Service Methods | camelCase | snake_case | `validatePermission()`, `validate_user_permission()` |
| Constants | SCREAMING_SNAKE_CASE | SCREAMING_SNAKE_CASE | `AGENT_NAMES`, `PERMISSION_OPERATIONS` |

---
