import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

/**
 * Standardized Query Client Configuration for Tests
 * 
 * Creates test-optimized QueryClient instances that:
 * - Disable retries for predictable test behavior
 * - Set immediate garbage collection and stale time
 * - Disable window focus/mount/reconnect refetching
 * - Suppress logging for clean test output
 */
export const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      // Disable retries for predictable test results
      retry: false,
      // Immediate garbage collection for test isolation
      gcTime: 0,
      // No stale time for fresh data in each test
      staleTime: 0,
      // Disable automatic refetching behaviors
      refetchOnWindowFocus: false,
      refetchOnMount: false,
      refetchOnReconnect: false,
      // Always allow network requests (for mocked fetch)
      networkMode: 'always',
    },
    mutations: { 
      // Disable mutation retries for predictable failures
      retry: false,
      // Always allow network requests (for mocked fetch)
      networkMode: 'always',
    }
  },
  // Suppress all logging during tests for clean output
  logger: {
    log: () => {},
    warn: () => {},
    error: () => {},
  }
})

/**
 * Test Wrapper Component with QueryClient Provider
 * 
 * Provides a configured QueryClient for testing React components
 * that use React Query hooks.
 */
interface TestQueryWrapperProps {
  children: React.ReactNode
  client?: QueryClient
}

export const TestQueryWrapper = ({ 
  children, 
  client = createTestQueryClient() 
}: TestQueryWrapperProps) => (
  <QueryClientProvider client={client}>
    {children}
  </QueryClientProvider>
)

/**
 * Hook to access the test QueryClient instance
 * 
 * Useful for advanced test scenarios where you need direct
 * access to the QueryClient (e.g., pre-populating cache)
 */
export const useTestQueryClient = () => createTestQueryClient()

/**
 * Utility to pre-populate QueryClient cache for tests
 * 
 * @param client - QueryClient instance
 * @param queries - Array of query key/data pairs to pre-populate
 */
export const populateTestCache = (
  client: QueryClient, 
  queries: Array<{ queryKey: any[], data: any }>
) => {
  queries.forEach(({ queryKey, data }) => {
    client.setQueryData(queryKey, data)
  })
}

/**
 * Common Query Keys used throughout the application
 * 
 * Centralized for consistency between production and test code
 */
export const QueryKeys = {
  // Authentication
  currentUser: () => ['auth', 'current-user'],
  authStatus: () => ['auth', 'status'],
  
  // User management
  users: () => ['users'],
  user: (id: string) => ['users', id],
  userPermissions: (userId: string) => ['users', userId, 'permissions'],
  
  // Client management
  clients: () => ['clients'],
  client: (id: string) => ['clients', id],
  
  // Permissions
  permissions: () => ['permissions'],
  permissionTemplates: () => ['permissions', 'templates'],
  permissionTemplate: (id: string) => ['permissions', 'templates', id],
  userAgentPermissions: (userId: string, agent: string) => ['permissions', 'users', userId, 'agents', agent],
  permissionAudit: (userId?: string, agent?: string) => ['permissions', 'audit', userId, agent].filter(Boolean),
  
  // Permission checks
  permissionCheck: (userId: string, agent: string, operation: string) => 
    ['permissions', 'check', userId, agent, operation],
    
  // Bulk operations
  bulkPermissions: () => ['permissions', 'bulk'],
} as const

export default {
  createTestQueryClient,
  TestQueryWrapper,
  useTestQueryClient,
  populateTestCache,
  QueryKeys,
}