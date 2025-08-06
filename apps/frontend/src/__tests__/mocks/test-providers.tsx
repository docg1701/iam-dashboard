/**
 * Test Provider Wrapper for React Testing Library
 * 
 * Provides all necessary context providers for testing permission components,
 * eliminating provider-related errors during test execution.
 */

import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Mock QueryClient for testing
const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      gcTime: 0,
    },
    mutations: {
      retry: false,
    },
  },
  logger: {
    log: () => {},
    warn: () => {},
    error: () => {},
  },
})

interface TestProvidersProps {
  children: React.ReactNode
}

/**
 * Comprehensive test wrapper providing all necessary contexts
 */
export const TestProviders: React.FC<TestProvidersProps> = ({ children }) => {
  const [queryClient] = React.useState(() => createTestQueryClient())

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

/**
 * Custom render function for React Testing Library
 * Use this instead of the default render function to automatically wrap components
 */
export const renderWithProviders = (ui: React.ReactElement, options: any = {}) => {
  const { container, ...restOptions } = options
  
  return {
    container: container || document.body,
    ...restOptions,
    wrapper: ({ children }: { children: React.ReactNode }) => (
      <TestProviders>{children}</TestProviders>
    ),
  }
}

/**
 * Enhanced wrapper for components requiring DOM portal support
 */
export const TestProvidersWithPortals: React.FC<TestProvidersProps> = ({ children }) => {
  const [queryClient] = React.useState(() => createTestQueryClient())
  
  // Create portal container for dialogs and modals
  React.useEffect(() => {
    const portalContainer = document.createElement('div')
    portalContainer.id = 'test-portal-container'
    document.body.appendChild(portalContainer)
    
    return () => {
      if (document.body.contains(portalContainer)) {
        document.body.removeChild(portalContainer)
      }
    }
  }, [])

  return (
    <QueryClientProvider client={queryClient}>
      <div data-testid="test-app-container">
        {children}
      </div>
    </QueryClientProvider>
  )
}

/**
 * Render function specifically for components that use portals (dialogs, tooltips, etc)
 */
export const renderWithPortals = (ui: React.ReactElement, options: any = {}) => {
  const { container, ...restOptions } = options
  
  return {
    container: container || document.body,
    ...restOptions,
    wrapper: ({ children }: { children: React.ReactNode }) => (
      <TestProvidersWithPortals>{children}</TestProvidersWithPortals>
    ),
  }
}