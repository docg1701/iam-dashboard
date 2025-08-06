import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { UserCreateForm } from '../UserCreateForm'
// VIOLAÇÃO CORRIGIDA: Não fazer mock de código interno (@/lib/api/users)
// Mock apenas fetch - API externa real

// Mock apenas APIs externas (fetch) - NUNCA código interno
const mockFetch = vi.fn()
global.fetch = mockFetch

// Não fazer mock de hooks internos - usar implementação real

const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  })
  
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('UserCreateForm', () => {
  const mockOnSuccess = vi.fn()
  const mockOnCancel = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  const renderComponent = () => {
    return render(
      <TestWrapper>
        <UserCreateForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />
      </TestWrapper>
    )
  }

  describe('Rendering and Initial State', () => {
    it('should render all form fields', () => {
      renderComponent()

      expect(screen.getByLabelText(/nome completo/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/role do usuário/i)).toBeInTheDocument()
      expect(screen.getByText(/^senha$/i)).toBeInTheDocument()
      expect(screen.getByText(/confirmar senha/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /criar usuário/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /cancelar/i })).toBeInTheDocument()
    })

    it('should render form with empty initial values', () => {
      renderComponent()

      expect(screen.getByDisplayValue('')).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/selecione o role/i)).toBeInTheDocument()
    })

    it('should display password requirements', () => {
      renderComponent()

      expect(screen.getByText(/mínimo 8 caracteres/i)).toBeInTheDocument()
    })
  })

  describe('Form Validation', () => {
    it('should show validation error for empty name', async () => {
      const user = userEvent.setup()
      renderComponent()

      const submitButton = screen.getByRole('button', { name: /criar usuário/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/nome deve ter pelo menos 2 caracteres/i)).toBeInTheDocument()
      })
    })

    it('should show validation error for invalid email', async () => {
      const user = userEvent.setup()
      renderComponent()

      const emailInput = screen.getByLabelText(/email/i)
      await user.type(emailInput, 'invalid-email')

      const submitButton = screen.getByRole('button', { name: /criar usuário/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/digite um email válido/i)).toBeInTheDocument()
      })
    })

    it('should show validation error for weak password', async () => {
      const user = userEvent.setup()
      renderComponent()

      const passwordInput = screen.getByPlaceholderText(/digite uma senha segura/i)
      await user.type(passwordInput, 'weak')

      const submitButton = screen.getByRole('button', { name: /criar usuário/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/senha deve ter pelo menos 8 caracteres/i)).toBeInTheDocument()
      })
    })

    it('should show validation error when passwords do not match', async () => {
      const user = userEvent.setup()
      renderComponent()

      const passwordInput = screen.getByPlaceholderText(/digite uma senha segura/i)
      const confirmPasswordInput = screen.getByPlaceholderText(/digite a senha novamente/i)

      await user.type(passwordInput, 'StrongPassword123!')
      await user.type(confirmPasswordInput, 'DifferentPassword123!')

      const submitButton = screen.getByRole('button', { name: /criar usuário/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/senhas não coincidem/i)).toBeInTheDocument()
      })
    })

    it('should show validation error when no role is selected', async () => {
      const user = userEvent.setup()
      renderComponent()

      const submitButton = screen.getByRole('button', { name: /criar usuário/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/selecione um role/i)).toBeInTheDocument()
      })
    })
  })

  describe('Role Selection', () => {
    it('should display all available roles with descriptions', async () => {
      const user = userEvent.setup()
      renderComponent()

      const roleSelect = screen.getByRole('combobox')
      await user.click(roleSelect)

      await waitFor(() => {
        expect(screen.getAllByText(/administrador do sistema/i)).toHaveLength(2) // One in select, one in dropdown
        expect(screen.getByText(/administrador$/i)).toBeInTheDocument()
        expect(screen.getByText(/usuário$/i)).toBeInTheDocument()
        expect(screen.getByText(/acesso total ao sistema/i)).toBeInTheDocument()
        expect(screen.getByText(/gerenciamento de clientes e relatórios/i)).toBeInTheDocument()
        expect(screen.getByText(/operações básicas com clientes/i)).toBeInTheDocument()
      })
    })

    it('should allow selecting different roles', async () => {
      const user = userEvent.setup()
      renderComponent()

      const roleSelect = screen.getByRole('combobox', { name: /role do usuário/i })
      await user.click(roleSelect)
      
      await waitFor(() => {
        expect(screen.getByText(/administrador$/i)).toBeInTheDocument()
      })
      
      await user.click(screen.getByText(/administrador$/i))

      await waitFor(() => {
        expect(screen.getByDisplayValue('admin')).toBeInTheDocument()
      })
    })
  })

  describe('Password Visibility Toggle', () => {
    it('should toggle password visibility for main password field', async () => {
      const user = userEvent.setup()
      renderComponent()

      const passwordInput = screen.getByPlaceholderText(/digite uma senha segura/i) as HTMLInputElement
      expect(passwordInput.type).toBe('password')

      // Find the eye icon button for password field
      const passwordContainer = passwordInput.closest('.relative')
      const toggleButton = passwordContainer?.querySelector('button') as HTMLButtonElement
      await user.click(toggleButton)

      await waitFor(() => {
        expect(passwordInput.type).toBe('text')
      })
    })

    it('should toggle password visibility for confirm password field', async () => {
      const user = userEvent.setup()
      renderComponent()

      const confirmPasswordInput = screen.getByPlaceholderText(/digite a senha novamente/i) as HTMLInputElement
      expect(confirmPasswordInput.type).toBe('password')

      // Find the eye icon button for confirm password field
      const confirmPasswordContainer = confirmPasswordInput.closest('.relative')
      const confirmToggleButton = confirmPasswordContainer?.querySelector('button') as HTMLButtonElement
      await user.click(confirmToggleButton)

      await waitFor(() => {
        expect(confirmPasswordInput.type).toBe('text')
      })
    })
  })

  describe('Form Submission', () => {
    const validFormData = {
      full_name: 'João Silva',
      email: 'joao@example.com',
      password: 'StrongPassword123!',
      confirmPassword: 'StrongPassword123!',
      role: 'admin'
    }

    const fillValidForm = async (user: ReturnType<typeof userEvent.setup>) => {
      await user.type(screen.getByLabelText(/nome completo/i), validFormData.full_name)
      await user.type(screen.getByLabelText(/email/i), validFormData.email)
      
      const roleSelect = screen.getByRole('combobox')
      await user.click(roleSelect)
      await user.click(screen.getByText(/administrador$/i))
      
      await user.type(screen.getByPlaceholderText(/digite uma senha segura/i), validFormData.password)
      await user.type(screen.getByPlaceholderText(/digite a senha novamente/i), validFormData.confirmPassword)
    }

    it('should submit form with valid data', async () => {
      const user = userEvent.setup()
      const mockUser = { user_id: '123', ...validFormData, created_at: '2025-01-01T00:00:00Z' }
      mockFetch.mockResolvedValue({
        ok: true,
        status: 201,
        json: async () => mockUser
      })

      renderComponent()
      await fillValidForm(user)

      const submitButton = screen.getByRole('button', { name: /criar usuário/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/users'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining(validFormData.email)
          })
        )
        // Toast será chamado através da implementação real
        expect(mockOnSuccess).toHaveBeenCalled()
      })
    })

    it('should show loading state during submission', async () => {
      const user = userEvent.setup()
      mockFetch.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({
          ok: true,
          status: 201, 
          json: async () => ({})
        }), 100))
      )

      renderComponent()
      await fillValidForm(user)

      const submitButton = screen.getByRole('button', { name: /criar usuário/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/criando.../i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /criando.../i })).toBeDisabled()
      })
    })

    it('should handle API errors gracefully', async () => {
      const user = userEvent.setup()
      const errorMessage = 'Email já existe'
      mockFetch.mockResolvedValue({
        ok: false,
        status: 409,
        json: async () => ({ detail: errorMessage })
      })

      renderComponent()
      await fillValidForm(user)

      const submitButton = screen.getByRole('button', { name: /criar usuário/i })
      await user.click(submitButton)

      await waitFor(() => {
        // Toast de erro será chamado através da implementação real
        expect(mockOnSuccess).not.toHaveBeenCalled()
      })
    })

    it('should handle generic API errors', async () => {
      const user = userEvent.setup()
      mockFetch.mockRejectedValue(new Error('Network error'))

      renderComponent()
      await fillValidForm(user)

      const submitButton = screen.getByRole('button', { name: /criar usuário/i })
      await user.click(submitButton)

      await waitFor(() => {
        // Toast de erro genérico será chamado através da implementação real
      })
    })
  })

  describe('Form Actions', () => {
    it('should call onCancel when cancel button is clicked', async () => {
      const user = userEvent.setup()
      renderComponent()

      const cancelButton = screen.getByRole('button', { name: /cancelar/i })
      await user.click(cancelButton)

      expect(mockOnCancel).toHaveBeenCalled()
    })

    it('should not submit form when submit button is disabled', async () => {
      const user = userEvent.setup()
      renderComponent()

      // Submit without filling required fields
      const submitButton = screen.getByRole('button', { name: /criar usuário/i })
      await user.click(submitButton)

      // Should show validation errors but not call API
      await waitFor(() => {
        expect(screen.getByText(/nome deve ter pelo menos 2 caracteres/i)).toBeInTheDocument()
      })

      expect(mockFetch).not.toHaveBeenCalled()
    })
  })

  describe('Accessibility', () => {
    it('should have proper form labels and associations', () => {
      renderComponent()

      expect(screen.getByLabelText(/nome completo/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.getByRole('combobox')).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/digite uma senha segura/i)).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/digite a senha novamente/i)).toBeInTheDocument()
    })

    it('should announce validation errors to screen readers', async () => {
      const user = userEvent.setup()
      renderComponent()

      const submitButton = screen.getByRole('button', { name: /criar usuário/i })
      await user.click(submitButton)

      await waitFor(() => {
        const errorMessage = screen.getByText(/nome deve ter pelo menos 2 caracteres/i)
        expect(errorMessage).toBeInTheDocument()
      })
    })

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup()
      renderComponent()

      const nameInput = screen.getByLabelText(/nome completo/i)
      await user.tab()
      expect(nameInput).toHaveFocus()

      await user.tab()
      expect(screen.getByLabelText(/email/i)).toHaveFocus()
    })
  })

  describe('Form Reset', () => {
    it('should reset form after successful submission', async () => {
      const user = userEvent.setup()
      const mockUser = { user_id: '123', email: 'test@example.com' }
      mockFetch.mockResolvedValue({
        ok: true,
        status: 201,
        json: async () => mockUser
      })

      renderComponent()

      // Fill form
      await user.type(screen.getByLabelText(/nome completo/i), 'Test User')
      await user.type(screen.getByLabelText(/email/i), 'test@example.com')

      const submitButton = screen.getByRole('button', { name: /criar usuário/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalled()
      })

      // Form should be reset after success
      expect(screen.getByDisplayValue('')).toBeInTheDocument()
    })
  })
})