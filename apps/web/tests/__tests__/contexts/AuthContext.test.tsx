/**
 * Comprehensive tests for AuthContext
 * CLAUDE.md Compliant: Only mocks external APIs (fetch), tests actual behavior
 */

import React from 'react'
import { render, screen, act, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach, afterEach, Mock } from 'vitest'
import { useRouter } from 'next/navigation'

import { AuthProvider, useAuth, usePermissions } from '@/contexts/AuthContext'
import { ErrorProvider } from '@/components/errors/ErrorContext'

// Mock external dependencies (CLAUDE.md compliant)
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
}))

// Note: ErrorContext is internal component - test with real implementation (CLAUDE.md compliant)

// Test component to access AuthContext
const TestComponent: React.FC = () => {
  const {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    refreshToken,
    setup2FA,
    enable2FA,
    disable2FA,
    clearError,
    retry,
  } = useAuth()

  return (
    <div>
      <div data-testid="user-id">{user?.id || 'not-authenticated'}</div>
      <div data-testid="user-email">{user?.email || 'no-email'}</div>
      <div data-testid="user-role">{user?.role || 'no-role'}</div>
      <div data-testid="is-authenticated">{isAuthenticated.toString()}</div>
      <div data-testid="is-loading">{isLoading.toString()}</div>
      <div data-testid="error-message">{error?.message || 'no-error'}</div>
      <div data-testid="error-code">{error?.code || 'no-error-code'}</div>
      <div data-testid="error-retryable">
        {error?.retryable?.toString() || 'no-retryable'}
      </div>
      <button
        data-testid="login-btn"
        onClick={() =>
          login({ email: 'test@example.com', password: 'password123' })
        }
      >
        Login
      </button>
      <button data-testid="logout-btn" onClick={() => logout()}>
        Logout
      </button>
      <button data-testid="refresh-btn" onClick={() => refreshToken()}>
        Refresh
      </button>
      <button data-testid="setup-2fa-btn" onClick={() => setup2FA()}>
        Setup 2FA
      </button>
      <button data-testid="enable-2fa-btn" onClick={() => enable2FA('123456')}>
        Enable 2FA
      </button>
      <button data-testid="disable-2fa-btn" onClick={() => disable2FA()}>
        Disable 2FA
      </button>
      <button data-testid="clear-error-btn" onClick={() => clearError()}>
        Clear Error
      </button>
      <button data-testid="retry-btn" onClick={() => retry()}>
        Retry
      </button>
    </div>
  )
}

// Test component for permissions
const PermissionsTestComponent: React.FC = () => {
  const { hasRole, isAdmin, isSysAdmin } = usePermissions()

  return (
    <div>
      <div data-testid="has-user-role">{hasRole('user').toString()}</div>
      <div data-testid="has-admin-role">{hasRole('admin').toString()}</div>
      <div data-testid="has-sysadmin-role">
        {hasRole('sysadmin').toString()}
      </div>
      <div data-testid="is-admin">{isAdmin().toString()}</div>
      <div data-testid="is-sysadmin">{isSysAdmin().toString()}</div>
    </div>
  )
}

