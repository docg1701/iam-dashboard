import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock apenas APIs externas - NUNCA componentes internos
global.fetch = vi.fn()

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

// Cleanup após cada teste
afterEach(() => {
  vi.clearAllMocks()
})