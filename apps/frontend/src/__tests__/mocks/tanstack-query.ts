/**
 * TanStack Query Mock Types and Utilities
 * 
 * Provides comprehensive type-safe mocks for TanStack Query mutations
 * and queries using proper TypeScript types for maximum type safety.
 */

import { vi } from 'vitest'
import type { UseMutationResult, UseQueryResult } from '@tanstack/react-query'

// Type definitions for mock utilities
interface MockMutationOverrides<TData = unknown, TError = Error, TVariables = void, TContext = unknown> {
  data?: TData
  error?: TError | null
  variables?: TVariables
  context?: TContext
  isIdle?: boolean
  isPending?: boolean
  isError?: boolean
  isSuccess?: boolean
  isPaused?: boolean
  failureCount?: number
  failureReason?: TError | null
  mutate?: ReturnType<typeof vi.fn>
  mutateAsync?: ReturnType<typeof vi.fn>
  reset?: ReturnType<typeof vi.fn>
  status?: 'idle' | 'pending' | 'error' | 'success'
  submittedAt?: number
}

interface MockQueryOverrides<TData = unknown, TError = Error> {
  data?: TData
  dataUpdatedAt?: number
  error?: TError | null
  errorUpdatedAt?: number
  errorUpdateCount?: number
  failureCount?: number
  failureReason?: TError | null
  fetchStatus?: 'idle' | 'fetching' | 'paused'
  isError?: boolean
  isEnabled?: boolean
  isFetched?: boolean
  isFetchedAfterMount?: boolean
  isFetching?: boolean
  isInitialLoading?: boolean
  isLoading?: boolean
  isLoadingError?: boolean
  isPaused?: boolean
  isPending?: boolean
  isPlaceholderData?: boolean
  isRefetchError?: boolean
  isRefetching?: boolean
  isStale?: boolean
  isSuccess?: boolean
  promise?: Promise<TData>
  refetch?: ReturnType<typeof vi.fn>
  status?: 'pending' | 'error' | 'success'
}

/**
 * Creates a complete mock for UseMutationResult with all required properties
 */
export function createMockMutation<TData = unknown, TError = Error, TVariables = void, TContext = unknown>(
  overrides: MockMutationOverrides<TData, TError, TVariables, TContext> = {}
): UseMutationResult<TData, TError, TVariables, TContext> {
  const baseMutation = {
    data: undefined as TData | undefined,
    error: null as TError | null,
    variables: undefined as TVariables | undefined,
    context: undefined as TContext | undefined,
    isIdle: true,
    isPending: false,
    isError: false,
    isSuccess: false,
    isPaused: false,
    failureCount: 0,
    failureReason: null as TError | null,
    mutate: vi.fn(),
    mutateAsync: vi.fn().mockResolvedValue(undefined),
    reset: vi.fn(),
    status: 'idle' as const,
    submittedAt: 0,
    ...overrides,
  }

  return baseMutation as UseMutationResult<TData, TError, TVariables, TContext>
}

/**
 * Creates a loading state mutation mock
 */
export function createLoadingMutation<TData = unknown, TError = Error, TVariables = void, TContext = unknown>(
  overrides: MockMutationOverrides<TData, TError, TVariables, TContext> = {}
): UseMutationResult<TData, TError, TVariables, TContext> {
  return createMockMutation<TData, TError, TVariables, TContext>({
    isIdle: false,
    isPending: true,
    status: 'pending',
    submittedAt: Date.now(),
    ...overrides,
  })
}

/**
 * Creates a success state mutation mock
 */
export function createSuccessMutation<TData = unknown, TError = Error, TVariables = void, TContext = unknown>(
  data: TData,
  variables?: TVariables,
  overrides: MockMutationOverrides<TData, TError, TVariables, TContext> = {}
): UseMutationResult<TData, TError, TVariables, TContext> {
  return createMockMutation<TData, TError, TVariables, TContext>({
    data,
    variables,
    isIdle: false,
    isSuccess: true,
    status: 'success',
    submittedAt: Date.now(),
    ...overrides,
  })
}

/**
 * Creates an error state mutation mock
 */
export function createErrorMutation<TData = unknown, TError = Error, TVariables = void, TContext = unknown>(
  error: TError,
  variables?: TVariables,
  overrides: MockMutationOverrides<TData, TError, TVariables, TContext> = {}
): UseMutationResult<TData, TError, TVariables, TContext> {
  return createMockMutation<TData, TError, TVariables, TContext>({
    error,
    variables,
    isIdle: false,
    isError: true,
    failureCount: 1,
    failureReason: error,
    status: 'error',
    submittedAt: Date.now(),
    ...overrides,
  })
}

/**
 * Creates a complete mock for UseQueryResult with all required properties
 */
export function createMockQuery<TData = unknown, TError = Error>(
  overrides: MockQueryOverrides<TData, TError> = {}
): UseQueryResult<TData, TError> {
  const baseQuery = {
    data: undefined as TData | undefined,
    dataUpdatedAt: 0,
    error: null as TError | null,
    errorUpdatedAt: 0,
    errorUpdateCount: 0,
    failureCount: 0,
    failureReason: null as TError | null,
    fetchStatus: 'idle' as const,
    isError: false,
    isEnabled: true,
    isFetched: true,
    isFetchedAfterMount: true,
    isFetching: false,
    isInitialLoading: false,
    isLoading: false,
    isLoadingError: false,
    isPaused: false,
    isPending: false,
    isPlaceholderData: false,
    isRefetchError: false,
    isRefetching: false,
    isStale: false,
    isSuccess: true,
    promise: Promise.resolve(undefined as TData),
    refetch: vi.fn().mockResolvedValue({} as { data: TData }),
    status: 'success' as const,
    ...overrides,
  }

  return baseQuery as UseQueryResult<TData, TError>
}

/**
 * Creates a loading state query mock
 */
export function createLoadingQuery<TData = unknown, TError = Error>(
  overrides: MockQueryOverrides<TData, TError> = {}
): UseQueryResult<TData, TError> {
  return createMockQuery<TData, TError>({
    data: undefined,
    isLoading: true,
    isPending: true,
    isSuccess: false,
    isFetched: false,
    isFetchedAfterMount: false,
    status: 'pending',
    fetchStatus: 'fetching',
    ...overrides,
  })
}

/**
 * Creates a success state query mock
 */
export function createSuccessQuery<TData = unknown, TError = Error>(
  data: TData,
  overrides: MockQueryOverrides<TData, TError> = {}
): UseQueryResult<TData, TError> {
  return createMockQuery<TData, TError>({
    data,
    isSuccess: true,
    isFetched: true,
    isFetchedAfterMount: true,
    status: 'success',
    dataUpdatedAt: Date.now(),
    ...overrides,
  })
}

/**
 * Creates an error state query mock
 */
export function createErrorQuery<TData = unknown, TError = Error>(
  error: TError,
  overrides: MockQueryOverrides<TData, TError> = {}
): UseQueryResult<TData, TError> {
  return createMockQuery<TData, TError>({
    data: undefined,
    error,
    isError: true,
    isSuccess: false,
    failureCount: 1,
    failureReason: error,
    status: 'error',
    errorUpdatedAt: Date.now(),
    ...overrides,
  })
}