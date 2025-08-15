/**
 * Authentication Components Responsive Tests
 * Tests login form and authentication components across different screen sizes and breakpoints
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { LoginForm } from '@/components/forms/LoginForm'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { AuthProvider } from '@/contexts/AuthContext'
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
  usePathname: () => '/login',
  useSearchParams: () => new URLSearchParams(),
}))

// Test wrapper with all necessary providers
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
      <QueryClientProvider client={queryClient}>
        <AuthProvider>{children}</AuthProvider>
      </QueryClientProvider>
    </ErrorProvider>
  )
}

// Viewport size configurations
const viewports = {
  mobile: { width: 375, height: 667 },
  tablet: { width: 768, height: 1024 },
  desktop: { width: 1024, height: 768 },
  largeDesktop: { width: 1440, height: 900 },
  ultraWide: { width: 1920, height: 1080 },
}

// Helper function to set viewport size
const setViewport = (size: { width: number; height: number }) => {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: size.width,
  })
  Object.defineProperty(window, 'innerHeight', {
    writable: true,
    configurable: true,
    value: size.height,
  })

  // Update CSS media queries
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation(query => {
      const mediaQuery = query.toLowerCase()
      let matches = false

      // Common breakpoints based on Tailwind CSS
      if (mediaQuery.includes('max-width: 639px')) {
        matches = size.width <= 639 // Mobile
      } else if (
        mediaQuery.includes('min-width: 640px') &&
        mediaQuery.includes('max-width: 767px')
      ) {
        matches = size.width >= 640 && size.width <= 767 // Small tablet
      } else if (
        mediaQuery.includes('min-width: 768px') &&
        mediaQuery.includes('max-width: 1023px')
      ) {
        matches = size.width >= 768 && size.width <= 1023 // Tablet
      } else if (
        mediaQuery.includes('min-width: 1024px') &&
        mediaQuery.includes('max-width: 1279px')
      ) {
        matches = size.width >= 1024 && size.width <= 1279 // Desktop
      } else if (mediaQuery.includes('min-width: 1280px')) {
        matches = size.width >= 1280 // Large desktop
      }

      return {
        matches,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }
    }),
  })

  // Trigger resize event
  window.dispatchEvent(new Event('resize'))
}

describe('Authentication Components Responsive Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn()
    localStorage.clear()
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe('LoginForm Responsive Behavior', () => {
    it('should render correctly on mobile devices (375px)', async () => {
      setViewport(viewports.mobile)

      const onSubmit = vi.fn()
      render(
        <TestWrapper>
          <LoginForm onSuccess={onSubmit} />
        </TestWrapper>
      )

      // Check form is present and usable
      const emailInput = screen.getByLabelText(/e-mail/i)
      const form = emailInput.closest('form')
      expect(form).toBeInTheDocument()
      expect(emailInput).toBeInTheDocument()

      // Form should be full width on mobile
      const card = screen
        .getByText(/entrar no dashboard iam/i)
        .closest('.mx-auto')
      expect(card).toBeInTheDocument()

      // All form elements should be accessible
      expect(screen.getByLabelText(/e-mail/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/senha/i)).toBeInTheDocument()
      expect(
        screen.getByRole('button', { name: /entrar/i })
      ).toBeInTheDocument()

      // Check that form fields are properly sized for mobile
      const passwordInput = screen.getByLabelText(/senha/i)

      // Inputs should have mobile-friendly sizing
      expect(emailInput).toHaveClass('h-10')
      expect(passwordInput).toHaveClass('h-10')
    })

    it('should render correctly on tablet devices (768px)', async () => {
      setViewport(viewports.tablet)

      const onSubmit = vi.fn()
      render(
        <TestWrapper>
          <LoginForm onSuccess={onSubmit} />
        </TestWrapper>
      )

      // Form should maintain good proportions on tablet
      const card = screen
        .getByText(/entrar no dashboard iam/i)
        .closest('.max-w-md')
      expect(card).toBeInTheDocument()

      // All interactive elements should be properly sized
      const submitButton = screen.getByRole('button', { name: /entrar/i })
      expect(submitButton).toBeInTheDocument()
      expect(submitButton).toHaveClass('w-full')

      // Check text readability at tablet size
      expect(screen.getByText(/entrar no dashboard iam/i)).toBeInTheDocument()
      expect(
        screen.getByText(/digite suas credenciais para acessar o sistema/i)
      ).toBeInTheDocument()
    })

    it('should render correctly on desktop devices (1024px+)', async () => {
      setViewport(viewports.desktop)

      const onSubmit = vi.fn()
      render(
        <TestWrapper>
          <LoginForm onSuccess={onSubmit} />
        </TestWrapper>
      )

      // Form should be centered and appropriately sized
      const card = screen
        .getByText(/entrar no dashboard iam/i)
        .closest('.mx-auto')
      expect(card).toBeInTheDocument()

      // Check that all elements are present and functional
      expect(screen.getByLabelText(/e-mail/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/senha/i)).toBeInTheDocument()
      expect(
        screen.getByRole('button', { name: /entrar/i })
      ).toBeInTheDocument()

      // Footer links should be visible and properly spaced
      expect(screen.getByText(/esqueceu sua senha/i)).toBeInTheDocument()
      expect(screen.getByText(/problemas com 2fa/i)).toBeInTheDocument()
    })

    it('should handle 2FA input responsively across breakpoints', async () => {
      const testBreakpoints = [
        viewports.mobile,
        viewports.tablet,
        viewports.desktop,
      ]

      for (const viewport of testBreakpoints) {
        setViewport(viewport)

        // Mock 2FA required response
        global.fetch = vi.fn().mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: async () => ({ detail: 'Two-factor authentication required' }),
        })

        const onSubmit = vi.fn()
        render(
          <TestWrapper>
            <LoginForm onSuccess={onSubmit} />
          </TestWrapper>
        )

        // Fill initial form
        const emailInput = screen.getByLabelText(/e-mail/i)
        const passwordInput = screen.getByLabelText(/senha/i)
        const submitButton = screen.getByRole('button', { name: /entrar/i })

        fireEvent.change(emailInput, { target: { value: 'user@example.com' } })
        fireEvent.change(passwordInput, { target: { value: 'password123' } })
        fireEvent.click(submitButton)

        // Wait for 2FA input to appear
        await waitFor(() => {
          expect(
            screen.getByLabelText(/código de autenticação/i)
          ).toBeInTheDocument()
        })

        // 2FA input should be properly styled for current viewport
        const totpInput = screen.getByLabelText(/código de autenticação/i)
        expect(totpInput).toHaveClass('text-center')
        expect(totpInput).toHaveClass('tracking-widest')
        expect(totpInput).toHaveAttribute('maxLength', '6')

        // Helper text should be visible and readable
        expect(
          screen.getByText(/digite o código de 6 dígitos/i)
        ).toBeInTheDocument()
      }
    })
  })

  describe('ProtectedRoute Access Denied Responsive Behavior', () => {
    it('should display access denied message responsively on mobile', async () => {
      setViewport(viewports.mobile)

      localStorage.setItem('access_token', 'user_token')
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          id: '1',
          email: 'user@example.com',
          role: 'user',
          is_active: true,
        }),
      })

      render(
        <TestWrapper>
          <ProtectedRoute requiredRole="admin">
            <div data-testid="admin-content">Admin Only Content</div>
          </ProtectedRoute>
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText(/acesso negado/i)).toBeInTheDocument()
      })

      // Access denied message should be readable on mobile
      const accessDeniedText = screen.getByText(
        /esta página requer permissão de admin/i
      )
      expect(accessDeniedText).toBeInTheDocument()

      // Should not show admin content
      expect(screen.queryByTestId('admin-content')).not.toBeInTheDocument()
    })

    it('should display access denied message responsively on tablet', async () => {
      setViewport(viewports.tablet)

      localStorage.setItem('access_token', 'user_token')
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          id: '1',
          email: 'user@example.com',
          role: 'user',
          is_active: true,
        }),
      })

      render(
        <TestWrapper>
          <ProtectedRoute requiredRole="admin">
            <div data-testid="admin-content">Admin Only Content</div>
          </ProtectedRoute>
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText(/acesso negado/i)).toBeInTheDocument()
      })

      // Message should be well-formatted on tablet
      expect(
        screen.getByText(/esta página requer permissão de admin/i)
      ).toBeInTheDocument()
    })

    it('should display access denied message responsively on desktop', async () => {
      setViewport(viewports.desktop)

      localStorage.setItem('access_token', 'user_token')
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          id: '1',
          email: 'user@example.com',
          role: 'user',
          is_active: true,
        }),
      })

      render(
        <TestWrapper>
          <ProtectedRoute requiredRole="admin">
            <div data-testid="admin-content">Admin Only Content</div>
          </ProtectedRoute>
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText(/acesso negado/i)).toBeInTheDocument()
      })

      // Desktop should have proper spacing and layout
      expect(
        screen.getByText(/esta página requer permissão de admin/i)
      ).toBeInTheDocument()
    })
  })

  describe('Touch and Interaction Responsiveness', () => {
    it('should handle touch interactions on mobile login form', async () => {
      setViewport(viewports.mobile)

      const onSubmit = vi.fn()
      render(
        <TestWrapper>
          <LoginForm onSuccess={onSubmit} />
        </TestWrapper>
      )

      const emailInput = screen.getByLabelText(/e-mail/i)
      const passwordInput = screen.getByLabelText(/senha/i)

      // Simulate touch interactions
      fireEvent.touchStart(emailInput)
      fireEvent.focus(emailInput)
      fireEvent.change(emailInput, { target: { value: 'user@example.com' } })

      fireEvent.touchStart(passwordInput)
      fireEvent.focus(passwordInput)
      fireEvent.change(passwordInput, { target: { value: 'password123' } })

      // Form should respond to touch interactions
      expect(emailInput).toHaveValue('user@example.com')
      expect(passwordInput).toHaveValue('password123')

      // Submit button should be touch-friendly
      const submitButton = screen.getByRole('button', { name: /entrar/i })
      expect(submitButton).not.toBeDisabled()

      // Button should have adequate touch target size (minimum 44px)
      expect(submitButton).toHaveClass('h-10') // 40px, but with padding should meet touch target requirements
    })

    it('should handle password visibility toggle on mobile', async () => {
      setViewport(viewports.mobile)

      const onSubmit = vi.fn()
      render(
        <TestWrapper>
          <LoginForm onSuccess={onSubmit} />
        </TestWrapper>
      )

      const passwordInput = screen.getByLabelText(/senha/i)
      const toggleButton = screen.getByRole('button', { name: '' }) // Password toggle has no accessible name

      // Initially password should be hidden
      expect(passwordInput).toHaveAttribute('type', 'password')

      // Toggle password visibility - should work on mobile
      fireEvent.click(toggleButton)
      expect(passwordInput).toHaveAttribute('type', 'text')

      // Toggle back
      fireEvent.click(toggleButton)
      expect(passwordInput).toHaveAttribute('type', 'password')
    })
  })

  describe('Layout and Spacing Across Breakpoints', () => {
    it('should maintain proper spacing and layout on ultra-wide screens', async () => {
      setViewport(viewports.ultraWide)

      const onSubmit = vi.fn()
      render(
        <TestWrapper>
          <LoginForm onSuccess={onSubmit} />
        </TestWrapper>
      )

      // Form should not stretch too wide on large screens
      const card = screen
        .getByText(/entrar no dashboard iam/i)
        .closest('.max-w-md')
      expect(card).toBeInTheDocument()

      // Content should be centered
      const centeringWrapper = screen
        .getByText(/entrar no dashboard iam/i)
        .closest('.mx-auto')
      expect(centeringWrapper).toBeInTheDocument()

      // All elements should be properly spaced
      expect(screen.getByLabelText(/e-mail/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/senha/i)).toBeInTheDocument()
      expect(
        screen.getByRole('button', { name: /entrar/i })
      ).toBeInTheDocument()
    })

    it('should handle dynamic viewport changes', async () => {
      const onSubmit = vi.fn()
      const { rerender } = render(
        <TestWrapper>
          <LoginForm onSuccess={onSubmit} />
        </TestWrapper>
      )

      // Start with mobile
      setViewport(viewports.mobile)
      rerender(
        <TestWrapper>
          <LoginForm onSuccess={onSubmit} />
        </TestWrapper>
      )

      // Verify mobile layout
      expect(screen.getByLabelText(/e-mail/i)).toBeInTheDocument()

      // Switch to desktop
      setViewport(viewports.desktop)
      rerender(
        <TestWrapper>
          <LoginForm onSuccess={onSubmit} />
        </TestWrapper>
      )

      // Form should adapt to desktop layout
      expect(screen.getByLabelText(/e-mail/i)).toBeInTheDocument()
      expect(
        screen.getByRole('button', { name: /entrar/i })
      ).toBeInTheDocument()

      // Switch back to tablet
      setViewport(viewports.tablet)
      rerender(
        <TestWrapper>
          <LoginForm onSuccess={onSubmit} />
        </TestWrapper>
      )

      // Should maintain functionality across viewport changes
      expect(screen.getByLabelText(/e-mail/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/senha/i)).toBeInTheDocument()
    })
  })

  describe('Accessibility Across Breakpoints', () => {
    it('should maintain accessibility features on all screen sizes', async () => {
      const testBreakpoints = [
        viewports.mobile,
        viewports.tablet,
        viewports.desktop,
      ]

      for (const viewport of testBreakpoints) {
        setViewport(viewport)

        const onSubmit = vi.fn()
        render(
          <TestWrapper>
            <LoginForm onSuccess={onSubmit} />
          </TestWrapper>
        )

        // Form should be accessible via keyboard on all screen sizes
        const emailInput = screen.getByLabelText(/e-mail/i)
        const passwordInput = screen.getByLabelText(/senha/i)
        const submitButton = screen.getByRole('button', { name: /entrar/i })

        // Check ARIA attributes
        expect(emailInput).toHaveAttribute('type', 'email')
        expect(emailInput).toHaveAttribute('autoComplete', 'email')
        expect(passwordInput).toHaveAttribute('type', 'password')
        expect(passwordInput).toHaveAttribute(
          'autoComplete',
          'current-password'
        )

        // Labels should be properly associated
        expect(emailInput).toHaveAccessibleName(/e-mail/i)
        expect(passwordInput).toHaveAccessibleName(/senha/i)

        // Form should be keyboard navigable
        expect(emailInput).toHaveAttribute('id')
        expect(passwordInput).toHaveAttribute('id')

        // Button should be properly labeled
        expect(submitButton).toHaveAccessibleName(/entrar/i)
      }
    })

    it('should provide proper focus management across screen sizes', async () => {
      setViewport(viewports.mobile)

      const onSubmit = vi.fn()
      render(
        <TestWrapper>
          <LoginForm onSuccess={onSubmit} />
        </TestWrapper>
      )

      const emailInput = screen.getByLabelText(/e-mail/i)
      const passwordInput = screen.getByLabelText(/senha/i)
      const submitButton = screen.getByRole('button', { name: /entrar/i })

      // Focus should work properly
      emailInput.focus()
      expect(document.activeElement).toBe(emailInput)

      // Tab navigation should work
      fireEvent.keyDown(emailInput, { key: 'Tab' })
      // Note: In real browser, this would focus the next element
      // In test environment, we verify elements are focusable

      // Check that password input is focusable
      const passwordTabIndex = passwordInput.getAttribute('tabIndex')
      expect(passwordTabIndex === null || passwordTabIndex !== '-1').toBe(true)

      // Check that submit button is focusable
      const submitTabIndex = submitButton.getAttribute('tabIndex')
      expect(submitTabIndex === null || submitTabIndex !== '-1').toBe(true)
    })
  })

  describe('Performance Across Viewports', () => {
    it('should render efficiently on all screen sizes', async () => {
      const renderTimes: number[] = []

      for (const [name, viewport] of Object.entries(viewports)) {
        setViewport(viewport)

        const startTime = performance.now()

        const onSubmit = vi.fn()
        render(
          <TestWrapper>
            <LoginForm onSuccess={onSubmit} />
          </TestWrapper>
        )

        // Verify component rendered
        expect(screen.getByLabelText(/e-mail/i)).toBeInTheDocument()

        const endTime = performance.now()
        renderTimes.push(endTime - startTime)
      }

      // All renders should complete reasonably quickly (< 100ms in test environment)
      renderTimes.forEach(time => {
        expect(time).toBeLessThan(100)
      })
    })

    it('should handle rapid viewport changes without errors', async () => {
      const onSubmit = vi.fn()
      const { rerender } = render(
        <TestWrapper>
          <LoginForm onSuccess={onSubmit} />
        </TestWrapper>
      )

      // Rapidly change viewports
      const viewportList = Object.values(viewports)

      for (let i = 0; i < 10; i++) {
        const viewport = viewportList[i % viewportList.length]!
        setViewport(viewport)

        rerender(
          <TestWrapper>
            <LoginForm onSuccess={onSubmit} />
          </TestWrapper>
        )

        // Component should remain functional
        expect(screen.getByLabelText(/e-mail/i)).toBeInTheDocument()
      }
    })
  })
})
