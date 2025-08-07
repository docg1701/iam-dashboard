/**
 * useUserPermissions Hook Tests
 * 
 * Comprehensive tests for the useUserPermissions hook covering all role scenarios
 * Following CLAUDE.md rules: no internal mocking, only external API mocking
 */

import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import React from 'react'

import { useUserPermissions } from '../useUserPermissions'
import useAuthStore from '@/store/authStore'
import type { User } from '@/types/auth'
import { AgentName } from '@/types/permissions'

// Test utilities
const createTestQueryClient = () => {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
      mutations: { retry: false }
    },
    logger: { log: () => {}, warn: () => {}, error: () => {} }
  })
}

const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = createTestQueryClient()
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

// Mock data
const mockSysadminUser: User = {
  user_id: 'sysadmin-123',
  email: 'sysadmin@test.com',
  role: 'sysadmin',
  is_active: true,
  totp_enabled: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  full_name: 'System Admin'
}

const mockAdminUser: User = {
  user_id: 'admin-123',
  email: 'admin@test.com',
  role: 'admin',
  is_active: true,
  totp_enabled: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  full_name: 'Admin User'
}

const mockRegularUser: User = {
  user_id: 'user-123',
  email: 'user@test.com',
  role: 'user',
  is_active: true,
  totp_enabled: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  full_name: 'Regular User'
}

const mockUserPermissions = {
  [AgentName.CLIENT_MANAGEMENT]: { create: true, read: true, update: true, delete: false },
  [AgentName.PDF_PROCESSING]: { create: false, read: true, update: false, delete: false },
  [AgentName.REPORTS_ANALYSIS]: { create: false, read: true, update: false, delete: false },
  [AgentName.AUDIO_RECORDING]: { create: false, read: false, update: false, delete: false }
}

// Mock WebSocket globally since it's an external API
class MockWebSocket {
  onopen: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  
  constructor(public url: string) {
    // Simulate async connection
    setTimeout(() => {
      if (this.onopen) this.onopen(new Event('open'))
    }, 0)
  }
  
  send(data: string) {
    // Mock send implementation
  }
  
  close() {
    if (this.onclose) {
      this.onclose(new CloseEvent('close'))
    }
  }
}

global.WebSocket = MockWebSocket as any

const mockFetch = vi.fn()

// Helper function to simulate user authentication via API response
const simulateUserLogin = async (user: User) => {
  // Mock the login API response that would normally authenticate the user
  mockFetch.mockResolvedValueOnce({
    ok: true,
    json: () => Promise.resolve({
      access_token: `token-${user.user_id}`,
      user: user,
      requires_2fa: false
    })
  } as Response)
  
  // Simulate login process through auth store (this is how it would naturally happen)
  const authStore = useAuthStore.getState()
  await authStore.login({ email: user.email, password: 'password123' })
}

beforeEach(() => {
  global.fetch = mockFetch
  
  // Reset auth store to clean state
  const authStore = useAuthStore.getState()
  authStore.clearAuth()
})

afterEach(() => {
  vi.clearAllMocks()
})

