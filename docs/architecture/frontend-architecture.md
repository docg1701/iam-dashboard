# Frontend Architecture

Frontend-specific architecture details based on Next.js 15 + React 19 + shadcn/ui with comprehensive custom branding support:

### Component Architecture

**Component Organization:**
```
apps/frontend/src/
├── app/                          # Next.js 15 App Router
│   ├── (auth)/                   # Route group for authentication
│   ├── (dashboard)/              # Protected dashboard routes
│   ├── globals.css               # Global styles + CSS variables
│   ├── layout.tsx                # Root layout with providers
│   └── page.tsx                  # Public homepage
├── components/                   # Reusable UI components
│   ├── ui/                       # shadcn/ui base components
│   ├── forms/                    # Complex form components
│   ├── layout/                   # Layout components
│   └── features/                 # Feature-specific components
├── lib/                          # Utilities and configurations
├── hooks/                        # Custom React hooks
├── store/                        # Client state management
└── types/                        # TypeScript type definitions
```

### State Management Architecture

**State Structure:**
```typescript
// Authentication Store (Zustand)
interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  requires2FA: boolean
  tempToken: string | null
  
  // Actions
  login: (email: string, password: string) => Promise<void>
  verify2FA: (code: string) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
  setUser: (user: User) => void
}

// UI State Store (Zustand)
interface UIState {
  sidebarOpen: boolean
  theme: 'light' | 'dark' | 'system'
  currentBranding: BrandingConfig
  
  // Actions
  toggleSidebar: () => void
  setTheme: (theme: 'light' | 'dark' | 'system') => void
  updateBranding: (branding: BrandingConfig) => void
}
```

### Routing Architecture

**Route Organization:**
- `/` - Public homepage
- `/login` - Authentication page
- `/dashboard` - Protected dashboard home
- `/dashboard/clients` - Client list with search/filters
- `/dashboard/clients/new` - New client registration
- `/dashboard/clients/[id]` - Client detail and edit
- `/dashboard/users` - User management (admin only)
- `/dashboard/system` - System configuration

### Frontend Services Layer

**API Client Setup:**
```typescript
class APIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1',
      timeout: 30000,
    })

    // Request interceptor for authentication
    this.client.interceptors.request.use((config) => {
      const token = useAuthStore.getState().token
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })

    // Response interceptor for error handling and token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          const { refreshToken, logout } = useAuthStore.getState()
          try {
            await refreshToken()
            return this.client.request(error.config)
          } catch (refreshError) {
            logout()
            window.location.href = '/login'
          }
        }
        return Promise.reject(error)
      }
    )
  }
}
```
