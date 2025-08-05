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
  const MockIcon = ({ className, ...props }: Record<string, unknown>) => 
    React.createElement('div', {
      'data-testid': props['data-testid'] || 'lucide-icon',
      className: className || 'lucide-icon',
      ...props
    }, props.children || 'Icon')
  
  // Create a comprehensive list of commonly used Lucide icons
  const icons = {
    // Basic icons
    Plus: MockIcon,
    Minus: MockIcon,
    X: MockIcon,
    Check: MockIcon,
    ChevronDown: MockIcon,
    ChevronUp: MockIcon,
    ChevronLeft: MockIcon,
    ChevronRight: MockIcon,
    
    // UI icons
    Search: MockIcon,
    Filter: MockIcon,
    Settings: MockIcon,
    MoreHorizontal: MockIcon,
    Eye: MockIcon,
    EyeOff: MockIcon,
    Edit: MockIcon,
    Trash: MockIcon,
    Copy: MockIcon,
    Download: MockIcon,
    Upload: MockIcon,
    Refresh: MockIcon,
    RefreshCw: MockIcon,
    
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
    Info: MockIcon,
    Warning: MockIcon,
    
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
    
    // Layout icons
    Layout: MockIcon,
    Grid: MockIcon,
    List: MockIcon,
    Table: MockIcon,
    
    // Fallback for any unknown icons
    default: MockIcon,
  }
  
  return new Proxy(icons, {
    get: (target, prop) => {
      if (typeof prop === 'string' && prop in target) {
        return target[prop as keyof typeof target]
      }
      // Return MockIcon for any unknown icon
      return MockIcon
    }
  })
})