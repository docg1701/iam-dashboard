/**
 * ProtectedRoute Component Tests
 * Tests route protection, authentication guards, and role-based access control
 * Following CLAUDE.md rules: no internal mocking, only external API mocking
 */
import { ProtectedRoute, withAuth, useAuth } from '../ProtectedRoute'
import useAuthStore from '@/store/authStore'
import type { User } from '@/types/auth'
import {
  describe, it, expect, vi, beforeEach, afterEach,
  renderWithProviders, screen, waitFor, act, userEvent,
  useTestSetup, mockSuccessfulFetch, mockFailedFetch
} from '@/test/test-template'
import {
  createMockUser, createMockAdmin, createMockSysAdmin,
  setupTestAuth, clearTestAuth, setupAuthenticatedUser,
  createMockJWTToken, createExpiredJWTToken
} from '@/test/auth-helpers'

// Track navigation actions via window.location (real behavior)
const originalLocation = window.location

// Use standardized test setup
useTestSetup()

// Preserve original location for navigation testing
beforeEach(() => {
  // Reset window.location for navigation testing - no vi.fn() mocks
  Object.defineProperty(window, 'location', {
    value: originalLocation,
    writable: true,
    configurable: true
  })
})

afterEach(() => {
  window.location = originalLocation
})

describe('ProtectedRoute', () => {
  it('should redirect to login when user is not authenticated', async () => {
    const TestComponent = () => <div>Protected Content</div>
    
    renderWithProviders(
      <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
    )
    
    await waitFor(() => {
      expect(screen.getByText(/redirecionando/i)).toBeInTheDocument()
    })
    
    // Should not render protected content
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('should render protected content when user is authenticated', async () => {
    const mockUser = createMockAdmin()
    const validToken = createMockJWTToken({ role: 'admin', user_id: mockUser.user_id })
    
    const TestComponent = () => <div>Protected Content</div>
    
    // Set authenticated user in store
    act(() => {
      setupTestAuth(mockUser, validToken)
    })
    
    renderWithProviders(
      <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
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
    
    renderWithProviders(
      <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
    )
    
    expect(screen.getByText(/verificando autenticação/i)).toBeInTheDocument()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('should support custom redirect path', async () => {
    const TestComponent = () => <div>Protected Content</div>
    
    renderWithProviders(
      <ProtectedRoute redirectTo="/custom-login">
          <TestComponent />
        </ProtectedRoute>
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
    
    renderWithProviders(
      <ProtectedRoute fallback={<CustomFallback />}>
          <TestComponent />
        </ProtectedRoute>
    )
    
    expect(screen.getByText('Custom Loading')).toBeInTheDocument()
  })

  describe('Role-based Access Control', () => {
    it('should allow sysadmin to access any role requirement', async () => {
      const mockUser = createMockSysAdmin()
      const validToken = createMockJWTToken({ role: mockUser.role, user_id: mockUser.user_id })
      
      const TestComponent = () => <div>Sysadmin Content</div>
      
      act(() => {
        setupTestAuth(mockUser, validToken)
      })
      
      renderWithProviders(
          <ProtectedRoute requiredRole="sysadmin">
            <TestComponent />
          </ProtectedRoute>
      )
      
      await waitFor(() => {
        expect(screen.getByText('Sysadmin Content')).toBeInTheDocument()
      })
    })

    it('should allow admin to access admin and user routes', async () => {
      const mockUser = createMockAdmin()
      const validToken = createMockJWTToken({ role: mockUser.role, user_id: mockUser.user_id })
      
      const TestComponent = () => <div>Admin Content</div>
      
      act(() => {
        setupTestAuth(mockUser, validToken)
      })
      
      renderWithProviders(
          <ProtectedRoute requiredRole="admin">
            <TestComponent />
          </ProtectedRoute>
      )
      
      await waitFor(() => {
        expect(screen.getByText('Admin Content')).toBeInTheDocument()
      })
    })

    it('should deny admin access to sysadmin routes', async () => {
      const mockUser = createMockAdmin()
      const validToken = createMockJWTToken({ role: mockUser.role, user_id: mockUser.user_id })
      
      const TestComponent = () => <div>Sysadmin Content</div>
      
      act(() => {
        setupTestAuth(mockUser, validToken)
      })
      
      renderWithProviders(
          <ProtectedRoute requiredRole="sysadmin">
            <TestComponent />
          </ProtectedRoute>
      )
      
      await waitFor(() => {
        expect(screen.getByText(/sem permissão/i)).toBeInTheDocument()
      })
      
      expect(screen.queryByText('Sysadmin Content')).not.toBeInTheDocument()
    })

    it('should allow user to access user routes only', async () => {
      const mockUser = createMockUser()
      const validToken = createMockJWTToken({ role: mockUser.role, user_id: mockUser.user_id })
      
      const TestComponent = () => <div>User Content</div>
      
      act(() => {
        setupTestAuth(mockUser, validToken)
      })
      
      renderWithProviders(
          <ProtectedRoute requiredRole="user">
            <TestComponent />
          </ProtectedRoute>
      )
      
      await waitFor(() => {
        expect(screen.getByText('User Content')).toBeInTheDocument()
      })
    })

    it('should deny user access to admin routes', async () => {
      const mockUser = createMockUser()
      const validToken = createMockJWTToken({ role: mockUser.role, user_id: mockUser.user_id })
      
      const TestComponent = () => <div>Admin Content</div>
      
      act(() => {
        setupTestAuth(mockUser, validToken)
      })
      
      renderWithProviders(
          <ProtectedRoute requiredRole="admin">
            <TestComponent />
          </ProtectedRoute>
      )
      
      await waitFor(() => {
        expect(screen.getByText(/sem permissão/i)).toBeInTheDocument()
      })
      
      expect(screen.queryByText('Admin Content')).not.toBeInTheDocument()
    })
  })

  describe('Token Expiration Handling', () => {
    it('should refresh expired token and continue to protected content', async () => {
      const mockUser = createMockAdmin()
      const expiredToken = createExpiredJWTToken({ role: mockUser.role, user_id: mockUser.user_id })
      const newToken = createMockJWTToken({ role: mockUser.role, user_id: mockUser.user_id })
      
      const TestComponent = () => <div>Protected Content</div>
      
      // Mock successful token refresh
      mockSuccessfulFetch('/auth/refresh', {
        access_token: newToken,
        token_type: 'bearer',
        expires_in: 3600
      })
      
      act(() => {
        setupTestAuth(mockUser, expiredToken)
      })
      
      renderWithProviders(
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
      )
      
      // Should show loading while refreshing token
      expect(screen.getByText(/verificando autenticação/i)).toBeInTheDocument()
      
      // After token refresh, should show protected content
      await waitFor(() => {
        expect(screen.getByText('Protected Content')).toBeInTheDocument()
      })
      
      // Verify token refresh was called
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/refresh'),
        expect.any(Object)
      )
    })

    it('should logout and redirect when token refresh fails', async () => {
      const mockUser = createMockAdmin()
      const expiredToken = createExpiredJWTToken({ role: mockUser.role, user_id: mockUser.user_id })
      
      const TestComponent = () => <div>Protected Content</div>
      
      // Mock failed token refresh
      mockFailedFetch('/auth/refresh', 'Token refresh failed', 401)
      
      act(() => {
        setupTestAuth(mockUser, expiredToken)
      })
      
      renderWithProviders(
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
      )
      
      await waitFor(() => {
        expect(screen.getByText(/redirecionando/i)).toBeInTheDocument()
      })
      
      // User should be logged out
      expect(useAuthStore.getState().isAuthenticated).toBe(false)
      expect(useAuthStore.getState().user).toBeNull()
    })

    it('should handle network errors during token refresh', async () => {
      const mockUser = createMockAdmin()
      const expiredToken = createExpiredJWTToken({ role: mockUser.role, user_id: mockUser.user_id })
      
      const TestComponent = () => <div>Protected Content</div>
      
      // Mock network error
      mockFailedFetch('/auth/refresh', 'Network Error', 500)
      
      act(() => {
        setupTestAuth(mockUser, expiredToken)
      })
      
      renderWithProviders(
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
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
      
      const mockUser = createMockAdmin()
      const validToken = createMockJWTToken({ role: mockUser.role, user_id: mockUser.user_id })
      
      act(() => {
        setupTestAuth(mockUser, validToken)
      })
      
      renderWithProviders(
        <WrappedComponent />
      )
      
      await waitFor(() => {
        expect(screen.getByText('Wrapped Component')).toBeInTheDocument()
      })
    })

    it('should pass props through to wrapped component', async () => {
      const TestComponent = ({ message }: { message: string }) => <div>{message}</div>
      const WrappedComponent = withAuth(TestComponent)
      
      const mockUser = createMockAdmin()
      const validToken = createMockJWTToken({ role: mockUser.role, user_id: mockUser.user_id })
      
      act(() => {
        setupTestAuth(mockUser, validToken)
      })
      
      renderWithProviders(
        <WrappedComponent message="Prop Message" />
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
      
      const mockUser = createMockAdmin()
      const validToken = createMockJWTToken({ role: mockUser.role, user_id: mockUser.user_id })
      
      act(() => {
        setupTestAuth(mockUser, validToken)
      })
      
      renderWithProviders(
          <TestComponent />
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
      
      renderWithProviders(
          <TestComponent />
      )
      
      // Initially not authenticated
      expect(screen.getByText('Authenticated: No')).toBeInTheDocument()
      
      // Login user
      const mockUser = createMockAdmin()
      const validToken = createMockJWTToken({ role: mockUser.role, user_id: mockUser.user_id })
      
      act(() => {
        setupTestAuth(mockUser, validToken)
      })
      
      await waitFor(() => {
        expect(screen.getByText('Authenticated: Yes')).toBeInTheDocument()
      })
    })
  })

  describe('Edge Cases', () => {
    it('should handle missing user with valid token', async () => {
      const validToken = createMockJWTToken({ role: 'admin', user_id: 'user-123' })
      
      const TestComponent = () => <div>Protected Content</div>
      
      // Set token but no user
      act(() => {
        useAuthStore.setState({ token: validToken, user: null, isAuthenticated: false })
      })
      
      renderWithProviders(
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
      )
      
      await waitFor(() => {
        expect(screen.getByText(/redirecionando/i)).toBeInTheDocument()
      })
    })

    it('should handle malformed JWT token', async () => {
      const mockUser = createMockAdmin()
      const malformedToken = 'invalid.token.here'
      
      const TestComponent = () => <div>Protected Content</div>
      
      act(() => {
        setupTestAuth(mockUser, malformedToken)
      })
      
      renderWithProviders(
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
      )
      
      await waitFor(() => {
        expect(screen.getByText(/redirecionando/i)).toBeInTheDocument()
      })
    })

    it('should handle component unmounting during async operations', async () => {
      const mockUser = createMockAdmin()
      const expiredToken = createExpiredJWTToken({ role: mockUser.role, user_id: mockUser.user_id })
      
      const TestComponent = () => <div>Protected Content</div>
      
      act(() => {
        setupTestAuth(mockUser, expiredToken)
      })
      
      const { unmount } = renderWithProviders(
        <ProtectedRoute>
          <TestComponent />
        </ProtectedRoute>
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
      
      renderWithProviders(
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
      )
      
      // Rapid role changes
      const adminUser = createMockAdmin()
      const userUser = createMockUser()
      const adminToken = createMockJWTToken({ role: adminUser.role, user_id: adminUser.user_id })
      const userToken = createMockJWTToken({ role: userUser.role, user_id: userUser.user_id })
      
      act(() => {
        setupTestAuth(adminUser, adminToken)
      })
      
      await waitFor(() => {
        expect(screen.getByText('Role: admin')).toBeInTheDocument()
      })
      
      act(() => {
        setupTestAuth(userUser, userToken)
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
      
      renderWithProviders(
          <ProtectedRoute fallback={<CustomFallback message="Custom Loading Message" />}>
            <TestComponent />
          </ProtectedRoute>
      )
      
      expect(screen.getByText('Custom Loading Message')).toBeInTheDocument()
    })
  })
})