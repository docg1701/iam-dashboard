/**
 * ClientRegistrationForm Integration Tests
 * Tests complete client registration workflow with real API integration
 * Following CLAUDE.md rules: no internal mocking, only external API mocking
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ClientRegistrationForm } from '../ClientRegistrationForm'
import { clientsAPI } from '@/lib/api/clients'
import { useToast } from '@/hooks/use-toast'
import type { ClientCreate, ClientResponse, ClientErrorResponse } from '@iam-dashboard/shared'

// Mock only external fetch API
const mockFetch = vi.fn()
global.fetch = mockFetch

// Test wrapper for providers
const createTestQueryClient = () => {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
      mutations: { retry: false }
    }
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

// Helper functions to get form fields reliably
const getNameField = () => screen.getByPlaceholderText(/joão silva santos/i)
const getCpfField = () => screen.getByPlaceholderText(/123\.456\.789-12/i)
const getBirthDateField = () => document.querySelector('input[name="birth_date"]') as HTMLInputElement
const getNotesField = () => screen.getByPlaceholderText(/informações adicionais/i)

beforeEach(() => {
  vi.clearAllMocks()
  mockFetch.mockReset()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('ClientRegistrationForm - Integration Tests', () => {
  // Complete Registration Flow Tests
  describe('Complete Client Registration Flow', () => {
    it('should complete full client registration workflow', async () => {
      const user = userEvent.setup()
      const mockOnSuccess = vi.fn()
      const mockOnError = vi.fn()
      
      const mockClientResponse: ClientResponse = {
        client_id: '123e4567-e89b-12d3-a456-426614174000',
        full_name: 'João Silva Santos',
        cpf: '***.***.***-89', // API returns masked CPF
        birth_date: '1990-05-15',
        status: 'active',
        notes: 'Cliente preferencial com histórico excelente',
        created_by: 'user123',
        updated_by: 'user123',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      }
      
      // Mock fetch response for API call
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockClientResponse)
      } as Response)
      
      // Mock API to create client
      const mockOnSubmit = vi.fn().mockResolvedValue(mockClientResponse)
      
      render(
        <TestWrapper>
          <ClientRegistrationForm
            onSubmit={mockOnSubmit}
            onSuccess={mockOnSuccess}
            onError={mockOnError}
          />
        </TestWrapper>
      )
      
      // Fill out complete form
      const nameField = getNameField()
      const cpfField = getCpfField()
      const birthDateField = getBirthDateField()
      const notesField = getNotesField()
      const submitButton = screen.getByRole('button', { name: /criar cliente/i })
      
      // Step 1: Fill personal information
      await user.type(nameField, 'João Silva Santos')
      expect(nameField).toHaveValue('João Silva Santos')
      
      // Step 2: Fill CPF with automatic formatting
      await user.type(cpfField, '12345678901')
      expect(cpfField).toHaveValue('123.456.789-01')
      
      // Step 3: Fill birth date
      await user.type(birthDateField, '1990-05-15')
      expect(birthDateField).toHaveValue('1990-05-15')
      
      // Step 4: Fill notes
      await user.type(notesField, 'Cliente preferencial com histórico excelente')
      expect(notesField).toHaveValue('Cliente preferencial com histórico excelente')
      
      // Step 5: Submit form
      await user.click(submitButton)
      
      // Should show loading state
      await waitFor(() => {
        expect(screen.getByText(/criando cliente/i)).toBeInTheDocument()
      })
      
      // Should call API with correct data
      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          full_name: 'João Silva Santos',
          cpf: '123.456.789-01',
          birth_date: '1990-05-15',
          notes: 'Cliente preferencial com histórico excelente'
        })
      })
      
      // Should call success callback
      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalledWith(mockClientResponse)
      })
      
      // Should reset form after success
      await waitFor(() => {
        expect(nameField).toHaveValue('')
        expect(cpfField).toHaveValue('')
        expect(birthDateField).toHaveValue('')
        expect(notesField).toHaveValue('')
      })
      
      // Should not call error callback
      expect(mockOnError).not.toHaveBeenCalled()
    })

    it('should handle API validation errors correctly', async () => {
      const user = userEvent.setup()
      const mockOnSuccess = vi.fn()
      const mockOnError = vi.fn()
      
      // Mock API validation error (duplicate CPF)
      const validationError: ClientErrorResponse = {
        detail: 'Client with this CPF already exists',
        field_errors: {
          cpf: ['CPF já está em uso por outro cliente']
        }
      }
      
      const mockOnSubmit = vi.fn().mockRejectedValue({
        response: {
          status: 409,
          data: validationError
        },
        message: 'Client with this CPF already exists'
      })
      
      render(
        <TestWrapper>
          <ClientRegistrationForm
            onSubmit={mockOnSubmit}
            onSuccess={mockOnSuccess}
            onError={mockOnError}
          />
        </TestWrapper>
      )
      
      // Fill form with duplicate CPF
      const nameField = getNameField()
      const cpfField = getCpfField()
      const birthDateField = getBirthDateField()
      const submitButton = screen.getByRole('button', { name: /criar cliente/i })
      
      await user.type(nameField, 'Maria Silva')
      await user.type(cpfField, '12345678901') // Duplicate CPF
      await user.type(birthDateField, '1985-03-10')
      
      await user.click(submitButton)
      
      // Should show API error
      await waitFor(() => {
        expect(screen.getByText(/client with this cpf already exists/i)).toBeInTheDocument()
      })
      
      // Should call error callback
      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalledWith('Client with this CPF already exists')
      })
      
      // Should not call success callback
      expect(mockOnSuccess).not.toHaveBeenCalled()
      
      // Form should retain values for correction
      expect(nameField).toHaveValue('Maria Silva')
      expect(cpfField).toHaveValue('123.456.789-01')
      expect(birthDateField).toHaveValue('1985-03-10')
    })

    it('should handle network errors gracefully', async () => {
      const user = userEvent.setup()
      const mockOnSuccess = vi.fn()
      const mockOnError = vi.fn()
      
      // Mock network error
      const mockOnSubmit = vi.fn().mockRejectedValue(new Error('Network Error'))
      
      render(
        <TestWrapper>
          <ClientRegistrationForm
            onSubmit={mockOnSubmit}
            onSuccess={mockOnSuccess}
            onError={mockOnError}
          />
        </TestWrapper>
      )
      
      // Fill and submit form
      const nameField = getNameField()
      const cpfField = getCpfField()
      const birthDateField = getBirthDateField()
      const submitButton = screen.getByRole('button', { name: /criar cliente/i })
      
      await user.type(nameField, 'João Silva')
      await user.type(cpfField, '12345678901')
      await user.type(birthDateField, '1990-05-15')
      
      await user.click(submitButton)
      
      // Should display network error
      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument()
      })
      
      // Should call error callback
      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalledWith('Network Error')
      })
      
      // Should not reset form on error
      expect(nameField).toHaveValue('João Silva')
      expect(cpfField).toHaveValue('123.456.789-01')
      expect(birthDateField).toHaveValue('1990-05-15')
    })

    it('should handle server timeout errors', async () => {
      const user = userEvent.setup()
      const mockOnError = vi.fn()
      
      // Mock timeout error
      const mockOnSubmit = vi.fn().mockImplementation(() => 
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Request timeout')), 50)
        )
      )
      
      render(
        <TestWrapper>
          <ClientRegistrationForm
            onSubmit={mockOnSubmit}
            onError={mockOnError}
          />
        </TestWrapper>
      )
      
      // Fill and submit form
      await user.type(getNameField(), 'João Silva')
      await user.type(getCpfField(), '12345678901')
      await user.type(getBirthDateField(), '1990-05-15')
      
      await user.click(screen.getByRole('button', { name: /criar cliente/i }))
      
      // Should handle timeout error
      await waitFor(() => {
        expect(screen.getByText(/request timeout/i)).toBeInTheDocument()
      }, { timeout: 2000 })
      
      expect(mockOnError).toHaveBeenCalledWith('Request timeout')
    })
  })

  // Form State Management Tests
  describe('Form State Management', () => {
    it('should maintain form state during validation errors', async () => {
      const user = userEvent.setup()
      const mockOnSubmit = vi.fn()
      
      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      const nameField = getNameField()
      const cpfField = getCpfField()
      const birthDateField = getBirthDateField()
      const notesField = getNotesField()
      const submitButton = screen.getByRole('button', { name: /criar cliente/i })
      
      // Fill form with invalid data
      await user.type(nameField, 'João Silva Santos')
      await user.type(cpfField, '12345678901')
      await user.type(birthDateField, '1990-05-15')
      await user.type(notesField, 'Some notes')
      
      // Clear required field to trigger validation
      await user.clear(nameField)
      await user.click(submitButton)
      
      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText(/nome completo é obrigatório/i)).toBeInTheDocument()
      })
      
      // Other fields should maintain their values
      expect(cpfField).toHaveValue('123.456.789-01')
      expect(birthDateField).toHaveValue('1990-05-15')
      expect(notesField).toHaveValue('Some notes')
      
      // Should not call submit function
      expect(mockOnSubmit).not.toHaveBeenCalled()
    })

    it('should handle multiple validation errors simultaneously', async () => {
      const user = userEvent.setup()
      const mockOnSubmit = vi.fn()
      
      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      const nameField = getNameField()
      const cpfField = getCpfField()
      const submitButton = screen.getByRole('button', { name: /criar cliente/i })
      
      // Fill with multiple invalid values
      await user.type(nameField, 'A') // Too short
      await user.type(cpfField, '123') // Invalid format
      
      await user.click(submitButton)
      
      // Should show multiple validation errors
      await waitFor(() => {
        expect(screen.getByText(/nome deve ter pelo menos 2 caracteres/i)).toBeInTheDocument()
        expect(screen.getByText(/cpf deve estar no formato xxx\.xxx\.xxx-xx/i)).toBeInTheDocument()
        expect(screen.getByText(/data de nascimento é obrigatória/i)).toBeInTheDocument()
      })
      
      // Form values should be preserved
      expect(nameField).toHaveValue('A')
      expect(cpfField).toHaveValue('123')
    })

    it('should clear validation errors when fields are corrected', async () => {
      const user = userEvent.setup()
      const mockOnSubmit = vi.fn()
      
      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      const nameField = getNameField()
      const submitButton = screen.getByRole('button', { name: /criar cliente/i })
      
      // Trigger validation error
      await user.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByText(/nome completo é obrigatório/i)).toBeInTheDocument()
      })
      
      // Fix the error
      await user.type(nameField, 'João Silva')
      
      // Error should clear when field is corrected
      await waitFor(() => {
        expect(screen.queryByText(/nome completo é obrigatório/i)).not.toBeInTheDocument()
      })
    })

    it('should preserve form state during loading', async () => {
      const user = userEvent.setup()
      
      // Mock slow API call
      const mockOnSubmit = vi.fn().mockImplementation(() => 
        new Promise(resolve => 
          setTimeout(() => resolve({
            client_id: '123',
            full_name: 'João Silva',
            cpf: '***.***.***-89',
            birth_date: '1990-05-15',
            status: 'active',
            created_by: 'user123',
            updated_by: 'user123',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z'
          } as ClientResponse), 100)
        )
      )
      
      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      // Fill form
      const nameField = getNameField()
      const cpfField = getCpfField()
      const birthDateField = getBirthDateField()
      const submitButton = screen.getByRole('button', { name: /criar cliente/i })
      
      await user.type(nameField, 'João Silva')
      await user.type(cpfField, '12345678901')
      await user.type(birthDateField, '1990-05-15')
      
      await user.click(submitButton)
      
      // During loading, form should show loading state but preserve values
      expect(screen.getByText(/criando cliente/i)).toBeInTheDocument()
      expect(nameField).toHaveValue('João Silva')
      expect(cpfField).toHaveValue('123.456.789-01')
      expect(birthDateField).toHaveValue('1990-05-15')
      
      // Fields should be disabled during loading
      expect(nameField).toBeDisabled()
      expect(cpfField).toBeDisabled()
      expect(birthDateField).toBeDisabled()
      expect(submitButton).toBeDisabled()
      
      // After completion, form should reset
      await waitFor(() => {
        expect(nameField).toHaveValue('')
        expect(cpfField).toHaveValue('')
        expect(birthDateField).toHaveValue('')
      })
    })
  })

  // Real API Integration Tests
  describe('Real API Integration', () => {
    it('should integrate with clients API service correctly', async () => {
      const user = userEvent.setup()
      
      const mockClientResponse: ClientResponse = {
        client_id: '123e4567-e89b-12d3-a456-426614174000',
        full_name: 'Ana Paula Silva',
        cpf: '***.***.***-76',
        birth_date: '1988-12-25',
        status: 'active',
        notes: 'Cliente VIP',
        created_by: 'user123',
        updated_by: 'user123',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      }
      
      // Mock fetch response for API call
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockClientResponse)
      } as Response)
      
      // Create a submit handler that uses the real API
      const handleSubmit = async (data: ClientCreate) => {
        return await clientsAPI.createClient(data)
      }
      
      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={handleSubmit} />
        </TestWrapper>
      )
      
      // Fill form
      await user.type(getNameField(), 'Ana Paula Silva')
      await user.type(getCpfField(), '987654321')
      await user.type(getBirthDateField(), '1988-12-25')
      await user.type(getNotesField(), 'Cliente VIP')
      
      // Submit form
      await user.click(screen.getByRole('button', { name: /criar cliente/i }))
      
      // Should call the API with correct data
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/clients'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('"full_name":"Ana Paula Silva"')
          })
        )
      })
    })

    it('should handle API error responses correctly', async () => {
      const user = userEvent.setup()
      const mockOnError = vi.fn()
      
      // Mock API error
      const apiError = {
        response: {
          status: 400,
          data: {
            detail: 'Invalid birth date format',
            field_errors: {
              birth_date: ['Data deve estar no formato AAAA-MM-DD']
            }
          }
        }
      }
      
      // Mock fetch to return error response
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: () => Promise.resolve({
          detail: 'Invalid birth date format',
          field_errors: {
            birth_date: ['Data deve estar no formato AAAA-MM-DD']
          }
        })
      } as Response)
      
      const handleSubmit = async (data: ClientCreate) => {
        try {
          return await clientsAPI.createClient(data)
        } catch (error) {
          throw error
        }
      }
      
      render(
        <TestWrapper>
          <ClientRegistrationForm
            onSubmit={handleSubmit}
            onError={mockOnError}
          />
        </TestWrapper>
      )
      
      // Fill and submit form
      await user.type(getNameField(), 'Carlos Santos')
      await user.type(getCpfField(), '111223344')
      await user.type(getBirthDateField(), '1975-08-30')
      
      await user.click(screen.getByRole('button', { name: /criar cliente/i }))
      
      // Should handle API error
      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalled()
      })
    })

    it('should handle successful API response with masked CPF', async () => {
      const user = userEvent.setup()
      const mockOnSuccess = vi.fn()
      
      const mockClientResponse: ClientResponse = {
        client_id: '456e7890-e89b-12d3-a456-426614174001',
        full_name: 'Roberto Santos',
        cpf: '***.***.***-57', // API returns masked CPF for security
        birth_date: '1992-07-18',
        status: 'active',
        created_by: 'user123',
        updated_by: 'user123',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      }
      
      // Mock fetch response for successful API call
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockClientResponse)
      } as Response)
      
      const handleSubmit = async (data: ClientCreate) => {
        return await clientsAPI.createClient(data)
      }
      
      render(
        <TestWrapper>
          <ClientRegistrationForm
            onSubmit={handleSubmit}
            onSuccess={mockOnSuccess}
          />
        </TestWrapper>
      )
      
      // Fill and submit form
      await user.type(getNameField(), 'Roberto Santos')
      await user.type(getCpfField(), '555113579')
      await user.type(getBirthDateField(), '1992-07-18')
      
      await user.click(screen.getByRole('button', { name: /criar cliente/i }))
      
      // Should receive masked CPF in response
      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalledWith(expect.objectContaining({
          client_id: '456e7890-e89b-12d3-a456-426614174001',
          full_name: 'Roberto Santos',
          cpf: '***.***.***-57', // Masked by API
          birth_date: '1992-07-18'
        }))
      })
    })
  })

  // User Experience Tests
  describe('User Experience Flow', () => {
    it('should provide smooth user experience for successful registration', async () => {
      const user = userEvent.setup()
      const mockOnSuccess = vi.fn()
      
      const mockClientResponse: ClientResponse = {
        client_id: '789e0123-e89b-12d3-a456-426614174002',
        full_name: 'Fernanda Costa',
        cpf: '***.***.***-80',
        birth_date: '1995-01-22',
        status: 'active',
        created_by: 'user123',
        updated_by: 'user123',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      }
      
      const mockOnSubmit = vi.fn().mockResolvedValue(mockClientResponse)
      
      render(
        <TestWrapper>
          <ClientRegistrationForm
            onSubmit={mockOnSubmit}
            onSuccess={mockOnSuccess}
          />
        </TestWrapper>
      )
      
      // User fills form progressively
      const nameField = getNameField()
      const cpfField = getCpfField()
      const birthDateField = getBirthDateField()
      
      // Step-by-step form filling
      await user.type(nameField, 'Fernanda Costa')
      expect(nameField).toHaveValue('Fernanda Costa')
      
      await user.type(cpfField, '246802468')
      expect(cpfField).toHaveValue('246.802.468-01')
      
      await user.type(birthDateField, '1995-01-22')
      expect(birthDateField).toHaveValue('1995-01-22')
      
      // Submit with confidence
      const submitButton = screen.getByRole('button', { name: /criar cliente/i })
      expect(submitButton).not.toBeDisabled()
      
      await user.click(submitButton)
      
      // Immediate feedback
      expect(screen.getByText(/criando cliente/i)).toBeInTheDocument()
      expect(submitButton).toBeDisabled()
      
      // Success handling
      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalledWith(mockClientResponse)
      })
      
      // Form resets for next entry
      await waitFor(() => {
        expect(nameField).toHaveValue('')
        expect(cpfField).toHaveValue('')
        expect(birthDateField).toHaveValue('')
      })
    })

    it('should guide user through error correction', async () => {
      const user = userEvent.setup()
      const mockOnSubmit = vi.fn()
      
      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      const submitButton = screen.getByRole('button', { name: /criar cliente/i })
      
      // User tries to submit empty form
      await user.click(submitButton)
      
      // Gets clear guidance
      await waitFor(() => {
        expect(screen.getByText(/nome completo é obrigatório/i)).toBeInTheDocument()
        expect(screen.getByText(/cpf é obrigatório/i)).toBeInTheDocument()
        expect(screen.getByText(/data de nascimento é obrigatória/i)).toBeInTheDocument()
      })
      
      // User fixes errors one by one
      const nameField = getNameField()
      await user.type(nameField, 'Pedro Silva')
      
      // Error for name disappears
      await waitFor(() => {
        expect(screen.queryByText(/nome completo é obrigatório/i)).not.toBeInTheDocument()
      })
      
      // Continue fixing other fields
      const cpfField = getCpfField()
      await user.type(cpfField, '12345678901')
      
      await waitFor(() => {
        expect(screen.queryByText(/cpf é obrigatório/i)).not.toBeInTheDocument()
      })
      
      const birthDateField = getBirthDateField()
      await user.type(birthDateField, '1980-06-15')
      
      await waitFor(() => {
        expect(screen.queryByText(/data de nascimento é obrigatória/i)).not.toBeInTheDocument()
      })
      
      // Now form can be submitted
      expect(submitButton).not.toBeDisabled()
    })

    it('should handle form reset gracefully', async () => {
      const user = userEvent.setup()
      const mockOnSubmit = vi.fn()
      
      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      // User fills form
      const nameField = getNameField()
      const cpfField = getCpfField()
      const birthDateField = getBirthDateField()
      const notesField = getNotesField()
      const clearButton = screen.getByRole('button', { name: /limpar formulário/i })
      
      await user.type(nameField, 'Test User')
      await user.type(cpfField, '12345678901')
      await user.type(birthDateField, '1990-01-01')
      await user.type(notesField, 'Test notes')
      
      // User decides to clear form
      await user.click(clearButton)
      
      // All fields should be empty
      expect(nameField).toHaveValue('')
      expect(cpfField).toHaveValue('')
      expect(birthDateField).toHaveValue('')
      expect(notesField).toHaveValue('')
      
      // Form should be ready for new input
      expect(clearButton).not.toBeDisabled()
      expect(screen.getByRole('button', { name: /criar cliente/i })).not.toBeDisabled()
    })
  })
})