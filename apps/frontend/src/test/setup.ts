import { expect, vi } from 'vitest'
import * as matchers from '@testing-library/jest-dom/matchers'
import { setupGlobalMocks, createMockPermissionAPI, createMockAuthStore, createMockApiClient } from '@/__tests__/mocks/api'

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
  const MockIcon = (props: any) => {
    const testId = props['data-testid'] || 'mock-icon'
    return { 
      $$typeof: Symbol.for('react.element'),
      type: 'div',
      props: { ...props, 'data-testid': testId }
    }
  }
  
  return new Proxy({}, {
    get: (target, prop) => {
      if (typeof prop === 'string') {
        return MockIcon
      }
      return target[prop as keyof typeof target]
    }
  })
})