describe('AuthContext', () => {
  const mockPush = vi.fn()
  // No longer needed - using real ErrorProvider
  const mockRouter = { push: mockPush }

  // Mock original fetch
  const originalFetch = global.fetch

  beforeEach(() => {
    vi.clearAllMocks()
    ;(useRouter as Mock).mockReturnValue(mockRouter)
    // Using real ErrorProvider - no mocking needed for internal components

    // Ensure NODE_ENV is set to test for token storage
    vi.stubEnv('NODE_ENV', 'test')

    // Mock fetch globally
    global.fetch = vi.fn()

    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn(),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn(),
      },
      writable: true,
    })
  })

  afterEach(() => {
    global.fetch = originalFetch
    vi.restoreAllMocks()
  })

  describe('Provider Initialization', () => {
    it('should provide default state values', () => {
      render(
        <ErrorProvider>
          <AuthProvider>
            <TestComponent />
          </AuthProvider>
        </ErrorProvider>
      )

      expect(screen.getByTestId('user-id')).toHaveTextContent(
        'not-authenticated'
      )
      expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false')
      expect(screen.getByTestId('error-message')).toHaveTextContent('no-error')
    })

    it('should throw error when useAuth used outside provider', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      expect(() => {
        render(<TestComponent />)
      }).toThrow('useAuth deve ser usado dentro de um AuthProvider')

      consoleSpy.mockRestore()
    })
  })

  describe('Login Functionality', () => {
    it('should handle successful login with valid credentials', async () => {
      const mockUser = {
        id: 'user-123',
        email: 'test@example.com',
        role: 'user' as const,
        is_active: true,
        has_2fa: false,
      }

      const mockResponse = {
        ok: true,
        json: () =>
          Promise.resolve({
            user: mockUser,
            access_token: 'token123',
            refresh_token: 'refresh123',
          }),
      }

      ;(global.fetch as Mock).mockResolvedValueOnce(mockResponse)

      render(
        <ErrorProvider>
          <AuthProvider>
            <TestComponent />
          </AuthProvider>
        </ErrorProvider>
      )

      await act(async () => {
        screen.getByTestId('login-btn').click()
      })

      await waitFor(() => {
        expect(screen.getByTestId('user-id')).toHaveTextContent('user-123')
        expect(screen.getByTestId('user-email')).toHaveTextContent(
          'test@example.com'
        )
        expect(screen.getByTestId('user-role')).toHaveTextContent('user')
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true')
      })

      expect(global.fetch).toHaveBeenCalledWith('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'test@example.com',
          password: 'password123',
        }),
        credentials: 'include',
        signal: expect.any(AbortSignal),
      })
    })

    it('should handle login failure with 401 unauthorized', async () => {
      const mockResponse = {
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: () => Promise.resolve({ detail: 'Invalid credentials' }),
      }

      ;(global.fetch as Mock).mockResolvedValueOnce(mockResponse)

      render(
        <ErrorProvider>
          <AuthProvider>
            <TestComponent />
          </AuthProvider>
        </ErrorProvider>
      )

      await act(async () => {
        screen.getByTestId('login-btn').click()
      })

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toHaveTextContent(
          'Invalid credentials'
        )
        expect(screen.getByTestId('error-code')).toHaveTextContent(
          'INVALID_CREDENTIALS'
        )
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent(
          'false'
        )
      })

      // Error should be handled by real ErrorProvider now
    })

    it('should handle 2FA required error', async () => {
      const mockResponse = {
        ok: false,
        status: 422,
        statusText: 'Unprocessable Entity',
        json: () => Promise.resolve({ detail: '2FA code required' }),
      }

      ;(global.fetch as Mock).mockResolvedValueOnce(mockResponse)

      render(
        <ErrorProvider>
          <AuthProvider>
            <TestComponent />
          </AuthProvider>
        </ErrorProvider>
      )

      await act(async () => {
        screen.getByTestId('login-btn').click()
      })

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toHaveTextContent(
          '2FA code required'
        )
        expect(screen.getByTestId('error-code')).toHaveTextContent(
          'MISSING_2FA'
        )
      })
    })

    it('should handle network timeout errors', async () => {
      ;(global.fetch as Mock).mockImplementation(() => {
        return new Promise((_, reject) => {
          setTimeout(() => {
            const error = new Error('The operation was aborted')
            error.name = 'AbortError'
            reject(error)
          }, 100)
        })
      })

      render(
        <ErrorProvider>
          <AuthProvider>
            <TestComponent />
          </AuthProvider>
        </ErrorProvider>
      )

      await act(async () => {
        screen.getByTestId('login-btn').click()
      })

      await waitFor(
        () => {
          expect(screen.getByTestId('error-message')).toHaveTextContent(
            'Timeout na conexão com o servidor'
          )
          expect(screen.getByTestId('error-code')).toHaveTextContent('TIMEOUT')
          expect(screen.getByTestId('error-retryable')).toHaveTextContent(
            'true'
          )
        },
        { timeout: 1000 }
      )
    })

    it('should handle network fetch errors', async () => {
      const networkError = new Error('Failed to fetch')
      networkError.name = 'TypeError'
      ;(global.fetch as Mock).mockRejectedValueOnce(networkError)

      render(
        <ErrorProvider>
          <AuthProvider>
            <TestComponent />
          </AuthProvider>
        </ErrorProvider>
      )

      await act(async () => {
        screen.getByTestId('login-btn').click()
      })

      await waitFor(() => {
        expect(screen.getByTestId('error-code')).toHaveTextContent(
          'NETWORK_ERROR'
        )
        expect(screen.getByTestId('error-retryable')).toHaveTextContent('true')
      })
    })

    it('should store tokens in localStorage during development', async () => {
      const mockUser = {
        id: 'user-123',
        email: 'test@example.com',
        role: 'user' as const,
        is_active: true,
        has_2fa: false,
      }

      const mockResponse = {
        ok: true,
        json: () =>
          Promise.resolve({
            user: mockUser,
            access_token: 'token123',
            refresh_token: 'refresh123',
          }),
      }

      ;(global.fetch as Mock).mockResolvedValueOnce(mockResponse)

      render(
        <ErrorProvider>
          <AuthProvider>
            <TestComponent />
          </AuthProvider>
        </ErrorProvider>
      )

      await act(async () => {
        screen.getByTestId('login-btn').click()
      })

      await waitFor(() => {
        expect(localStorage.setItem).toHaveBeenCalledWith(
          'access_token',
          'token123'
        )
        expect(localStorage.setItem).toHaveBeenCalledWith(
          'refresh_token',
          'refresh123'
        )
      })
    })
  })

  describe('Logout Functionality', () => {
    it('should handle successful logout', async () => {
      const mockResponse = { ok: true }
      ;(global.fetch as Mock).mockResolvedValueOnce(mockResponse)
      ;(localStorage.getItem as Mock).mockReturnValue('token123')

      render(
        <ErrorProvider>
          <AuthProvider>
            <TestComponent />
          </AuthProvider>
        </ErrorProvider>
      )

      await act(async () => {
        screen.getByTestId('logout-btn').click()
      })

      await waitFor(() => {
        expect(screen.getByTestId('user-id')).toHaveTextContent(
          'not-authenticated'
        )
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent(
          'false'
        )
      })

      expect(localStorage.removeItem).toHaveBeenCalledWith('access_token')
      expect(localStorage.removeItem).toHaveBeenCalledWith('refresh_token')
      expect(mockPush).toHaveBeenCalledWith('/login')
    })

    it('should handle logout even when server call fails', async () => {
      ;(global.fetch as Mock).mockRejectedValueOnce(new Error('Server error'))
      ;(localStorage.getItem as Mock).mockReturnValue('token123')

      render(
        <ErrorProvider>
          <AuthProvider>
            <TestComponent />
          </AuthProvider>
        </ErrorProvider>
      )

      await act(async () => {
        screen.getByTestId('logout-btn').click()
      })

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent(
          'false'
        )
      })

      expect(mockPush).toHaveBeenCalledWith('/login')
    })
  })

  describe('Token Refresh', () => {
    it('should handle successful token refresh', async () => {
      const mockResponse = {
        ok: true,
        json: async () => ({
          access_token: 'new-token',
          refresh_token: 'new-refresh-token',
        }),
      }

      // Mock the initial auth check (first call)
      ;(global.fetch as Mock)
        .mockResolvedValueOnce({
          ok: false, // Auth check fails, that's ok for this test
          status: 401,
        })
        .mockResolvedValueOnce(mockResponse) // Refresh token call
      ;(localStorage.getItem as Mock).mockReturnValue('refresh123')

      const { container } = render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      )

      // Wait for component to render
      await waitFor(() => {
        expect(screen.getByTestId('refresh-btn')).toBeInTheDocument()
      })

      const refreshBtn = screen.getByTestId('refresh-btn')

      // Call refreshToken function
      await act(async () => {
        refreshBtn.click()
      })

      // Wait for the fetch call to complete and verify it was called
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/v1/auth/refresh',
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({ refresh_token: 'refresh123' }),
          })
        )
      })

      expect(localStorage.setItem).toHaveBeenCalledWith(
        'access_token',
        'new-token'
      )
      expect(localStorage.setItem).toHaveBeenCalledWith(
        'refresh_token',
        'new-refresh-token'
      )
    })

    it('should logout when refresh token is invalid', async () => {
      const mockResponse = { ok: false, status: 401 }
      ;(global.fetch as Mock).mockResolvedValueOnce(mockResponse)
      ;(localStorage.getItem as Mock).mockReturnValue('invalid-refresh')

      render(
        <ErrorProvider>
          <AuthProvider>
            <TestComponent />
          </AuthProvider>
        </ErrorProvider>
      )

      await act(async () => {
        screen.getByTestId('refresh-btn').click()
      })

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login')
      })
    })
  })

  describe('2FA Functionality', () => {
    it('should handle 2FA setup', async () => {
      const mockResponse = {
        ok: true,
        json: () =>
          Promise.resolve({
            secret: 'SECRET123',
            qr_code_url: 'data:image/png;base64,...',
            backup_codes: ['code1', 'code2'],
          }),
      }

      ;(global.fetch as Mock).mockResolvedValueOnce(mockResponse)
      ;(localStorage.getItem as Mock).mockReturnValue('token123')

      render(
        <ErrorProvider>
          <AuthProvider>
            <TestComponent />
          </AuthProvider>
        </ErrorProvider>
      )

      await act(async () => {
        await fireEvent.click(screen.getByTestId('setup-2fa-btn'))
      })

      expect(global.fetch).toHaveBeenCalledWith('/api/v1/auth/setup-2fa', {
        method: 'GET',
        headers: { Authorization: 'Bearer token123' },
        credentials: 'include',
      })
    })

    it('should handle 2FA enable with user state update', async () => {
      // First set up a user
      const mockUser = {
        id: 'user-123',
        email: 'test@example.com',
        role: 'user' as const,
        is_active: true,
        has_2fa: false,
      }

      const loginResponse = {
        ok: true,
        json: () => Promise.resolve({ user: mockUser }),
      }

      const enable2FAResponse = {
        ok: true,
        json: () => Promise.resolve({ success: true }),
      }

      ;(global.fetch as Mock)
        .mockResolvedValueOnce(loginResponse)
        .mockResolvedValueOnce(enable2FAResponse)
      ;(localStorage.getItem as Mock).mockReturnValue('token123')

      render(
        <ErrorProvider>
          <AuthProvider>
            <TestComponent />
          </AuthProvider>
        </ErrorProvider>
      )

      // Login first
      await act(async () => {
        screen.getByTestId('login-btn').click()
      })

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true')
      })

      // Enable 2FA
      await act(async () => {
        screen.getByTestId('enable-2fa-btn').click()
      })

      expect(global.fetch).toHaveBeenLastCalledWith('/api/v1/auth/enable-2fa', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer token123',
        },
        body: JSON.stringify({ totp_code: '123456' }),
        credentials: 'include',
      })
    })
  })

  describe('Error Handling', () => {
    it('should clear errors', async () => {
      const mockResponse = {
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Test error' }),
      }

      ;(global.fetch as Mock).mockResolvedValueOnce(mockResponse)

      render(
        <ErrorProvider>
          <AuthProvider>
            <TestComponent />
          </AuthProvider>
        </ErrorProvider>
      )

      // Trigger error
      await act(async () => {
        screen.getByTestId('login-btn').click()
      })

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toHaveTextContent(
          'Test error'
        )
      })

      // Clear error
      await act(async () => {
        screen.getByTestId('clear-error-btn').click()
      })

      expect(screen.getByTestId('error-message')).toHaveTextContent('no-error')
    })

    it('should handle retry functionality', async () => {
      const mockResponse = {
        ok: false,
        status: 500,
        json: () => Promise.resolve({ detail: 'Server error' }),
      }

      const successResponse = {
        ok: true,
        json: () =>
          Promise.resolve({
            user: {
              id: 'user-123',
              email: 'test@example.com',
              role: 'user' as const,
              is_active: true,
              has_2fa: false,
            },
          }),
      }

      ;(global.fetch as Mock)
        .mockResolvedValueOnce(mockResponse)
        .mockResolvedValueOnce(successResponse)

      render(
        <ErrorProvider>
          <AuthProvider>
            <TestComponent />
          </AuthProvider>
        </ErrorProvider>
      )

      // Trigger error
      await act(async () => {
        screen.getByTestId('login-btn').click()
      })

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toHaveTextContent(
          'Server error'
        )
      })

      // Retry
      await act(async () => {
        screen.getByTestId('retry-btn').click()
      })

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true')
      })
    })
  })

  describe('usePermissions Hook', () => {
    const renderWithUser = (role: 'user' | 'admin' | 'sysadmin') => {
      const mockUser = {
        id: 'user-123',
        email: 'test@example.com',
        role,
        is_active: true,
        has_2fa: false,
      }

      const TestWrapper: React.FC = () => {
        const auth = useAuth()

        React.useEffect(() => {
          auth.login({ email: 'test@example.com', password: 'password' })
        }, [])

        if (!auth.isAuthenticated) {
          return <div>Loading...</div>
        }

        return <PermissionsTestComponent />
      }

      const loginResponse = {
        ok: true,
        json: () => Promise.resolve({ user: mockUser }),
      }

      ;(global.fetch as Mock).mockResolvedValueOnce(loginResponse)

      return render(
        <AuthProvider>
          <TestWrapper />
        </AuthProvider>
      )
    }

    it('should correctly check user role permissions', async () => {
      renderWithUser('user')

      await waitFor(() => {
        expect(screen.getByTestId('has-user-role')).toHaveTextContent('true')
        expect(screen.getByTestId('has-admin-role')).toHaveTextContent('false')
        expect(screen.getByTestId('has-sysadmin-role')).toHaveTextContent(
          'false'
        )
        expect(screen.getByTestId('is-admin')).toHaveTextContent('false')
        expect(screen.getByTestId('is-sysadmin')).toHaveTextContent('false')
      })
    })

    it('should correctly check admin role permissions', async () => {
      renderWithUser('admin')

      await waitFor(() => {
        expect(screen.getByTestId('has-user-role')).toHaveTextContent('true')
        expect(screen.getByTestId('has-admin-role')).toHaveTextContent('true')
        expect(screen.getByTestId('has-sysadmin-role')).toHaveTextContent(
          'false'
        )
        expect(screen.getByTestId('is-admin')).toHaveTextContent('true')
        expect(screen.getByTestId('is-sysadmin')).toHaveTextContent('false')
      })
    })

    it('should correctly check sysadmin role permissions', async () => {
      renderWithUser('sysadmin')

      await waitFor(() => {
        expect(screen.getByTestId('has-user-role')).toHaveTextContent('true')
        expect(screen.getByTestId('has-admin-role')).toHaveTextContent('true')
        expect(screen.getByTestId('has-sysadmin-role')).toHaveTextContent(
          'true'
        )
        expect(screen.getByTestId('is-admin')).toHaveTextContent('true')
        expect(screen.getByTestId('is-sysadmin')).toHaveTextContent('true')
      })
    })

    it('should return false for all permissions when user is null', () => {
      render(
        <AuthProvider>
          <PermissionsTestComponent />
        </AuthProvider>
      )

      expect(screen.getByTestId('has-user-role')).toHaveTextContent('false')
      expect(screen.getByTestId('has-admin-role')).toHaveTextContent('false')
      expect(screen.getByTestId('has-sysadmin-role')).toHaveTextContent('false')
      expect(screen.getByTestId('is-admin')).toHaveTextContent('false')
      expect(screen.getByTestId('is-sysadmin')).toHaveTextContent('false')
    })
  })
})
