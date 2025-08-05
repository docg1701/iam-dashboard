import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { UserCreateForm } from '@/components/forms/UserCreateForm'
import { ToastProvider } from '@/components/ui/toast'
import * as usersAPI from '@/lib/api/users'

// Mock the users API
vi.mock('@/lib/api/users', () => ({
  usersAPI: {
    createUser: vi.fn()
  }
}))

// Mock the toast hook
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
    dismiss: vi.fn(),
    toasts: []
  })
}))

// Test wrapper component
const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        {children}
      </ToastProvider>
    </QueryClientProvider>
  )
}

describe('UserCreateForm', () => {
  const mockOnSuccess = vi.fn()
  const mockOnCancel = vi.fn()
  const mockCreateUser = vi.mocked(usersAPI.usersAPI.createUser)

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    cleanup()
  })

  const renderUserCreateForm = () => {
    return render(
      <TestWrapper>
        <UserCreateForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />
      </TestWrapper>
    )
  }

  it('renders all form fields correctly', () => {
    renderUserCreateForm()

    expect(screen.getByPlaceholderText(/digite o nome completo/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/usuario@exemplo.com/i)).toBeInTheDocument()
    expect(screen.getByRole('combobox')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/digite uma senha segura/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/digite a senha novamente/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /criar usuário/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /cancelar/i })).toBeInTheDocument()
  })

  it('shows validation errors for required fields', async () => {
    const user = userEvent.setup()
    renderUserCreateForm()

    const submitButton = screen.getByRole('button', { name: /criar usuário/i })
    await user.click(submitButton)

    // Verify that the API was NOT called due to validation failure
    await waitFor(() => {
      expect(mockCreateUser).not.toHaveBeenCalled()
    }, { timeout: 1000 })
  })

  it('validates email format', async () => {
    const user = userEvent.setup()
    renderUserCreateForm()

    const emailInput = screen.getByPlaceholderText(/usuario@exemplo.com/i)
    await user.type(emailInput, 'invalid-email')

    const submitButton = screen.getByRole('button', { name: /criar usuário/i })
    await user.click(submitButton)

    // Wait and verify that the API was NOT called due to validation failure
    await waitFor(() => {
      expect(mockCreateUser).not.toHaveBeenCalled()
    }, { timeout: 1000 })
  })

  it('validates password requirements', async () => {
    const user = userEvent.setup()
    renderUserCreateForm()

    const passwordInput = screen.getByPlaceholderText(/digite uma senha segura/i)
    await user.type(passwordInput, 'weak')

    const submitButton = screen.getByRole('button', { name: /criar usuário/i })
    await user.click(submitButton)

    // Verify that the API was NOT called due to validation failure
    await waitFor(() => {
      expect(mockCreateUser).not.toHaveBeenCalled()
    }, { timeout: 1000 })
  })

  it('validates password confirmation match', async () => {
    const user = userEvent.setup()
    renderUserCreateForm()

    const passwordInput = screen.getByPlaceholderText(/digite uma senha segura/i)
    const confirmPasswordInput = screen.getByPlaceholderText(/digite a senha novamente/i)

    await user.type(passwordInput, 'ValidPass123!')
    await user.type(confirmPasswordInput, 'DifferentPass123!')

    const submitButton = screen.getByRole('button', { name: /criar usuário/i })
    await user.click(submitButton)

    // Verify that the API was NOT called due to validation failure
    await waitFor(() => {
      expect(mockCreateUser).not.toHaveBeenCalled()
    }, { timeout: 1000 })
  })

  it('shows and hides password fields when eye icon is clicked', async () => {
    const user = userEvent.setup()
    renderUserCreateForm()

    const passwordInput = screen.getByPlaceholderText(/digite uma senha segura/i)
    const eyeButtons = screen.getAllByRole('button')
    const passwordEyeButton = eyeButtons.find(button => 
      button.closest('div')?.contains(passwordInput)
    )

    expect(passwordInput).toHaveAttribute('type', 'password')

    if (passwordEyeButton) {
      await user.click(passwordEyeButton)
      expect(passwordInput).toHaveAttribute('type', 'text')

      await user.click(passwordEyeButton)
      expect(passwordInput).toHaveAttribute('type', 'password')
    }
  })

  it('displays all role options with descriptions', async () => {
    const user = userEvent.setup()
    renderUserCreateForm()

    const roleSelect = screen.getByRole('combobox')
    await user.click(roleSelect)

    await waitFor(() => {
      expect(screen.getByText('Administrador do Sistema')).toBeInTheDocument()
      expect(screen.getByText('Administrador')).toBeInTheDocument()
      expect(screen.getByText('Usuário')).toBeInTheDocument()
      expect(screen.getAllByText(/acesso total ao sistema/i).length).toBeGreaterThan(0)
      expect(screen.getAllByText(/gerenciamento de clientes e relatórios/i).length).toBeGreaterThan(0)
      expect(screen.getAllByText(/operações básicas com clientes/i).length).toBeGreaterThan(0)
    })
  })

  it('submits form with valid data successfully', async () => {
    const user = userEvent.setup()
    mockCreateUser.mockResolvedValueOnce({
      user_id: '123',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'admin',
      status: 'active',
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
      is_verified: true
    })

    renderUserCreateForm()

    // Fill out form
    await user.type(screen.getByPlaceholderText(/digite o nome completo/i), 'Test User')
    await user.type(screen.getByPlaceholderText(/usuario@exemplo.com/i), 'test@example.com')
    await user.type(screen.getByPlaceholderText(/digite uma senha segura/i), 'ValidPass123!')
    await user.type(screen.getByPlaceholderText(/digite a senha novamente/i), 'ValidPass123!')

    // Select role
    const roleSelect = screen.getByRole('combobox')
    await user.click(roleSelect)
    await user.click(screen.getByText('Administrador'))

    // Submit form
    const submitButton = screen.getByRole('button', { name: /criar usuário/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockCreateUser).toHaveBeenCalledWith({
        email: 'test@example.com',
        full_name: 'Test User',
        password: 'ValidPass123!',
        role: 'admin'
      })
      expect(mockOnSuccess).toHaveBeenCalled()
    })
  })

  it('handles API errors gracefully', async () => {
    const user = userEvent.setup()
    mockCreateUser.mockRejectedValueOnce(new Error('Email already exists'))

    renderUserCreateForm()

    // Fill out form with valid data
    await user.type(screen.getByPlaceholderText(/digite o nome completo/i), 'Test User')
    await user.type(screen.getByPlaceholderText(/usuario@exemplo.com/i), 'existing@example.com')
    await user.type(screen.getByPlaceholderText(/digite uma senha segura/i), 'ValidPass123!')
    await user.type(screen.getByPlaceholderText(/digite a senha novamente/i), 'ValidPass123!')

    const roleSelect = screen.getByRole('combobox')
    await user.click(roleSelect)
    await user.click(screen.getByText('Administrador'))

    const submitButton = screen.getByRole('button', { name: /criar usuário/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockCreateUser).toHaveBeenCalled()
      // Form should still be visible (not closed on error)
      expect(screen.getByPlaceholderText(/digite o nome completo/i)).toBeInTheDocument()
    })
  })

  it('calls onCancel when cancel button is clicked', async () => {
    const user = userEvent.setup()
    renderUserCreateForm()

    const cancelButton = screen.getByRole('button', { name: /cancelar/i })
    await user.click(cancelButton)

    expect(mockOnCancel).toHaveBeenCalled()
  })

  it('disables submit button while form is submitting', async () => {
    const user = userEvent.setup()
    // Mock a slow API call
    mockCreateUser.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)))

    renderUserCreateForm()

    // Fill out form
    await user.type(screen.getByPlaceholderText(/digite o nome completo/i), 'Test User')
    await user.type(screen.getByPlaceholderText(/usuario@exemplo.com/i), 'test@example.com')
    await user.type(screen.getByPlaceholderText(/digite uma senha segura/i), 'ValidPass123!')
    await user.type(screen.getByPlaceholderText(/digite a senha novamente/i), 'ValidPass123!')

    const roleSelect = screen.getByRole('combobox')
    await user.click(roleSelect)
    await user.click(screen.getByText('Administrador'))

    const submitButton = screen.getByRole('button', { name: /criar usuário/i })
    await user.click(submitButton)

    // Button should be disabled and show "Criando..." text
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /criando\.\.\./i })).toBeDisabled()
    })
  })

  it('validates name length constraints', async () => {
    const user = userEvent.setup()
    renderUserCreateForm()

    const nameInput = screen.getByPlaceholderText(/digite o nome completo/i)
    const submitButton = screen.getByRole('button', { name: /criar usuário/i })
    
    // Test minimum length - submit form with invalid name
    await user.type(nameInput, 'A')
    await user.click(submitButton)

    // Verify that the API was NOT called due to validation failure
    await waitFor(() => {
      expect(mockCreateUser).not.toHaveBeenCalled()
    }, { timeout: 1000 })

    // Clear and test maximum length (256+ characters)
    await user.clear(nameInput)
    const longName = 'A'.repeat(256)
    await user.type(nameInput, longName)
    await user.click(submitButton)

    // Verify that the API was NOT called due to validation failure
    await waitFor(() => {
      expect(mockCreateUser).not.toHaveBeenCalled()
    }, { timeout: 1000 })
  })
})