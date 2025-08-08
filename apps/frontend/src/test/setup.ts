import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Configure React Testing Library environment for better act() handling
global.IS_REACT_ACT_ENVIRONMENT = true

// Mock React's internal DevTools to reduce act() warnings from third-party components
if (typeof globalThis !== 'undefined') {
  globalThis.__REACT_DEVTOOLS_GLOBAL_HOOK__ = {
    isDisabled: true,
    supportsFiber: true,
    inject: () => {},
    onCommitFiberRoot: () => {},
    onCommitFiberUnmount: () => {},
  }
}

// Handle stderr warnings from React Testing Library for Radix UI components
const originalStderrWrite = process.stderr.write
process.stderr.write = function(chunk: any, encoding?: any, fd?: any) {
  if (typeof chunk === 'string') {
    if (chunk.includes('An update to Select inside a test was not wrapped in act') ||
        chunk.includes('An update to SelectItemText inside a test was not wrapped in act')) {
      return true
    }
  }
  return originalStderrWrite.call(process.stderr, chunk, encoding, fd)
}

// Robust fetch mock implementation with smart API endpoint defaults
const createMockResponse = (data: any, status = 200, ok = true) => ({
  ok,
  status,
  statusText: ok ? 'OK' : 'Error',
  json: () => Promise.resolve(data),
  text: () => Promise.resolve(JSON.stringify(data)),
  headers: new Headers({ 'content-type': 'application/json' }),
  clone: function() { return this },
  body: null,
  bodyUsed: false,
  arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
  blob: () => Promise.resolve(new Blob()),
  formData: () => Promise.resolve(new FormData()),
})

// Global fetch mock setup with smart defaults
global.fetch = vi.fn()

// Default successful mock responses based on endpoint patterns
const setupDefaultFetchMocks = () => {
  vi.mocked(global.fetch).mockImplementation((url, options) => {
    const method = options?.method || 'GET'
    const urlStr = url.toString()
    
    // Auth API endpoints
    if (urlStr.includes('/auth/')) {
      if (method === 'POST' && urlStr.includes('/login')) {
        return Promise.resolve(createMockResponse({
          access_token: 'mock-jwt-token-12345',
          token_type: 'bearer',
          expires_in: 3600,
          user: {
            user_id: 'test-user-123',
            email: 'test@example.com',
            full_name: 'Test User',
            role: 'admin',
            is_active: true,
            totp_enabled: false,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z'
          }
        }))
      }
      if (method === 'POST' && urlStr.includes('/2fa/verify')) {
        return Promise.resolve(createMockResponse({
          access_token: 'mock-jwt-token-final',
          token_type: 'bearer',
          expires_in: 3600,
          user: {
            user_id: 'test-user-123',
            email: 'test@example.com',
            full_name: 'Test User',
            role: 'admin',
            is_active: true,
            totp_enabled: true,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z'
          }
        }))
      }
      if (urlStr.includes('/refresh')) {
        return Promise.resolve(createMockResponse({
          access_token: 'mock-refreshed-token',
          token_type: 'bearer',
          expires_in: 3600
        }))
      }
      if (urlStr.includes('/logout')) {
        return Promise.resolve(createMockResponse({ success: true }))
      }
    }
    
    // Permissions API endpoints
    if (urlStr.includes('/permissions')) {
      if (urlStr.includes('/users/') && method === 'GET') {
        // Extract user ID from URL (e.g., /permissions/users/admin-123)
        const userIdMatch = urlStr.match(/\/users\/([^/?]+)/)
        const requestedUserId = userIdMatch ? userIdMatch[1] : 'test-user-123'
        
        // Provide full permissions for admin users and basic permissions for regular users
        const isAdmin = requestedUserId.includes('admin') || urlStr.includes('admin')
        
        const permissions = [
          {
            permission_id: 'perm-client-' + requestedUserId,
            user_id: requestedUserId,
            agent_name: 'client_management',
            permissions: isAdmin 
              ? { create: true, read: true, update: true, delete: true }
              : { create: false, read: true, update: true, delete: false },
            created_by_user_id: 'admin-123',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z'
          },
          {
            permission_id: 'perm-pdf-' + requestedUserId,
            user_id: requestedUserId,
            agent_name: 'pdf_processing',
            permissions: isAdmin 
              ? { create: true, read: true, update: true, delete: false }
              : { create: false, read: true, update: false, delete: false },
            created_by_user_id: 'admin-123',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z'
          },
          {
            permission_id: 'perm-reports-' + requestedUserId,
            user_id: requestedUserId,
            agent_name: 'reports_analysis',
            permissions: isAdmin 
              ? { create: true, read: true, update: true, delete: false }
              : { create: false, read: true, update: false, delete: false },
            created_by_user_id: 'admin-123',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z'
          },
          {
            permission_id: 'perm-audio-' + requestedUserId,
            user_id: requestedUserId,
            agent_name: 'audio_recording',
            permissions: isAdmin 
              ? { create: true, read: true, update: false, delete: false }
              : { create: false, read: true, update: false, delete: false },
            created_by_user_id: 'admin-123',
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z'
          }
        ]
        
        return Promise.resolve(createMockResponse({
          user_id: requestedUserId,
          permissions: permissions,
          last_updated: '2025-01-01T00:00:00Z'
        }))
      }
      if (urlStr.includes('/templates') && method === 'GET') {
        return Promise.resolve(createMockResponse({
          templates: [
            {
              template_id: 'template-123',
              template_name: 'Default User',
              description: 'Basic permissions for regular users',
              permissions: {
                client_management: { create: false, read: true, update: true, delete: false },
                pdf_processing: { create: false, read: true, update: false, delete: false }
              },
              is_system_template: true,
              created_by_user_id: 'admin-123',
              created_at: '2025-01-01T00:00:00Z',
              updated_at: '2025-01-01T00:00:00Z'
            }
          ],
          total: 1
        }))
      }
    }
    
    // Users API endpoints
    if (urlStr.includes('/users')) {
      return Promise.resolve(createMockResponse({
        user_id: 'test-user-123',
        email: 'test@example.com',
        full_name: 'Test User',
        role: 'admin',
        is_active: true,
        totp_enabled: false,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z'
      }))
    }
    
    // Clients API endpoints
    if (urlStr.includes('/clients')) {
      return Promise.resolve(createMockResponse({
        client_id: 'client-123',
        name: 'Test Client',
        cpf: '123.456.789-09',
        birth_date: '1990-01-01',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
        is_active: true
      }))
    }
    
    // Default successful response for unknown endpoints
    return Promise.resolve(createMockResponse({ success: true }))
  })
}

