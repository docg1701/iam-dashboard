import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React, { ReactNode } from 'react'
import {
  useUserPermissions,
  usePermissionCheck,
} from '@/hooks/useUserPermissions'
import { AgentName, UserPermissionMatrix } from '@/types/permissions'
import { PermissionAPI } from '@/lib/api/permissions'

// Test wrapper component
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  function Wrapper({ children }: { children: ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children)
  }

  return Wrapper
}

// Mock permission data
const mockPermissionMatrix: UserPermissionMatrix = {
  user_id: 'test-user-id',
  permissions: {
    [AgentName.CLIENT_MANAGEMENT]: {
      create: true,
      read: true,
      update: false,
      delete: false,
    },
    [AgentName.PDF_PROCESSING]: {
      create: false,
      read: true,
      update: false,
      delete: false,
    },
    [AgentName.REPORTS_ANALYSIS]: {
      create: false,
      read: false,
      update: false,
      delete: false,
    },
    [AgentName.AUDIO_RECORDING]: {
      create: false,
      read: false,
      update: false,
      delete: false,
    },
  },
  last_updated: '2024-01-01T00:00:00Z',
}

describe('useUserPermissions', () => {
  const mockGetUserPermissions = vi.mocked(PermissionAPI.User.getUserPermissions)
  const mockHasPermission = vi.mocked(PermissionAPI.Utils.hasPermission)
  const mockHasAgentPermission = vi.mocked(PermissionAPI.Utils.hasAgentPermission)

  beforeEach(() => {
    vi.clearAllMocks()
    mockGetUserPermissions.mockResolvedValue(mockPermissionMatrix)
    mockHasPermission.mockReturnValue(true)
    mockHasAgentPermission.mockReturnValue(true)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('should fetch user permissions on mount', async () => {
    const wrapper = createWrapper()

    const { result } = renderHook(() => useUserPermissions('test-user-id'), {
      wrapper,
    })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(mockGetUserPermissions).toHaveBeenCalledWith('test-user-id')
    expect(result.current.permissions).toEqual(mockPermissionMatrix.permissions)
  })

  it('should check permissions correctly', async () => {
    const wrapper = createWrapper()

    const { result } = renderHook(() => useUserPermissions('test-user-id'), {
      wrapper,
    })

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    act(() => {
      result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, 'create')
    })

    expect(mockHasPermission).toHaveBeenCalledWith(
      mockPermissionMatrix.permissions,
      AgentName.CLIENT_MANAGEMENT,
      'create'
    )
  })

  it('should handle permission errors', async () => {
    const mockError = new Error('Permission fetch failed')
    
    // Clear all mocks and set up error scenario
    vi.clearAllMocks()
    mockGetUserPermissions.mockRejectedValue(mockError)

    const wrapper = createWrapper()

    const { result } = renderHook(() => useUserPermissions('test-user-id'), {
      wrapper,
    })

    await waitFor(
      () => {
        expect(result.current.isLoading).toBe(false)
      },
      { timeout: 3000 }
    )

    expect(result.current.error).toBeTruthy()
    expect(result.current.permissions).toBeNull()
  })
})

describe('usePermissionCheck', () => {
  const mockGetUserPermissions = vi.mocked(PermissionAPI.User.getUserPermissions)
  const mockHasPermission = vi.mocked(PermissionAPI.Utils.hasPermission)

  beforeEach(() => {
    vi.clearAllMocks()
    mockGetUserPermissions.mockResolvedValue(mockPermissionMatrix)
    mockHasPermission.mockReturnValue(true)
  })

  it('should check specific permission', async () => {
    const wrapper = createWrapper()

    const { result } = renderHook(
      () => usePermissionCheck(AgentName.CLIENT_MANAGEMENT, 'create', 'test-user-id'),
      { wrapper }
    )

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.allowed).toBe(true)
    expect(result.current.agent).toBe(AgentName.CLIENT_MANAGEMENT)
    expect(result.current.operation).toBe('create')
  })
})