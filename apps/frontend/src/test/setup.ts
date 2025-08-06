import { expect, vi } from 'vitest'
import * as matchers from '@testing-library/jest-dom/matchers'
import { setupGlobalMocks, createMockPermissionAPI, createMockAuthStore, createMockApiClient } from '@/__tests__/mocks/api'
import React from 'react'

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers)

// Setup global mocks (fetch, WebSocket, console)
setupGlobalMocks()

// Global test setup
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
} as any

// happy-dom provides built-in Range and Selection support, so we don't need to mock these

// Mock getBoundingClientRect for better layout testing
Element.prototype.getBoundingClientRect = vi.fn(() => ({
  bottom: 0,
  height: 0,
  left: 0,
  right: 0,
  top: 0,
  width: 0,
  x: 0,
  y: 0,
  toJSON: vi.fn(),
}))

// Mock getComputedStyle
Object.defineProperty(window, 'getComputedStyle', {
  value: vi.fn(() => ({
    getPropertyValue: vi.fn(() => ''),
    display: 'block',
    visibility: 'visible',
    opacity: '1',
  })),
})

// Mock hasPointerCapture and scrollIntoView for Radix UI components
if (typeof Element !== 'undefined') {
  if (!Element.prototype.hasPointerCapture) {
    Element.prototype.hasPointerCapture = vi.fn().mockReturnValue(false)
    Element.prototype.setPointerCapture = vi.fn()
    Element.prototype.releasePointerCapture = vi.fn()
  }
  
  if (!Element.prototype.scrollIntoView) {
    Element.prototype.scrollIntoView = vi.fn()
  }
}

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// UI Components are mocked at the component level in individual test files
// This prevents conflicts and allows for more granular control

// Mock common shadcn/ui components that are used across multiple test files
// These are basic mocks that individual tests can override if needed

// Mock Select components globally to prevent SelectItem value prop errors
vi.mock('@/components/ui/select', () => {
  const React = require('react')
  
  return {
    Select: ({ children, value, onValueChange, disabled, ...props }: any) => (
      React.createElement('div', {
        'data-testid': 'select',
        'data-value': value,
        'data-disabled': disabled,
        role: 'combobox',
        onClick: () => {
          if (!disabled && onValueChange) {
            // Default selection behavior for tests
            onValueChange('test-value')
          }
        },
        ...props
      }, children)
    ),
    SelectContent: ({ children, ...props }: any) => (
      React.createElement('div', {
        'data-testid': 'select-content',
        ...props
      }, children)
    ),
    SelectItem: ({ children, value = 'default-value', ...props }: any) => (
      React.createElement('div', {
        'data-testid': 'select-item',
        'data-value': value,
        ...props
      }, children)
    ),
    SelectTrigger: ({ children, ...props }: any) => (
      React.createElement('div', {
        'data-testid': 'select-trigger',
        ...props
      }, children)
    ),
    SelectValue: ({ placeholder, ...props }: any) => (
      React.createElement('div', {
        'data-testid': 'select-value',
        ...props
      }, placeholder)
    ),
  }
})

// Mock Button component globally with proper click handling
vi.mock('@/components/ui/button', () => {
  const React = require('react')
  
  return {
    Button: ({ children, onClick, disabled, variant, size, className, ...props }: any) => (
      React.createElement('button', {
        'data-testid': 'button',
        'data-variant': variant,
        'data-size': size,
        className,
        disabled,
        onClick: () => {
          if (!disabled && onClick) {
            onClick()
          }
        },
        ...props
      }, children)
    ),
  }
})

// Mock Dialog components globally
vi.mock('@/components/ui/dialog', () => {
  const React = require('react')
  
  return {
    Dialog: ({ children, open }: any) => {
      if (!open) return null
      return React.createElement('div', {
        'data-testid': 'dialog'
      }, children)
    },
    DialogContent: ({ children }: any) => (
      React.createElement('div', {
        'data-testid': 'dialog-content'
      }, children)
    ),
    DialogDescription: ({ children }: any) => (
      React.createElement('div', {
        'data-testid': 'dialog-description'
      }, children)
    ),
    DialogFooter: ({ children }: any) => (
      React.createElement('div', {
        'data-testid': 'dialog-footer'
      }, children)
    ),
    DialogHeader: ({ children }: any) => (
      React.createElement('div', {
        'data-testid': 'dialog-header'
      }, children)
    ),
    DialogTitle: ({ children }: any) => (
      React.createElement('div', {
        'data-testid': 'dialog-title'
      }, children)
    ),
    DialogTrigger: ({ children }: any) => (
      React.createElement('div', {
        'data-testid': 'dialog-trigger'
      }, children)
    ),
  }
})

