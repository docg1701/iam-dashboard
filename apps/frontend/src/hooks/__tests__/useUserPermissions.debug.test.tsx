/**
 * Debug test for useUserPermissions hook
 * 
 * Isolate the permission check logic to understand why it's returning true
 * when it should return false for admin users without specific permissions.
 */

import React from 'react'
import { renderHook, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

import { usePermissionCheck, useUserPermissions } from '../useUserPermissions'
import { AgentName } from '@/types/permissions'
import { 
  createMockAdminUser,
  createMockUserAgentPermission,
  setupPermissionAPITest,
  createTestQueryClientConfig
} from '@/test/api-mocks'
import { setupAuthenticatedUser } from '@/test/auth-helpers'
import useAuthStore from '@/store/authStore'

const createTestQueryClient = () => new QueryClient(createTestQueryClientConfig())

const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = createTestQueryClient()
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('useUserPermissions Debug', () => {
  beforeEach(() => {
    // Setup mocks
    global.fetch = vi.fn()
    global.ResizeObserver = vi.fn().mockImplementation(() => ({
      observe: vi.fn(),
      unobserve: vi.fn(),
      disconnect: vi.fn(),
    }))
    global.WebSocket = vi.fn().mockImplementation(() => ({
      close: vi.fn(),
      send: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      CONNECTING: 0,
      OPEN: 1,
      CLOSING: 2,
      CLOSED: 3,
      readyState: 1,
      url: '',
      protocol: '',
      extensions: '',
      bufferedAmount: 0,
      binaryType: 'blob' as BinaryType,
      onopen: null,
      onclose: null,
      onmessage: null,
      onerror: null,
      dispatchEvent: vi.fn(),
    })) as any
  })

  afterEach(() => {
    vi.clearAllMocks()
    useAuthStore.getState().clearAuth()
  })

  it('should return false for admin user without delete permission', async () => {
    // Setup limited admin user
    const limitedAdminUser = createMockAdminUser({
      user_id: 'debug-admin-123',
      email: 'debug.admin@test.com'
    })

    await act(async () => {
      // Setup auth state
      setupAuthenticatedUser('admin')
      useAuthStore.setState({ user: limitedAdminUser })

      // Setup API mock with NO delete permission for PDF processing
      const adminPermissions = [
        createMockUserAgentPermission(limitedAdminUser.user_id, AgentName.PDF_PROCESSING, 
          { create: true, read: true, update: true, delete: false }) // NO delete permission
      ]

      setupPermissionAPITest({ 
        userId: limitedAdminUser.user_id,
        userPermissions: adminPermissions
      })
    })

    // Test the hook directly
    const { result } = renderHook(
      () => usePermissionCheck(AgentName.PDF_PROCESSING, 'delete'),
      { wrapper: TestWrapper }
    )

    // Wait for the API call to complete
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    console.log('usePermissionCheck result:', result.current)
    console.log('User ID:', limitedAdminUser.user_id)
    console.log('Agent:', AgentName.PDF_PROCESSING)
    console.log('Operation:', 'delete')
    console.log('Allowed:', result.current.allowed)

    // The permission check should return false
    expect(result.current.allowed).toBe(false)
  })

  it('should return the correct permission matrix', async () => {
    // Setup limited admin user
    const limitedAdminUser = createMockAdminUser({
      user_id: 'matrix-admin-123',
      email: 'matrix.admin@test.com'
    })

    await act(async () => {
      // Setup auth state
      setupAuthenticatedUser('admin')
      useAuthStore.setState({ user: limitedAdminUser })

      // Setup API mock with NO delete permission for PDF processing
      const adminPermissions = [
        createMockUserAgentPermission(limitedAdminUser.user_id, AgentName.PDF_PROCESSING, 
          { create: true, read: true, update: true, delete: false }) // NO delete permission
      ]

      setupPermissionAPITest({ 
        userId: limitedAdminUser.user_id,
        userPermissions: adminPermissions
      })
    })

    // Test the main hook
    const { result } = renderHook(
      () => useUserPermissions(),
      { wrapper: TestWrapper }
    )

    // Wait for the API call to complete
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    console.log('useUserPermissions result:', {
      permissions: result.current.permissions,
      error: result.current.error,
      isLoading: result.current.isLoading
    })

    // Check the permission matrix directly
    const pdfPermissions = result.current.permissions?.[AgentName.PDF_PROCESSING]
    console.log('PDF Processing permissions:', pdfPermissions)

    expect(pdfPermissions?.delete).toBe(false)
  })
})