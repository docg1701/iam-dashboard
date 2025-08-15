/**
 * Authentication Flow Integration Tests
 * Tests complete user authentication workflows including login, logout, 2FA, and token management
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'
import { ErrorProvider } from '@/components/errors/ErrorContext'
import { LoginForm } from '@/components/forms/LoginForm'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'

// Mock Next.js navigation
const mockPush = vi.fn()
const mockReplace = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    prefetch: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
  }),
  usePathname: () => '/login',
  useSearchParams: () => new URLSearchParams(),
}))

// Test wrapper with all necessary providers
const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: Infinity },
      mutations: { retry: false },
    },
  })

  return (
    <ErrorProvider
      enableConsoleLogging={false}
      enableGlobalErrorHandler={false}
    >
      <QueryClientProvider client={queryClient}>
        <AuthProvider>{children}</AuthProvider>
      </QueryClientProvider>
    </ErrorProvider>
  )
}

// Mock dashboard component for testing protected routes
const MockDashboard = () => (
  <div data-testid="dashboard">
    <h1>Dashboard</h1>
    <p>Protected content</p>
  </div>
)

describe('Authentication Flow Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn()
    localStorage.clear()
    sessionStorage.clear()
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe('Login Flow Integration', () => {
    it('should complete successful login flow without 2FA', async () => {
      const mockUser = {
        id: '1',
        email: 'user@example.com',
        name: 'Test User',
        role: 'user',
        is_active: true,
        has_2fa: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      // Mock successful login API response
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          access_token: 'mock_access_token_123',
          refresh_token: 'mock_refresh_token_456',
          token_type: 'bearer',
          expires_in: 3600,
          user: mockUser,
        }),
      })

      const onSuccess = vi.fn()
      const onError = vi.fn()

      render(
        <TestWrapper>
          <LoginForm onSuccess={onSuccess} onError={onError} />
        </TestWrapper>
      )

      // Fill in login credentials
      const emailInput = screen.getByLabelText(/e-mail/i)
      const passwordInput = screen.getByLabelText(/senha/i)
      const submitButton = screen.getByRole('button', { name: /entrar/i })

      fireEvent.change(emailInput, { target: { value: 'user@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })

      // Submit the form
      fireEvent.click(submitButton)

      // Wait for login to complete
      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalled()
      })

      // Verify API call was made correctly
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/v1/auth/login',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: 'user@example.com',
            password: 'password123',
            totp_code: '',
          }),
          credentials: 'include',
        })
      )

      // Verify tokens are stored (in development mode)
      expect(localStorage.getItem('access_token')).toBe('mock_access_token_123')
      expect(localStorage.getItem('refresh_token')).toBe(
        'mock_refresh_token_456'
      )
    })

    it('should handle 2FA authentication flow', async () => {
      const mockUser = {
        id: '1',
        email: 'user@example.com',
        name: 'Test User',
        role: 'user',
        is_active: true,
        has_2fa: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      // Mock 2FA required response followed by successful login
      global.fetch = vi
        .fn()
        .mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: async () => ({
            detail: 'Two-factor authentication required',
            requires_2fa: true,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({
            access_token: 'mock_access_token_123',
            refresh_token: 'mock_refresh_token_456',
            token_type: 'bearer',
            expires_in: 3600,
            user: mockUser,
          }),
        })

      const onSuccess = vi.fn()
      const onError = vi.fn()

      render(
        <TestWrapper>
          <LoginForm onSuccess={onSuccess} onError={onError} />
        </TestWrapper>
      )

      // Initial login attempt
      const emailInput = screen.getByLabelText(/e-mail/i)
      const passwordInput = screen.getByLabelText(/senha/i)
      const submitButton = screen.getByRole('button', { name: /entrar/i })

      fireEvent.change(emailInput, { target: { value: 'user@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      fireEvent.click(submitButton)

      // Wait for 2FA input to appear
      await waitFor(() => {
        expect(
          screen.getByLabelText(/código de autenticação/i)
        ).toBeInTheDocument()
      })

      // Enter 2FA code
      const totpInput = screen.getByLabelText(/código de autenticação/i)
      fireEvent.change(totpInput, { target: { value: '123456' } })
      fireEvent.click(submitButton)

      // Wait for successful login
      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalled()
      })

      // Verify both API calls were made
      expect(global.fetch).toHaveBeenCalledTimes(2)
    })

    it('should handle login failure with proper error display', async () => {
      // Mock failed login response
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({
          detail: 'Invalid email or password',
        }),
      })

      const onSuccess = vi.fn()
      const onError = vi.fn()

      render(
        <TestWrapper>
          <LoginForm onSuccess={onSuccess} onError={onError} />
        </TestWrapper>
      )

      const emailInput = screen.getByLabelText(/e-mail/i)
      const passwordInput = screen.getByLabelText(/senha/i)
      const submitButton = screen.getByRole('button', { name: /entrar/i })

      fireEvent.change(emailInput, { target: { value: 'user@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } })
      fireEvent.click(submitButton)

      // Wait for error to be handled
      await waitFor(() => {
        expect(onError).toHaveBeenCalledWith('Invalid email or password')
      })

      // Verify success callback was not called
      expect(onSuccess).not.toHaveBeenCalled()
    })
  })

  describe('Protected Route Integration', () => {
    it('should allow access to protected content when authenticated', async () => {
      const mockUser = {
        id: '1',
        email: 'user@example.com',
        name: 'Test User',
        role: 'user',
        is_active: true,
        has_2fa: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      // Set up authenticated state
      localStorage.setItem('access_token', 'valid_token')
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockUser,
      })

      render(
        <TestWrapper>
          <ProtectedRoute>
            <MockDashboard />
          </ProtectedRoute>
        </TestWrapper>
      )

      // Wait for authentication check and content to load
      await waitFor(() => {
        expect(screen.getByTestId('dashboard')).toBeInTheDocument()
      })

      // Verify user profile API was called
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/auth/me', {
        headers: {
          Authorization: 'Bearer valid_token',
        },
        credentials: 'include',
      })
    })

    it('should redirect to login when not authenticated', async () => {
      // No token in localStorage

      render(
        <TestWrapper>
          <ProtectedRoute>
            <MockDashboard />
          </ProtectedRoute>
        </TestWrapper>
      )

      // Should redirect to login
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login')
      })

      // Protected content should not be rendered
      expect(screen.queryByTestId('dashboard')).not.toBeInTheDocument()
    })

    it('should handle role-based access control', async () => {
      const mockUser = {
        id: '1',
        email: 'user@example.com',
        name: 'Regular User',
        role: 'user',
        is_active: true,
        has_2fa: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      localStorage.setItem('access_token', 'valid_token')
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockUser,
      })

      render(
        <TestWrapper>
          <ProtectedRoute requiredRole="admin">
            <MockDashboard />
          </ProtectedRoute>
        </TestWrapper>
      )

      // Should show access denied message
      await waitFor(() => {
        expect(screen.getByText(/acesso negado/i)).toBeInTheDocument()
      })

      // Protected content should not be rendered
      expect(screen.queryByTestId('dashboard')).not.toBeInTheDocument()
    })
  })

  describe('Token Refresh Integration', () => {
    it('should automatically refresh expired tokens', async () => {
      const mockUser = {
        id: '1',
        email: 'user@example.com',
        name: 'Test User',
        role: 'user',
        is_active: true,
        has_2fa: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      localStorage.setItem('access_token', 'expired_token')
      localStorage.setItem('refresh_token', 'valid_refresh_token')

      // Mock expired token response followed by successful refresh
      global.fetch = vi
        .fn()
        .mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: async () => ({ detail: 'Token expired' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({
            access_token: 'new_access_token',
            refresh_token: 'new_refresh_token',
            token_type: 'bearer',
            expires_in: 3600,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => mockUser,
        })

      render(
        <TestWrapper>
          <ProtectedRoute>
            <MockDashboard />
          </ProtectedRoute>
        </TestWrapper>
      )

      // Wait for token refresh and successful authentication
      await waitFor(() => {
        expect(screen.getByTestId('dashboard')).toBeInTheDocument()
      })

      // Verify refresh token was used
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          refresh_token: 'valid_refresh_token',
        }),
        credentials: 'include',
      })

      // Verify new tokens were stored
      expect(localStorage.getItem('access_token')).toBe('new_access_token')
      expect(localStorage.getItem('refresh_token')).toBe('new_refresh_token')
    })

    it('should logout when refresh token is invalid', async () => {
      localStorage.setItem('access_token', 'expired_token')
      localStorage.setItem('refresh_token', 'invalid_refresh_token')

      // Mock failed token refresh
      global.fetch = vi
        .fn()
        .mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: async () => ({ detail: 'Token expired' }),
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: async () => ({ detail: 'Invalid refresh token' }),
        })

      render(
        <TestWrapper>
          <ProtectedRoute>
            <MockDashboard />
          </ProtectedRoute>
        </TestWrapper>
      )

      // Should redirect to login after failed refresh
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login')
      })

      // Tokens should be cleared
      expect(localStorage.getItem('access_token')).toBeNull()
      expect(localStorage.getItem('refresh_token')).toBeNull()
    })
  })

  describe('Logout Flow Integration', () => {
    it('should handle complete logout flow', async () => {
      // Set up authenticated state
      localStorage.setItem('access_token', 'valid_token')
      localStorage.setItem('refresh_token', 'valid_refresh_token')

      // Mock logout API response
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ message: 'Logged out successfully' }),
      })

      const TestLogoutComponent = () => {
        const { logout } = useAuth()
        return (
          <button data-testid="logout-btn" onClick={logout}>
            Logout
          </button>
        )
      }

      render(
        <TestWrapper>
          <TestLogoutComponent />
        </TestWrapper>
      )

      const logoutButton = screen.getByTestId('logout-btn')
      fireEvent.click(logoutButton)

      // Wait for logout to complete
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login')
      })

      // Verify logout API was called
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/auth/logout', {
        method: 'POST',
        headers: {
          Authorization: 'Bearer valid_token',
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      })

      // Verify tokens were cleared
      expect(localStorage.getItem('access_token')).toBeNull()
      expect(localStorage.getItem('refresh_token')).toBeNull()
    })
  })

  describe('Session Management Integration', () => {
    it('should handle session persistence across page reloads', async () => {
      const mockUser = {
        id: '1',
        email: 'user@example.com',
        name: 'Test User',
        role: 'user',
        is_active: true,
        has_2fa: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      // Simulate existing session
      localStorage.setItem('access_token', 'existing_token')

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockUser,
      })

      render(
        <TestWrapper>
          <ProtectedRoute>
            <MockDashboard />
          </ProtectedRoute>
        </TestWrapper>
      )

      // Should automatically authenticate with existing token
      await waitFor(() => {
        expect(screen.getByTestId('dashboard')).toBeInTheDocument()
      })

      // Should call user profile API with stored token
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/auth/me', {
        headers: {
          Authorization: 'Bearer existing_token',
        },
        credentials: 'include',
      })
    })

    it('should handle concurrent authentication requests', async () => {
      const mockUser = {
        id: '1',
        email: 'user@example.com',
        name: 'Test User',
        role: 'user',
        is_active: true,
        has_2fa: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      localStorage.setItem('access_token', 'valid_token')

      // Mock delayed response to test concurrent handling
      global.fetch = vi.fn().mockImplementation(
        () =>
          new Promise(resolve =>
            setTimeout(
              () =>
                resolve({
                  ok: true,
                  status: 200,
                  json: async () => mockUser,
                }),
              100
            )
          )
      )

      // Render multiple protected routes simultaneously
      render(
        <TestWrapper>
          <ProtectedRoute>
            <div data-testid="route-1">Route 1</div>
          </ProtectedRoute>
          <ProtectedRoute>
            <div data-testid="route-2">Route 2</div>
          </ProtectedRoute>
        </TestWrapper>
      )

      // Wait for both routes to be accessible
      await waitFor(() => {
        expect(screen.getByTestId('route-1')).toBeInTheDocument()
        expect(screen.getByTestId('route-2')).toBeInTheDocument()
      })

      // Should only make one API call despite multiple protected routes
      expect(global.fetch).toHaveBeenCalledTimes(1)
    })
  })
})