// Mock Input component globally
vi.mock('@/components/ui/input', () => {
  const React = require('react')
  
  const Input = React.forwardRef<HTMLInputElement, any>((props, ref) => {
    return React.createElement('input', {
      ref,
      'data-testid': 'input',
      ...props,
    })
  })
  Input.displayName = 'Input'
  
  return {
    Input,
    default: Input,
  }
})

// Mock Badge component globally
vi.mock('@/components/ui/badge', () => {
  const React = require('react')
  
  return {
    Badge: ({ children, variant, className }: any) => (
      React.createElement('span', {
        'data-testid': 'badge',
        'data-variant': variant,
        className
      }, children)
    ),
  }
})

// Mock Card components globally
vi.mock('@/components/ui/card', () => {
  const React = require('react')
  
  return {
    Card: ({ children, ...props }: any) => (
      React.createElement('div', {
        'data-testid': 'card',
        ...props
      }, children)
    ),
    CardContent: ({ children, className, ...props }: any) => (
      React.createElement('div', {
        'data-testid': 'card-content',
        className,
        ...props
      }, children)
    ),
    CardDescription: ({ children, ...props }: any) => (
      React.createElement('div', {
        'data-testid': 'card-description',
        ...props
      }, children)
    ),
    CardHeader: ({ children, className, ...props }: any) => (
      React.createElement('div', {
        'data-testid': 'card-header',
        className,
        ...props
      }, children)
    ),
    CardTitle: ({ children, className, ...props }: any) => (
      React.createElement('div', {
        'data-testid': 'card-title',
        className,
        ...props
      }, children)
    ),
  }
})

// Mock toast globally since it's used across many components
const mockToast = vi.fn()
vi.mock('@/components/ui/toast', () => ({
  toast: mockToast,
  useToast: vi.fn(() => ({
    toast: mockToast,
  })),
  ToastProvider: ({ children }: { children: React.ReactNode }) => {
    return React.createElement('div', {
      'data-testid': 'toast-provider',
    }, children)
  },
  Toaster: () => {
    return React.createElement('div', {
      'data-testid': 'toaster',
    })
  },
}))

// Export the mock for access in tests
global.__mockToast = mockToast

// Mock Textarea component which isn't handled in individual tests
vi.mock('@/components/ui/textarea', async () => {
  const React = await import('react')
  const Textarea = React.forwardRef<HTMLTextAreaElement, any>((props, ref) => {
    return React.createElement('textarea', {
      ref,
      'data-testid': 'textarea',
      ...props,
    })
  })
  Textarea.displayName = 'Textarea'
  
  return {
    Textarea,
    default: Textarea,
  }
})

// Mock the main API modules globally
vi.mock('@/lib/api', () => ({
  apiClient: createMockApiClient(),
}))

vi.mock('@/lib/api/permissions', () => ({
  UserPermissionAPI: createMockPermissionAPI().User,
  PermissionTemplateAPI: createMockPermissionAPI().Template,
  PermissionAuditAPI: createMockPermissionAPI().Audit,
  PermissionUtils: createMockPermissionAPI().Utils,
  PermissionAPI: createMockPermissionAPI(),
}))

vi.mock('@/lib/api/users', () => ({
  getUsers: vi.fn().mockResolvedValue([]),
  getUser: vi.fn().mockResolvedValue({}),
  createUser: vi.fn().mockResolvedValue({}),
  updateUser: vi.fn().mockResolvedValue({}),
  deleteUser: vi.fn().mockResolvedValue(undefined),
}))

vi.mock('@/lib/api/clients', () => ({
  getClients: vi.fn().mockResolvedValue([]),
  getClient: vi.fn().mockResolvedValue({}),
  createClient: vi.fn().mockResolvedValue({}),
  updateClient: vi.fn().mockResolvedValue({}),
  deleteClient: vi.fn().mockResolvedValue(undefined),
}))

