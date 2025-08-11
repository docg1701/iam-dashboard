# Frontend Architecture

The frontend architecture implements permission-aware interfaces with complete branding customization, supporting the revolutionary agent-based access system that enables 90% employee access.

## Component Architecture

### Component Organization
```
apps/web/src/
├── components/           # Reusable UI components
│   ├── ui/              # shadcn/ui base components
│   ├── forms/           # Form components with validation
│   ├── navigation/      # Navigation and routing components
│   ├── permission/      # Permission-aware wrapper components
│   └── branding/        # Custom branding components
├── pages/               # Next.js 15 App Router pages
│   ├── (auth)/         # Authentication route group
│   ├── dashboard/       # Main dashboard pages
│   ├── clients/         # Client management pages
│   └── admin/          # Administrative interfaces
├── hooks/               # Custom React hooks
│   ├── useAuth.ts      # Authentication state management
│   ├── usePermissions.ts # Permission validation hooks
│   └── useClients.ts    # Client data management
├── services/            # API client services
│   ├── api.ts          # Base API client configuration
│   ├── auth.service.ts  # Authentication service
│   └── clients.service.ts # Client management service
├── stores/              # Zustand state management
│   ├── authStore.ts    # Authentication state
│   ├── permissionStore.ts # Permission state
│   └── uiStore.ts      # UI state (themes, modals)
└── utils/               # Frontend utilities
    ├── validation.ts   # Form validation schemas
    ├── permissions.ts  # Permission checking utilities
    └── api-client.ts   # HTTP client configuration
```

## State Management Architecture

### State Structure
```typescript
// Authentication Store (Zustand)
interface AuthState {
  user: User | null;
  tokens: {
    accessToken: string | null;
    refreshToken: string | null;
  };
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
}

// Permission Store (Zustand with TanStack Query integration)
interface PermissionState {
  permissions: UserAgentPermission[];
  hasPermission: (agent: AgentName, operation: PermissionOperation) => boolean;
  refreshPermissions: () => Promise<void>;
  subscribeToUpdates: () => void;
}
```

---