// Mock do matchMedia para componentes responsivos
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock do ResizeObserver para componentes adaptativos
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock do IntersectionObserver para scroll infinito
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock pointer capture APIs para Radix UI
Element.prototype.hasPointerCapture = vi.fn(() => false)
Element.prototype.setPointerCapture = vi.fn()
Element.prototype.releasePointerCapture = vi.fn()

// Mock scrollTo e scrollIntoView para navegação
Element.prototype.scrollTo = vi.fn()
Element.prototype.scrollIntoView = vi.fn()
window.scrollTo = vi.fn()

// Mock getBoundingClientRect para layout calculations
Element.prototype.getBoundingClientRect = vi.fn(() => ({
  x: 0,
  y: 0,
  top: 0,
  left: 0,
  bottom: 0,
  right: 0,
  width: 0,
  height: 0,
  toJSON: vi.fn(),
}))

// Mock getComputedStyle
window.getComputedStyle = vi.fn(() => ({
  getPropertyValue: vi.fn(() => ''),
})) as any

// Mock WebSocket - API externa
global.WebSocket = vi.fn().mockImplementation((url) => ({
  url,
  readyState: 1, // OPEN
  CONNECTING: 0,
  OPEN: 1,
  CLOSING: 2,
  CLOSED: 3,
  close: vi.fn(),
  send: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  dispatchEvent: vi.fn(),
  onopen: null,
  onclose: null,
  onmessage: null,
  onerror: null,
})) as any

// Mock console.warn para suprimir warnings esperados em testes
const originalWarn = console.warn
beforeAll(() => {
  console.warn = vi.fn()
})

afterAll(() => {
  console.warn = originalWarn
})

// Setup default mocks before each test
beforeEach(() => {
  vi.clearAllMocks()
  setupDefaultFetchMocks()
})

// Cleanup após cada teste
afterEach(() => {
  vi.clearAllMocks()
})