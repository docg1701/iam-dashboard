/**
 * LoginForm Component Tests
 * Tests authentication form behavior and user interactions
 * Following CLAUDE.md rules: no internal mocking, only external API mocking
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { LoginForm } from '../LoginForm'

// Mock only external fetch API
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

beforeEach(() => {
  vi.clearAllMocks()
  mockFetch.mockReset()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('LoginForm', () => {
  it('should render login form with email and password fields', () => {
    render(
      <TestWrapper>
        <LoginForm />
      </TestWrapper>
    )
    
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/senha/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /entrar/i })).toBeInTheDocument()
  })

  it('should validate email field correctly', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <LoginForm />
      </TestWrapper>
    )
    
    const emailField = screen.getByLabelText(/email/i)
    const submitButton = screen.getByRole('button', { name: /entrar/i })
    
    // Try to submit with invalid email
    await user.type(emailField, 'invalid-email')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/email inválido/i)).toBeInTheDocument()
    })
  })

  it('should validate password field correctly', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <LoginForm />
      </TestWrapper>
    )
    
    const passwordField = screen.getByLabelText(/senha/i)
    const submitButton = screen.getByRole('button', { name: /entrar/i })
    
    // Try to submit with empty password
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/senha é obrigatória/i)).toBeInTheDocument()
    })
  })

  it('should handle successful login without 2FA', async () => {
    const user = userEvent.setup()
    
    // Mock successful login response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        access_token: 'mock-token',
        token_type: 'bearer',
        expires_in: 3600,
        requires_2fa: false,
        user: {
          user_id: 'user-123',
          email: 'test@example.com',
          role: 'admin',
          full_name: 'Test User'
        }
      })
    } as Response)
    
    render(
      <TestWrapper>
        <LoginForm />
      </TestWrapper>
    )
    
    const emailField = screen.getByLabelText(/email/i)
    const passwordField = screen.getByLabelText(/senha/i)
    const submitButton = screen.getByRole('button', { name: /entrar/i })
    
    await user.type(emailField, 'test@example.com')
    await user.type(passwordField, 'password123')
    await user.click(submitButton)
    
    // Should show loading state
    await waitFor(() => {
      expect(screen.getByText(/entrando/i)).toBeInTheDocument()
    })
    
    // Should call login API
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/login'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          }),
          body: JSON.stringify({
            email: 'test@example.com',
            password: 'password123'
          })
        })
      )
    })
  })

  it('should handle 2FA requirement correctly', async () => {
    const user = userEvent.setup()
    
    // Mock login response requiring 2FA
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        requires_2fa: true,
        session_id: 'temp-session-123',
        message: '2FA code required'
      })
    } as Response)
    
    render(
      <TestWrapper>
        <LoginForm />
      </TestWrapper>
    )
    
    const emailField = screen.getByLabelText(/email/i)
    const passwordField = screen.getByLabelText(/senha/i)
    const submitButton = screen.getByRole('button', { name: /entrar/i })
    
    await user.type(emailField, 'test@example.com')
    await user.type(passwordField, 'password123')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/código 2fa/i)).toBeInTheDocument()
    })
  })

  it('should handle login errors correctly', async () => {
    const user = userEvent.setup()
    
    // Mock login error response
    mockFetch.mockRejectedValueOnce(new Error('Invalid credentials'))
    
    render(
      <TestWrapper>
        <LoginForm />
      </TestWrapper>
    )
    
    const emailField = screen.getByLabelText(/email/i)
    const passwordField = screen.getByLabelText(/senha/i)
    const submitButton = screen.getByRole('button', { name: /entrar/i })
    
    await user.type(emailField, 'wrong@example.com')
    await user.type(passwordField, 'wrongpassword')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/credenciais inválidas/i)).toBeInTheDocument()
    })
  })

  it('should handle account lockout error', async () => {
    const user = userEvent.setup()
    
    // Mock account lockout response
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 423,
      json: () => Promise.resolve({
        detail: 'Account locked due to too many failed login attempts'
      })
    } as Response)
    
    render(
      <TestWrapper>
        <LoginForm />
      </TestWrapper>
    )
    
    const emailField = screen.getByLabelText(/email/i)
    const passwordField = screen.getByLabelText(/senha/i)
    const submitButton = screen.getByRole('button', { name: /entrar/i })
    
    await user.type(emailField, 'locked@example.com')
    await user.type(passwordField, 'password123')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/conta bloqueada/i)).toBeInTheDocument()
    })
  })

  it('should display loading state during form submission', async () => {
    const user = userEvent.setup()
    
    // Mock delayed response
    mockFetch.mockImplementationOnce(() => 
      new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({ access_token: 'token' })
        } as Response), 100)
      )
    )
    
    render(
      <TestWrapper>
        <LoginForm />
      </TestWrapper>
    )
    
    const emailField = screen.getByLabelText(/email/i)
    const passwordField = screen.getByLabelText(/senha/i)
    const submitButton = screen.getByRole('button', { name: /entrar/i })
    
    await user.type(emailField, 'test@example.com')
    await user.type(passwordField, 'password123')
    await user.click(submitButton)
    
    // Should show loading state immediately
    expect(screen.getByText(/entrando/i)).toBeInTheDocument()
    expect(submitButton).toBeDisabled()
  })

  it('should handle keyboard navigation correctly', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <LoginForm />
      </TestWrapper>
    )
    
    const emailField = screen.getByLabelText(/email/i)
    const passwordField = screen.getByLabelText(/senha/i)
    const submitButton = screen.getByRole('button', { name: /entrar/i })
    
    // Focus should start on email field
    emailField.focus()
    expect(emailField).toHaveFocus()
    
    // Tab to password field
    await user.tab()
    expect(passwordField).toHaveFocus()
    
    // Tab to submit button
    await user.tab()
    expect(submitButton).toHaveFocus()
    
    // Enter key should submit form when button is focused
    await user.type(emailField, 'test@example.com')
    await user.type(passwordField, 'password123')
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ access_token: 'token' })
    } as Response)
    
    submitButton.focus()
    await user.keyboard('{Enter}')
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled()
    })
  })

  it('should handle password visibility toggle', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <LoginForm />
      </TestWrapper>
    )
    
    const passwordField = screen.getByLabelText(/senha/i)
    const toggleButton = screen.getByRole('button', { name: /mostrar senha/i })
    
    // Initially password should be hidden
    expect(passwordField).toHaveAttribute('type', 'password')
    
    // Click toggle to show password
    await user.click(toggleButton)
    expect(passwordField).toHaveAttribute('type', 'text')
    
    // Click toggle to hide password again
    await user.click(toggleButton)
    expect(passwordField).toHaveAttribute('type', 'password')
  })

  it('should preserve form state during 2FA flow', async () => {
    const user = userEvent.setup()
    
    // Mock login response requiring 2FA
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        requires_2fa: true,
        session_id: 'temp-session-123'
      })
    } as Response)
    
    render(
      <TestWrapper>
        <LoginForm />
      </TestWrapper>
    )
    
    const emailField = screen.getByLabelText(/email/i)
    const passwordField = screen.getByLabelText(/senha/i)
    const submitButton = screen.getByRole('button', { name: /entrar/i })
    
    await user.type(emailField, 'test@example.com')
    await user.type(passwordField, 'password123')
    await user.click(submitButton)
    
    // Should transition to 2FA form
    await waitFor(() => {
      expect(screen.getByText(/código 2fa/i)).toBeInTheDocument()
    })
    
    // Email should still be visible for context
    expect(screen.getByText('test@example.com')).toBeInTheDocument()
  })

  it('should handle rate limiting error', async () => {
    const user = userEvent.setup()
    
    // Mock rate limiting response
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 429,
      json: () => Promise.resolve({
        detail: 'Too many requests. Try again in 60 seconds.'
      })
    } as Response)
    
    render(
      <TestWrapper>
        <LoginForm />
      </TestWrapper>
    )
    
    const emailField = screen.getByLabelText(/email/i)
    const passwordField = screen.getByLabelText(/senha/i)
    const submitButton = screen.getByRole('button', { name: /entrar/i })
    
    await user.type(emailField, 'test@example.com')
    await user.type(passwordField, 'password123')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/muitas tentativas/i)).toBeInTheDocument()
    })
  })
})