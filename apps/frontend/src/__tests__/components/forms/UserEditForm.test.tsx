import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { UserEditForm } from '@/components/forms/UserEditForm'
import { ToastProvider } from '@/components/ui/toast'
import * as usersAPI from '@/lib/api/users'
import type { User } from '@iam-dashboard/shared'

// Mock the users API
vi.mock('@/lib/api/users', () => ({
  usersAPI: {
    updateUser: vi.fn()
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

// Mock React Hook Form to properly handle defaultValues
vi.mock('react-hook-form', () => {
  const React = require('react')
  
  return {
    useForm: ({ defaultValues = {} } = {}) => ({
      register: vi.fn(() => ({
        onChange: vi.fn(),
        onBlur: vi.fn(),
        name: 'test',
        ref: vi.fn(),
      })),
      handleSubmit: vi.fn((fn) => (e) => {
        e?.preventDefault?.()
        return fn(defaultValues)
      }),
      formState: {
        errors: {},
        isSubmitting: false,
        isValid: true,
        isDirty: false,
        isLoading: false,
      },
      watch: vi.fn(() => defaultValues),
      setValue: vi.fn(),
      getValues: vi.fn(() => defaultValues),
      reset: vi.fn(),
      control: { _defaultValues: defaultValues },
      clearErrors: vi.fn(),
      setError: vi.fn(),
    }),
    FormProvider: ({ children, ...props }: any) => (
      React.createElement('div', {
        'data-testid': 'form-provider',
        ...props,
      }, children)
    ),
    Controller: ({ render, control, name }: any) => {
      const defaultValues = control?._defaultValues || {}
      const mockFieldProps = {
        field: {
          onChange: vi.fn(),
          onBlur: vi.fn(),
          value: defaultValues[name] || '',
          name,
          ref: vi.fn(),
        },
        fieldState: {
          error: null,
          isDirty: false,
          isTouched: false,
        },
        formState: {
          isSubmitting: false,
          isValid: true,
        },
      }
      return render ? render(mockFieldProps) : null
    },
    useController: vi.fn((config) => {
      const defaultValues = config?.control?._defaultValues || {}
      return {
        field: {
          onChange: vi.fn(),
          onBlur: vi.fn(),
          value: defaultValues[config?.name] || '',
          name: config?.name || 'test',
          ref: vi.fn(),
        },
        fieldState: {
          error: null,
          isDirty: false,
          isTouched: false,
        },
        formState: {
          isSubmitting: false,
          isValid: true,
        },
      }
    }),
    useFormContext: vi.fn(() => ({
      register: vi.fn(),
      handleSubmit: vi.fn(),
      formState: { errors: {} },
      watch: vi.fn(),
      setValue: vi.fn(),
      getValues: vi.fn(() => ({})),
      getFieldState: vi.fn(() => ({
        error: null,
        isDirty: false,
        isTouched: false,
        invalid: false,
      })),
      control: {},
    })),
  }
})

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

describe('UserEditForm', () => {
  const mockOnSuccess = vi.fn()
  const mockOnCancel = vi.fn()
  const mockUpdateUser = vi.mocked(usersAPI.usersAPI.updateUser)

  const mockUser: User = {
    user_id: '123',
    email: 'john.doe@example.com',
    full_name: 'John Doe',
    role: 'admin',
    status: 'active',
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z',
    last_login_at: '2023-06-01T00:00:00Z',
    is_verified: true
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    cleanup()
  })

  const renderUserEditForm = (user: User = mockUser) => {
    return render(
      <TestWrapper>
        <UserEditForm user={user} onSuccess={mockOnSuccess} onCancel={mockOnCancel} />
      </TestWrapper>
    )
  }

  it('renders form with pre-filled user data', () => {
    renderUserEditForm()

    expect(screen.getByDisplayValue('John Doe')).toBeInTheDocument()
    expect(screen.getByDisplayValue('john.doe@example.com')).toBeInTheDocument()
    expect(screen.getByText('Administrador')).toBeInTheDocument() // Role should be selected
  })

  it('displays user information section with correct data', () => {
    renderUserEditForm()

    expect(screen.getByText(/informações do usuário/i)).toBeInTheDocument()
    expect(screen.getByText(/status.*ativo/i)).toBeInTheDocument()
    expect(screen.getByText(/criado em.*01\/01\/2023/i)).toBeInTheDocument()
    expect(screen.getByText(/última atualização.*01\/01\/2023/i)).toBeInTheDocument()
    expect(screen.getByText(/último login.*01\/06\/2023/i)).toBeInTheDocument()
  })

  it('shows inactive status for inactive users', () => {
    const inactiveUser = { ...mockUser, status: 'inactive' as const }
    renderUserEditForm(inactiveUser)

    expect(screen.getByText(/status.*inativo/i)).toBeInTheDocument()
  })

  it('hides last login when user has never logged in', () => {
    const userWithoutLogin = { ...mockUser, last_login_at: undefined }
    renderUserEditForm(userWithoutLogin)

    expect(screen.queryByText(/último login/i)).not.toBeInTheDocument()
  })

  it('validates email format on edit', async () => {
    const user = userEvent.setup()
    renderUserEditForm()

    const emailInput = screen.getByDisplayValue('john.doe@example.com')
    await user.clear(emailInput)
    await user.type(emailInput, 'invalid-email')

    const submitButton = screen.getByRole('button', { name: /salvar alterações/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/digite um email válido/i)).toBeInTheDocument()
    })
  })

  it('validates name length constraints', async () => {
    const user = userEvent.setup()
    renderUserEditForm()

    const nameInput = screen.getByDisplayValue('John Doe')
    await user.clear(nameInput)
    await user.type(nameInput, 'A')

    const submitButton = screen.getByRole('button', { name: /salvar alterações/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/nome deve ter pelo menos 2 caracteres/i)).toBeInTheDocument()
    })
  })

  it('disables submit button when no changes are made', () => {
    renderUserEditForm()

    const submitButton = screen.getByRole('button', { name: /salvar alterações/i })
    expect(submitButton).toBeDisabled()
  })

  it('enables submit button when changes are made', async () => {
    const user = userEvent.setup()
    renderUserEditForm()

    const nameInput = screen.getByDisplayValue('John Doe')
    await user.clear(nameInput)
    await user.type(nameInput, 'Jane Doe')

    const submitButton = screen.getByRole('button', { name: /salvar alterações/i })
    expect(submitButton).toBeEnabled()
  })

  it('submits form with changed data successfully', async () => {
    const user = userEvent.setup()
    mockUpdateUser.mockResolvedValueOnce({
      ...mockUser,
      full_name: 'Jane Doe',
      updated_at: '2023-06-15T00:00:00Z'
    })

    renderUserEditForm()

    // Make changes
    const nameInput = screen.getByDisplayValue('John Doe')
    await user.clear(nameInput)
    await user.type(nameInput, 'Jane Doe')

    const emailInput = screen.getByDisplayValue('john.doe@example.com')
    await user.clear(emailInput)
    await user.type(emailInput, 'jane.doe@example.com')

    // Change role
    const roleSelect = screen.getByRole('combobox')
    await user.click(roleSelect) 
    await user.click(screen.getByText('Usuário'))

    // Submit form
    const submitButton = screen.getByRole('button', { name: /salvar alterações/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockUpdateUser).toHaveBeenCalledWith('123', {
        email: 'jane.doe@example.com',
        full_name: 'Jane Doe',
        role: 'user'
      })
      expect(mockOnSuccess).toHaveBeenCalled()
    })
  })

  it('handles API errors gracefully', async () => {
    const user = userEvent.setup()
    mockUpdateUser.mockRejectedValueOnce(new Error('Email already exists'))

    renderUserEditForm()

    // Make changes
    const nameInput = screen.getByDisplayValue('John Doe')
    await user.clear(nameInput)
    await user.type(nameInput, 'Jane Doe')

    const submitButton = screen.getByRole('button', { name: /salvar alterações/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockUpdateUser).toHaveBeenCalled()
      // Form should still be visible (not closed on error)
      expect(screen.getByDisplayValue('Jane Doe')).toBeInTheDocument()
    })
  })

  it('calls onCancel when cancel button is clicked', async () => {
    const user = userEvent.setup()
    renderUserEditForm()

    const cancelButton = screen.getByRole('button', { name: /cancelar/i })
    await user.click(cancelButton)

    expect(mockOnCancel).toHaveBeenCalled()
  })

  it('disables submit button while form is submitting', async () => {
    const user = userEvent.setup()
    // Mock a slow API call
    mockUpdateUser.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)))

    renderUserEditForm()

    // Make a change
    const nameInput = screen.getByDisplayValue('John Doe')
    await user.clear(nameInput)
    await user.type(nameInput, 'Jane Doe')

    const submitButton = screen.getByRole('button', { name: /salvar alterações/i })
    await user.click(submitButton)

    // Button should be disabled and show "Salvando..." text
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /salvando\.\.\./i })).toBeDisabled()
    })
  })

  it('shows role descriptions in select options', async () => {
    const user = userEvent.setup()
    renderUserEditForm()

    const roleSelect = screen.getByRole('combobox')
    await user.click(roleSelect)

    await waitFor(() => {
      expect(screen.getByText(/acesso total ao sistema/i)).toBeInTheDocument()
      expect(screen.getByText(/gerenciamento de clientes e relatórios/i)).toBeInTheDocument()
      expect(screen.getByText(/operações básicas com clientes/i)).toBeInTheDocument()
    })
  })

  it('shows role change warning message', () => {
    renderUserEditForm()

    expect(screen.getByText(/alterações no role afetam as permissões do usuário no sistema/i)).toBeInTheDocument()
  })

  it('detects changes correctly for email field', async () => {
    const user = userEvent.setup()
    renderUserEditForm()

    // Initially disabled
    expect(screen.getByRole('button', { name: /salvar alterações/i })).toBeDisabled()

    // Change email
    const emailInput = screen.getByDisplayValue('john.doe@example.com')
    await user.clear(emailInput)
    await user.type(emailInput, 'new.email@example.com')

    // Should be enabled
    expect(screen.getByRole('button', { name: /salvar alterações/i })).toBeEnabled()

    // Revert change
    await user.clear(emailInput)
    await user.type(emailInput, 'john.doe@example.com')

    // Should be disabled again
    expect(screen.getByRole('button', { name: /salvar alterações/i })).toBeDisabled()
  })

  it('detects changes correctly for role field', async () => {
    const user = userEvent.setup()
    renderUserEditForm()

    // Initially disabled
    expect(screen.getByRole('button', { name: /salvar alterações/i })).toBeDisabled()

    // Change role
    const roleSelect = screen.getByRole('combobox')
    await user.click(roleSelect)
    await user.click(screen.getByText('Usuário'))

    // Should be enabled
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /salvar alterações/i })).toBeEnabled()
    })
  })
})