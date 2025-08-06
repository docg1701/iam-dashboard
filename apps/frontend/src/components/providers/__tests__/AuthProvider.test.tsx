/**
 * AuthProvider Component Tests
 * Tests authentication context provider, role-based access, and integration with Zustand store
 * Following CLAUDE.md rules: no internal mocking, only external API mocking
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider, useAuthContext, RoleGuard, ResourceGuard } from '../AuthProvider'
import useAuthStore from '@/store/authStore'
import type { User } from '@/types/auth'

// Mock only external fetch API for token refresh
const mockFetch = vi.fn()
global.fetch = mockFetch

// Test wrapper for providers
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

// Helper function to create mock users with different roles
const createMockUser = (role: 'sysadmin' | 'admin' | 'user'): User => ({
  user_id: `user-${role}-123`,
  email: `${role}@example.com`,
  full_name: `Test ${role}`,
  role,
  is_active: true,
  totp_enabled: false,
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
})

// Helper to create valid JWT token
const createValidToken = () => {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
  const payload = btoa(JSON.stringify({ 
    exp: Math.floor(Date.now() / 1000) + 3600, // expires in 1 hour
    user_id: 'user-123'
  }))
  const signature = 'mock-signature'
  return `${header}.${payload}.${signature}`
}

// Helper to create expired JWT token
const createExpiredToken = () => {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
  const payload = btoa(JSON.stringify({ 
    exp: Math.floor(Date.now() / 1000) - 3600, // expired 1 hour ago
    user_id: 'user-123'
  }))
  const signature = 'mock-signature'
  return `${header}.${payload}.${signature}`
}

beforeEach(() => {
  vi.clearAllMocks()
  mockFetch.mockReset()
  
  // Reset auth store to initial state
  useAuthStore.getState().clearAuth()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('AuthProvider', () => {
  describe('Context Provider Setup', () => {
    it('should render children and provide auth context', () => {
      const TestChild = () => {
        const context = useAuthContext()
        return (
          <div>
            <div data-testid="authenticated">{context.isAuthenticated.toString()}</div>
            <div data-testid="loading">{context.isLoading.toString()}</div>
          </div>
        )
      }

      render(
        <TestWrapper>
          <AuthProvider>
            <TestChild />
          </AuthProvider>
        </TestWrapper>
      )

      expect(screen.getByTestId('authenticated')).toHaveTextContent('false')
      expect(screen.getByTestId('loading')).toHaveTextContent('false')
    })

    it('should throw error when useAuthContext is used outside provider', () => {
      const TestChild = () => {
        useAuthContext()
        return <div>Should not render</div>
      }

      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      expect(() => {
        render(
          <TestWrapper>
            <TestChild />
          </TestWrapper>
        )
      }).toThrow('useAuthContext must be used within an AuthProvider')

      consoleSpy.mockRestore()
    })

    it('should provide all required context values', () => {
      const TestChild = () => {
        const context = useAuthContext()
        return (
          <div>
            <div data-testid="user">{context.user ? 'exists' : 'null'}</div>
            <div data-testid="authenticated">{context.isAuthenticated.toString()}</div>
            <div data-testid="loading">{context.isLoading.toString()}</div>
            <div data-testid="is-admin">{context.isAdmin.toString()}</div>
            <div data-testid="is-sysadmin">{context.isSysAdmin.toString()}</div>
            <div data-testid="has-role-function">{typeof context.hasRole === 'function' ? 'function' : 'not-function'}</div>
            <div data-testid="has-any-role-function">{typeof context.hasAnyRole === 'function' ? 'function' : 'not-function'}</div>
            <div data-testid="can-access-function">{typeof context.canAccess === 'function' ? 'function' : 'not-function'}</div>
          </div>
        )
      }

      render(
        <TestWrapper>
          <AuthProvider>
            <TestChild />
          </AuthProvider>
        </TestWrapper>
      )

      expect(screen.getByTestId('user')).toHaveTextContent('null')
      expect(screen.getByTestId('authenticated')).toHaveTextContent('false')
      expect(screen.getByTestId('loading')).toHaveTextContent('false')
      expect(screen.getByTestId('is-admin')).toHaveTextContent('false')
      expect(screen.getByTestId('is-sysadmin')).toHaveTextContent('false')
      expect(screen.getByTestId('has-role-function')).toHaveTextContent('function')
      expect(screen.getByTestId('has-any-role-function')).toHaveTextContent('function')
      expect(screen.getByTestId('can-access-function')).toHaveTextContent('function')
    })
  })

  describe('Auth State Propagation', () => {
    it('should propagate authenticated user state to children', () => {
      const mockUser = createMockUser('admin')
      const validToken = createValidToken()

      const TestChild = () => {
        const context = useAuthContext()
        return (
          <div>
            <div data-testid="authenticated">{context.isAuthenticated.toString()}</div>
            <div data-testid="user-email">{context.user?.email || 'no-email'}</div>
            <div data-testid="user-role">{context.user?.role || 'no-role'}</div>
            <div data-testid="is-admin">{context.isAdmin.toString()}</div>
          </div>
        )
      }

      act(() => {
        useAuthStore.getState().setUser(mockUser)
        useAuthStore.getState().setToken(validToken)
      })

      render(
        <TestWrapper>
          <AuthProvider>
            <TestChild />
          </AuthProvider>
        </TestWrapper>
      )

      expect(screen.getByTestId('authenticated')).toHaveTextContent('true')
      expect(screen.getByTestId('user-email')).toHaveTextContent('admin@example.com')
      expect(screen.getByTestId('user-role')).toHaveTextContent('admin')
      expect(screen.getByTestId('is-admin')).toHaveTextContent('true')
    })

    it('should propagate loading state to children', () => {
      const TestChild = () => {
        const context = useAuthContext()
        return (
          <div data-testid="loading">{context.isLoading.toString()}</div>
        )
      }

      act(() => {
        useAuthStore.getState().setLoading(true)
      })

      render(
        <TestWrapper>
          <AuthProvider>
            <TestChild />
          </AuthProvider>
        </TestWrapper>
      )

      expect(screen.getByTestId('loading')).toHaveTextContent('true')
    })

    it('should update context when auth state changes', () => {
      const mockUser = createMockUser('user')
      const validToken = createValidToken()

      const TestChild = () => {
        const context = useAuthContext()
        return (
          <div>
            <div data-testid="authenticated">{context.isAuthenticated.toString()}</div>
            <div data-testid="user-role">{context.user?.role || 'no-role'}</div>
          </div>
        )
      }

      const { rerender } = render(
        <TestWrapper>
          <AuthProvider>
            <TestChild />
          </AuthProvider>
        </TestWrapper>
      )

      expect(screen.getByTestId('authenticated')).toHaveTextContent('false')
      expect(screen.getByTestId('user-role')).toHaveTextContent('no-role')

      // Login user
      act(() => {
        useAuthStore.getState().setUser(mockUser)
        useAuthStore.getState().setToken(validToken)
      })

      rerender(
        <TestWrapper>
          <AuthProvider>
            <TestChild />
          </AuthProvider>
        </TestWrapper>
      )

      expect(screen.getByTestId('authenticated')).toHaveTextContent('true')
      expect(screen.getByTestId('user-role')).toHaveTextContent('user')

      // Logout user
      act(() => {
        useAuthStore.getState().clearAuth()
      })

      rerender(
        <TestWrapper>
          <AuthProvider>
            <TestChild />
          </AuthProvider>
        </TestWrapper>
      )

      expect(screen.getByTestId('authenticated')).toHaveTextContent('false')
      expect(screen.getByTestId('user-role')).toHaveTextContent('no-role')
    })
  })

  describe('Role-based Access Functions', () => {
    it('should provide hasRole function that works correctly', () => {
      const mockUser = createMockUser('admin')
      const validToken = createValidToken()

      const TestChild = () => {
        const context = useAuthContext()
        return (
          <div>
            <div data-testid="has-admin">{context.hasRole('admin').toString()}</div>
            <div data-testid="has-user">{context.hasRole('user').toString()}</div>
            <div data-testid="has-sysadmin">{context.hasRole('sysadmin').toString()}</div>
          </div>
        )
      }

      act(() => {
        useAuthStore.getState().setUser(mockUser)
        useAuthStore.getState().setToken(validToken)
      })

      render(
        <TestWrapper>
          <AuthProvider>
            <TestChild />
          </AuthProvider>
        </TestWrapper>
      )

      expect(screen.getByTestId('has-admin')).toHaveTextContent('true')
      expect(screen.getByTestId('has-user')).toHaveTextContent('true') // Admin can access user resources
      expect(screen.getByTestId('has-sysadmin')).toHaveTextContent('false')
    })

    it('should provide hasAnyRole function that works correctly', () => {
      const mockUser = createMockUser('user')
      const validToken = createValidToken()

      const TestChild = () => {
        const context = useAuthContext()
        return (
          <div>
            <div data-testid="has-admin-or-user">{context.hasAnyRole(['admin', 'user']).toString()}</div>
            <div data-testid="has-sysadmin-or-admin">{context.hasAnyRole(['sysadmin', 'admin']).toString()}</div>
            <div data-testid="has-user-only">{context.hasAnyRole(['user']).toString()}</div>
          </div>
        )
      }

      act(() => {
        useAuthStore.getState().setUser(mockUser)
        useAuthStore.getState().setToken(validToken)
      })

      render(
        <TestWrapper>
          <AuthProvider>
            <TestChild />
          </AuthProvider>
        </TestWrapper>
      )

      expect(screen.getByTestId('has-admin-or-user')).toHaveTextContent('true')
      expect(screen.getByTestId('has-sysadmin-or-admin')).toHaveTextContent('false')
      expect(screen.getByTestId('has-user-only')).toHaveTextContent('true')
    })

    it('should provide isAdmin and isSysAdmin computed properties', () => {
      const sysadminUser = createMockUser('sysadmin')
      const adminUser = createMockUser('admin')
      const regularUser = createMockUser('user')
      const validToken = createValidToken()

      const TestChild = () => {
        const context = useAuthContext()
        return (
          <div>
            <div data-testid="is-admin">{context.isAdmin.toString()}</div>
            <div data-testid="is-sysadmin">{context.isSysAdmin.toString()}</div>
          </div>
        )
      }

      // Test sysadmin
      act(() => {
        useAuthStore.getState().setUser(sysadminUser)
        useAuthStore.getState().setToken(validToken)
      })

      const { rerender } = render(
        <TestWrapper>
          <AuthProvider>
            <TestChild />
          </AuthProvider>
        </TestWrapper>
      )

      expect(screen.getByTestId('is-admin')).toHaveTextContent('true') // Sysadmin has admin permissions
      expect(screen.getByTestId('is-sysadmin')).toHaveTextContent('true')

      // Test admin
      act(() => {
        useAuthStore.getState().setUser(adminUser)
      })

      rerender(
        <TestWrapper>
          <AuthProvider>
            <TestChild />
          </AuthProvider>
        </TestWrapper>
      )

      expect(screen.getByTestId('is-admin')).toHaveTextContent('true')
      expect(screen.getByTestId('is-sysadmin')).toHaveTextContent('false')

      // Test regular user
      act(() => {
        useAuthStore.getState().setUser(regularUser)
      })

      rerender(
        <TestWrapper>
          <AuthProvider>
            <TestChild />
          </AuthProvider>
        </TestWrapper>
      )

      expect(screen.getByTestId('is-admin')).toHaveTextContent('false')
      expect(screen.getByTestId('is-sysadmin')).toHaveTextContent('false')
    })
  })

  describe('Resource-based Access Control', () => {
    it('should provide canAccess function for resource-based permissions', () => {
      const adminUser = createMockUser('admin')
      const validToken = createValidToken()

      const TestChild = () => {
        const context = useAuthContext()
        return (
          <div>
            <div data-testid="can-read-users">{context.canAccess('users', 'read').toString()}</div>
            <div data-testid="can-create-users">{context.canAccess('users', 'create').toString()}</div>
            <div data-testid="can-delete-users">{context.canAccess('users', 'delete').toString()}</div>
            <div data-testid="can-read-clients">{context.canAccess('clients', 'read').toString()}</div>
            <div data-testid="can-read-settings">{context.canAccess('settings', 'read').toString()}</div>
            <div data-testid="can-update-settings">{context.canAccess('settings', 'update').toString()}</div>
            <div data-testid="can-read-audit">{context.canAccess('audit', 'read').toString()}</div>
          </div>
        )
      }

      act(() => {
        useAuthStore.getState().setUser(adminUser)
        useAuthStore.getState().setToken(validToken)
      })

      render(
        <TestWrapper>
          <AuthProvider>
            <TestChild />
          </AuthProvider>
        </TestWrapper>
      )

      // Admin permissions
      expect(screen.getByTestId('can-read-users')).toHaveTextContent('true')
      expect(screen.getByTestId('can-create-users')).toHaveTextContent('true')
      expect(screen.getByTestId('can-delete-users')).toHaveTextContent('false') // Only sysadmin
      expect(screen.getByTestId('can-read-clients')).toHaveTextContent('true')
      expect(screen.getByTestId('can-read-settings')).toHaveTextContent('true')
      expect(screen.getByTestId('can-update-settings')).toHaveTextContent('false') // Only sysadmin
      expect(screen.getByTestId('can-read-audit')).toHaveTextContent('false') // Only sysadmin
    })

    it('should handle canAccess with default read action', () => {
      const userRole = createMockUser('user')
      const validToken = createValidToken()

      const TestChild = () => {
        const context = useAuthContext()
        return (
          <div>
            <div data-testid="can-access-clients">{context.canAccess('clients').toString()}</div>
            <div data-testid="can-access-users">{context.canAccess('users').toString()}</div>
            <div data-testid="can-access-reports">{context.canAccess('reports').toString()}</div>
          </div>
        )
      }

      act(() => {
        useAuthStore.getState().setUser(userRole)
        useAuthStore.getState().setToken(validToken)
      })

      render(
        <TestWrapper>
          <AuthProvider>
            <TestChild />
          </AuthProvider>
        </TestWrapper>
      )

      expect(screen.getByTestId('can-access-clients')).toHaveTextContent('true')
      expect(screen.getByTestId('can-access-users')).toHaveTextContent('false')
      expect(screen.getByTestId('can-access-reports')).toHaveTextContent('true')
    })

    it('should return false for canAccess when user is not authenticated', () => {
      const TestChild = () => {
        const context = useAuthContext()
        return (
          <div>
            <div data-testid="can-access-anything">{context.canAccess('clients', 'read').toString()}</div>
          </div>
        )
      }

      render(
        <TestWrapper>
          <AuthProvider>
            <TestChild />
          </AuthProvider>
        </TestWrapper>
      )

      expect(screen.getByTestId('can-access-anything')).toHaveTextContent('false')
    })

    it('should return false for canAccess with unknown resource', () => {
      const adminUser = createMockUser('admin')
      const validToken = createValidToken()

      const TestChild = () => {
        const context = useAuthContext()
        return (
          <div>
            <div data-testid="can-access-unknown">{context.canAccess('unknown-resource', 'read').toString()}</div>
          </div>
        )
      }

      act(() => {
        useAuthStore.getState().setUser(adminUser)
        useAuthStore.getState().setToken(validToken)
      })

      render(
        <TestWrapper>
          <AuthProvider>
            <TestChild />
          </AuthProvider>
        </TestWrapper>
      )

      expect(screen.getByTestId('can-access-unknown')).toHaveTextContent('false')
    })
  })

  describe('Token Refresh Functionality', () => {
    it('should auto-refresh expired token on mount', async () => {
      const mockUser = createMockUser('admin')
      const expiredToken = createExpiredToken()
      const newToken = createValidToken()

      act(() => {
        useAuthStore.getState().setUser(mockUser)
        useAuthStore.getState().setToken(expiredToken)
      })

      // Mock successful token refresh
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          access_token: newToken,
          token_type: 'bearer',
          expires_in: 3600
        })
      } as Response)

      const TestChild = () => {
        const context = useAuthContext()
        return <div data-testid="authenticated">{context.isAuthenticated.toString()}</div>
      }

      render(
        <TestWrapper>
          <AuthProvider>
            <TestChild />
          </AuthProvider>
        </TestWrapper>
      )

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/auth/refresh'),
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              'Authorization': `Bearer ${expiredToken}`
            })
          })
        )
      })

      // Should remain authenticated after refresh
      expect(screen.getByTestId('authenticated')).toHaveTextContent('true')
    })

    it('should logout when token refresh fails', async () => {
      const mockUser = createMockUser('admin')
      const expiredToken = createExpiredToken()

      act(() => {
        useAuthStore.getState().setUser(mockUser)
        useAuthStore.getState().setToken(expiredToken)
      })

      // Mock failed token refresh
      mockFetch.mockRejectedValueOnce(new Error('Token refresh failed'))

      const TestChild = () => {
        const context = useAuthContext()
        return (
          <div>
            <div data-testid="authenticated">{context.isAuthenticated.toString()}</div>
            <div data-testid="user">{context.user ? 'exists' : 'null'}</div>
          </div>
        )
      }

      render(
        <TestWrapper>
          <AuthProvider>
            <TestChild />
          </AuthProvider>
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByTestId('authenticated')).toHaveTextContent('false')
        expect(screen.getByTestId('user')).toHaveTextContent('null')
      })
    })

    it('should handle interval-based token refresh', async () => {
      vi.useFakeTimers()

      const mockUser = createMockUser('admin')
      const validToken = createValidToken()
      const newToken = createValidToken()

      act(() => {
        useAuthStore.getState().setUser(mockUser)
        useAuthStore.getState().setToken(validToken)
      })

      // Mock successful token refresh
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          access_token: newToken,
          token_type: 'bearer',
          expires_in: 3600
        })
      } as Response)

      const TestChild = () => {
        const context = useAuthContext()
        return <div data-testid="authenticated">{context.isAuthenticated.toString()}</div>
      }

      render(
        <TestWrapper>
          <AuthProvider>
            <TestChild />
          </AuthProvider>
        </TestWrapper>
      )

      // Fast forward 5 minutes to trigger interval
      await act(async () => {
        vi.advanceTimersByTime(5 * 60 * 1000)
        await vi.runAllTimersAsync()
      })

      // Should call refresh due to interval
      expect(mockFetch).toHaveBeenCalled()

      vi.useRealTimers()
    })

    it('should cleanup interval on unmount', async () => {
      vi.useFakeTimers()

      const mockUser = createMockUser('admin')
      const validToken = createValidToken()

      act(() => {
        useAuthStore.getState().setUser(mockUser)
        useAuthStore.getState().setToken(validToken)
      })

      const TestChild = () => {
        const context = useAuthContext()
        return <div data-testid="authenticated">{context.isAuthenticated.toString()}</div>
      }

      const { unmount } = render(
        <TestWrapper>
          <AuthProvider>
            <TestChild />
          </AuthProvider>
        </TestWrapper>
      )

      unmount()

      // Fast forward time after unmount
      await act(async () => {
        vi.advanceTimersByTime(10 * 60 * 1000)
        await vi.runAllTimersAsync()
      })

      // Should not call refresh after unmount
      expect(mockFetch).not.toHaveBeenCalled()

      vi.useRealTimers()
    })
  })
})

describe('RoleGuard Component', () => {
  it('should render children when user has required role', () => {
    const adminUser = createMockUser('admin')
    const validToken = createValidToken()

    act(() => {
      useAuthStore.getState().setUser(adminUser)
      useAuthStore.getState().setToken(validToken)
    })

    render(
      <TestWrapper>
        <AuthProvider>
          <RoleGuard roles={['admin']}>
            <div data-testid="protected-content">Conteúdo de Admin</div>
          </RoleGuard>
        </AuthProvider>
      </TestWrapper>
    )

    expect(screen.getByTestId('protected-content')).toBeInTheDocument()
    expect(screen.getByText('Conteúdo de Admin')).toBeInTheDocument()
  })

  it('should render fallback when user lacks required role', () => {
    const userRole = createMockUser('user')
    const validToken = createValidToken()

    act(() => {
      useAuthStore.getState().setUser(userRole)
      useAuthStore.getState().setToken(validToken)
    })

    render(
      <TestWrapper>
        <AuthProvider>
          <RoleGuard 
            roles={['admin']} 
            fallback={<div data-testid="access-denied">Acesso Negado</div>}
          >
            <div data-testid="protected-content">Conteúdo de Admin</div>
          </RoleGuard>
        </AuthProvider>
      </TestWrapper>
    )

    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
    expect(screen.getByTestId('access-denied')).toBeInTheDocument()
    expect(screen.getByText('Acesso Negado')).toBeInTheDocument()
  })

  it('should render null fallback by default when access denied', () => {
    const userRole = createMockUser('user')
    const validToken = createValidToken()

    act(() => {
      useAuthStore.getState().setUser(userRole)
      useAuthStore.getState().setToken(validToken)
    })

    render(
      <TestWrapper>
        <AuthProvider>
          <RoleGuard roles={['admin']}>
            <div data-testid="protected-content">Conteúdo de Admin</div>
          </RoleGuard>
        </AuthProvider>
      </TestWrapper>
    )

    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })

  it('should handle multiple roles with requireAll=false (default)', () => {
    const userRole = createMockUser('user')
    const validToken = createValidToken()

    act(() => {
      useAuthStore.getState().setUser(userRole)
      useAuthStore.getState().setToken(validToken)
    })

    render(
      <TestWrapper>
        <AuthProvider>
          <RoleGuard roles={['admin', 'user']}>
            <div data-testid="protected-content">Conteúdo Multi-Role</div>
          </RoleGuard>
        </AuthProvider>
      </TestWrapper>
    )

    // Should render because user has one of the required roles
    expect(screen.getByTestId('protected-content')).toBeInTheDocument()
  })

  it('should handle multiple roles with requireAll=true', () => {
    const adminUser = createMockUser('admin')
    const validToken = createValidToken()

    act(() => {
      useAuthStore.getState().setUser(adminUser)
      useAuthStore.getState().setToken(validToken)
    })

    render(
      <TestWrapper>
        <AuthProvider>
          <RoleGuard roles={['admin', 'sysadmin']} requireAll={true}>
            <div data-testid="protected-content">Conteúdo Restrito</div>
          </RoleGuard>
        </AuthProvider>
      </TestWrapper>
    )

    // Should not render because admin doesn't have sysadmin role
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })

  it('should work with sysadmin having all permissions', () => {
    const sysadminUser = createMockUser('sysadmin')
    const validToken = createValidToken()

    act(() => {
      useAuthStore.getState().setUser(sysadminUser)
      useAuthStore.getState().setToken(validToken)
    })

    render(
      <TestWrapper>
        <AuthProvider>
          <RoleGuard roles={['admin', 'sysadmin']} requireAll={true}>
            <div data-testid="protected-content">Conteúdo Super Restrito</div>
          </RoleGuard>
        </AuthProvider>
      </TestWrapper>
    )

    // Should render because sysadmin has both admin and sysadmin permissions
    expect(screen.getByTestId('protected-content')).toBeInTheDocument()
  })
})

describe('ResourceGuard Component', () => {
  it('should render children when user has resource access', () => {
    const adminUser = createMockUser('admin')
    const validToken = createValidToken()

    act(() => {
      useAuthStore.getState().setUser(adminUser)
      useAuthStore.getState().setToken(validToken)
    })

    render(
      <TestWrapper>
        <AuthProvider>
          <ResourceGuard resource="users" action="read">
            <div data-testid="user-list">Lista de Usuários</div>
          </ResourceGuard>
        </AuthProvider>
      </TestWrapper>
    )

    expect(screen.getByTestId('user-list')).toBeInTheDocument()
    expect(screen.getByText('Lista de Usuários')).toBeInTheDocument()
  })

  it('should render fallback when user lacks resource access', () => {
    const userRole = createMockUser('user')
    const validToken = createValidToken()

    act(() => {
      useAuthStore.getState().setUser(userRole)
      useAuthStore.getState().setToken(validToken)
    })

    render(
      <TestWrapper>
        <AuthProvider>
          <ResourceGuard 
            resource="users" 
            action="read"
            fallback={<div data-testid="no-access">Sem Acesso aos Usuários</div>}
          >
            <div data-testid="user-list">Lista de Usuários</div>
          </ResourceGuard>
        </AuthProvider>
      </TestWrapper>
    )

    expect(screen.queryByTestId('user-list')).not.toBeInTheDocument()
    expect(screen.getByTestId('no-access')).toBeInTheDocument()
    expect(screen.getByText('Sem Acesso aos Usuários')).toBeInTheDocument()
  })

  it('should use default read action when action not specified', () => {
    const userRole = createMockUser('user')
    const validToken = createValidToken()

    act(() => {
      useAuthStore.getState().setUser(userRole)
      useAuthStore.getState().setToken(validToken)
    })

    render(
      <TestWrapper>
        <AuthProvider>
          <ResourceGuard resource="clients">
            <div data-testid="client-list">Lista de Clientes</div>
          </ResourceGuard>
        </AuthProvider>
      </TestWrapper>
    )

    // User can read clients by default
    expect(screen.getByTestId('client-list')).toBeInTheDocument()
    expect(screen.getByText('Lista de Clientes')).toBeInTheDocument()
  })

  it('should render null fallback by default when access denied', () => {
    const userRole = createMockUser('user')
    const validToken = createValidToken()

    act(() => {
      useAuthStore.getState().setUser(userRole)
      useAuthStore.getState().setToken(validToken)
    })

    render(
      <TestWrapper>
        <AuthProvider>
          <ResourceGuard resource="settings" action="update">
            <div data-testid="settings-form">Configurações</div>
          </ResourceGuard>
        </AuthProvider>
      </TestWrapper>
    )

    // User cannot update settings
    expect(screen.queryByTestId('settings-form')).not.toBeInTheDocument()
  })
})

describe('Error Handling and Edge Cases', () => {
  it('should handle context provider without authenticated user', () => {
    const TestChild = () => {
      const context = useAuthContext()
      return (
        <div>
          <div data-testid="can-access-test">{context.canAccess('clients', 'read').toString()}</div>
          <div data-testid="has-role-test">{context.hasRole('user').toString()}</div>
        </div>
      )
    }

    render(
      <TestWrapper>
        <AuthProvider>
          <TestChild />
        </AuthProvider>
      </TestWrapper>
    )

    expect(screen.getByTestId('can-access-test')).toHaveTextContent('false')
    expect(screen.getByTestId('has-role-test')).toHaveTextContent('false')
  })

  it('should handle rapid state changes without errors', () => {
    const TestChild = () => {
      const context = useAuthContext()
      return (
        <div>
          <div data-testid="authenticated">{context.isAuthenticated.toString()}</div>
          <div data-testid="user-email">{context.user?.email || 'no-email'}</div>
        </div>
      )
    }

    const { rerender } = render(
      <TestWrapper>
        <AuthProvider>
          <TestChild />
        </AuthProvider>
      </TestWrapper>
    )

    // Rapid state changes
    const users = [
      createMockUser('user'),
      createMockUser('admin'),
      createMockUser('sysadmin'),
    ]
    const validToken = createValidToken()

    users.forEach((user, index) => {
      act(() => {
        useAuthStore.getState().setUser(user)
        useAuthStore.getState().setToken(validToken)
      })

      rerender(
        <TestWrapper>
          <AuthProvider>
            <TestChild />
          </AuthProvider>
        </TestWrapper>
      )

      expect(screen.getByTestId('authenticated')).toHaveTextContent('true')
      expect(screen.getByTestId('user-email')).toHaveTextContent(`${user.role}@example.com`)
    })
  })

  it('should handle component unmounting during token refresh', async () => {
    const mockUser = createMockUser('admin')
    const expiredToken = createExpiredToken()

    act(() => {
      useAuthStore.getState().setUser(mockUser)
      useAuthStore.getState().setToken(expiredToken)
    })

    // Mock slow token refresh
    mockFetch.mockImplementationOnce(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({ access_token: createValidToken() })
        } as Response), 100)
      )
    )

    const TestChild = () => {
      const context = useAuthContext()
      return <div data-testid="authenticated">{context.isAuthenticated.toString()}</div>
    }

    const { unmount } = render(
      <TestWrapper>
        <AuthProvider>
          <TestChild />
        </AuthProvider>
      </TestWrapper>
    )

    // Unmount before token refresh completes
    unmount()

    // Should not throw errors or cause memory leaks
    await new Promise(resolve => setTimeout(resolve, 150))
  })
})