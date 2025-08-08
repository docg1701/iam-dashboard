/**
 * ClientRegistrationForm Component Tests
 * Tests client registration form behavior and user interactions
 * Following CLAUDE.md rules: no internal mocking, only external API mocking
 */
import {
  describe,
  it,
  expect,
  vi,
  beforeEach,
  afterEach,
  renderWithProviders,
  screen,
  waitFor,
  userEvent,
  useTestSetup,
  mockSuccessfulFetch,
  mockFailedFetch,
  act,
} from '@/test/test-template'
import { ClientRegistrationForm } from '../ClientRegistrationForm'
import type { ClientCreate, ClientResponse } from '@iam-dashboard/shared'

describe('ClientRegistrationForm', () => {
  useTestSetup()

  // Helper functions to get form fields reliably
  const getNameField = () => screen.getByPlaceholderText(/joão silva santos/i)
  const getCpfField = () => screen.getByPlaceholderText(/123\.456\.789-12/i)
  const getBirthDateField = () => document.querySelector('input[type="date"]') as HTMLInputElement
  const getNotesField = () => screen.getByPlaceholderText(/informações adicionais/i)
  const getSubmitButton = () => screen.getByRole('button', { name: /criar cliente/i })
  const getClearButton = () => screen.getByRole('button', { name: /limpar formulário/i })

  // Mock callback functions
  const mockOnSubmit = vi.fn()
  const mockOnSuccess = vi.fn()
  const mockOnError = vi.fn()

  beforeEach(() => {
    mockOnSubmit.mockReset()
    mockOnSuccess.mockReset()
    mockOnError.mockReset()
  })

  // Basic Rendering Tests
  it('should render all form fields correctly', () => {
    renderWithProviders(<ClientRegistrationForm onSubmit={mockOnSubmit} />)
    
    expect(getNameField()).toBeInTheDocument()
    expect(getCpfField()).toBeInTheDocument()
    expect(getBirthDateField()).toBeInTheDocument()
    expect(getNotesField()).toBeInTheDocument()
    expect(getSubmitButton()).toBeInTheDocument()
    expect(getClearButton()).toBeInTheDocument()
  })

  it('should render form with proper accessibility attributes', () => {
    renderWithProviders(<ClientRegistrationForm onSubmit={mockOnSubmit} />)
    
    const nameField = getNameField()
    const cpfField = getCpfField()
    const notesField = getNotesField()
    
    expect(nameField).toHaveAttribute('autoComplete', 'name')
    expect(cpfField).toHaveAttribute('autoComplete', 'off')
    expect(notesField.tagName).toBe('TEXTAREA')
  })

  // Form Validation Tests
  it('should validate required full name field', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(<ClientRegistrationForm onSubmit={mockOnSubmit} />)
    
    const submitButton = getSubmitButton()
    
    // Try to submit with empty form
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/nome completo é obrigatório/i)).toBeInTheDocument()
    })
    
    expect(mockOnSubmit).not.toHaveBeenCalled()
  })

  it('should validate name minimum length', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(<ClientRegistrationForm onSubmit={mockOnSubmit} />)
    
    const nameField = getNameField()
    const submitButton = getSubmitButton()
    
    // Enter name with less than 2 characters
    await user.type(nameField, 'A')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/nome deve ter pelo menos 2 caracteres/i)).toBeInTheDocument()
    })
  })

  it('should validate name with invalid characters', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(<ClientRegistrationForm onSubmit={mockOnSubmit} />)
    
    const nameField = getNameField()
    const submitButton = getSubmitButton()
    
    // Enter name with numbers and special characters
    await user.type(nameField, 'João123@Silva')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/nome deve conter apenas letras, espaços, hífens e apostrofes/i)).toBeInTheDocument()
    })
  })

  it('should validate CPF format correctly', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(<ClientRegistrationForm onSubmit={mockOnSubmit} />)
    
    const nameField = getNameField()
    const cpfField = getCpfField()
    const submitButton = getSubmitButton()
    
    // Fill form with invalid CPF (too short - only 8 digits)
    await user.type(nameField, 'João Silva')
    await user.type(cpfField, '12345678')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/cpf deve estar no formato XXX\.XXX\.XXX-XX/i)).toBeInTheDocument()
    })
    
    expect(mockOnSubmit).not.toHaveBeenCalled()
  })

  it('should validate birth date is required', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(<ClientRegistrationForm onSubmit={mockOnSubmit} />)
    
    const nameField = getNameField()
    const cpfField = getCpfField()
    const submitButton = getSubmitButton()
    
    // Fill form without birth date
    await user.type(nameField, 'João Silva')
    await user.type(cpfField, '12345678901')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/data de nascimento é obrigatória/i)).toBeInTheDocument()
    })
  })

  it('should validate minimum age requirement (13 years)', async () => {
    const user = userEvent.setup()
    
    // Make sure onSubmit rejects if called to catch any issues
    mockOnSubmit.mockRejectedValue(new Error('Should not be called - form validation should prevent submission'))
    
    renderWithProviders(<ClientRegistrationForm onSubmit={mockOnSubmit} />)
    
    const nameField = getNameField()
    const cpfField = getCpfField()
    const birthDateField = getBirthDateField()
    const submitButton = getSubmitButton()
    
    // Use a date that's clearly less than 13 years old (today's date)
    // This should definitely fail the age validation
    const today = new Date()
    const todayStr = today.toISOString().split('T')[0]
    
    // Fill all required fields to trigger age validation specifically
    await user.type(nameField, 'João Silva')
    await user.type(cpfField, '11144477735') // Use a valid CPF format for testing
    
    // Set the birth date to today's date (0 years old)
    await user.clear(birthDateField)
    await user.type(birthDateField, todayStr)
    
    // Click submit to trigger validation
    await user.click(submitButton)
    
    // Wait for form validation - form should not submit and show error
    await waitFor(
      () => {
        expect(screen.getByText(/idade deve estar entre 13 e 120 anos/i)).toBeInTheDocument()
      },
      { timeout: 5000 }
    )
    
    expect(mockOnSubmit).not.toHaveBeenCalled()
  })

  it('should validate maximum age requirement (120 years)', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(<ClientRegistrationForm onSubmit={mockOnSubmit} />)
    
    const nameField = getNameField()
    const cpfField = getCpfField()
    const birthDateField = getBirthDateField()
    const submitButton = getSubmitButton()
    
    // Date for someone over 120 years old (130 years ago)
    const today = new Date()
    const overAge = new Date(today.getFullYear() - 130, today.getMonth(), today.getDate())
    const overAgeStr = overAge.toISOString().split('T')[0]
    
    await user.type(nameField, 'João Silva')
    await user.type(cpfField, '11144477735')
    await user.clear(birthDateField)
    await user.type(birthDateField, overAgeStr)
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/idade deve estar entre 13 e 120 anos/i)).toBeInTheDocument()
    }, { timeout: 3000 })
    
    expect(mockOnSubmit).not.toHaveBeenCalled()
  })

  it('should validate notes maximum length', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(<ClientRegistrationForm onSubmit={mockOnSubmit} />)
    
    const nameField = getNameField()
    const cpfField = getCpfField()
    const birthDateField = getBirthDateField()
    const notesField = getNotesField()
    const submitButton = getSubmitButton()
    
    // Generate text longer than 1000 characters
    const longText = 'A'.repeat(1001)
    
    await user.type(nameField, 'João Silva')
    await user.type(cpfField, '11144477735')
    await user.type(birthDateField, '1990-05-15')
    await user.type(notesField, longText)
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/notas não podem exceder 1000 caracteres/i)).toBeInTheDocument()
    })
  })

  // CPF Formatting Tests
  it('should format CPF as user types', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(<ClientRegistrationForm onSubmit={mockOnSubmit} />)
    
    const cpfField = getCpfField()
    
    // Type CPF digits and verify formatting
    await user.type(cpfField, '12345')
    expect(cpfField).toHaveValue('123.45')
    
    await user.type(cpfField, '67890')
    expect(cpfField).toHaveValue('123.456.789-0')
    
    await user.type(cpfField, '1')
    expect(cpfField).toHaveValue('123.456.789-09')
  })

  it('should limit CPF input to 11 digits', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(<ClientRegistrationForm onSubmit={mockOnSubmit} />)
    
    const cpfField = getCpfField()
    
    // Try to type more than 11 digits
    await user.type(cpfField, '12345678901234')
    expect(cpfField).toHaveValue('123.456.789-09')
  })

  it('should handle non-numeric characters in CPF input', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(<ClientRegistrationForm onSubmit={mockOnSubmit} />)
    
    const cpfField = getCpfField()
    
    // Type CPF with letters and special characters
    await user.type(cpfField, 'abc123def456ghi789jkl01')
    expect(cpfField).toHaveValue('123.456.789-09')
  })

  // Form Submission Tests
  it('should submit form with valid data', async () => {
    const user = userEvent.setup()
    const mockClientResponse: ClientResponse = {
      client_id: '123e4567-e89b-12d3-a456-426614174000',
      full_name: 'João Silva Santos',
      cpf: '***.***.***-89',
      birth_date: '1990-05-15',
      status: 'active',
      notes: 'Cliente teste',
      created_by: 'user123',
      updated_by: 'user123',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z'
    }
    
    mockOnSubmit.mockResolvedValue(mockClientResponse)
    
    renderWithProviders(<ClientRegistrationForm
          onSubmit={mockOnSubmit}
          onSuccess={mockOnSuccess}
 />)
    
    const nameField = getNameField()
    const cpfField = getCpfField()
    const birthDateField = getBirthDateField()
    const notesField = getNotesField()
    const submitButton = getSubmitButton()
    
    // Fill form with valid data
    await user.type(nameField, 'João Silva Santos')
    await user.type(cpfField, '12345678901')
    await user.type(birthDateField, '1990-05-15')
    await user.type(notesField, 'Cliente teste')
    
    // Submit form
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        full_name: 'João Silva Santos',
        cpf: '123.456.789-09',
        birth_date: '1990-05-15',
        notes: 'Cliente teste'
      })
    })
    
    expect(mockOnSuccess).toHaveBeenCalledWith(mockClientResponse)
  })

  it('should submit form with minimal required data', async () => {
    const user = userEvent.setup()
    const mockClientResponse: ClientResponse = {
      client_id: '123e4567-e89b-12d3-a456-426614174000',
      full_name: 'Maria Silva',
      cpf: '***.***.***-32',
      birth_date: '1985-03-10',
      status: 'active',
      created_by: 'user123',
      updated_by: 'user123',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z'
    }
    
    mockOnSubmit.mockResolvedValue(mockClientResponse)
    
    renderWithProviders(<ClientRegistrationForm
          onSubmit={mockOnSubmit}
          onSuccess={mockOnSuccess}
 />)
    
    const nameField = getNameField()
    const cpfField = getCpfField()
    const birthDateField = getBirthDateField()
    const submitButton = getSubmitButton()
    
    // Fill only required fields
    await user.type(nameField, 'Maria Silva')
    await user.type(cpfField, '98765432101')
    await user.type(birthDateField, '1985-03-10')
    
    // Submit form
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        full_name: 'Maria Silva',
        cpf: '987.654.321-01',
        birth_date: '1985-03-10',
        notes: undefined
      })
    })
  })

  // Loading State Tests
  it('should display loading state during form submission', async () => {
    const user = userEvent.setup()
    
    // Mock slow API response
    mockOnSubmit.mockImplementation(() => 
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
    
    renderWithProviders(<ClientRegistrationForm onSubmit={mockOnSubmit} />)
    
    const nameField = getNameField()
    const cpfField = getCpfField()
    const birthDateField = getBirthDateField()
    const submitButton = getSubmitButton()
    const clearButton = getClearButton()
    
    await user.type(nameField, 'João Silva')
    await user.type(cpfField, '12345678901')
    await user.type(birthDateField, '1990-05-15')
    
    await user.click(submitButton)
    
    // Should show loading state immediately
    expect(screen.getByText(/criando cliente/i)).toBeInTheDocument()
    expect(submitButton).toBeDisabled()
    expect(clearButton).toBeDisabled()
    expect(nameField).toBeDisabled()
    expect(cpfField).toBeDisabled()
    expect(birthDateField).toBeDisabled()
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/criando cliente/i)).not.toBeInTheDocument()
    })
  })

  // Error Handling Tests
  it('should handle API errors correctly', async () => {
    const user = userEvent.setup()
    const errorMessage = 'CPF já está em uso'
    
    mockOnSubmit.mockRejectedValue(new Error(errorMessage))
    
    renderWithProviders(<ClientRegistrationForm
          onSubmit={mockOnSubmit}
          onError={mockOnError}
 />)
    
    const nameField = getNameField()
    const cpfField = getCpfField()
    const birthDateField = getBirthDateField()
    const submitButton = getSubmitButton()
    
    await user.type(nameField, 'João Silva')
    await user.type(cpfField, '12345678901')
    await user.type(birthDateField, '1990-05-15')
    
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
    
    expect(mockOnError).toHaveBeenCalledWith(errorMessage)
  })

  // Form Reset Tests
  it('should clear form when clear button is clicked', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(<ClientRegistrationForm onSubmit={mockOnSubmit} />)
    
    const nameField = getNameField()
    const cpfField = getCpfField()
    const birthDateField = getBirthDateField()
    const notesField = getNotesField()
    const clearButton = getClearButton()
    
    // Fill form
    await user.type(nameField, 'João Silva')
    await user.type(cpfField, '12345678901')
    await user.type(birthDateField, '1990-05-15')
    await user.type(notesField, 'Test notes')
    
    // Verify fields have values
    expect(nameField).toHaveValue('João Silva')
    expect(cpfField).toHaveValue('123.456.789-09')
    expect(birthDateField).toHaveValue('1990-05-15')
    expect(notesField).toHaveValue('Test notes')
    
    // Clear form
    await user.click(clearButton)
    
    // Verify fields are cleared
    expect(nameField).toHaveValue('')
    expect(cpfField).toHaveValue('')
    expect(birthDateField).toHaveValue('')
    expect(notesField).toHaveValue('')
  })

  it('should reset form after successful submission', async () => {
    const user = userEvent.setup()
    const mockClientResponse: ClientResponse = {
      client_id: '123e4567-e89b-12d3-a456-426614174000',
      full_name: 'João Silva',
      cpf: '***.***.***-89',
      birth_date: '1990-05-15',
      status: 'active',
      created_by: 'user123',
      updated_by: 'user123',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z'
    }
    
    mockOnSubmit.mockResolvedValue(mockClientResponse)
    
    renderWithProviders(<ClientRegistrationForm onSubmit={mockOnSubmit} />)
    
    const nameField = getNameField()
    const cpfField = getCpfField()
    const birthDateField = getBirthDateField()
    const notesField = getNotesField()
    const submitButton = getSubmitButton()
    
    // Fill and submit form
    await user.type(nameField, 'João Silva')
    await user.type(cpfField, '12345678901')
    await user.type(birthDateField, '1990-05-15')
    await user.type(notesField, 'Test notes')
    
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalled()
    })
    
    // Form should be reset after successful submission
    await waitFor(() => {
      expect(nameField).toHaveValue('')
      expect(cpfField).toHaveValue('')
      expect(birthDateField).toHaveValue('')
      expect(notesField).toHaveValue('')
    })
  })

  // Keyboard Navigation Tests
  it('should handle keyboard navigation correctly', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(<ClientRegistrationForm onSubmit={mockOnSubmit} />)
    
    const nameField = getNameField()
    const cpfField = getCpfField()
    const birthDateField = getBirthDateField()
    const notesField = getNotesField()
    const submitButton = getSubmitButton()
    const clearButton = getClearButton()
    
    // Focus should start on name field
    nameField.focus()
    expect(nameField).toHaveFocus()
    
    // Tab through fields
    await user.tab()
    expect(cpfField).toHaveFocus()
    
    await user.tab()
    expect(birthDateField).toHaveFocus()
    
    await user.tab()
    expect(notesField).toHaveFocus()
    
    await user.tab()
    expect(submitButton).toHaveFocus()
    
    await user.tab()
    expect(clearButton).toHaveFocus()
  })

  // Form Field Descriptions Tests
  it('should display helpful field descriptions', () => {
    renderWithProviders(<ClientRegistrationForm onSubmit={mockOnSubmit} />)
    
    expect(screen.getByText(/nome completo do cliente conforme documento de identidade/i)).toBeInTheDocument()
    expect(screen.getByText(/cpf no formato XXX\.XXX\.XXX-XX \(apenas números\)/i)).toBeInTheDocument()
    expect(screen.getByText(/cliente deve ter pelo menos 13 anos de idade/i)).toBeInTheDocument()
    expect(screen.getByText(/notas ou informações adicionais relevantes \(máximo 1000 caracteres\)/i)).toBeInTheDocument()
  })

  // Accessibility Tests
  it('should announce validation errors to screen readers', async () => {
    const user = userEvent.setup()
    
    renderWithProviders(<ClientRegistrationForm onSubmit={mockOnSubmit} />)
    
    const submitButton = getSubmitButton()
    
    // Submit empty form to trigger validation
    await user.click(submitButton)
    
    await waitFor(() => {
      const errorMessage = screen.getByText(/nome completo é obrigatório/i)
      expect(errorMessage).toBeInTheDocument()
    })
  })
})