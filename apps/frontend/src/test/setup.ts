import '@testing-library/jest-dom'
import { vi } from 'vitest'

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
        return Promise.resolve(createMockResponse({
          user_id: 'test-user-123',
          permissions: [
            {
              permission_id: 'perm-client-123',
              user_id: 'test-user-123',
              agent_name: 'client_management',
              permissions: { create: true, read: true, update: true, delete: false },
              created_by_user_id: 'admin-123',
              created_at: '2025-01-01T00:00:00Z',
              updated_at: '2025-01-01T00:00:00Z'
            }
          ],
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
        ssn: '123-45-6789',
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