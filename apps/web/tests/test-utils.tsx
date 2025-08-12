/**
 * Custom render function and test utilities for React Testing Library.
 */

import { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from '@/components/theme-provider'
import { ErrorProvider } from '@/components/errors/ErrorContext'

// Create a custom QueryClient for tests
const createTestQueryClient = () => 
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: Infinity,
      },
      mutations: {
        retry: false,
      },
    },
  })

// Mock localStorage for tests
const mockLocalStorage = (() => {
  let store: Record<string, string> = {}
  
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value
    },
    removeItem: (key: string) => {
      delete store[key]
    },
    clear: () => {
      store = {}
    },
  }
})()

// Setup mock localStorage globally for tests
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
})

// Custom render function with providers
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  queryClient?: QueryClient
}

function customRender(
  ui: ReactElement,
  {
    queryClient = createTestQueryClient(),
    ...renderOptions
  }: CustomRenderOptions = {}
) {
  const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
    return (
      <ErrorProvider enableConsoleLogging={false} enableGlobalErrorHandler={false}>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </ErrorProvider>
    )
  }

  return render(ui, { wrapper: AllTheProviders, ...renderOptions })
}

// Mock data generators
export const mockUser = {
  id: '1',
  email: 'test@example.com',
  name: 'Test User',
  role: 'user',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
}

export const mockClient = {
  id: '1',
  name: 'Test Client',
  email: 'client@example.com',
  cpf_cnpj: '12345678901',
  phone: '+55 11 99999-9999',
  status: 'active' as const,
  metadata: {},
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
}

// Utility functions for tests
export const waitForLoadingToFinish = () =>
  new Promise((resolve) => setTimeout(resolve, 0))

export const createMockIntersectionObserver = () => {
  const mockIntersectionObserver = {
    observe: vi.fn(),
    disconnect: vi.fn(),
    unobserve: vi.fn(),
  }

  window.IntersectionObserver = vi.fn().mockImplementation(() => mockIntersectionObserver)
  
  return mockIntersectionObserver
}

// Custom matchers (if needed)
declare global {
  namespace Vi {
    interface JestAssertion<T = any> {
      toHaveNoViolations(): void
    }
  }
}

// Re-export everything from React Testing Library
export * from '@testing-library/react'
export { userEvent } from '@testing-library/user-event'

// Export our custom render as the default render
export { customRender as render }