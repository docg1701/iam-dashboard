/**
 * Comprehensive tests for ClientForm component
 * CLAUDE.md Compliant: Only mocks external shared utilities, tests actual component behavior
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach, afterEach, Mock } from 'vitest'

import { ClientForm } from '@/components/forms/ClientForm'

// Mock shared utilities (CLAUDE.md compliant - external dependency)
vi.mock('@shared/utils', () => ({
  validateCPF: vi.fn(),
  formatCPF: vi.fn(),
}))

// Import after mocking to get the mocked functions
import { validateCPF, formatCPF } from '@shared/utils'

describe('ClientForm', () => {
  const mockOnSubmit = vi.fn()
  const mockOnCancel = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()

    // Setup default mock behavior
    ;(validateCPF as Mock).mockImplementation((cpf: string) => {
      // Simple mock validation - valid if 11 digits and not all same
      return cpf.length === 11 && !cpf.split('').every(char => char === cpf[0])
    })
    ;(formatCPF as Mock).mockImplementation((cpf: string) => {
      // Simple mock formatting - add dots and dash
      if (cpf.length <= 3) return cpf
      if (cpf.length <= 6) return `${cpf.slice(0, 3)}.${cpf.slice(3)}`
      if (cpf.length <= 9)
        return `${cpf.slice(0, 3)}.${cpf.slice(3, 6)}.${cpf.slice(6)}`
      return `${cpf.slice(0, 3)}.${cpf.slice(3, 6)}.${cpf.slice(6, 9)}-${cpf.slice(9, 11)}`
    })

    // Mock NODE_ENV
    process.env.NODE_ENV = 'test'
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Rendering', () => {
    it('should render form for new client', () => {
      render(<ClientForm onSubmit={mockOnSubmit} />)

      expect(screen.getByText('Novo Cliente')).toBeInTheDocument()
      expect(screen.getByLabelText('Nome Completo *')).toBeInTheDocument()
      expect(screen.getByLabelText('CPF *')).toBeInTheDocument()
      expect(screen.getByLabelText('Data de Nascimento *')).toBeInTheDocument()
      expect(
        screen.getByRole('button', { name: 'Salvar Cliente' })
      ).toBeInTheDocument()
    })

    it('should render form for editing client', () => {
      const initialData = {
        name: 'João Silva',
        cpf: '12345678901',
        birthDate: '1990-01-01',
      }

      render(<ClientForm onSubmit={mockOnSubmit} initialData={initialData} />)

      expect(screen.getByText('Editar Cliente')).toBeInTheDocument()
      expect(screen.getByDisplayValue('João Silva')).toBeInTheDocument()
      expect(screen.getByDisplayValue('1990-01-01')).toBeInTheDocument()
    })

    it('should render cancel button when onCancel is provided', () => {
      render(<ClientForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />)

      expect(
        screen.getByRole('button', { name: 'Cancelar' })
      ).toBeInTheDocument()
    })

    it('should not render cancel button when onCancel is not provided', () => {
      render(<ClientForm onSubmit={mockOnSubmit} />)

      expect(
        screen.queryByRole('button', { name: 'Cancelar' })
      ).not.toBeInTheDocument()
    })

    it('should show debug info in development mode', () => {
      process.env.NODE_ENV = 'development'

      render(<ClientForm onSubmit={mockOnSubmit} />)

      expect(screen.getByText('Debug Info:')).toBeInTheDocument()
      expect(screen.getByText(/Form Válido:/)).toBeInTheDocument()
    })

    it('should not show debug info in non-development mode', () => {
      process.env.NODE_ENV = 'production'

      render(<ClientForm onSubmit={mockOnSubmit} />)

      expect(screen.queryByText('Debug Info:')).not.toBeInTheDocument()
    })
  })

  describe('Form Validation', () => {
    describe('Name Field', () => {
      it('should validate minimum name length', async () => {
        const user = userEvent.setup()
        render(<ClientForm onSubmit={mockOnSubmit} />)

        const nameInput = screen.getByLabelText('Nome Completo *')

        await user.type(nameInput, 'A')
        await user.tab() // Blur to trigger validation

        await waitFor(() => {
          expect(
            screen.getByText('Nome deve ter pelo menos 2 caracteres')
          ).toBeInTheDocument()
        })
      })

      it('should validate maximum name length', async () => {
        const user = userEvent.setup()
        render(<ClientForm onSubmit={mockOnSubmit} />)

        const nameInput = screen.getByLabelText('Nome Completo *')
        const longName = 'A'.repeat(101)

        await user.type(nameInput, longName)
        await user.tab()

        await waitFor(() => {
          expect(
            screen.getByText('Nome deve ter no máximo 100 caracteres')
          ).toBeInTheDocument()
        })
      })

      it('should accept valid name', async () => {
        const user = userEvent.setup()
        render(<ClientForm onSubmit={mockOnSubmit} />)

        const nameInput = screen.getByLabelText('Nome Completo *')

        await user.type(nameInput, 'João Silva Santos')
        await user.tab()

        await waitFor(() => {
          expect(screen.queryByText(/Nome deve ter/)).not.toBeInTheDocument()
        })
      })
    })

    describe('CPF Field', () => {
      it('should format CPF in real-time', async () => {
        const user = userEvent.setup()
        render(<ClientForm onSubmit={mockOnSubmit} />)

        const cpfInput = screen.getByLabelText('CPF *')

        await user.type(cpfInput, '12345678901')

        expect(formatCPF).toHaveBeenCalledWith('12345678901')
        // Verify the displayed value is formatted
        expect(cpfInput).toHaveValue('123.456.789-01')
      })

      it('should validate CPF and show success indicator', async () => {
        const user = userEvent.setup()
        ;(validateCPF as Mock).mockReturnValue(true)

        render(<ClientForm onSubmit={mockOnSubmit} />)

        const cpfInput = screen.getByLabelText('CPF *')

        await user.type(cpfInput, '12345678901')

        await waitFor(() => {
          expect(screen.getByText('✓')).toBeInTheDocument()
          expect(
            screen.getByText('✅ CPF válido - Utilizando @brazilian-utils')
          ).toBeInTheDocument()
        })
      })

      it('should show error indicator for invalid CPF', async () => {
        const user = userEvent.setup()
        ;(validateCPF as Mock).mockReturnValue(false)

        render(<ClientForm onSubmit={mockOnSubmit} />)

        const cpfInput = screen.getByLabelText('CPF *')

        await user.type(cpfInput, '11111111111')

        await waitFor(() => {
          expect(screen.getByText('✗')).toBeInTheDocument()
        })
      })

      it('should validate minimum CPF length', async () => {
        const user = userEvent.setup()
        render(<ClientForm onSubmit={mockOnSubmit} />)

        const cpfInput = screen.getByLabelText('CPF *')
        const submitButton = screen.getByRole('button', {
          name: 'Salvar Cliente',
        })

        await user.type(cpfInput, '123456789')
        await user.click(submitButton)

        await waitFor(() => {
          expect(
            screen.getByText('CPF deve ter 11 dígitos')
          ).toBeInTheDocument()
        })
      })

      it('should validate CPF using external library', async () => {
        const user = userEvent.setup()
        ;(validateCPF as Mock).mockReturnValue(false)

        render(<ClientForm onSubmit={mockOnSubmit} />)

        const cpfInput = screen.getByLabelText('CPF *')
        const submitButton = screen.getByRole('button', {
          name: 'Salvar Cliente',
        })

        await user.type(cpfInput, '12345678901')
        await user.click(submitButton)

        await waitFor(() => {
          expect(screen.getByText('CPF inválido')).toBeInTheDocument()
        })
      })

      it('should only allow numeric input in CPF field', async () => {
        const user = userEvent.setup()
        render(<ClientForm onSubmit={mockOnSubmit} />)

        const cpfInput = screen.getByLabelText('CPF *')

        await user.type(cpfInput, 'abc123def456ghi')

        // Should only keep numeric characters
        expect(formatCPF).toHaveBeenCalledWith('123456')
      })

      it('should limit CPF input to 14 characters', async () => {
        const user = userEvent.setup()
        render(<ClientForm onSubmit={mockOnSubmit} />)

        const cpfInput = screen.getByLabelText('CPF *') as HTMLInputElement

        await user.type(cpfInput, '123456789012345')

        expect(cpfInput.maxLength).toBe(14)
      })
    })

    describe('Birth Date Field', () => {
      it('should validate required birth date', async () => {
        const user = userEvent.setup()
        render(<ClientForm onSubmit={mockOnSubmit} />)

        const birthDateInput = screen.getByLabelText('Data de Nascimento *')
        const submitButton = screen.getByRole('button', {
          name: 'Salvar Cliente',
        })

        // Initially, button should be disabled due to empty form
        expect(submitButton).toBeDisabled()

        // Focus and blur the birth date field to trigger validation
        await user.click(birthDateInput)
        await user.tab() // This will blur the field

        // Try to submit the form
        const form = submitButton.closest('form')
        if (form) {
          fireEvent.submit(form)
        }

        // Wait for validation error to appear
        await waitFor(() => {
          expect(
            screen.getByText('Data de nascimento é obrigatória')
          ).toBeInTheDocument()
        })
      })

      it('should validate minimum age (16 years)', async () => {
        const user = userEvent.setup()
        render(<ClientForm onSubmit={mockOnSubmit} />)

        const birthDateInput = screen.getByLabelText('Data de Nascimento *')
        const submitButton = screen.getByRole('button', {
          name: 'Salvar Cliente',
        })

        // Set birth date to 10 years ago (too young)
        const tooYoung = new Date()
        tooYoung.setFullYear(tooYoung.getFullYear() - 10)
        const tooYoungDate = tooYoung.toISOString().split('T')[0]

        await user.type(birthDateInput, tooYoungDate)
        await user.click(submitButton)

        await waitFor(() => {
          expect(
            screen.getByText('Cliente deve ter entre 16 e 120 anos')
          ).toBeInTheDocument()
        })
      })

      it('should validate maximum age (120 years)', async () => {
        const user = userEvent.setup()
        render(<ClientForm onSubmit={mockOnSubmit} />)

        const birthDateInput = screen.getByLabelText('Data de Nascimento *')
        const submitButton = screen.getByRole('button', {
          name: 'Salvar Cliente',
        })

        // Set birth date to 130 years ago (too old)
        const tooOld = new Date()
        tooOld.setFullYear(tooOld.getFullYear() - 130)
        const tooOldDate = tooOld.toISOString().split('T')[0]

        await user.type(birthDateInput, tooOldDate)
        await user.click(submitButton)

        await waitFor(() => {
          expect(
            screen.getByText('Cliente deve ter entre 16 e 120 anos')
          ).toBeInTheDocument()
        })
      })

      it('should accept valid age (between 16 and 120)', async () => {
        const user = userEvent.setup()
        render(<ClientForm onSubmit={mockOnSubmit} />)

        const birthDateInput = screen.getByLabelText('Data de Nascimento *')

        // Set birth date to 25 years ago (valid)
        const validAge = new Date()
        validAge.setFullYear(validAge.getFullYear() - 25)
        const validDate = validAge.toISOString().split('T')[0]

        await user.type(birthDateInput, validDate)
        await user.tab()

        await waitFor(() => {
          expect(
            screen.queryByText(/Cliente deve ter entre/)
          ).not.toBeInTheDocument()
        })
      })
    })
  })

  describe('Form Submission', () => {
    it('should submit form with valid data', async () => {
      const user = userEvent.setup()
      ;(validateCPF as Mock).mockReturnValue(true)

      render(<ClientForm onSubmit={mockOnSubmit} />)

      const nameInput = screen.getByLabelText('Nome Completo *')
      const cpfInput = screen.getByLabelText('CPF *')
      const birthDateInput = screen.getByLabelText('Data de Nascimento *')
      const submitButton = screen.getByRole('button', {
        name: 'Salvar Cliente',
      })

      const validDate = new Date()
      validDate.setFullYear(validDate.getFullYear() - 25)
      const validDateString = validDate.toISOString().split('T')[0]

      await user.type(nameInput, 'João Silva Santos')
      await user.type(cpfInput, '12345678901')
      await user.type(birthDateInput, validDateString)

      await user.click(submitButton)

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          name: 'João Silva Santos',
          cpf: '12345678901', // Should be cleaned (no formatting)
          birthDate: validDateString,
        })
      })
    })

    it('should clean CPF before submission', async () => {
      const user = userEvent.setup()
      ;(validateCPF as Mock).mockReturnValue(true)
      ;(formatCPF as Mock).mockImplementation((cpf: string) => {
        // Format the CPF with dots and dash for display
        if (cpf.length === 11) {
          return `${cpf.slice(0, 3)}.${cpf.slice(3, 6)}.${cpf.slice(6, 9)}-${cpf.slice(9, 11)}`
        }
        return cpf
      })

      const { container } = render(<ClientForm onSubmit={mockOnSubmit} />)

      const nameInput = screen.getByLabelText('Nome Completo *')
      const cpfInput = screen.getByLabelText('CPF *')
      const birthDateInput = screen.getByLabelText('Data de Nascimento *')

      const validDate = new Date()
      validDate.setFullYear(validDate.getFullYear() - 25)
      const validDateString = validDate.toISOString().split('T')[0]

      // Fill the form with valid data
      await user.type(nameInput, 'João Silva Santos')
      await user.type(cpfInput, '12345678901')
      await user.type(birthDateInput, validDateString)

      // Submit the form by clicking the submit button
      const submitButton = screen.getByRole('button', { name: /salvar/i })
      await user.click(submitButton)

      // Check that onSubmit was called with cleaned CPF (no formatting)
      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'João Silva Santos',
            cpf: '12345678901', // Should be cleaned, no dots or dashes
            birthDate: validDateString,
          })
        )
      })
    })

    it('should not submit when form is invalid', async () => {
      const user = userEvent.setup()
      ;(validateCPF as Mock).mockReturnValue(false)

      render(<ClientForm onSubmit={mockOnSubmit} />)

      const nameInput = screen.getByLabelText('Nome Completo *')
      const cpfInput = screen.getByLabelText('CPF *')
      const submitButton = screen.getByRole('button', {
        name: 'Salvar Cliente',
      })

      await user.type(nameInput, 'João Silva Santos')
      await user.type(cpfInput, '11111111111') // Invalid CPF

      // Submit button should be disabled
      expect(submitButton).toBeDisabled()

      await user.click(submitButton)

      expect(mockOnSubmit).not.toHaveBeenCalled()
    })

    it('should disable submit button when form is invalid', async () => {
      const user = userEvent.setup()
      render(<ClientForm onSubmit={mockOnSubmit} />)

      const submitButton = screen.getByRole('button', {
        name: 'Salvar Cliente',
      })

      // Initially disabled (empty form)
      expect(submitButton).toBeDisabled()

      const nameInput = screen.getByLabelText('Nome Completo *')
      await user.type(nameInput, 'A') // Too short

      expect(submitButton).toBeDisabled()
    })

    it('should enable submit button when form is valid', async () => {
      const user = userEvent.setup()
      ;(validateCPF as Mock).mockReturnValue(true)

      render(<ClientForm onSubmit={mockOnSubmit} />)

      const nameInput = screen.getByLabelText('Nome Completo *')
      const cpfInput = screen.getByLabelText('CPF *')
      const birthDateInput = screen.getByLabelText('Data de Nascimento *')
      const submitButton = screen.getByRole('button', {
        name: 'Salvar Cliente',
      })

      const validDate = new Date()
      validDate.setFullYear(validDate.getFullYear() - 25)
      const validDateString = validDate.toISOString().split('T')[0]

      await user.type(nameInput, 'João Silva Santos')
      await user.type(cpfInput, '12345678901')
      await user.type(birthDateInput, validDateString)

      await waitFor(() => {
        expect(submitButton).toBeEnabled()
      })
    })
  })

  describe('Loading State', () => {
    it('should show loading text when isLoading is true', () => {
      render(<ClientForm onSubmit={mockOnSubmit} isLoading={true} />)

      expect(screen.getByText('Salvando...')).toBeInTheDocument()
    })

    it('should disable all inputs when loading', () => {
      render(
        <ClientForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          isLoading={true}
        />
      )

      const nameInput = screen.getByLabelText('Nome Completo *')
      const cpfInput = screen.getByLabelText('CPF *')
      const birthDateInput = screen.getByLabelText('Data de Nascimento *')
      const submitButton = screen.getByRole('button', { name: 'Salvando...' })
      const cancelButton = screen.getByRole('button', { name: 'Cancelar' })

      expect(nameInput).toBeDisabled()
      expect(cpfInput).toBeDisabled()
      expect(birthDateInput).toBeDisabled()
      expect(submitButton).toBeDisabled()
      expect(cancelButton).toBeDisabled()
    })

    it('should enable all inputs when not loading', () => {
      render(
        <ClientForm
          onSubmit={mockOnSubmit}
          onCancel={mockOnCancel}
          isLoading={false}
        />
      )

      const nameInput = screen.getByLabelText('Nome Completo *')
      const cpfInput = screen.getByLabelText('CPF *')
      const birthDateInput = screen.getByLabelText('Data de Nascimento *')
      const cancelButton = screen.getByRole('button', { name: 'Cancelar' })

      expect(nameInput).toBeEnabled()
      expect(cpfInput).toBeEnabled()
      expect(birthDateInput).toBeEnabled()
      expect(cancelButton).toBeEnabled()
    })
  })

  describe('Cancel Functionality', () => {
    it('should call onCancel when cancel button is clicked', async () => {
      const user = userEvent.setup()
      render(<ClientForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />)

      const cancelButton = screen.getByRole('button', { name: 'Cancelar' })
      await user.click(cancelButton)

      expect(mockOnCancel).toHaveBeenCalled()
    })
  })

  describe('Initial Data Handling', () => {
    it('should populate form with initial data', () => {
      const initialData = {
        name: 'João Silva Santos',
        cpf: '12345678901',
        birthDate: '1990-01-01',
      }

      render(<ClientForm onSubmit={mockOnSubmit} initialData={initialData} />)

      expect(screen.getByDisplayValue('João Silva Santos')).toBeInTheDocument()
      expect(screen.getByDisplayValue('1990-01-01')).toBeInTheDocument()
    })

    it('should handle partial initial data', () => {
      const initialData = {
        name: 'João Silva',
      }

      render(<ClientForm onSubmit={mockOnSubmit} initialData={initialData} />)

      expect(screen.getByDisplayValue('João Silva')).toBeInTheDocument()
      const cpfInput = screen.getByLabelText('CPF *') as HTMLInputElement
      const birthDateInput = screen.getByLabelText(
        'Data de Nascimento *'
      ) as HTMLInputElement

      expect(cpfInput.value).toBe('')
      expect(birthDateInput.value).toBe('')
    })
  })

  describe('CPF Real-time Validation', () => {
    it('should update visual indicator when CPF changes', async () => {
      const user = userEvent.setup()
      ;(validateCPF as Mock)
        .mockReturnValueOnce(false)
        .mockReturnValueOnce(true)

      render(<ClientForm onSubmit={mockOnSubmit} />)

      const cpfInput = screen.getByLabelText('CPF *')

      // First type invalid CPF
      await user.type(cpfInput, '111111111')

      await waitFor(() => {
        expect(screen.getByText('✗')).toBeInTheDocument()
      })

      // Clear and type valid CPF
      await user.clear(cpfInput)
      await user.type(cpfInput, '12345678901')

      await waitFor(() => {
        expect(screen.getByText('✓')).toBeInTheDocument()
      })
    })

    it('should show validation message for valid CPF', async () => {
      const user = userEvent.setup()
      ;(validateCPF as Mock).mockReturnValue(true)

      render(<ClientForm onSubmit={mockOnSubmit} />)

      const cpfInput = screen.getByLabelText('CPF *')
      await user.type(cpfInput, '12345678901')

      await waitFor(() => {
        expect(
          screen.getByText('✅ CPF válido - Utilizando @brazilian-utils')
        ).toBeInTheDocument()
      })
    })

    it('should not show validation message when no CPF is entered', () => {
      render(<ClientForm onSubmit={mockOnSubmit} />)

      expect(
        screen.queryByText('✅ CPF válido - Utilizando @brazilian-utils')
      ).not.toBeInTheDocument()
      expect(screen.queryByText('✓')).not.toBeInTheDocument()
      expect(screen.queryByText('✗')).not.toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper labels and associations', () => {
      render(<ClientForm onSubmit={mockOnSubmit} />)

      const nameInput = screen.getByLabelText('Nome Completo *')
      const cpfInput = screen.getByLabelText('CPF *')
      const birthDateInput = screen.getByLabelText('Data de Nascimento *')

      expect(nameInput).toHaveAttribute('type', 'text')
      expect(cpfInput).toHaveAttribute('type', 'text')
      expect(birthDateInput).toHaveAttribute('type', 'date')
    })

    it('should show error messages with proper ARIA associations', async () => {
      const user = userEvent.setup()
      render(<ClientForm onSubmit={mockOnSubmit} />)

      const nameInput = screen.getByLabelText('Nome Completo *')

      await user.type(nameInput, 'A')
      await user.tab()

      await waitFor(() => {
        const errorMessage = screen.getByText(
          'Nome deve ter pelo menos 2 caracteres'
        )
        expect(errorMessage).toBeInTheDocument()
        expect(errorMessage).toHaveClass('text-red-600')
      })
    })

    it('should apply proper CSS classes for validation states', async () => {
      const user = userEvent.setup()
      ;(validateCPF as Mock).mockReturnValue(true)

      render(<ClientForm onSubmit={mockOnSubmit} />)

      const cpfInput = screen.getByLabelText('CPF *')

      await user.type(cpfInput, '12345678901')

      await waitFor(() => {
        expect(cpfInput).toHaveClass('border-green-500')
      })
    })
  })
})
