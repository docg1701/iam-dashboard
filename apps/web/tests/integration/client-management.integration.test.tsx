/**
 * Client Management Integration Tests
 * Tests complete client management workflows including creation, validation, and form handling
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ClientForm } from '@/components/forms/ClientForm'
import { ErrorProvider } from '@/components/errors/ErrorContext'

// Mock Next.js navigation
const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
  }),
  usePathname: () => '/clients',
  useSearchParams: () => new URLSearchParams(),
}))

// Mock @shared/utils for CPF validation (CLAUDE.md compliant - external dependency)
vi.mock('@shared/utils', () => ({
  validateCPF: vi.fn((cpf: string) => {
    // Simple mock validation for testing
    const cleanCPF = cpf.replace(/\D/g, '')
    return cleanCPF.length === 11 && cleanCPF !== '00000000000'
  }),
  formatCPF: vi.fn((cpf: string) => {
    const cleanCPF = cpf.replace(/\D/g, '')
    if (cleanCPF.length <= 11) {
      return cleanCPF.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4')
    }
    return cleanCPF
  }),
}))

// Import the mocked utilities after mock setup
import { validateCPF, formatCPF } from '@shared/utils'

// Test wrapper with providers
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
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </ErrorProvider>
  )
}

// Mock client data
const mockClientData = {
  name: 'João da Silva Santos',
  cpf: '12345678901',
  birthDate: '1990-05-15',
}

const mockInvalidClientData = {
  name: 'A', // Too short
  cpf: '00000000000', // Invalid CPF
  birthDate: '2010-01-01', // Too young
}

describe('Client Management Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn()
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe('Client Creation Flow', () => {
    it('should handle successful client creation with valid data', async () => {
      const onSubmit = vi.fn()
      const onCancel = vi.fn()

      render(
        <TestWrapper>
          <ClientForm onSubmit={onSubmit} onCancel={onCancel} />
        </TestWrapper>
      )

      // Fill in the form with valid data
      const nameInput = screen.getByLabelText(/nome completo/i)
      const cpfInput = screen.getByLabelText(/cpf/i)
      const birthDateInput = screen.getByLabelText(/data de nascimento/i)
      const submitButton = screen.getByRole('button', {
        name: /salvar cliente/i,
      })

      fireEvent.change(nameInput, { target: { value: mockClientData.name } })
      fireEvent.change(cpfInput, { target: { value: mockClientData.cpf } })
      fireEvent.change(birthDateInput, {
        target: { value: mockClientData.birthDate },
      })

      // Wait for form validation
      await waitFor(
        () => {
          expect(submitButton).not.toBeDisabled()
        },
        { timeout: 15000 }
      )

      // Submit the form
      fireEvent.click(submitButton)

      // Wait for submission
      await waitFor(
        () => {
          expect(onSubmit).toHaveBeenCalledWith({
            name: mockClientData.name,
            cpf: mockClientData.cpf,
            birthDate: mockClientData.birthDate,
          })
        },
        { timeout: 30000 }
      )
    }, 30000)

    it('should validate form fields and show errors for invalid data', async () => {
      const onSubmit = vi.fn()

      render(
        <TestWrapper>
          <ClientForm onSubmit={onSubmit} />
        </TestWrapper>
      )

      const nameInput = screen.getByLabelText(/nome completo/i)
      const cpfInput = screen.getByLabelText(/cpf/i)
      const birthDateInput = screen.getByLabelText(/data de nascimento/i)
      const submitButton = screen.getByRole('button', {
        name: /salvar cliente/i,
      })

      // Fill with invalid data
      fireEvent.change(nameInput, {
        target: { value: mockInvalidClientData.name },
      })
      fireEvent.change(cpfInput, {
        target: { value: mockInvalidClientData.cpf },
      })
      fireEvent.change(birthDateInput, {
        target: { value: mockInvalidClientData.birthDate },
      })

      // Trigger form validation
      fireEvent.blur(nameInput)
      fireEvent.blur(cpfInput)
      fireEvent.blur(birthDateInput)

      // Wait for validation errors to appear
      await waitFor(() => {
        expect(
          screen.getByText(/nome deve ter pelo menos 2 caracteres/i)
        ).toBeInTheDocument()
        expect(screen.getByText(/cpf inválido/i)).toBeInTheDocument()
        expect(
          screen.getByText(/cliente deve ter entre 16 e 120 anos/i)
        ).toBeInTheDocument()
      })

      // Submit button should be disabled
      expect(submitButton).toBeDisabled()

      // Form should not be submitted
      expect(onSubmit).not.toHaveBeenCalled()
    })

    it('should handle real-time CPF validation and formatting', async () => {
      const onSubmit = vi.fn()

      render(
        <TestWrapper>
          <ClientForm onSubmit={onSubmit} />
        </TestWrapper>
      )

      const cpfInput = screen.getByLabelText(/cpf/i)

      // Type CPF gradually to test real-time validation
      fireEvent.change(cpfInput, { target: { value: '123' } })

      // Should show invalid indicator initially
      await waitFor(() => {
        expect(screen.getByText('✗')).toBeInTheDocument()
      })

      // Complete valid CPF
      fireEvent.change(cpfInput, { target: { value: '12345678901' } })

      // Should show valid indicator
      await waitFor(() => {
        expect(screen.getByText('✓')).toBeInTheDocument()
        expect(
          screen.getByText(/cpf válido - utilizando @brazilian-utils/i)
        ).toBeInTheDocument()
      })

      // Verify formatting was applied (mocked)
      expect(formatCPF).toHaveBeenCalled()
    })

    it('should handle form submission with loading state', async () => {
      const onSubmit = vi
        .fn()
        .mockImplementation(
          () => new Promise(resolve => setTimeout(resolve, 1000))
        )

      render(
        <TestWrapper>
          <ClientForm onSubmit={onSubmit} isLoading={false} />
        </TestWrapper>
      )

      const nameInput = screen.getByLabelText(/nome completo/i)
      const cpfInput = screen.getByLabelText(/cpf/i)
      const birthDateInput = screen.getByLabelText(/data de nascimento/i)

      // Fill valid data
      fireEvent.change(nameInput, { target: { value: mockClientData.name } })
      fireEvent.change(cpfInput, { target: { value: mockClientData.cpf } })
      fireEvent.change(birthDateInput, {
        target: { value: mockClientData.birthDate },
      })

      const submitButton = screen.getByRole('button', {
        name: /salvar cliente/i,
      })
      fireEvent.click(submitButton)

      // Should show loading state immediately
      await waitFor(() => {
        expect(screen.getByText(/salvando.../i)).toBeInTheDocument()
      })

      // Form fields should be disabled during loading
      expect(nameInput).toBeDisabled()
      expect(cpfInput).toBeDisabled()
      expect(birthDateInput).toBeDisabled()
    })
  })

  describe('Client Edit Flow', () => {
    it('should populate form with existing client data for editing', async () => {
      const initialData = {
        name: 'Maria Silva',
        cpf: '98765432109',
        birthDate: '1985-10-20',
      }

      const onSubmit = vi.fn()

      render(
        <TestWrapper>
          <ClientForm onSubmit={onSubmit} initialData={initialData} />
        </TestWrapper>
      )

      // Verify form is populated with initial data
      expect(screen.getByDisplayValue(initialData.name)).toBeInTheDocument()
      expect(
        screen.getByDisplayValue(initialData.birthDate)
      ).toBeInTheDocument()

      // CPF should be formatted
      await waitFor(() => {
        expect(formatCPF).toHaveBeenCalledWith(initialData.cpf)
      })

      // Title should indicate edit mode
      expect(screen.getByText(/editar cliente/i)).toBeInTheDocument()
    })

    it('should handle client data updates', async () => {
      const initialData = {
        name: 'Original Name',
        cpf: '12345678901',
        birthDate: '1990-01-01',
      }

      const onSubmit = vi.fn()

      render(
        <TestWrapper>
          <ClientForm onSubmit={onSubmit} initialData={initialData} />
        </TestWrapper>
      )

      const nameInput = screen.getByDisplayValue(initialData.name)

      // Update the name
      fireEvent.change(nameInput, { target: { value: 'Updated Name' } })

      const submitButton = screen.getByRole('button', {
        name: /salvar cliente/i,
      })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith({
          name: 'Updated Name',
          cpf: initialData.cpf,
          birthDate: initialData.birthDate,
        })
      })
    })
  })

  describe('Form Validation Integration', () => {
    it('should validate age requirements correctly', async () => {
      const onSubmit = vi.fn()

      render(
        <TestWrapper>
          <ClientForm onSubmit={onSubmit} />
        </TestWrapper>
      )

      const birthDateInput = screen.getByLabelText(/data de nascimento/i)

      // Test too young (current year - 15 years)
      const currentYear = new Date().getFullYear()
      const tooYoungDate = `${currentYear - 15}-01-01`
      fireEvent.change(birthDateInput, { target: { value: tooYoungDate } })
      fireEvent.blur(birthDateInput)

      await waitFor(() => {
        expect(
          screen.getByText(/cliente deve ter entre 16 e 120 anos/i)
        ).toBeInTheDocument()
      })

      // Test valid age (25 years old)
      const validDate = `${currentYear - 25}-01-01`
      fireEvent.change(birthDateInput, { target: { value: validDate } })

      await waitFor(() => {
        expect(
          screen.queryByText(/cliente deve ter entre 16 e 120 anos/i)
        ).not.toBeInTheDocument()
      })

      // Test too old (130 years old)
      const tooOldDate = `${currentYear - 130}-01-01`
      fireEvent.change(birthDateInput, { target: { value: tooOldDate } })
      fireEvent.blur(birthDateInput)

      await waitFor(() => {
        expect(
          screen.getByText(/cliente deve ter entre 16 e 120 anos/i)
        ).toBeInTheDocument()
      })
    })

    it('should handle CPF validation edge cases', async () => {
      const onSubmit = vi.fn()

      render(
        <TestWrapper>
          <ClientForm onSubmit={onSubmit} />
        </TestWrapper>
      )

      const cpfInput = screen.getByLabelText(/cpf/i)

      // Test invalid CPFs
      const invalidCPFs = ['00000000000', '11111111111', '123456789']

      for (const invalidCPF of invalidCPFs) {
        fireEvent.change(cpfInput, { target: { value: invalidCPF } })
        fireEvent.blur(cpfInput)

        await waitFor(() => {
          expect(screen.getByText('✗')).toBeInTheDocument()
        })
      }

      // Test valid CPF
      fireEvent.change(cpfInput, { target: { value: '12345678901' } })

      await waitFor(() => {
        expect(screen.getByText('✓')).toBeInTheDocument()
      })
    })

    it('should prevent submission with invalid form state', async () => {
      const onSubmit = vi.fn()

      render(
        <TestWrapper>
          <ClientForm onSubmit={onSubmit} />
        </TestWrapper>
      )

      const submitButton = screen.getByRole('button', {
        name: /salvar cliente/i,
      })

      // Initially form should be invalid (empty fields)
      expect(submitButton).toBeDisabled()

      // Fill only name (form still invalid)
      const nameInput = screen.getByLabelText(/nome completo/i)
      fireEvent.change(nameInput, { target: { value: 'Valid Name' } })

      // Form should still be disabled
      await waitFor(() => {
        expect(submitButton).toBeDisabled()
      })

      // Submit button click should not trigger onSubmit
      fireEvent.click(submitButton)
      expect(onSubmit).not.toHaveBeenCalled()
    })
  })

  describe('Error Handling Integration', () => {
    it('should handle form cancellation', async () => {
      const onSubmit = vi.fn()
      const onCancel = vi.fn()

      render(
        <TestWrapper>
          <ClientForm onSubmit={onSubmit} onCancel={onCancel} />
        </TestWrapper>
      )

      const cancelButton = screen.getByRole('button', { name: /cancelar/i })
      fireEvent.click(cancelButton)

      expect(onCancel).toHaveBeenCalled()
    })

    it('should maintain form state during validation errors', async () => {
      const onSubmit = vi.fn()

      render(
        <TestWrapper>
          <ClientForm onSubmit={onSubmit} />
        </TestWrapper>
      )

      const nameInput = screen.getByLabelText(/nome completo/i)
      const cpfInput = screen.getByLabelText(/cpf/i)

      // Fill some valid data
      fireEvent.change(nameInput, { target: { value: 'Valid Name' } })
      fireEvent.change(cpfInput, { target: { value: '12345678901' } })

      // Fill invalid birth date
      const birthDateInput = screen.getByLabelText(/data de nascimento/i)
      fireEvent.change(birthDateInput, { target: { value: '2010-01-01' } })
      fireEvent.blur(birthDateInput)

      // Wait for validation error
      await waitFor(() => {
        expect(
          screen.getByText(/cliente deve ter entre 16 e 120 anos/i)
        ).toBeInTheDocument()
      })

      // Valid data should still be in form
      expect(nameInput).toHaveValue('Valid Name')
      expect(cpfInput).toHaveValue('12345678901')
    })

    it('should handle form reset after successful submission', async () => {
      const onSubmit = vi.fn()

      render(
        <TestWrapper>
          <ClientForm onSubmit={onSubmit} />
        </TestWrapper>
      )

      const nameInput = screen.getByLabelText(/nome completo/i)
      const cpfInput = screen.getByLabelText(/cpf/i)
      const birthDateInput = screen.getByLabelText(/data de nascimento/i)

      // Fill and submit form
      fireEvent.change(nameInput, { target: { value: mockClientData.name } })
      fireEvent.change(cpfInput, { target: { value: mockClientData.cpf } })
      fireEvent.change(birthDateInput, {
        target: { value: mockClientData.birthDate },
      })

      const submitButton = screen.getByRole('button', {
        name: /salvar cliente/i,
      })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalled()
      })

      // Form validation state should be maintained
      expect(submitButton).not.toBeDisabled()
    })
  })

  describe('Development Mode Integration', () => {
    it('should show debug information in development mode', async () => {
      // Set development mode
      const originalEnv = process.env.NODE_ENV
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: 'development',
        writable: true,
        configurable: true,
      })

      const onSubmit = vi.fn()

      render(
        <TestWrapper>
          <ClientForm onSubmit={onSubmit} />
        </TestWrapper>
      )

      const cpfInput = screen.getByLabelText(/cpf/i)
      fireEvent.change(cpfInput, { target: { value: '12345678901' } })

      // Debug info should be visible in development
      await waitFor(() => {
        expect(screen.getByText(/debug info:/i)).toBeInTheDocument()
        expect(screen.getByText(/cpf input:/i)).toBeInTheDocument()
        expect(screen.getByText(/cpf formatado:/i)).toBeInTheDocument()
        expect(screen.getByText(/cpf válido:/i)).toBeInTheDocument()
        expect(screen.getByText(/form válido:/i)).toBeInTheDocument()
      })

      // Restore original environment
      vi.unstubAllEnvs()
    })

    it('should hide debug information in production mode', async () => {
      // Set production mode
      vi.stubEnv('NODE_ENV', 'production')

      const onSubmit = vi.fn()

      render(
        <TestWrapper>
          <ClientForm onSubmit={onSubmit} />
        </TestWrapper>
      )

      // Debug info should not be visible in production
      expect(screen.queryByText(/debug info:/i)).not.toBeInTheDocument()

      // Restore original environment
      vi.unstubAllEnvs()
    })
  })
})