// NOTE: useUserPermissions hook is NOT globally mocked to allow for dedicated hook testing
// Individual test files can mock these as needed for their specific test scenarios

// Mock the auth store
vi.mock('@/store/authStore', () => {
  const mockStore = createMockAuthStore()
  
  // Create a function that returns the store when called as a hook
  const useAuthStore = () => mockStore
  
  // Add getState as a static method
  useAuthStore.getState = () => mockStore
  useAuthStore.setState = mockStore.setState
  useAuthStore.subscribe = mockStore.subscribe
  
  return {
    default: useAuthStore,
    __esModule: true,
  }
})

// Mock React Hook Form
vi.mock('react-hook-form', () => {
  const React = require('react')
  
  // Mock FormProvider component
  const MockFormProvider = ({ children, ...props }: any) => {
    return React.createElement('div', {
      'data-testid': 'form-provider',
      ...props,
    }, children)
  }
  MockFormProvider.displayName = 'FormProvider'
  
  return {
    FormProvider: MockFormProvider,
    useForm: ({ defaultValues = {} } = {}) => ({
      register: vi.fn(() => ({
        onChange: vi.fn(),
        onBlur: vi.fn(),
        name: 'test',
        ref: vi.fn(),
      })),
      handleSubmit: vi.fn((fn) => (e) => {
        e?.preventDefault?.()
        return fn(defaultValues)
      }),
      formState: {
        errors: {},
        isSubmitting: false,
        isValid: true,
        isDirty: false,
        isLoading: false,
      },
      watch: vi.fn(),
      setValue: vi.fn(),
      getValues: vi.fn(() => defaultValues),
      reset: vi.fn(),
      control: {},
      clearErrors: vi.fn(),
      setError: vi.fn(),
    }),
    useWatch: vi.fn(),
    Controller: ({ render, control, name }: any) => {
      const mockFieldProps = {
        field: {
          onChange: vi.fn(),
          onBlur: vi.fn(),
          value: '',
          name,
          ref: vi.fn(),
        },
        fieldState: {
          error: null,
          isDirty: false,
          isTouched: false,
        },
        formState: {
          isSubmitting: false,
          isValid: true,
        },
      }
      return render ? render(mockFieldProps) : null
    },
    useController: vi.fn(() => ({
      field: {
        onChange: vi.fn(),
        onBlur: vi.fn(),
        value: '',
        name: 'test',
        ref: vi.fn(),
      },
      fieldState: {
        error: null,
        isDirty: false,
        isTouched: false,
      },
      formState: {
        isSubmitting: false,
        isValid: true,
      },
    })),
    useFormContext: vi.fn(() => ({
      register: vi.fn(),
      handleSubmit: vi.fn(),
      formState: { errors: {} },
      watch: vi.fn(),
      setValue: vi.fn(),
      getValues: vi.fn(() => ({})),
      getFieldState: vi.fn(() => ({
        error: null,
        isDirty: false,
        isTouched: false,
        invalid: false,
      })),
      control: {},
    })),
  }
})

// Mock @hookform/resolvers
vi.mock('@hookform/resolvers/zod', () => ({
  zodResolver: vi.fn(() => vi.fn()),
}))

// Mock TanStack Query - flexible mocks that can be overridden by individual tests
vi.mock('@tanstack/react-query', () => {
  // Default mock implementations that can be overridden
  const defaultUseQuery = vi.fn(() => ({
    data: null,
    isLoading: false,
    isError: false,
    error: null,
    refetch: vi.fn(),
    dataUpdatedAt: 0,
    status: 'success' as const,
    fetchStatus: 'idle' as const,
  }))

  const defaultUseMutation = vi.fn(() => ({
    mutate: vi.fn(),
    mutateAsync: vi.fn().mockResolvedValue({}),
    isLoading: false,
    isPending: false,
    isError: false,
    isSuccess: false,
    error: null,
    data: null,
    reset: vi.fn(),
    status: 'idle' as const,
  }))

  const defaultUseQueryClient = vi.fn(() => ({
    invalidateQueries: vi.fn(),
    setQueryData: vi.fn(),
    getQueryData: vi.fn(),
    refetchQueries: vi.fn(),
    clear: vi.fn(),
  }))

  const defaultQueryClient = vi.fn(() => ({
    invalidateQueries: vi.fn(),
    setQueryData: vi.fn(),
    getQueryData: vi.fn(),
    refetchQueries: vi.fn(),
    clear: vi.fn(),
    mount: vi.fn(),
    unmount: vi.fn(),
  }))

  return {
    useQuery: defaultUseQuery,
    useMutation: defaultUseMutation,
    useQueryClient: defaultUseQueryClient,
    QueryClient: defaultQueryClient,
    QueryClientProvider: ({ children }: any) => children,
    // Allow individual tests to access the default mocks for overriding
    __mocks: {
      useQuery: defaultUseQuery,
      useMutation: defaultUseMutation,
      useQueryClient: defaultUseQueryClient,
      QueryClient: defaultQueryClient,
    }
  }
})

