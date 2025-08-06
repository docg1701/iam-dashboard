/**
 * ProtectedRoute Component Tests
 * Tests route protection, authentication guards, and role-based access control
 * Following CLAUDE.md rules: no internal mocking, only external API mocking
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ProtectedRoute, withAuth, useAuth } from '../ProtectedRoute'
import useAuthStore from '@/store/authStore'
import type { User } from '@/types/auth'

// Mock only external fetch API for token refresh
const mockFetch = vi.fn()
global.fetch = mockFetch

// Track navigation actions via window.location (real behavior)
const originalLocation = window.location

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
const createValidToken = (userId: string, role: string): string => {
  const payload = {
    sub: userId,
    role: role,
    exp: Math.floor(Date.now() / 1000) + 3600 // 1 hour from now
  }
  return `header.${btoa(JSON.stringify(payload))}.signature`
}

// Helper to create expired JWT token
const createExpiredToken = (userId: string, role: string): string => {
  const payload = {
    sub: userId,
    role: role,
    exp: Math.floor(Date.now() / 1000) - 3600 // 1 hour ago
  }
  return `header.${btoa(JSON.stringify(payload))}.signature`
}

beforeEach(() => {
  vi.clearAllMocks()
  mockFetch.mockReset()
  
  // Reset auth store to clean state
  useAuthStore.setState({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: false,
    requires2FA: false,
    tempToken: null
  })
  
  // Reset window.location for navigation testing - no vi.fn() mocks
  Object.defineProperty(window, 'location', {
    value: originalLocation,
    writable: true,
    configurable: true
  })
})

afterEach(() => {
  vi.restoreAllMocks()
  window.location = originalLocation
})

describe('ProtectedRoute', () => {
  it('should redirect to login when user is not authenticated', async () => {
    const TestComponent = () => <div>Protected Content</div>
    
    render(
      <TestWrapper>
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      </TestWrapper>
    )
    
    await waitFor(() => {
      expect(screen.getByText(/redirecionando/i)).toBeInTheDocument()
    })
    
    // Should not render protected content
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('should render protected content when user is authenticated', async () => {
    const mockUser = createMockUser('admin')
    const validToken = createValidToken(mockUser.user_id, mockUser.role)
    
    const TestComponent = () => <div>Protected Content</div>
    
    // Set authenticated user in store
    act(() => {
      useAuthStore.getState().setUser(mockUser)
      useAuthStore.getState().setToken(validToken)
    })
    
    render(
      <TestWrapper>
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      </TestWrapper>
    )
    
    await waitFor(() => {
      expect(screen.getByText('Protected Content')).toBeInTheDocument()
    })
  })

  it('should show loading state while checking authentication', async () => {
    const TestComponent = () => <div>Protected Content</div>
    
    // Set loading state
    act(() => {
      useAuthStore.setState({ isLoading: true })
    })
    
    render(
      <TestWrapper>
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
      </TestWrapper>
    )
    
    expect(screen.getByText(/verificando autenticação/i)).toBeInTheDocument()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('should support custom redirect path', async () => {
    const TestComponent = () => <div>Protected Content</div>
    
    render(
      <TestWrapper>
        <ProtectedRoute redirectTo="/custom-login">
          <TestComponent />
        </ProtectedRoute>
      </TestWrapper>
    )
    
    await waitFor(() => {
      expect(screen.getByText(/redirecionando/i)).toBeInTheDocument()
    })
  })

  it('should support custom fallback component', async () => {
    const TestComponent = () => <div>Protected Content</div>
    const CustomFallback = () => <div>Custom Loading</div>
    
    act(() => {
      useAuthStore.setState({ isLoading: true })
    })
    
    render(
      <TestWrapper>
        <ProtectedRoute fallback={<CustomFallback />}>
          <TestComponent />
        </ProtectedRoute>
      </TestWrapper>
    )
    
    expect(screen.getByText('Custom Loading')).toBeInTheDocument()
  })

  describe('Role-based Access Control', () => {
    it('should allow sysadmin to access any role requirement', async () => {
      const mockUser = createMockUser('sysadmin')
      const validToken = createValidToken(mockUser.user_id, mockUser.role)
      
      const TestComponent = () => <div>Sysadmin Content</div>
      
      act(() => {
        useAuthStore.getState().setUser(mockUser)
        useAuthStore.getState().setToken(validToken)
      })
      
      render(
        <TestWrapper>
          <ProtectedRoute requiredRole="sysadmin">
            <TestComponent />
          </ProtectedRoute>
        </TestWrapper>
      )
      
      await waitFor(() => {
        expect(screen.getByText('Sysadmin Content')).toBeInTheDocument()
      })
    })

    it('should allow admin to access admin and user routes', async () => {
      const mockUser = createMockUser('admin')
      const validToken = createValidToken(mockUser.user_id, mockUser.role)
      
      const TestComponent = () => <div>Admin Content</div>
      
      act(() => {
        useAuthStore.getState().setUser(mockUser)
        useAuthStore.getState().setToken(validToken)
      })
      
      render(
        <TestWrapper>
          <ProtectedRoute requiredRole="admin">
            <TestComponent />
          </ProtectedRoute>
        </TestWrapper>
      )
      
      await waitFor(() => {
        expect(screen.getByText('Admin Content')).toBeInTheDocument()
      })
    })

    it('should deny admin access to sysadmin routes', async () => {
      const mockUser = createMockUser('admin')
      const validToken = createValidToken(mockUser.user_id, mockUser.role)
      
      const TestComponent = () => <div>Sysadmin Content</div>
      
      act(() => {
        useAuthStore.getState().setUser(mockUser)
        useAuthStore.getState().setToken(validToken)
      })
      
      render(
        <TestWrapper>
          <ProtectedRoute requiredRole="sysadmin">
            <TestComponent />
          </ProtectedRoute>
        </TestWrapper>
      )
      
      await waitFor(() => {
        expect(screen.getByText(/sem permissão/i)).toBeInTheDocument()
      })
      
      expect(screen.queryByText('Sysadmin Content')).not.toBeInTheDocument()
    })

    it('should allow user to access user routes only', async () => {
      const mockUser = createMockUser('user')
      const validToken = createValidToken(mockUser.user_id, mockUser.role)
      
      const TestComponent = () => <div>User Content</div>
      
      act(() => {
        useAuthStore.getState().setUser(mockUser)
        useAuthStore.getState().setToken(validToken)
      })
      
      render(
        <TestWrapper>
          <ProtectedRoute requiredRole="user">
            <TestComponent />
          </ProtectedRoute>
        </TestWrapper>
      )
      
      await waitFor(() => {
        expect(screen.getByText('User Content')).toBeInTheDocument()
      })
    })

    it('should deny user access to admin routes', async () => {
      const mockUser = createMockUser('user')
      const validToken = createValidToken(mockUser.user_id, mockUser.role)
      
      const TestComponent = () => <div>Admin Content</div>
      
      act(() => {
        useAuthStore.getState().setUser(mockUser)
        useAuthStore.getState().setToken(validToken)
      })
      
      render(
        <TestWrapper>
          <ProtectedRoute requiredRole="admin">
            <TestComponent />
          </ProtectedRoute>
        </TestWrapper>
      )
      
      await waitFor(() => {
        expect(screen.getByText(/sem permissão/i)).toBeInTheDocument()
      })
      
      expect(screen.queryByText('Admin Content')).not.toBeInTheDocument()
    })
  })

  describe('Token Expiration Handling', () => {
    it('should refresh expired token and continue to protected content', async () => {
      const mockUser = createMockUser('admin')
      const expiredToken = createExpiredToken(mockUser.user_id, mockUser.role)
      const newToken = createValidToken(mockUser.user_id, mockUser.role)
      
      const TestComponent = () => <div>Protected Content</div>
      
      // Mock successful token refresh
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          access_token: newToken,
          token_type: 'bearer',
          expires_in: 3600
        })
      } as Response)
      
      act(() => {
        useAuthStore.getState().setUser(mockUser)
        useAuthStore.getState().setToken(expiredToken)
      })
      
      render(
        <TestWrapper>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </TestWrapper>
      )
      
      // Should show loading while refreshing token
      expect(screen.getByText(/verificando autenticação/i)).toBeInTheDocument()
      
      // After token refresh, should show protected content
      await waitFor(() => {
        expect(screen.getByText('Protected Content')).toBeInTheDocument()
      })
      
      // Verify token refresh was called
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/refresh'),
        expect.any(Object)
      )
    })

    it('should logout and redirect when token refresh fails', async () => {
      const mockUser = createMockUser('admin')
      const expiredToken = createExpiredToken(mockUser.user_id, mockUser.role)
      
      const TestComponent = () => <div>Protected Content</div>
      
      // Mock failed token refresh
      mockFetch.mockRejectedValueOnce(new Error('Token refresh failed'))
      
      act(() => {
        useAuthStore.getState().setUser(mockUser)
        useAuthStore.getState().setToken(expiredToken)
      })
      
      render(
        <TestWrapper>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </TestWrapper>
      )
      
      await waitFor(() => {
        expect(screen.getByText(/redirecionando/i)).toBeInTheDocument()
      })
      
      // User should be logged out
      expect(useAuthStore.getState().isAuthenticated).toBe(false)
      expect(useAuthStore.getState().user).toBeNull()
    })

    it('should handle network errors during token refresh', async () => {
      const mockUser = createMockUser('admin')
      const expiredToken = createExpiredToken(mockUser.user_id, mockUser.role)
      
      const TestComponent = () => <div>Protected Content</div>
      
      // Mock network error
      mockFetch.mockRejectedValueOnce(new Error('Network Error'))
      
      act(() => {
        useAuthStore.getState().setUser(mockUser)
        useAuthStore.getState().setToken(expiredToken)
      })
      
      render(
        <TestWrapper>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </TestWrapper>
      )
      
      await waitFor(() => {
        expect(screen.getByText(/redirecionando/i)).toBeInTheDocument()
      })
    })
  })

  describe('withAuth Higher-Order Component', () => {
    it('should wrap component with authentication protection', async () => {
      const TestComponent = () => <div>Wrapped Component</div>
      const WrappedComponent = withAuth(TestComponent)
      
      const mockUser = createMockUser('admin')
      const validToken = createValidToken(mockUser.user_id, mockUser.role)
      
      act(() => {
        useAuthStore.getState().setUser(mockUser)
        useAuthStore.getState().setToken(validToken)
      })
      
      render(
        <TestWrapper>
          <WrappedComponent />
        </TestWrapper>
      )
      
      await waitFor(() => {
        expect(screen.getByText('Wrapped Component')).toBeInTheDocument()
      })
    })

    it('should pass props through to wrapped component', async () => {
      const TestComponent = ({ message }: { message: string }) => <div>{message}</div>
      const WrappedComponent = withAuth(TestComponent)
      
      const mockUser = createMockUser('admin')
      const validToken = createValidToken(mockUser.user_id, mockUser.role)
      
      act(() => {
        useAuthStore.getState().setUser(mockUser)
        useAuthStore.getState().setToken(validToken)
      })
      
      render(
        <TestWrapper>
          <WrappedComponent message="Prop Message" />
        </TestWrapper>
      )
      
      await waitFor(() => {
        expect(screen.getByText('Prop Message')).toBeInTheDocument()
      })
    })
  })

  describe('useAuth Hook', () => {
    it('should return auth state and computed values', () => {
      const TestComponent = () => {
        const { user, isAuthenticated, isAdmin, isSysAdmin } = useAuth()
        return (
          <div>
            <div>Authenticated: {isAuthenticated ? 'Yes' : 'No'}</div>
            <div>Is Admin: {isAdmin ? 'Yes' : 'No'}</div>
            <div>Is SysAdmin: {isSysAdmin ? 'Yes' : 'No'}</div>
          </div>
        )
      }
      
      const mockUser = createMockUser('admin')
      const validToken = createValidToken(mockUser.user_id, mockUser.role)
      
      act(() => {
        useAuthStore.getState().setUser(mockUser)
        useAuthStore.getState().setToken(validToken)
      })
      
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )
      
      expect(screen.getByText('Authenticated: Yes')).toBeInTheDocument()
      expect(screen.getByText('Is Admin: Yes')).toBeInTheDocument()
      expect(screen.getByText('Is SysAdmin: No')).toBeInTheDocument()
    })

    it('should update when auth state changes', async () => {
      const TestComponent = () => {
        const { isAuthenticated } = useAuth()
        return <div>Authenticated: {isAuthenticated ? 'Yes' : 'No'}</div>
      }
      
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )
      
      // Initially not authenticated
      expect(screen.getByText('Authenticated: No')).toBeInTheDocument()
      
      // Login user
      const mockUser = createMockUser('admin')
      const validToken = createValidToken(mockUser.user_id, mockUser.role)
      
      act(() => {
        useAuthStore.getState().setUser(mockUser)
        useAuthStore.getState().setToken(validToken)
      })
      
      await waitFor(() => {
        expect(screen.getByText('Authenticated: Yes')).toBeInTheDocument()
      })
    })
  })

  describe('Edge Cases', () => {
    it('should handle missing user with valid token', async () => {
      const validToken = createValidToken('user-123', 'admin')
      
      const TestComponent = () => <div>Protected Content</div>
      
      // Set token but no user
      act(() => {
        useAuthStore.getState().setToken(validToken)
      })
      
      render(
        <TestWrapper>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </TestWrapper>
      )
      
      await waitFor(() => {
        expect(screen.getByText(/redirecionando/i)).toBeInTheDocument()
      })
    })

    it('should handle malformed JWT token', async () => {
      const mockUser = createMockUser('admin')
      const malformedToken = 'invalid.token.here'
      
      const TestComponent = () => <div>Protected Content</div>
      
      act(() => {
        useAuthStore.getState().setUser(mockUser)
        useAuthStore.getState().setToken(malformedToken)
      })
      
      render(
        <TestWrapper>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </TestWrapper>
      )
      
      await waitFor(() => {
        expect(screen.getByText(/redirecionando/i)).toBeInTheDocument()
      })
    })

    it('should handle component unmounting during async operations', async () => {
      const mockUser = createMockUser('admin')
      const expiredToken = createExpiredToken(mockUser.user_id, mockUser.role)
      
      const TestComponent = () => <div>Protected Content</div>
      
      act(() => {
        useAuthStore.getState().setUser(mockUser)
        useAuthStore.getState().setToken(expiredToken)
      })
      
      const { unmount } = render(
        <TestWrapper>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </TestWrapper>
      )
      
      // Unmount before token refresh completes
      unmount()
      
      // Should not throw errors
    })

    it('should handle rapid role changes', async () => {
      const TestComponent = () => {
        const { user } = useAuth()
        return <div>Role: {user?.role || 'none'}</div>
      }
      
      render(
        <TestWrapper>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </TestWrapper>
      )
      
      // Rapid role changes
      const adminUser = createMockUser('admin')
      const userUser = createMockUser('user')
      const adminToken = createValidToken(adminUser.user_id, adminUser.role)
      const userToken = createValidToken(userUser.user_id, userUser.role)
      
      act(() => {
        useAuthStore.getState().setUser(adminUser)
        useAuthStore.getState().setToken(adminToken)
      })
      
      await waitFor(() => {
        expect(screen.getByText('Role: admin')).toBeInTheDocument()
      })
      
      act(() => {
        useAuthStore.getState().setUser(userUser)
        useAuthStore.getState().setToken(userToken)
      })
      
      await waitFor(() => {
        expect(screen.getByText('Role: user')).toBeInTheDocument()
      })
    })

    it('should handle custom fallback component with props', async () => {
      const TestComponent = () => <div>Protected Content</div>
      const CustomFallback = ({ message }: { message: string }) => <div>{message}</div>
      
      act(() => {
        useAuthStore.setState({ isLoading: true })
      })
      
      render(
        <TestWrapper>
          <ProtectedRoute fallback={<CustomFallback message="Custom Loading Message" />}>
            <TestComponent />
          </ProtectedRoute>
        </TestWrapper>
      )
      
      expect(screen.getByText('Custom Loading Message')).toBeInTheDocument()
    })
  })
})