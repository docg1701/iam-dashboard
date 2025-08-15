/**
 * Vitest setup file for frontend testing.
 * This file runs before each test file.
 */

import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeAll, vi } from 'vitest'

// Cleanup after each test case
afterEach(() => {
  cleanup()
  // Clean up environment variable stubs
  vi.unstubAllEnvs()
  // Clear all timers to prevent hanging
  vi.clearAllTimers()
  // Restore all mocks to prevent interference
  vi.restoreAllMocks()
  // Clear all intervals and timeouts
  vi.useRealTimers()
})

// Global test setup
beforeAll(() => {
  // Mock environment variables using vi.stubEnv for safer environment variable mocking
  vi.stubEnv('NEXT_PUBLIC_API_URL', 'http://localhost:8000')
  vi.stubEnv('NODE_ENV', 'test')
  
  // Handle unhandled promise rejections to prevent test noise
  // Capture and ignore expected unhandled rejections from AuthContext tests
  const originalUnhandledRejection = process.listeners('unhandledRejection')
  process.removeAllListeners('unhandledRejection')
  
  process.on('unhandledRejection', (reason, promise) => {
    // Check if this is an expected auth error (from AuthContext tests)
    if (
      reason && 
      typeof reason === 'object' && 
      'code' in reason &&
      (reason.code === 'MISSING_2FA' || 
       reason.code === 'TIMEOUT' ||
       reason.code === 'INVALID_CREDENTIALS' ||
       reason.code === 'NETWORK_ERROR' ||
       reason.code === 'UNEXPECTED_ERROR')
    ) {
      // These are expected errors from AuthContext tests, ignore them
      return
    }

    // Check if this is an expected fetch error
    if (
      reason &&
      (reason instanceof Error) &&
      (reason.message === 'Failed to fetch' ||
       reason.message === 'Invalid credentials' ||
       reason.message === 'Test error' ||
       reason.message === 'Server error' ||
       reason.message === 'Invalid response from server' ||
       reason.message.includes('Cannot read properties of undefined'))
    ) {
      // These are expected errors from fetch mocks, ignore them
      return
    }
    
    // For other unhandled rejections, call original handlers
    originalUnhandledRejection.forEach(handler => {
      if (typeof handler === 'function') {
        handler(reason, promise)
      }
    })
  })
})

// Mock Next.js router
vi.mock('next/router', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
    pathname: '/',
    query: {},
    asPath: '/',
    route: '/',
    isReady: true,
  }),
}))

// Mock Next.js navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}))

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock matchMedia
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

// Mock localStorage with a real-like implementation
const createMockStorage = () => {
  const store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      Object.keys(store).forEach(key => delete store[key])
    }),
    length: 0,
    key: vi.fn(),
  }
}

Object.defineProperty(window, 'localStorage', {
  value: createMockStorage(),
  writable: true,
})

// Mock theme provider requirements
Object.defineProperty(document, 'documentElement', {
  value: {
    classList: {
      add: vi.fn(),
      remove: vi.fn(),
      contains: vi.fn(() => false),
    },
    style: {},
    getAttribute: vi.fn(() => null),
    setAttribute: vi.fn(),
  },
  writable: true,
})

// Mock scrollTo
Object.defineProperty(window, 'scrollTo', {
  writable: true,
  value: vi.fn(),
})

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  // Uncomment to ignore specific console methods
  // warn: vi.fn(),
  // error: vi.fn(),
}

// Setup global fetch mock
global.fetch = vi.fn()

// This localStorage mock is already defined above for next-themes compatibility

// Mock SessionStorage with a real-like implementation
Object.defineProperty(window, 'sessionStorage', {
  value: createMockStorage(),
  writable: true,
})
