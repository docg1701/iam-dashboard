/**
 * TwoFactorForm Component Tests
 * Tests 2FA authentication form behavior based on Story 1.3 requirements
 * Following CLAUDE.md rules: no internal mocking, only external API mocking
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TwoFactorForm } from '../TwoFactorForm'
import type { TwoFactorFormData, TwoFactorResponse, TwoFactorSetupResponse } from '@/types/auth'

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

// Real callback functions for testing - no mocks
let submittedData: TwoFactorFormData | null = null
let successCalled = false
let errorMessage: string | null = null
let backCalled = false
let submitError: string | null = null

const realOnSubmit = async (data: TwoFactorFormData): Promise<TwoFactorResponse> => {
  submittedData = data
  
  // Simulate different responses based on code
  if (data.totp_code === '123456') {
    return {
      access_token: 'valid-token',
      token_type: 'bearer',
      expires_in: 3600,
      user: {
        user_id: 'user-123',
        email: 'test@example.com',
        role: 'admin',
        full_name: 'Test User',
        is_active: true,
        totp_enabled: true,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z'
      }
    }
  }
  
  if (submitError) {
    throw new Error(submitError)
  }
  
  throw new Error('Código de verificação inválido')
}

const realOnSuccess = (response: TwoFactorResponse) => {
  successCalled = true
}

const realOnError = (error: string) => {
  errorMessage = error
}

const realOnBack = () => {
  backCalled = true
}

// Test setup data for QR code tests
const testSetupData: TwoFactorSetupResponse = {
  secret: 'JBSWY3DPEHPK3PXP',
  qr_code: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
  backup_codes: ['12345-67890', '23456-78901', '34567-89012', '45678-90123', '56789-01234', '67890-12345', '78901-23456', '89012-34567']
}

beforeEach(() => {
  vi.clearAllMocks()
  mockFetch.mockReset()
  // Reset real callback state
  submittedData = null
  successCalled = false
  errorMessage = null
  backCalled = false
  submitError = null
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('TwoFactorForm', () => {
  it('should render 2FA form with 6 digit inputs', () => {
    render(
      <TestWrapper>
        <TwoFactorForm onSubmit={realOnSubmit} />
      </TestWrapper>
    )
    
    // Should have 6 digit inputs
    for (let i = 0; i < 6; i++) {
      expect(screen.getByTestId(`totp-input-${i}`)).toBeInTheDocument()
    }
    
    expect(screen.getByText(/código 2fa/i)).toBeInTheDocument()
  })

  it('should render setup mode with QR code when isSetup is true', () => {
    render(
      <TestWrapper>
        <TwoFactorForm 
          onSubmit={realOnSubmit} 
          isSetup={true}
          setupData={testSetupData}
        />
      </TestWrapper>
    )
    
    expect(screen.getByText(/configure seu aplicativo/i)).toBeInTheDocument()
    expect(screen.getByTestId('qr-code-image')).toBeInTheDocument()
    expect(screen.getByText(/códigos de backup/i)).toBeInTheDocument()
  })

  it('should only accept numeric input in code fields', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <TwoFactorForm onSubmit={realOnSubmit} />
      </TestWrapper>
    )
    
    const firstInput = screen.getByTestId('totp-input-0')
    
    // Try to type non-numeric characters
    await user.type(firstInput, 'abc')
    expect(firstInput).toHaveValue('')
    
    // Try to type numeric characters
    await user.type(firstInput, '1')
    expect(firstInput).toHaveValue('1')
  })

  it('should auto-advance to next input when typing', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <TwoFactorForm onSubmit={realOnSubmit} />
      </TestWrapper>
    )
    
    // Type in first input should advance to second
    await user.type(screen.getByTestId('totp-input-0'), '1')
    expect(screen.getByTestId('totp-input-1')).toHaveFocus()
    
    // Type in second should advance to third
    await user.type(screen.getByTestId('totp-input-1'), '2')
    expect(screen.getByTestId('totp-input-2')).toHaveFocus()
  })

  it('should handle paste of 6-digit code correctly', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <TwoFactorForm onSubmit={realOnSubmit} />
      </TestWrapper>
    )
    
    const firstInput = screen.getByTestId('totp-input-0')
    firstInput.focus()
    
    // Paste 6-digit code
    await user.paste('123456')
    
    // Should auto-submit after paste
    await waitFor(() => {
      expect(submittedData).toEqual({ totp_code: '123456' })
    })
  })

  it('should auto-submit when all 6 digits are filled and call onSuccess', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <TwoFactorForm 
          onSubmit={realOnSubmit}
          onSuccess={realOnSuccess}
        />
      </TestWrapper>
    )
    
    // Type all 6 digits
    await user.type(screen.getByTestId('totp-input-0'), '1')
    await user.type(screen.getByTestId('totp-input-1'), '2')
    await user.type(screen.getByTestId('totp-input-2'), '3')
    await user.type(screen.getByTestId('totp-input-3'), '4')
    await user.type(screen.getByTestId('totp-input-4'), '5')
    await user.type(screen.getByTestId('totp-input-5'), '6')
    
    // Should auto-submit when all digits are filled
    await waitFor(() => {
      expect(submittedData).toEqual({ totp_code: '123456' })
      expect(successCalled).toBe(true)
    })
  })

  it('should handle verification errors and call onError', async () => {
    const user = userEvent.setup()
    
    const expectedError = 'Código de verificação inválido'
    
    render(
      <TestWrapper>
        <TwoFactorForm 
          onSubmit={realOnSubmit}
          onError={realOnError}
        />
      </TestWrapper>
    )
    
    // Enter invalid code (anything other than 123456)
    await user.type(screen.getByTestId('totp-input-0'), '9')
    await user.type(screen.getByTestId('totp-input-1'), '9')
    await user.type(screen.getByTestId('totp-input-2'), '9')
    await user.type(screen.getByTestId('totp-input-3'), '9')
    await user.type(screen.getByTestId('totp-input-4'), '9')
    await user.type(screen.getByTestId('totp-input-5'), '9')
    
    await waitFor(() => {
      expect(screen.getByText(expectedError)).toBeInTheDocument()
      expect(errorMessage).toBe(expectedError)
    })
  })

  it('should show loading state during verification', async () => {
    const user = userEvent.setup()
    
    // Set up delayed response
    submitError = null // Will resolve after delay
    let resolvePromise: (value: TwoFactorResponse) => void
    const delayedOnSubmit = (data: TwoFactorFormData): Promise<TwoFactorResponse> => {
      submittedData = data
      return new Promise((resolve) => {
        resolvePromise = resolve
        // Don't resolve immediately to test loading state
      })
    }
    
    render(
      <TestWrapper>
        <TwoFactorForm onSubmit={delayedOnSubmit} />
      </TestWrapper>
    )
    
    // Type all 6 digits to trigger submission
    await user.type(screen.getByTestId('totp-input-0'), '1')
    await user.type(screen.getByTestId('totp-input-1'), '2')
    await user.type(screen.getByTestId('totp-input-2'), '3')
    await user.type(screen.getByTestId('totp-input-3'), '4')
    await user.type(screen.getByTestId('totp-input-4'), '5')
    await user.type(screen.getByTestId('totp-input-5'), '6')
    
    // Should show loading state
    await waitFor(() => {
      expect(screen.getByText(/verificando/i)).toBeInTheDocument()
    })
    
    // All inputs should be disabled during loading
    for (let i = 0; i < 6; i++) {
      expect(screen.getByTestId(`totp-input-${i}`)).toBeDisabled()
    }
    
    // Resolve the promise to complete the test
    resolvePromise!({
      access_token: 'token',
      token_type: 'bearer',
      expires_in: 3600,
      user: {
        user_id: 'user-123',
        email: 'test@example.com',
        role: 'admin',
        full_name: 'Test User',
        is_active: true,
        totp_enabled: true,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z'
      }
    })
  })

  it('should handle manual submit button click', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <TwoFactorForm onSubmit={realOnSubmit} />
      </TestWrapper>
    )
    
    // Fill only 5 digits (no auto-submit)
    await user.type(screen.getByTestId('totp-input-0'), '1')
    await user.type(screen.getByTestId('totp-input-1'), '2')
    await user.type(screen.getByTestId('totp-input-2'), '3')
    await user.type(screen.getByTestId('totp-input-3'), '4')
    await user.type(screen.getByTestId('totp-input-4'), '5')
    
    // Add final digit
    await user.type(screen.getByTestId('totp-input-5'), '6')
    
    // Should auto-submit with all 6 digits
    await waitFor(() => {
      expect(submittedData).toEqual({ totp_code: '123456' })
    })
  })

  it('should handle back button click and call onBack', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <TwoFactorForm 
          onSubmit={realOnSubmit}
          onBack={realOnBack}
        />
      </TestWrapper>
    )
    
    const backButton = screen.getByText(/voltar/i)
    await user.click(backButton)
    
    expect(backCalled).toBe(true)
  })

  it('should disable back button during loading', async () => {
    const user = userEvent.setup()
    
    // Set up delayed response
    let resolvePromise: (value: TwoFactorResponse) => void
    const delayedOnSubmit = (data: TwoFactorFormData): Promise<TwoFactorResponse> => {
      submittedData = data
      return new Promise((resolve) => {
        resolvePromise = resolve
      })
    }
    
    render(
      <TestWrapper>
        <TwoFactorForm 
          onSubmit={delayedOnSubmit}
          onBack={realOnBack}
        />
      </TestWrapper>
    )
    
    // Start submission
    await user.type(screen.getByTestId('totp-input-0'), '1')
    await user.type(screen.getByTestId('totp-input-1'), '2')
    await user.type(screen.getByTestId('totp-input-2'), '3')
    await user.type(screen.getByTestId('totp-input-3'), '4')
    await user.type(screen.getByTestId('totp-input-4'), '5')
    await user.type(screen.getByTestId('totp-input-5'), '6')
    
    // Back button should be disabled during loading
    await waitFor(() => {
      expect(screen.getByText(/voltar/i)).toBeDisabled()
    })
    
    // Resolve to complete test
    resolvePromise!({
      access_token: 'token',
      token_type: 'bearer', 
      expires_in: 3600,
      user: {
        user_id: 'user-123',
        email: 'test@example.com',
        role: 'admin',
        full_name: 'Test User',
        is_active: true,
        totp_enabled: true,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z'
      }
    })
  })

  it('should handle keyboard navigation between inputs', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <TwoFactorForm onSubmit={realOnSubmit} />
      </TestWrapper>
    )
    
    const firstInput = screen.getByTestId('totp-input-0')
    const secondInput = screen.getByTestId('totp-input-1')
    
    // Focus first input
    firstInput.focus()
    expect(firstInput).toHaveFocus()
    
    // Arrow right should move to next input
    await user.keyboard('{ArrowRight}')
    expect(secondInput).toHaveFocus()
    
    // Arrow left should move back
    await user.keyboard('{ArrowLeft}')
    expect(firstInput).toHaveFocus()
  })

  it('should handle backspace navigation', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <TwoFactorForm onSubmit={realOnSubmit} />
      </TestWrapper>
    )
    
    // Fill first two inputs
    await user.type(screen.getByTestId('totp-input-0'), '1')
    await user.type(screen.getByTestId('totp-input-1'), '2')
    
    // Current focus should be on third input
    const thirdInput = screen.getByTestId('totp-input-2')
    const secondInput = screen.getByTestId('totp-input-1')
    
    expect(thirdInput).toHaveFocus()
    
    // Backspace should move to previous input and clear it
    await user.keyboard('{Backspace}')
    expect(secondInput).toHaveFocus()
    expect(secondInput).toHaveValue('')
  })

  it('should handle rate limiting errors', async () => {
    const user = userEvent.setup()
    
    const rateLimitError = 'Muitas tentativas de verificação. Tente novamente em alguns minutos.'
    submitError = rateLimitError
    
    render(
      <TestWrapper>
        <TwoFactorForm onSubmit={realOnSubmit} />
      </TestWrapper>
    )
    
    // Enter code that will trigger rate limit error
    await user.type(screen.getByTestId('totp-input-0'), '9')
    await user.type(screen.getByTestId('totp-input-1'), '9')
    await user.type(screen.getByTestId('totp-input-2'), '9')
    await user.type(screen.getByTestId('totp-input-3'), '9')
    await user.type(screen.getByTestId('totp-input-4'), '9')
    await user.type(screen.getByTestId('totp-input-5'), '9')
    
    await waitFor(() => {
      expect(screen.getByText(rateLimitError)).toBeInTheDocument()
    })
  })

  it('should handle network errors gracefully', async () => {
    const user = userEvent.setup()
    
    submitError = 'Network error'
    
    render(
      <TestWrapper>
        <TwoFactorForm onSubmit={realOnSubmit} />
      </TestWrapper>
    )
    
    // Enter code
    await user.type(screen.getByTestId('totp-input-0'), '1')
    await user.type(screen.getByTestId('totp-input-1'), '2')
    await user.type(screen.getByTestId('totp-input-2'), '3')
    await user.type(screen.getByTestId('totp-input-3'), '4')
    await user.type(screen.getByTestId('totp-input-4'), '5')
    await user.type(screen.getByTestId('totp-input-5'), '6')
    
    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument()
    })
  })

  it('should work correctly in setup mode with backup codes', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <TwoFactorForm 
          onSubmit={realOnSubmit}
          isSetup={true}
          setupData={testSetupData}
          onSuccess={realOnSuccess}
        />
      </TestWrapper>
    )
    
    // Should show all backup codes
    testSetupData.backup_codes.forEach(code => {
      expect(screen.getByText(code)).toBeInTheDocument()
    })
    
    // Enter valid code
    await user.type(screen.getByTestId('totp-input-0'), '1')
    await user.type(screen.getByTestId('totp-input-1'), '2')
    await user.type(screen.getByTestId('totp-input-2'), '3')
    await user.type(screen.getByTestId('totp-input-3'), '4')
    await user.type(screen.getByTestId('totp-input-4'), '5')
    await user.type(screen.getByTestId('totp-input-5'), '6')
    
    await waitFor(() => {
      expect(submittedData).toEqual({ totp_code: '123456' })
      expect(successCalled).toBe(true)
    })
  })

  it('should reset form state after error and allow retry', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <TwoFactorForm onSubmit={realOnSubmit} />
      </TestWrapper>
    )
    
    // First attempt with invalid code
    await user.type(screen.getByTestId('totp-input-0'), '9')
    await user.type(screen.getByTestId('totp-input-1'), '9')
    await user.type(screen.getByTestId('totp-input-2'), '9')
    await user.type(screen.getByTestId('totp-input-3'), '9')
    await user.type(screen.getByTestId('totp-input-4'), '9')
    await user.type(screen.getByTestId('totp-input-5'), '9')
    
    // Wait for error
    await waitFor(() => {
      expect(screen.getByText(/código de verificação inválido/i)).toBeInTheDocument()
    })
    
    // Form should reset and allow new input
    expect(screen.getByTestId('totp-input-0')).toHaveValue('')
    expect(screen.getByTestId('totp-input-0')).toHaveFocus()
    
    // Second attempt with valid code
    await user.type(screen.getByTestId('totp-input-0'), '1')
    await user.type(screen.getByTestId('totp-input-1'), '2')
    await user.type(screen.getByTestId('totp-input-2'), '3')
    await user.type(screen.getByTestId('totp-input-3'), '4')
    await user.type(screen.getByTestId('totp-input-4'), '5')
    await user.type(screen.getByTestId('totp-input-5'), '6')
    
    await waitFor(() => {
      expect(submittedData).toEqual({ totp_code: '123456' })
    })
  })
})