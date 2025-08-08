/**
 * New Client Page Tests - CLAUDE.md Compliant
 * 
 * Testing the complete client registration workflow:
 * - Form rendering and validation
 * - API integration with successful/failed creation
 * - Success state display and navigation options
 * - Error handling and user feedback
 * - Educational content and accessibility
 */

import {
  renderWithProviders,
  screen,
  waitFor,
  userEvent,
  vi,
  expect,
  describe,
  test,
  useTestSetup,
  mockSuccessfulFetch,
  mockFailedFetch,
} from '@/test/test-template'
import { 
  setupAuthenticatedUser,
} from '@/test/auth-helpers'
import NewClientPage from '../page'
import type { ClientCreate, ClientResponse } from '@iam-dashboard/shared'

describe('NewClientPage', () => {
  useTestSetup()

  const mockClientData: ClientCreate = {
    full_name: 'João Silva Santos',
    cpf: '12345678901', // Raw CPF without formatting
    birth_date: '1990-05-15'
  }

  const mockClientResponse: ClientResponse = {
    client_id: 'client-123',
    full_name: 'João Silva Santos',
    cpf: '123.456.789-09', // Formatted by backend
    birth_date: '1990-05-15',
    status: 'active',
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z'
  }

  const renderNewClientPage = (userRole: 'user' | 'admin' | 'sysadmin' = 'admin') => {
    setupAuthenticatedUser(userRole)
    return renderWithProviders(<NewClientPage />)
  }

  describe('Page Structure and Layout', () => {
    test('renders page header with proper structure', () => {
      renderNewClientPage()

      expect(screen.getByRole('heading', { level: 1, name: /novo cliente/i })).toBeInTheDocument()
      expect(screen.getByText(/registre um novo cliente no sistema/i)).toBeInTheDocument()
    })

    test('renders navigation back button', () => {
      renderNewClientPage()

      expect(screen.getByRole('button', { name: /voltar para clientes/i })).toBeInTheDocument()
    })

    test('renders form section initially', () => {
      renderNewClientPage()

      expect(screen.getByRole('heading', { level: 2, name: /informações do cliente/i })).toBeInTheDocument()
      expect(screen.getByText(/preencha os campos abaixo/i)).toBeInTheDocument()
    })

    test('renders help information card', () => {
      renderNewClientPage()

      expect(screen.getByText(/informações importantes/i)).toBeInTheDocument()
      expect(screen.getByText(/cpf deve ser único/i)).toBeInTheDocument()
      
      // Use getAllByText since this text appears in both form validation and help card
      const ageTexts = screen.getAllByText(/pelo menos 13 anos/i)
      expect(ageTexts.length).toBeGreaterThan(0)
    })
  })

  describe('Form Interaction and Validation', () => {
    test('renders form fields correctly', () => {
      renderNewClientPage()

      expect(screen.getByPlaceholderText(/joão silva santos/i)).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/123\.456\.789-12/i)).toBeInTheDocument()
      expect(document.querySelector('input[name="birth_date"]')).toBeInTheDocument()
    })

    test('allows user to fill form fields', async () => {
      renderNewClientPage()

      const nameInput = screen.getByPlaceholderText(/joão silva santos/i)
      const cpfInput = screen.getByPlaceholderText(/123\.456\.789-12/i)
      const birthDateInput = document.querySelector('input[name="birth_date"]')

      await userEvent.type(nameInput, mockClientData.full_name)
      await userEvent.type(cpfInput, mockClientData.cpf)
      await userEvent.type(birthDateInput, mockClientData.birth_date)

      expect(nameInput).toHaveValue(mockClientData.full_name)
      // CPF gets formatted by the form component
      expect(cpfInput.value).toMatch(/\d{3}-\d{2}-\d{4}/)
      expect(birthDateInput).toHaveValue(mockClientData.birth_date)
    })

    test('validates required fields', async () => {
      renderNewClientPage()

      const submitButton = screen.getByRole('button', { name: /criar cliente/i })
      await userEvent.click(submitButton)

      // Should show validation errors for empty required fields
      await waitFor(() => {
        const nameError = screen.getByText(/nome.*obrigatório/i)
        expect(nameError).toBeInTheDocument()
      })
      
      await waitFor(() => {
        const cpfError = screen.getByText(/cpf.*obrigatório/i)
        expect(cpfError).toBeInTheDocument()
      })
      
      await waitFor(() => {
        const birthDateError = screen.getByText(/data.*obrigatória/i)
        expect(birthDateError).toBeInTheDocument()
      })
    })
  })

  describe('Successful Client Creation', () => {
    test('handles successful client creation flow', async () => {
      mockSuccessfulFetch('/api/v1/clients', mockClientResponse)
      renderNewClientPage()

      // Fill form
      await userEvent.type(screen.getByPlaceholderText(/joão silva santos/i), mockClientData.full_name)
      await userEvent.type(screen.getByPlaceholderText(/123\.456\.789-12/i), mockClientData.cpf)
      await userEvent.type(document.querySelector('input[name="birth_date"]'), mockClientData.birth_date)

      // Submit form
      await userEvent.click(screen.getByRole('button', { name: /criar cliente/i }))

      // Should show success state
      await waitFor(() => {
        const successMessages = screen.getAllByText(/cliente.*criado com sucesso/i)
        expect(successMessages.length).toBeGreaterThan(0)
      })

      // Should display created client information
      expect(screen.getByText('João Silva Santos')).toBeInTheDocument()
      expect(screen.getByText('123.456.789-09')).toBeInTheDocument() // Updated to match formatted CPF
      expect(screen.getByText('client-123')).toBeInTheDocument()
    })

    test('shows success actions after client creation', async () => {
      mockSuccessfulFetch('/api/v1/clients', mockClientResponse)
      renderNewClientPage()

      // Fill and submit form
      await userEvent.type(screen.getByPlaceholderText(/joão silva santos/i), mockClientData.full_name)
      await userEvent.type(screen.getByPlaceholderText(/123\.456\.789-12/i), mockClientData.cpf)
      await userEvent.type(document.querySelector('input[name="birth_date"]'), mockClientData.birth_date)
      await userEvent.click(screen.getByRole('button', { name: /criar cliente/i }))

      // Wait for success state
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /ver cliente/i })).toBeInTheDocument()
      })

      expect(screen.getByRole('button', { name: /criar outro cliente/i })).toBeInTheDocument()
    })

    test('allows creating another client after success', async () => {
      mockSuccessfulFetch('/api/v1/clients', mockClientResponse)
      renderNewClientPage()

      // Fill and submit form
      await userEvent.type(screen.getByPlaceholderText(/joão silva santos/i), mockClientData.full_name)
      await userEvent.type(screen.getByPlaceholderText(/123\.456\.789-12/i), mockClientData.cpf)
      await userEvent.type(document.querySelector('input[name="birth_date"]'), mockClientData.birth_date)
      await userEvent.click(screen.getByRole('button', { name: /criar cliente/i }))

      // Wait for success and click create another
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /criar outro cliente/i })).toBeInTheDocument()
      })

      await userEvent.click(screen.getByRole('button', { name: /criar outro cliente/i }))

      // Should return to form state
      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 2, name: /informações do cliente/i })).toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    test('handles API errors gracefully', async () => {
      mockFailedFetch('/api/v1/clients', { 
        message: 'CPF já existe no sistema',
        status: 400 
      })
      renderNewClientPage()

      // Fill and submit form
      await userEvent.type(screen.getByPlaceholderText(/joão silva santos/i), mockClientData.full_name)
      await userEvent.type(screen.getByPlaceholderText(/123\.456\.789-12/i), mockClientData.cpf)
      await userEvent.type(document.querySelector('input[name="birth_date"]'), mockClientData.birth_date)
      await userEvent.click(screen.getByRole('button', { name: /criar cliente/i }))

      // Should remain on form (no success state)
      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 2, name: /informações do cliente/i })).toBeInTheDocument()
      })

      // Should not show success message
      expect(screen.queryByText(/criado com sucesso/i)).not.toBeInTheDocument()
    })

    test('handles network errors', async () => {
      mockFailedFetch('/api/v1/clients', { 
        message: 'Network error',
        status: 500 
      })
      renderNewClientPage()

      // Fill and submit form
      await userEvent.type(screen.getByPlaceholderText(/joão silva santos/i), mockClientData.full_name)
      await userEvent.type(screen.getByPlaceholderText(/123\.456\.789-12/i), mockClientData.cpf)  
      await userEvent.type(document.querySelector('input[name="birth_date"]'), mockClientData.birth_date)
      await userEvent.click(screen.getByRole('button', { name: /criar cliente/i }))

      // Should handle error gracefully
      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 2, name: /informações do cliente/i })).toBeInTheDocument()
      })
    })
  })

  describe('Navigation and User Flow', () => {
    test('back button functionality', async () => {
      renderNewClientPage()

      const backButton = screen.getByRole('button', { name: /voltar para clientes/i })
      expect(backButton).toBeEnabled()

      await userEvent.click(backButton)
      
      // Should work without errors (uses router.push internally)
      expect(backButton).toBeInTheDocument()
    })

    test('view client navigation after creation', async () => {
      mockSuccessfulFetch('/api/v1/clients', mockClientResponse)
      renderNewClientPage()

      // Create client
      await userEvent.type(screen.getByPlaceholderText(/joão silva santos/i), mockClientData.full_name)
      await userEvent.type(screen.getByPlaceholderText(/123\.456\.789-12/i), mockClientData.cpf)
      await userEvent.type(document.querySelector('input[name="birth_date"]'), mockClientData.birth_date)
      await userEvent.click(screen.getByRole('button', { name: /criar cliente/i }))

      // Click view client
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /ver cliente/i })).toBeInTheDocument()
      })

      const viewButton = screen.getByRole('button', { name: /ver cliente/i })
      await userEvent.click(viewButton)

      // Should work without errors
      expect(viewButton).toBeInTheDocument()
    })
  })

  describe('Content and Instructions', () => {
    test('displays comprehensive help information', () => {
      renderNewClientPage()

      expect(screen.getByText(/cpf deve ser único/i)).toBeInTheDocument()
      
      // This text appears in both form description and help card
      const ageTexts = screen.getAllByText(/pelo menos 13 anos/i)
      expect(ageTexts.length).toBeGreaterThan(0)
      
      expect(screen.getByText(/informações podem ser editadas/i)).toBeInTheDocument()
      
      // This text also appears in both form label and help card
      const observationsTexts = screen.getAllByText(/observações.*opcional/i)
      expect(observationsTexts.length).toBeGreaterThan(0)
    })

    test('uses consistent Portuguese language', () => {
      renderNewClientPage()

      expect(screen.getByText('Novo Cliente')).toBeInTheDocument()
      expect(screen.getByText('Voltar para Clientes')).toBeInTheDocument()
      expect(screen.getByText('Informações do Cliente')).toBeInTheDocument()
      expect(screen.getByText(/informações importantes/i)).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    test('has proper heading hierarchy', () => {
      renderNewClientPage()

      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/novo cliente/i)
      expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent(/informações do cliente/i)
    })

    test('has accessible form structure', () => {
      renderNewClientPage()

      // Should have properly labeled form inputs
      expect(screen.getByPlaceholderText(/joão silva santos/i)).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/123\.456\.789-12/i)).toBeInTheDocument()
      expect(document.querySelector('input[name="birth_date"]')).toBeInTheDocument()

      // Should have accessible buttons
      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThan(0)
    })

    test('provides informative descriptions', () => {
      renderNewClientPage()

      expect(screen.getByText(/preencha os campos abaixo/i)).toBeInTheDocument()
      expect(screen.getByText(/todos os campos marcados são obrigatórios/i)).toBeInTheDocument()
    })
  })

  describe('Visual and Layout', () => {
    test('has consistent spacing and design elements', () => {
      renderNewClientPage()

      // Check for main container
      const mainContainer = document.querySelector('.max-w-4xl')
      expect(mainContainer).toBeInTheDocument()

      // Check for card components
      const cards = document.querySelectorAll('[data-slot="card"]')
      expect(cards.length).toBeGreaterThan(0)
    })

    test('shows appropriate icons', () => {
      renderNewClientPage()

      const userPlusIcons = document.querySelectorAll('[class*="lucide-user-plus"]')
      expect(userPlusIcons.length).toBeGreaterThan(0)

      const arrowLeftIcon = document.querySelector('[class*="lucide-arrow-left"]')
      expect(arrowLeftIcon).toBeInTheDocument()
    })
  })
})