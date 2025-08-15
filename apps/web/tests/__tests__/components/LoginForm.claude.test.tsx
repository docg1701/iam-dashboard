/**
 * CLAUDE.md Compliant LoginForm tests
 * Only mocks external APIs, uses real components and contexts
 */

import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

import { LoginForm } from '@/components/forms/LoginForm'
import { AuthProvider } from '@/contexts/AuthContext'
import { ErrorProvider } from '@/components/errors/ErrorContext'
import { Toaster } from '@/components/ui/toaster'

// Mock external dependencies only (CLAUDE.md compliant)
global.fetch = vi.fn()

// Mock Lucide icons (external library)
vi.mock('lucide-react', () => ({
  Eye: ({ className }: { className?: string }) => (
    <span data-testid="eye-icon" className={className} />
  ),
  EyeOff: ({ className }: { className?: string }) => (
    <span data-testid="eye-off-icon" className={className} />
  ),
  Loader2: ({ className }: { className?: string }) => (
    <span data-testid="loader-icon" className={className} />
  ),
  X: ({ className }: { className?: string }) => (
    <span data-testid="x-icon" className={className} />
  ),
}))

// Test wrapper with real providers (CLAUDE.md compliant)
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ErrorProvider>
    <AuthProvider>
      {children}
      <Toaster />
    </AuthProvider>
  </ErrorProvider>
)

describe('LoginForm - CLAUDE.md Compliant', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()

    // Mock successful login API response (external dependency)
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          access_token: 'test_token',
          refresh_token: 'test_refresh',
          user: {
            id: 1,
            email: 'test@example.com',
            role: 'user',
            is_active: true,
            has_2fa: false,
          },
        }),
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Rendering', () => {
    it('should render the login form with all required fields', () => {
      render(
        <TestWrapper>
          <LoginForm />
        </TestWrapper>
      )

      expect(screen.getByText('Entrar no Dashboard IAM')).toBeInTheDocument()
      expect(screen.getByLabelText('E-mail')).toBeInTheDocument()
      expect(screen.getByLabelText('Senha')).toBeInTheDocument()
      expect(screen.getByLabelText('Lembrar de mim')).toBeInTheDocument()
      expect(
        screen.getByRole('button', { name: /entrar/i })
      ).toBeInTheDocument()
    })

    it('should not show TOTP input initially', () => {
      render(
        <TestWrapper>
          <LoginForm />
        </TestWrapper>
      )

      expect(screen.queryByText('Código 2FA')).not.toBeInTheDocument()
      expect(screen.queryByPlaceholderText('000000')).not.toBeInTheDocument()
    })
  })

  describe('Form Validation', () => {
    it('should validate email and password are required', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <LoginForm />
        </TestWrapper>
      )

      const submitButton = screen.getByRole('button', { name: /entrar/i })
      await user.click(submitButton)

      // Should not call API when form is invalid
      expect(global.fetch).not.toHaveBeenCalled()
    })

    it('should enable submit button when email and password are filled', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <LoginForm />
        </TestWrapper>
      )

      const emailInput = screen.getByLabelText('E-mail')
      const passwordInput = screen.getByLabelText('Senha')
      const submitButton = screen.getByRole('button', { name: /entrar/i })

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'password123')

      // Button should be enabled with valid inputs
      expect(submitButton).not.toBeDisabled()
    })
  })

  describe('External API Integration', () => {
    it('should call login API with correct data', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <LoginForm />
        </TestWrapper>
      )

      const emailInput = screen.getByLabelText('E-mail')
      const passwordInput = screen.getByLabelText('Senha')
      const submitButton = screen.getByRole('button', { name: /entrar/i })

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'password123')
      await user.click(submitButton)

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/v1/auth/login',
          expect.objectContaining({
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              email: 'test@example.com',
              password: 'password123',
              totp_code: '',
              remember_me: false,
            }),
            credentials: 'include',
          })
        )
      })
    })

    it('should handle API errors gracefully', async () => {
      const user = userEvent.setup()

      // Mock API error response
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        json: () =>
          Promise.resolve({
            detail: 'Invalid credentials',
          }),
      })

      render(
        <TestWrapper>
          <LoginForm />
        </TestWrapper>
      )

      const emailInput = screen.getByLabelText('E-mail')
      const passwordInput = screen.getByLabelText('Senha')
      const submitButton = screen.getByRole('button', { name: /entrar/i })

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'wrongpassword')
      await user.click(submitButton)

      // Should show error message without crashing
      await waitFor(
        () => {
          expect(screen.getByText(/erro/i)).toBeInTheDocument()
        },
        { timeout: 5000 }
      )
    })
  })
})
