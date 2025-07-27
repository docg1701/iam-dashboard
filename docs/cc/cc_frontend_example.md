# FRONTEND_DEVELOPER_GUIDE.md

This file provides comprehensive guidance when working with the Next.js 15 application with React 19 and TypeScript.

## Core Development Philosophy

### KISS (Keep It Simple, Stupid)
Simplicity should be a key goal in design. Choose straightforward solutions over complex ones whenever possible.

### YAGNI (You Aren't Gonna Need It)
Avoid building functionality on speculation. Implement features only when they are needed.

### Design Principles
- **Vertical Slice Architecture**: Organize by features, not layers.
- **Component-First**: Build with reusable, composable components with single responsibility.
- **Fail Fast**: Validate inputs early, throw errors immediately.

## 🧱 Code Structure & Modularity

### File and Component Limits
- **Never create a file longer than 500 lines of code.** If approaching this limit, refactor.
- **Components should be under 200 lines** for better maintainability.
- **Functions should be short and focused (sub 50 lines)** and have a single responsibility.

## 🏗️ Project Structure (Vertical Slice Architecture)

This project adopts the feature-based structure from the starter template.

```
src/
├── app/                   # Next.js App Router
├── components/            # Shared UI components
│   ├── ui/                # Base components (shadcn/ui)
│   └── common/            # Application-specific shared components
├── features/              # Feature-based modules (RECOMMENDED)
│   └── [feature]/
│       ├── __tests__/     # Co-located tests
│       ├── components/    # Feature components
│       ├── hooks/         # Feature-specific hooks
│       ├── api/           # API integration (using TanStack Query)
│       ├── schemas/       # Zod validation schemas
│       └── types/         # TypeScript types
├── lib/                   # Core utilities and configurations
├── hooks/                 # Shared custom hooks
└── types/                 # Shared TypeScript types
```

## 🎯 TypeScript Configuration (STRICT REQUIREMENTS)

### MUST Follow These Compiler Options
The `tsconfig.json` is configured for maximum strictness. Key rules include:
- `"strict": true`
- `"noImplicitAny": true`
- `"strictNullChecks": true`
- `"noUncheckedIndexedAccess": true`

### MANDATORY Type Requirements
- **NEVER use `any` type** - use `unknown` if type is truly unknown.
- **MUST have explicit return types** for all functions and components.
- **MUST use type inference from Zod schemas** using `z.infer<typeof schema>`.
- **NEVER use `@ts-ignore`** or `@ts-expect-error` - fix the type issue properly.

## 📦 Package Management & Dependencies

- Use `npm` as the package manager for the frontend workspace.
- All dependencies are managed in `apps/frontend/package.json`.

## 🛡️ Data Validation with Zod (MANDATORY FOR ALL EXTERNAL DATA)

### MUST Follow These Validation Rules
- **MUST validate ALL external data**: API responses, form inputs, URL params.
- **MUST fail fast**: Validate at system boundaries, throw errors immediately.
- **MUST use type inference**: Always derive TypeScript types from Zod schemas.

### Form Validation with React Hook Form & Zod
This is the mandatory pattern for all forms.

```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const formSchema = z.object({
  email: z.string().email(),
  username: z.string().min(3),
});

type FormData = z.infer<typeof formSchema>;

function UserForm(): React.ReactElement {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(formSchema),
  });

  const onSubmit = async (data: FormData) => {
    // Handle validated data
  };

  return <form onSubmit={handleSubmit(onSubmit)}>{/* Form fields */}</form>;
}
```

## 🧪 Testing Strategy (MANDATORY REQUIREMENTS)

### MUST Meet These Testing Standards
- **MINIMUM 80% code coverage** - NO EXCEPTIONS.
- **MUST co-locate tests** with components in `__tests__` folders.
- **MUST use React Testing Library** for all component tests.
- **MUST test user behavior**, not implementation details.
- **MUST mock external dependencies** (API calls, etc.).
- **Test Runner**: **Jest**, as configured in the starter template.

## 🎨 Component Guidelines (STRICT REQUIREMENTS)

### MANDATORY Component Documentation (JSDoc)

All shared or complex components **MUST** have a JSDoc block explaining their purpose, props, and usage.

```typescript
/**
 * A reusable button component with consistent styling.
 * @param {object} props - The component props.
 * @param {'primary' | 'secondary'} props.variant - The visual style of the button.
 * @param {React.ReactNode} props.children - The content of the button.
 * @returns {React.ReactElement} The rendered button component.
 */
```

## 🔄 State Management (STRICT HIERARCHY)

### MUST Follow This State Hierarchy
1.  **Local State**: `useState` ONLY for non-complex, component-specific state.
2.  **URL State**: Use search params (`useSearchParams`) for state that should be bookmarkable/shareable.
3.  **Server State**: **TanStack Query** MUST be used for ALL API data (fetching, caching, mutations).
4.  **Global State**: **Zustand** should ONLY be used for global UI state that is not persisted on the server (e.g., theme, sidebar state).

### Server State Pattern (TanStack Query)
This is the mandatory pattern for interacting with the backend API.

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userSchema } from '@/features/users/schemas'; // Zod schema

// Assumes a generated, type-safe API client
import { api } from '@/lib/api-client';

function useUser(id: string) {
  return useQuery({
    queryKey: ['user', id],
    queryFn: async () => {
      const data = await api.getUserById(id);
      return userSchema.parse(data); // Validate API response
    },
  });
}
```

## 🔐 Security Requirements (MANDATORY)

- **Input Validation**: **MUST** sanitize ALL user inputs with Zod before processing.
- **XSS Prevention**: Handled by React's default JSX escaping. **NEVER** use `dangerouslySetInnerHTML` without proper sanitization.
- **CSRF Protection**: Next.js provides some default protection. Ensure all state-changing operations are handled via API routes that verify origin.
- **Environment Variables**: All public environment variables **MUST** be prefixed with `NEXT_PUBLIC_`. Never expose secrets to the client.

## 💅 Code Style & Quality

### ESLint & Prettier Configuration (MANDATORY)
- The project is pre-configured with a strict ESLint and Prettier setup.
- All code **MUST** pass linting and formatting checks to be committed.
- **Enforcement**: This is handled automatically by the Husky pre-commit hook.

## ⚠️ CRITICAL GUIDELINES (MUST FOLLOW ALL)

1.  **ENFORCE strict TypeScript** - ZERO compromises on type safety.
2.  **VALIDATE everything with Zod** - ALL external data must be validated.
3.  **MINIMUM 80% test coverage** - NO EXCEPTIONS.
4.  **MUST co-locate related files** (e.g., components, tests, styles).
5.  **MAXIMUM 500 lines per file** / **200 lines per component**.
6.  **MUST handle ALL states** - Loading, error, empty, and success.
7.  **MUST use semantic commits** (`feat:`, `fix:`, `docs:`, etc.).
8.  **MUST write JSDoc** for all exported functions and components.
9.  **NEVER use `any` type**.
10. **MUST pass ALL automated checks** before any merge.

## 🔍 Search Command Requirements

**CRITICAL**: Always use `rg` (ripgrep) instead of `grep` and `find`.

```bash
# ✅ Use rg
rg "pattern"

# ✅ Use rg with file filtering
rg --files -g "*.tsx"
```