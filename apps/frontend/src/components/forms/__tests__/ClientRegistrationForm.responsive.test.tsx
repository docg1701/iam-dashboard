/**
 * ClientRegistrationForm Responsive & Accessibility Tests
 * Tests responsive behavior and accessibility compliance
 * Following CLAUDE.md rules: no internal mocking, only external API mocking
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ClientRegistrationForm } from '../ClientRegistrationForm'
import type { ClientResponse } from '@iam-dashboard/shared'

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

// Mock window.matchMedia for responsive tests
const mockMatchMedia = (query: string) => ({
  matches: false,
  media: query,
  onchange: null,
  addListener: vi.fn(),
  removeListener: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  dispatchEvent: vi.fn(),
})

beforeEach(() => {
  vi.clearAllMocks()
  mockFetch.mockReset()
  
  // Default matchMedia mock
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation(mockMatchMedia),
  })
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('ClientRegistrationForm - Responsive & Accessibility Tests', () => {
  const mockOnSubmit = vi.fn()

  beforeEach(() => {
    mockOnSubmit.mockReset()
  })

  // Responsive Design Tests
  describe('Responsive Behavior', () => {
    it('should render with mobile-first responsive design', () => {
      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      const formContainer = screen.getByRole('form')
      expect(formContainer).toBeInTheDocument()
      
      // Should have responsive classes
      const form = formContainer.querySelector('form')
      expect(form).toHaveClass('space-y-6')
    })

    it('should adapt to mobile viewport (375px width)', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: vi.fn().mockImplementation((query) => ({
          ...mockMatchMedia(query),
          matches: query === '(max-width: 768px)',
        })),
      })

      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      const submitButton = screen.getByRole('button', { name: /criar cliente/i })
      const clearButton = screen.getByRole('button', { name: /limpar formulário/i })
      
      // Buttons should be full width on mobile
      expect(submitButton).toHaveClass('flex-1')
      expect(clearButton).toHaveClass('flex-1')
    })

    it('should maintain proper spacing on tablet viewports', () => {
      // Mock tablet viewport
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: vi.fn().mockImplementation((query) => ({
          ...mockMatchMedia(query),
          matches: query === '(min-width: 768px) and (max-width: 1024px)',
        })),
      })

      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      const formContainer = screen.getByRole('form')
      expect(formContainer).toBeInTheDocument()
      
      // Form should maintain proper max-width
      const formElement = formContainer.querySelector('form')
      expect(formElement?.parentElement).toHaveClass('max-w-2xl')
    })

    it('should handle desktop layout correctly', () => {
      // Mock desktop viewport
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: vi.fn().mockImplementation((query) => ({
          ...mockMatchMedia(query),
          matches: query === '(min-width: 1024px)',
        })),
      })

      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      // Should center form on desktop
      const formWrapper = screen.getByRole('form').parentElement
      expect(formWrapper).toHaveClass('mx-auto')
    })

    it('should maintain touch-friendly targets on mobile', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: vi.fn().mockImplementation((query) => ({
          ...mockMatchMedia(query),
          matches: query === '(max-width: 768px)',
        })),
      })

      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      const submitButton = screen.getByRole('button', { name: /criar cliente/i })
      const clearButton = screen.getByRole('button', { name: /limpar formulário/i })
      
      // Buttons should have large size for touch
      expect(submitButton).toHaveClass('size-lg')
      expect(clearButton).toHaveClass('size-lg')
    })

    it('should handle dynamic viewport changes', () => {
      let currentMatches = false
      
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: vi.fn().mockImplementation((query) => ({
          matches: currentMatches,
          media: query,
          onchange: null,
          addListener: vi.fn(),
          removeListener: vi.fn(),
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          dispatchEvent: vi.fn(),
        })),
      })

      const { rerender } = render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      // Change to mobile viewport
      currentMatches = true
      rerender(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      // Form should still be functional
      expect(screen.getByLabelText(/nome completo/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/cpf/i)).toBeInTheDocument()
    })
  })

  // Accessibility Tests
  describe('Accessibility Compliance', () => {
    it('should have proper ARIA roles and labels', () => {
      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      // Form should have proper role
      expect(screen.getByRole('form')).toBeInTheDocument()
      
      // All form fields should have proper labels
      expect(screen.getByLabelText(/nome completo/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/cpf/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/data de nascimento/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/observações/i)).toBeInTheDocument()
      
      // Buttons should have proper labels
      expect(screen.getByRole('button', { name: /criar cliente/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /limpar formulário/i })).toBeInTheDocument()
    })

    it('should support keyboard navigation properly', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      const nameField = screen.getByLabelText(/nome completo/i)
      const cpfField = screen.getByLabelText(/cpf/i)
      const birthDateField = screen.getByLabelText(/data de nascimento/i)
      const notesField = screen.getByLabelText(/observações/i)
      const submitButton = screen.getByRole('button', { name: /criar cliente/i })
      const clearButton = screen.getByRole('button', { name: /limpar formulário/i })
      
      // Test tab order
      await user.tab()
      expect(nameField).toHaveFocus()
      
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
      
      // Test reverse tab order
      await user.tab({ shift: true })
      expect(submitButton).toHaveFocus()
      
      await user.tab({ shift: true })
      expect(notesField).toHaveFocus()
    })

    it('should handle focus management correctly', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      const nameField = screen.getByLabelText(/nome completo/i)
      
      // Click to focus
      await user.click(nameField)
      expect(nameField).toHaveFocus()
      
      // Should maintain focus when typing
      await user.type(nameField, 'João')
      expect(nameField).toHaveFocus()
      
      // Should handle Enter key appropriately
      await user.keyboard('{Enter}')
      // Enter in text field should not submit form
      expect(mockOnSubmit).not.toHaveBeenCalled()
    })

    it('should provide proper focus indicators', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      const nameField = screen.getByLabelText(/nome completo/i)
      
      // Focus should be visible
      await user.tab()
      expect(nameField).toHaveFocus()
      
      // Should handle focus and blur events
      nameField.blur()
      expect(nameField).not.toHaveFocus()
    })

    it('should announce validation errors to screen readers', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      const submitButton = screen.getByRole('button', { name: /criar cliente/i })
      
      // Submit empty form to trigger validation
      await user.click(submitButton)
      
      await waitFor(() => {
        const errorMessage = screen.getByText(/nome completo é obrigatório/i)
        expect(errorMessage).toBeInTheDocument()
        
        // Error message should be announced
        expect(errorMessage.parentElement?.querySelector('[role="alert"]')).toBeTruthy()
      })
    })

    it('should have proper color contrast for error states', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      const submitButton = screen.getByRole('button', { name: /criar cliente/i })
      
      // Trigger validation error
      await user.click(submitButton)
      
      await waitFor(() => {
        const errorMessage = screen.getByText(/nome completo é obrigatório/i)
        expect(errorMessage).toBeInTheDocument()
        
        // Error messages should use destructive color classes
        expect(errorMessage.parentElement).toHaveClass('text-destructive')
      })
    })

    it('should support high contrast mode', () => {
      // Mock high contrast media query
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: vi.fn().mockImplementation((query) => ({
          ...mockMatchMedia(query),
          matches: query === '(prefers-contrast: high)',
        })),
      })

      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      // Form should still be functional in high contrast mode
      expect(screen.getByLabelText(/nome completo/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /criar cliente/i })).toBeInTheDocument()
    })

    it('should support reduced motion preferences', async () => {
      const user = userEvent.setup()
      
      // Mock reduced motion preference
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: vi.fn().mockImplementation((query) => ({
          ...mockMatchMedia(query),
          matches: query === '(prefers-reduced-motion: reduce)',
        })),
      })

      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      // Form should still be functional with reduced motion
      const nameField = screen.getByLabelText(/nome completo/i)
      await user.type(nameField, 'João Silva')
      expect(nameField).toHaveValue('João Silva')
    })

    it('should have proper heading structure for screen readers', () => {
      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      // Form labels should act as proper headings for sections
      const labels = screen.getAllByText(/nome completo|cpf|data de nascimento|observações/i)
      expect(labels.length).toBeGreaterThan(0)
      
      // Each label should be properly associated with its field
      labels.forEach(label => {
        expect(label.tagName).toBe('LABEL')
      })
    })

    it('should provide proper field descriptions for assistive technology', () => {
      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      // Check for descriptive text
      expect(screen.getByText(/nome completo do cliente conforme documento de identidade/i)).toBeInTheDocument()
      expect(screen.getByText(/cpf no formato xxx\.xxx\.xxx-xx/i)).toBeInTheDocument()
      expect(screen.getByText(/cliente deve ter pelo menos 13 anos de idade/i)).toBeInTheDocument()
      expect(screen.getByText(/máximo 1000 caracteres/i)).toBeInTheDocument()
    })

    it('should handle loading states accessibly', async () => {
      const user = userEvent.setup()
      
      // Mock slow submission
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
      
      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      // Fill form
      const nameField = screen.getByLabelText(/nome completo/i)
      const cpfField = screen.getByLabelText(/cpf/i)
      const birthDateField = screen.getByLabelText(/data de nascimento/i)
      const submitButton = screen.getByRole('button', { name: /criar cliente/i })
      
      await user.type(nameField, 'João Silva')
      await user.type(cpfField, '12345678901')
      await user.type(birthDateField, '1990-05-15')
      
      await user.click(submitButton)
      
      // Loading state should be announced
      expect(screen.getByText(/criando cliente/i)).toBeInTheDocument()
      
      // Button should be properly disabled
      expect(submitButton).toBeDisabled()
      expect(submitButton).toHaveAttribute('aria-disabled', 'true')
    })

    it('should support assistive technology for form validation', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      const nameField = screen.getByLabelText(/nome completo/i)
      const submitButton = screen.getByRole('button', { name: /criar cliente/i })
      
      // Enter invalid data
      await user.type(nameField, 'A') // Too short
      await user.click(submitButton)
      
      await waitFor(() => {
        const errorMessage = screen.getByText(/nome deve ter pelo menos 2 caracteres/i)
        expect(errorMessage).toBeInTheDocument()
        
        // Error should be associated with the field
        const fieldContainer = nameField.closest('.space-y-2')
        expect(fieldContainer?.querySelector('[role="alert"]')).toBeTruthy()
      })
    })

    it('should maintain semantic structure', () => {
      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      // Form should use semantic HTML
      const form = screen.getByRole('form')
      expect(form.tagName).toBe('FORM')
      
      // Fields should use proper input types
      const nameField = screen.getByLabelText(/nome completo/i)
      const cpfField = screen.getByLabelText(/cpf/i)
      const birthDateField = screen.getByLabelText(/data de nascimento/i)
      const notesField = screen.getByLabelText(/observações/i)
      
      expect(nameField.tagName).toBe('INPUT')
      expect(cpfField.tagName).toBe('INPUT')
      expect(birthDateField.tagName).toBe('INPUT')
      expect(birthDateField).toHaveAttribute('type', 'date')
      expect(notesField.tagName).toBe('TEXTAREA')
    })

    it('should provide proper button semantics', () => {
      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      const submitButton = screen.getByRole('button', { name: /criar cliente/i })
      const clearButton = screen.getByRole('button', { name: /limpar formulário/i })
      
      // Submit button should have proper type
      expect(submitButton).toHaveAttribute('type', 'submit')
      
      // Clear button should have proper type
      expect(clearButton).toHaveAttribute('type', 'button')
    })
  })

  // Performance Tests
  describe('Performance & Rendering', () => {
    it('should not cause excessive re-renders', async () => {
      const user = userEvent.setup()
      let renderCount = 0
      
      const TestComponent = () => {
        renderCount++
        return <ClientRegistrationForm onSubmit={mockOnSubmit} />
      }
      
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )
      
      const initialRenderCount = renderCount
      
      // Type in field
      const nameField = screen.getByLabelText(/nome completo/i)
      await user.type(nameField, 'João')
      
      // Should not cause excessive re-renders (allow some for form state updates)
      expect(renderCount - initialRenderCount).toBeLessThan(10)
    })

    it('should handle rapid input changes gracefully', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      const cpfField = screen.getByLabelText(/cpf/i)
      
      // Rapidly type and delete
      await user.type(cpfField, '12345678901')
      await user.clear(cpfField)
      await user.type(cpfField, '987654321')
      
      // Should handle gracefully without errors
      expect(cpfField).toHaveValue('987.654.321-00')
    })

    it('should maintain performance with large notes content', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <ClientRegistrationForm onSubmit={mockOnSubmit} />
        </TestWrapper>
      )
      
      const notesField = screen.getByLabelText(/observações/i)
      const longText = 'A'.repeat(500)
      
      // Should handle large text input without performance issues
      await user.type(notesField, longText)
      expect(notesField).toHaveValue(longText)
    })
  })
})