// Mock Next.js environment
vi.mock('@/lib/env', () => ({
  env: {
    NEXT_PUBLIC_API_URL: 'http://localhost:8000',
    NEXT_PUBLIC_APP_NAME: 'IAM Dashboard Test',
  },
}))

// Mock useRouter from Next.js
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
  usePathname: () => '/test-path',
  useSearchParams: () => new URLSearchParams(),
}))

// Mock Lucide React icons to avoid rendering issues
vi.mock('lucide-react', () => {
  const MockIcon = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement> & { children?: React.ReactNode; 'data-testid'?: string }>((props, ref) => {
    const { className, children, ...restProps } = props
    return React.createElement('div', {
      ref,
      'data-testid': props['data-testid'] || 'lucide-icon',
      className: className || 'lucide-icon',
      ...restProps
    }, children || 'Icon')
  })
  
  MockIcon.displayName = 'MockIcon'
  
  // Create a comprehensive list of all Lucide icons used in the app
  const icons = {
    // Basic icons
    Plus: MockIcon,
    Minus: MockIcon,
    X: MockIcon,
    Check: MockIcon,
    CheckIcon: MockIcon,
    ChevronDown: MockIcon,
    ChevronDownIcon: MockIcon,
    ChevronUp: MockIcon,
    ChevronUpIcon: MockIcon,
    ChevronLeft: MockIcon,
    ChevronRight: MockIcon,
    
    // Loading/Status icons
    Loader: MockIcon,
    Loader2: MockIcon,
    
    // UI icons
    Search: MockIcon,
    Filter: MockIcon,
    Settings: MockIcon,
    MoreHorizontal: MockIcon,
    Eye: MockIcon,
    EyeOff: MockIcon,
    Edit: MockIcon,
    Trash: MockIcon,
    Trash2: MockIcon,
    Copy: MockIcon,
    Download: MockIcon,
    Upload: MockIcon,
    Refresh: MockIcon,
    RefreshCw: MockIcon,
    Save: MockIcon,
    
    // User/Admin icons
    User: MockIcon,
    Users: MockIcon,
    Shield: MockIcon,
    Key: MockIcon,
    Lock: MockIcon,
    Unlock: MockIcon,
    
    // Status icons
    AlertTriangle: MockIcon,
    CheckCircle: MockIcon,
    XCircle: MockIcon,
    XIcon: MockIcon,
    Info: MockIcon,
    Warning: MockIcon,
    Star: MockIcon,
    
    // Navigation icons
    ArrowLeft: MockIcon,
    ArrowRight: MockIcon,
    ArrowUp: MockIcon,
    ArrowDown: MockIcon,
    
    // Content icons
    Calendar: MockIcon,
    Clock: MockIcon,
    History: MockIcon,
    Activity: MockIcon,
    FileText: MockIcon,
    
    // Layout icons
    Layout: MockIcon,
    Grid: MockIcon,
    List: MockIcon,
    Table: MockIcon,
    
    // Fallback for any unknown icons
    default: MockIcon,
  }
  
  // Create a proxy to handle any missing icons dynamically
  const iconsWithProxy = new Proxy(icons, {
    get(target, prop) {
      if (prop in target) {
        return target[prop]
      }
      // Return MockIcon for any unknown icon
      return MockIcon
    }
  })
  
  // Return both the individual icons and a proxy for unknown icons
  return {
    ...iconsWithProxy,
    // Default export as MockIcon
    default: MockIcon,
    __esModule: true,
  }
})