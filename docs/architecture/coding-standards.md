# Coding Standards

The platform implements **minimal but critical** standards for AI agents to ensure consistency and prevent common mistakes across the fullstack multi-agent architecture.

### Critical Fullstack Rules

- **Type Sharing:** Always define shared types in `shared/types/` and import from there. Never duplicate type definitions between agents or frontend/backend
- **Database Access:** Agents can only READ from other agents' tables, never modify. Each agent writes only to its own tables
- **API Calls:** Never make direct HTTP calls - always use the FastAPI service layer with proper error handling
- **Environment Variables:** Access only through config objects in `core/config.py`, never process.env directly
- **Error Handling:** All API routes must use the standard FastAPI exception handler with structured error responses
- **Agent Independence:** Each agent must function independently - no direct inter-agent communication except through database
- **Validation:** ALL external data must be validated using Pydantic models and Zod schemas at system boundaries
- **Authentication:** Use the centralized auth middleware - never implement custom auth logic in agents
- **CSS Variables:** Custom branding changes only through CSS variables system - never hardcode brand colors
- **File Organization:** Maximum 500 lines per file, functions under 50 lines - split larger files into modules
- **Testing Requirements:** 80% minimum code coverage - no exceptions for any module or agent
- **Language Consistency:** All code, comments, and technical content in English - UI content in Portuguese (Brazil)
- **Type Safety:** Never use `Any` type annotations - always use specific types. Create proper TypeScript interfaces or Pydantic models instead

### Naming Conventions

| Element | Frontend | Backend | Agent Tables | Example |
|---------|----------|---------|--------------|----------|
| Components | PascalCase | - | - | `ClientForm.tsx` |
| Hooks | camelCase with 'use' | - | - | `useClientData.ts` |
| API Routes | - | kebab-case | - | `/api/client-management` |
| Database Tables | - | snake_case | `agent{N}_{entity}` | `agent1_clients` |
| Agent Services | - | PascalCase | - | `ClientManagementService` |
| Shared Types | PascalCase | PascalCase | - | `ClientCreateRequest` |
| CSS Classes | kebab-case | - | - | `client-form-container` |
| Environment Variables | UPPER_SNAKE_CASE | UPPER_SNAKE_CASE | - | `DATABASE_URL` |