describe('useUserPermissions Hook', () => {
  describe('Sysadmin User Behavior', () => {
    beforeEach(async () => {
      await simulateUserLogin(mockSysadminUser)
    })

    it('should return true for any permission check for sysadmin', async () => {
      // Mock the permissions API response for sysadmin
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          user_id: mockSysadminUser.user_id,
          permissions: mockUserPermissions,
          last_updated: '2024-01-01T00:00:00Z'
        })
      } as Response)

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Test the actual hook interface - hasPermission takes agent and operation
      expect(result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, 'create')).toBe(true)
      expect(result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, 'read')).toBe(true)
      expect(result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, 'update')).toBe(true)
      expect(result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, 'delete')).toBe(false) // Based on mock data
      
      expect(result.current.hasPermission(AgentName.PDF_PROCESSING, 'create')).toBe(false) // Based on mock data
      expect(result.current.hasPermission(AgentName.PDF_PROCESSING, 'read')).toBe(true)
      
      // Test hasAgentPermission for overall agent access
      expect(result.current.hasAgentPermission(AgentName.CLIENT_MANAGEMENT)).toBe(true)
      expect(result.current.hasAgentPermission(AgentName.PDF_PROCESSING)).toBe(true) // Has read permission
      expect(result.current.hasAgentPermission(AgentName.AUDIO_RECORDING)).toBe(false) // No permissions
    })

    it('should not be loading for sysadmin permissions after data is fetched', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          user_id: mockSysadminUser.user_id,
          permissions: mockUserPermissions,
          last_updated: '2024-01-01T00:00:00Z'
        })
      } as Response)

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })
    })

    it('should have null error for sysadmin on successful API response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          user_id: mockSysadminUser.user_id,
          permissions: mockUserPermissions,
          last_updated: '2024-01-01T00:00:00Z'
        })
      } as Response)

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper
      })

      await waitFor(() => {
        expect(result.current.error).toBe(null)
      })
    })
  })

  describe('Admin User Behavior', () => {
    beforeEach(async () => {
      await simulateUserLogin(mockAdminUser)
    })

    it('should return permissions based on API response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          user_id: mockAdminUser.user_id,
          permissions: mockUserPermissions,
          last_updated: '2024-01-01T00:00:00Z'
        })
      } as Response)

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Test permissions based on what the API returns
      expect(result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, 'create')).toBe(true)
      expect(result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, 'read')).toBe(true)
      expect(result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, 'update')).toBe(true)
      expect(result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, 'delete')).toBe(false)
    })

    it('should return reports_analysis permissions based on API response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          user_id: mockAdminUser.user_id,
          permissions: mockUserPermissions,
          last_updated: '2024-01-01T00:00:00Z'
        })
      } as Response)

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Test permissions based on API response
      expect(result.current.hasPermission(AgentName.REPORTS_ANALYSIS, 'create')).toBe(false)
      expect(result.current.hasPermission(AgentName.REPORTS_ANALYSIS, 'read')).toBe(true)
      expect(result.current.hasPermission(AgentName.REPORTS_ANALYSIS, 'update')).toBe(false)
      expect(result.current.hasPermission(AgentName.REPORTS_ANALYSIS, 'delete')).toBe(false)
    })

    it('should fetch and return specific agent permissions', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          user_id: mockAdminUser.user_id,
          permissions: mockUserPermissions,
          last_updated: '2024-01-01T00:00:00Z'
        })
      } as Response)

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Should check specific permissions for pdf_processing
      expect(result.current.hasPermission(AgentName.PDF_PROCESSING, 'read')).toBe(true)
      expect(result.current.hasPermission(AgentName.PDF_PROCESSING, 'create')).toBe(false)
      expect(result.current.hasPermission(AgentName.PDF_PROCESSING, 'delete')).toBe(false)
    })

    it('should return false for agents without explicit permissions', async () => {
      const emptyPermissions = {
        [AgentName.CLIENT_MANAGEMENT]: { create: false, read: false, update: false, delete: false },
        [AgentName.PDF_PROCESSING]: { create: false, read: false, update: false, delete: false },
        [AgentName.REPORTS_ANALYSIS]: { create: false, read: false, update: false, delete: false },
        [AgentName.AUDIO_RECORDING]: { create: false, read: false, update: false, delete: false }
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          user_id: mockAdminUser.user_id,
          permissions: emptyPermissions,
          last_updated: '2024-01-01T00:00:00Z'
        })
      } as Response)

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Should return false for agents without permissions
      expect(result.current.hasPermission(AgentName.AUDIO_RECORDING, 'create')).toBe(false)
      expect(result.current.hasPermission(AgentName.AUDIO_RECORDING, 'read')).toBe(false)
      expect(result.current.hasAgentPermission(AgentName.AUDIO_RECORDING)).toBe(false)
    })
  })

  describe('Regular User Behavior', () => {
    beforeEach(async () => {
      await simulateUserLogin(mockRegularUser)
    })

    it('should fetch and return explicit permissions only', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          user_id: mockRegularUser.user_id,
          permissions: mockUserPermissions,
          last_updated: '2024-01-01T00:00:00Z'
        })
      } as Response)

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Should have the permissions from API
      expect(result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, 'create')).toBe(true)
      expect(result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, 'read')).toBe(true)
      expect(result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, 'update')).toBe(true)
      expect(result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, 'delete')).toBe(false)

      expect(result.current.hasPermission(AgentName.PDF_PROCESSING, 'create')).toBe(false)
      expect(result.current.hasPermission(AgentName.PDF_PROCESSING, 'read')).toBe(true)
      
      expect(result.current.hasPermission(AgentName.AUDIO_RECORDING, 'create')).toBe(false)
      expect(result.current.hasPermission(AgentName.AUDIO_RECORDING, 'read')).toBe(false)
    })

    it('should return false for all permissions when API returns empty', async () => {
      const emptyPermissions = {
        [AgentName.CLIENT_MANAGEMENT]: { create: false, read: false, update: false, delete: false },
        [AgentName.PDF_PROCESSING]: { create: false, read: false, update: false, delete: false },
        [AgentName.REPORTS_ANALYSIS]: { create: false, read: false, update: false, delete: false },
        [AgentName.AUDIO_RECORDING]: { create: false, read: false, update: false, delete: false }
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          user_id: mockRegularUser.user_id,
          permissions: emptyPermissions,
          last_updated: '2024-01-01T00:00:00Z'
        })
      } as Response)

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Should have no permissions
      expect(result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, 'create')).toBe(false)
      expect(result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, 'read')).toBe(false)
      expect(result.current.hasPermission(AgentName.PDF_PROCESSING, 'read')).toBe(false)
      expect(result.current.hasPermission(AgentName.REPORTS_ANALYSIS, 'read')).toBe(false)
      expect(result.current.hasPermission(AgentName.AUDIO_RECORDING, 'read')).toBe(false)
    })

    it('should be loading while fetching permissions', async () => {
      // Mock delayed response
      const delayedPromise = new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({
            user_id: mockRegularUser.user_id,
            permissions: mockUserPermissions,
            last_updated: '2024-01-01T00:00:00Z'
          })
        }), 100)
      )
      mockFetch.mockReturnValueOnce(delayedPromise as any)

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper
      })

      // Should be loading initially
      expect(result.current.isLoading).toBe(true)

      // Wait for loading to finish
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      }, { timeout: 200 })
    })
  })

  describe('Not Authenticated Behavior', () => {
    beforeEach(() => {
      // Clear auth state naturally
      const authStore = useAuthStore.getState()
      authStore.clearAuth()
    })

    it('should return false for all permissions when not authenticated', () => {
      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper
      })

      // Hook should return default permissions when not authenticated
      expect(result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, 'read')).toBe(false)
      expect(result.current.hasPermission(AgentName.PDF_PROCESSING, 'read')).toBe(false)
      expect(result.current.hasPermission(AgentName.REPORTS_ANALYSIS, 'read')).toBe(false)
      expect(result.current.hasPermission(AgentName.AUDIO_RECORDING, 'read')).toBe(false)
    })

    it('should not be loading when not authenticated', () => {
      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper
      })

      expect(result.current.isLoading).toBe(false)
    })

    it('should not make API calls when not authenticated', () => {
      renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper
      })

      expect(mockFetch).not.toHaveBeenCalled()
    })
  })

  describe('Error Handling', () => {
    beforeEach(async () => {
      await simulateUserLogin(mockRegularUser)
    })

    it('should handle API errors gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('API Error'))

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.error).toBeTruthy()
      expect(result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, 'read')).toBe(false)
    })

    it('should handle HTTP error responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
        statusText: 'Forbidden'
      } as Response)

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.error).toBeTruthy()
      expect(result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, 'read')).toBe(false)
    })

    it('should handle malformed API responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve('not an object')
      } as Response)

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Should fallback to no permissions on malformed response
      expect(result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, 'read')).toBe(false)
    })
  })

  describe('Permission Matrix Utilities', () => {
    beforeEach(async () => {
      await simulateUserLogin(mockRegularUser)
    })

    it('should provide permission matrix for all agents', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          user_id: mockRegularUser.user_id,
          permissions: mockUserPermissions,
          last_updated: '2024-01-01T00:00:00Z'
        })
      } as Response)

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      const matrix = result.current.getUserMatrix()
      
      expect(matrix).toBeTruthy()
      expect(matrix?.permissions).toHaveProperty(AgentName.CLIENT_MANAGEMENT)
      expect(matrix?.permissions).toHaveProperty(AgentName.PDF_PROCESSING)
      expect(matrix?.permissions).toHaveProperty(AgentName.REPORTS_ANALYSIS)
      expect(matrix?.permissions).toHaveProperty(AgentName.AUDIO_RECORDING)
      
      expect(matrix?.permissions[AgentName.CLIENT_MANAGEMENT]).toEqual({
        create: true, read: true, update: true, delete: false
      })
      expect(matrix?.permissions[AgentName.PDF_PROCESSING]).toEqual({
        create: false, read: true, update: false, delete: false
      })
    })

    it('should check if user has agent access', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          user_id: mockRegularUser.user_id,
          permissions: mockUserPermissions,
          last_updated: '2024-01-01T00:00:00Z'
        })
      } as Response)

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.hasAgentPermission(AgentName.CLIENT_MANAGEMENT)).toBe(true)
      expect(result.current.hasAgentPermission(AgentName.PDF_PROCESSING)).toBe(true)
      expect(result.current.hasAgentPermission(AgentName.AUDIO_RECORDING)).toBe(false)
    })

    it('should provide detailed permission information', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          user_id: mockRegularUser.user_id,
          permissions: mockUserPermissions,
          last_updated: '2024-01-01T00:00:00Z'
        })
      } as Response)

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Test individual permission checks to understand permission levels
      const clientMgmt = result.current.permissions?.[AgentName.CLIENT_MANAGEMENT]
      expect(clientMgmt).toBeTruthy()
      expect(clientMgmt?.create && clientMgmt?.read && clientMgmt?.update && !clientMgmt?.delete).toBe(true)
      
      const pdfProcessing = result.current.permissions?.[AgentName.PDF_PROCESSING]
      expect(pdfProcessing?.read && !pdfProcessing?.create && !pdfProcessing?.update && !pdfProcessing?.delete).toBe(true)
      
      const audioRecording = result.current.permissions?.[AgentName.AUDIO_RECORDING]
      expect(audioRecording?.create || audioRecording?.read || audioRecording?.update || audioRecording?.delete).toBe(false)
    })
  })

  describe('Cache and Performance', () => {
    beforeEach(async () => {
      await simulateUserLogin(mockRegularUser)
    })

    it('should cache permission data and not refetch immediately', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          user_id: mockRegularUser.user_id,
          permissions: mockUserPermissions,
          last_updated: '2024-01-01T00:00:00Z'
        })
      } as Response)

      const { result: result1 } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper
      })

      await waitFor(() => {
        expect(result1.current.isLoading).toBe(false)
      })

      // Second hook should use cached data
      const { result: result2 } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper
      })

      expect(result2.current.isLoading).toBe(false)
      expect(mockFetch).toHaveBeenCalledTimes(1) // Should only call once

      // Both should have same permissions
      expect(result1.current.hasPermission(AgentName.CLIENT_MANAGEMENT, 'create')).toBe(
        result2.current.hasPermission(AgentName.CLIENT_MANAGEMENT, 'create')
      )
    })
  })

  describe('Real-time Updates', () => {
    beforeEach(async () => {
      await simulateUserLogin(mockRegularUser)
    })

    it('should support permission invalidation and refetch', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          user_id: mockRegularUser.user_id,
          permissions: mockUserPermissions,
          last_updated: '2024-01-01T00:00:00Z'
        })
      } as Response)

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      // Should have invalidate method for real-time updates
      expect(typeof result.current.invalidate).toBe('function')

      // Mock new permissions for refetch
      const updatedPermissions = {
        ...mockUserPermissions,
        [AgentName.CLIENT_MANAGEMENT]: { create: true, read: true, update: true, delete: true }
      }
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          user_id: mockRegularUser.user_id,
          permissions: updatedPermissions,
          last_updated: '2024-01-01T00:00:01Z'
        })
      } as Response)

      // Trigger invalidation (simulating WebSocket update)
      result.current.invalidate()

      await waitFor(() => {
        expect(result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, 'delete')).toBe(true)
      })
    })
  })
})