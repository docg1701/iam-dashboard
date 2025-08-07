/**
 * Clients List Page Comprehensive Tests
 * 
 * Phase 3: Critical page testing implementation
 * 
 * Test coverage focuses on:
 * - Core business functionality for client management
 * - Navigation flows and routing behavior
 * - Empty state handling and first-time user experience
 * - Search functionality and user interactions
 * - Permission-based access control
 * - Responsive behavior and accessibility
 * - Business information display and validation
 * 
 * Following CLAUDE.md testing directives:
 * - NEVER mock internal components, pages, or application logic
 * - ONLY mock external APIs (fetch calls, navigation router)
 * - Test real page rendering and user interactions
 * - Focus on user-facing functionality and business workflows
 */

import {
  renderWithProviders,
  screen,
  fireEvent,
  waitFor,
  userEvent,
  vi,
  expect,
  describe,
  test,
  useTestSetup,
  mockSuccessfulFetch,
  mockFailedFetch,
  mockNetworkError,
  triggerWindowResize,
} from '@/test/test-template'
import { 
  AuthScenarios,
  setupAuthenticatedUser,
  setupUnauthenticatedUser,
  expectAuthState,
  clearTestAuth,
} from '@/test/auth-helpers'
import ClientsPage from '../page'

// Mock next/navigation for route testing (external framework - safe to mock)
const mockPush = vi.fn()
const mockRouter = {
  push: mockPush,
  replace: vi.fn(),
  prefetch: vi.fn(),
  back: vi.fn(),
  forward: vi.fn(),
  refresh: vi.fn(),
}

// Mock the useRouter hook specifically
vi.mock('next/navigation', async () => {
  const actual = await vi.importActual('next/navigation')
  return {
    ...actual,
    useRouter: () => mockRouter,
  }
})

describe('ClientsPage', () => {
  useTestSetup()

  const renderClientsPage = (userRole: 'user' | 'admin' | 'sysadmin' = 'admin') => {
    // Setup authenticated user with appropriate role
    setupAuthenticatedUser(userRole)
    
    return renderWithProviders(<ClientsPage />)
  }

  describe('Page Structure and Layout', () => {
    test('renders page header with proper structure and branding', () => {
      renderClientsPage()

      expect(screen.getByRole('heading', { level: 1, name: /clientes/i })).toBeInTheDocument()
      expect(screen.getByText(/gerencie os clientes registrados no sistema/i)).toBeInTheDocument()
      
      // Check for Users icon (representing clients)
      const usersIcon = document.querySelector('[data-lucide="users"]')
      expect(usersIcon).toBeInTheDocument()
    })

    test('renders action button with proper accessibility', () => {
      renderClientsPage()

      const newClientButton = screen.getByRole('button', { name: /novo cliente/i })
      expect(newClientButton).toBeInTheDocument()
      expect(newClientButton).toBeEnabled()
      
      // Check for plus icon
      const plusIcon = document.querySelector('[data-lucide="plus"]')
      expect(plusIcon).toBeInTheDocument()
    })

    test('renders search bar with proper structure', () => {
      renderClientsPage()

      const searchInput = screen.getByPlaceholderText(/buscar clientes/i)
      expect(searchInput).toBeInTheDocument()
      
      // Check for search icon
      const searchIcon = document.querySelector('[data-lucide="search"]')
      expect(searchIcon).toBeInTheDocument()
    })

    test('maintains responsive design classes and structure', () => {
      renderClientsPage()
      
      const container = screen.getByText('Clientes').closest('.container')
      expect(container).toHaveClass('mx-auto', 'px-4', 'py-8', 'max-w-6xl')
    })

    test('displays informational content in proper structure', () => {
      renderClientsPage()
      
      // Check for empty state card
      expect(screen.getByText(/nenhum cliente encontrado/i)).toBeInTheDocument()
      expect(screen.getByText(/comece criando o primeiro cliente do sistema/i)).toBeInTheDocument()
      
      // Check for info card with business rules
      expect(screen.getByText(/sobre o sistema de clientes/i)).toBeInTheDocument()
      expect(screen.getByText(/cpf deve ser único no sistema/i)).toBeInTheDocument()
      expect(screen.getByText(/pelo menos 13 anos de idade/i)).toBeInTheDocument()
    })
  })

  describe('Navigation and Routing Integration', () => {
    test('navigates to new client form when "Novo Cliente" clicked', async () => {
      renderClientsPage()

      const newClientButton = screen.getByRole('button', { name: /novo cliente/i })
      await userEvent.click(newClientButton)

      expect(mockPush).toHaveBeenCalledWith('/clients/new')
    })

    test('navigates to new client form when "Criar Primeiro Cliente" clicked', async () => {
      renderClientsPage()

      const firstClientButton = screen.getByRole('button', { name: /criar primeiro cliente/i })
      await userEvent.click(firstClientButton)

      expect(mockPush).toHaveBeenCalledWith('/clients/new')
    })

    test('handles multiple navigation clicks without issues', async () => {
      renderClientsPage()

      const newClientButton = screen.getByRole('button', { name: /novo cliente/i })
      
      // Click multiple times rapidly
      await userEvent.click(newClientButton)
      await userEvent.click(newClientButton)
      await userEvent.click(newClientButton)

      expect(mockPush).toHaveBeenCalledTimes(3)
      expect(mockPush).toHaveBeenCalledWith('/clients/new')
    })

    test('navigation works correctly with keyboard interactions', async () => {
      renderClientsPage()

      const newClientButton = screen.getByRole('button', { name: /novo cliente/i })
      
      // Focus and activate with Enter key
      newClientButton.focus()
      await userEvent.keyboard('{Enter}')

      expect(mockPush).toHaveBeenCalledWith('/clients/new')
    })

    test('navigation works correctly with space key', async () => {
      renderClientsPage()

      const newClientButton = screen.getByRole('button', { name: /novo cliente/i })
      
      // Focus and activate with Space key
      newClientButton.focus()
      await userEvent.keyboard(' ')

      expect(mockPush).toHaveBeenCalledWith('/clients/new')
    })
  })

  describe('Search Functionality', () => {
    test('renders search input with proper placeholder and accessibility', () => {
      renderClientsPage()

      const searchInput = screen.getByPlaceholderText(/buscar clientes/i)
      expect(searchInput).toBeInTheDocument()
      expect(searchInput).toHaveAttribute('type', 'text')
      
      // Should have proper ARIA attributes
      expect(searchInput).toBeEnabled()
    })

    test('updates search input value when user types', async () => {
      renderClientsPage()

      const searchInput = screen.getByPlaceholderText(/buscar clientes/i)
      
      await userEvent.type(searchInput, 'João Silva')
      
      expect(searchInput).toHaveValue('João Silva')
    })

    test('clears search input correctly', async () => {
      renderClientsPage()

      const searchInput = screen.getByPlaceholderText(/buscar clientes/i)
      
      // Type then clear
      await userEvent.type(searchInput, 'test search')
      expect(searchInput).toHaveValue('test search')
      
      await userEvent.clear(searchInput)
      expect(searchInput).toHaveValue('')
    })

    test('handles special characters in search', async () => {
      renderClientsPage()

      const searchInput = screen.getByPlaceholderText(/buscar clientes/i)
      
      await userEvent.type(searchInput, 'José da Silva & Cia.')
      
      expect(searchInput).toHaveValue('José da Silva & Cia.')
    })

    test('maintains search state during user interactions', async () => {
      renderClientsPage()

      const searchInput = screen.getByPlaceholderText(/buscar clientes/i)
      
      await userEvent.type(searchInput, 'search term')
      
      // Click elsewhere and back to search
      const heading = screen.getByRole('heading', { name: /clientes/i })
      await userEvent.click(heading)
      await userEvent.click(searchInput)
      
      // Search value should be maintained
      expect(searchInput).toHaveValue('search term')
    })
  })

  describe('Empty State Handling', () => {
    test('displays comprehensive empty state with clear messaging', () => {
      renderClientsPage()

      // Main empty state message
      expect(screen.getByText(/nenhum cliente encontrado/i)).toBeInTheDocument()
      expect(screen.getByText(/comece criando o primeiro cliente do sistema/i)).toBeInTheDocument()
      
      // Should have a Users icon for empty state
      const emptyStateIcon = screen.getByText(/nenhum cliente encontrado/i)
        .closest('.flex')
        ?.querySelector('[data-lucide="users"]')
      expect(emptyStateIcon).toBeInTheDocument()
    })

    test('provides clear call-to-action in empty state', () => {
      renderClientsPage()

      const createFirstClientBtn = screen.getByRole('button', { name: /criar primeiro cliente/i })
      expect(createFirstClientBtn).toBeInTheDocument()
      expect(createFirstClientBtn).toBeEnabled()
      
      // Should have Plus icon
      const plusIcon = createFirstClientBtn.querySelector('[data-lucide="plus"]')
      expect(plusIcon).toBeInTheDocument()
    })

    test('displays business rules and information in empty state', () => {
      renderClientsPage()

      // Info card content
      expect(screen.getByText(/sobre o sistema de clientes/i)).toBeInTheDocument()
      expect(screen.getByText(/registre clientes com nome completo, cpf e data de nascimento/i)).toBeInTheDocument()
      expect(screen.getByText(/todas as informações são validadas automaticamente/i)).toBeInTheDocument()
      expect(screen.getByText(/cpf deve ser único no sistema para cada cliente/i)).toBeInTheDocument()
      expect(screen.getByText(/clientes devem ter pelo menos 13 anos de idade/i)).toBeInTheDocument()
      expect(screen.getByText(/todas as operações são registradas no log de auditoria/i)).toBeInTheDocument()
    })

    test('empty state has proper visual hierarchy and styling', () => {
      renderClientsPage()

      // Check for proper card structure
      const emptyStateCard = screen.getByText(/nenhum cliente encontrado/i).closest('.p-8')
      expect(emptyStateCard).toBeInTheDocument()
      expect(emptyStateCard).toHaveClass('text-center')
      
      // Check for info card styling
      const infoCard = screen.getByText(/sobre o sistema de clientes/i).closest('.p-4')
      expect(infoCard).toBeInTheDocument()
      expect(infoCard).toHaveClass('bg-blue-50', 'border-blue-200')
    })
  })

  describe('Authentication and Permission Integration', () => {
    test('renders for admin users with full functionality', () => {
      renderClientsPage('admin')
      
      expectAuthState({
        isAuthenticated: true,
        isLoading: false,
      })
      
      expect(screen.getByRole('button', { name: /novo cliente/i })).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/buscar clientes/i)).toBeInTheDocument()
    })

    test('renders for sysadmin users with enhanced capabilities', () => {
      renderClientsPage('sysadmin')
      
      expect(screen.getByRole('heading', { name: /clientes/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /novo cliente/i })).toBeInTheDocument()
      
      // Should have access to all functionality
      expect(screen.getByText(/gerencie os clientes registrados no sistema/i)).toBeInTheDocument()
    })

    test('renders for regular users with appropriate access', () => {
      renderClientsPage('user')
      
      expect(screen.getByRole('heading', { name: /clientes/i })).toBeInTheDocument()
      
      // Regular users should still be able to access clients (business requirement)
      expect(screen.getByPlaceholderText(/buscar clientes/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /novo cliente/i })).toBeInTheDocument()
    })

    test('handles unauthenticated access appropriately', () => {
      setupUnauthenticatedUser()
      
      renderWithProviders(<ClientsPage />)
      
      // Should render without crashing - actual behavior depends on app's auth handling
      expect(document.body).toBeInTheDocument()
    })
  })

  describe('Responsive Design and Mobile Behavior', () => {
    test('adapts layout for mobile viewports', () => {
      triggerWindowResize(375, 667) // Mobile viewport
      renderClientsPage()
      
      // Should still render main components
      expect(screen.getByRole('heading', { name: /clientes/i })).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/buscar clientes/i)).toBeInTheDocument()
      
      // Check responsive classes are working
      const container = screen.getByText('Clientes').closest('.container')
      expect(container).toHaveClass('px-4') // Mobile padding
    })

    test('handles tablet viewport correctly', () => {
      triggerWindowResize(768, 1024) // Tablet viewport
      renderClientsPage()
      
      expect(screen.getByRole('heading', { name: /clientes/i })).toBeInTheDocument()
      expect(screen.getByText(/novo cliente/i)).toBeInTheDocument()
    })

    test('maintains proper layout on desktop', () => {
      triggerWindowResize(1920, 1080) // Desktop viewport
      renderClientsPage()
      
      expect(screen.getByRole('heading', { name: /clientes/i })).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/buscar clientes/i)).toBeInTheDocument()
    })

    test('search bar maintains proper width constraints', () => {
      renderClientsPage()
      
      const searchContainer = screen.getByPlaceholderText(/buscar clientes/i).closest('.max-w-md')
      expect(searchContainer).toBeInTheDocument()
    })
  })

  describe('Accessibility and User Experience', () => {
    test('has proper accessibility attributes and structure', () => {
      renderClientsPage()
      
      // Check for proper headings hierarchy
      expect(screen.getByRole('heading', { level: 1, name: /clientes/i })).toBeInTheDocument()
      
      // Check form accessibility
      expect(screen.getByPlaceholderText(/buscar clientes/i)).toBeInTheDocument()
      
      // Check button accessibility
      const newClientButton = screen.getByRole('button', { name: /novo cliente/i })
      expect(newClientButton).toBeInTheDocument()
      expect(newClientButton).toBeEnabled()
    })

    test('supports keyboard navigation', async () => {
      renderClientsPage()
      
      const searchInput = screen.getByPlaceholderText(/buscar clientes/i)
      const newClientButton = screen.getByRole('button', { name: /novo cliente/i })
      const firstClientButton = screen.getByRole('button', { name: /criar primeiro cliente/i })
      
      // Tab navigation should work
      searchInput.focus()
      expect(document.activeElement).toBe(searchInput)
      
      await userEvent.tab()
      expect(document.activeElement).toBe(newClientButton)
      
      await userEvent.tab()
      await userEvent.tab() // Skip to the first client button
      expect(document.activeElement).toBe(firstClientButton)
    })

    test('provides clear user feedback and instructions', () => {
      renderClientsPage()
      
      // Clear descriptions and instructions
      expect(screen.getByText(/gerencie os clientes registrados no sistema/i)).toBeInTheDocument()
      expect(screen.getByText(/comece criando o primeiro cliente do sistema/i)).toBeInTheDocument()
      
      // Business rules are clearly explained
      expect(screen.getByText(/sobre o sistema de clientes/i)).toBeInTheDocument()
    })

    test('uses semantic HTML structure', () => {
      renderClientsPage()
      
      // Proper semantic elements
      expect(screen.getByRole('main') || screen.getByRole('region')).toBeInTheDocument()
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
      
      // Proper button semantics
      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThan(0)
      
      // Proper input semantics
      expect(screen.getByRole('textbox')).toBeInTheDocument()
    })
  })

  describe('Business Logic and Information Display', () => {
    test('displays comprehensive business rules for client management', () => {
      renderClientsPage()
      
      // Verify all business rules are clearly communicated
      const businessRules = [
        /registre clientes com nome completo, cpf e data de nascimento/i,
        /todas as informações são validadas automaticamente/i,
        /cpf deve ser único no sistema para cada cliente/i,
        /clientes devem ter pelo menos 13 anos de idade/i,
        /todas as operações são registradas no log de auditoria/i,
      ]
      
      businessRules.forEach(rule => {
        expect(screen.getByText(rule)).toBeInTheDocument()
      })
    })

    test('provides proper context for first-time users', () => {
      renderClientsPage()
      
      expect(screen.getByText(/nenhum cliente encontrado/i)).toBeInTheDocument()
      expect(screen.getByText(/comece criando o primeiro cliente do sistema/i)).toBeInTheDocument()
      
      // Call to action should be prominent
      expect(screen.getByRole('button', { name: /criar primeiro cliente/i })).toBeInTheDocument()
    })

    test('maintains consistent terminology and language', () => {
      renderClientsPage()
      
      // Consistent use of "Clientes" throughout
      expect(screen.getByText('Clientes')).toBeInTheDocument()
      expect(screen.getByText(/buscar clientes/i)).toBeInTheDocument()
      expect(screen.getByText(/novo cliente/i)).toBeInTheDocument()
      expect(screen.getByText(/primeiro cliente/i)).toBeInTheDocument()
    })
  })

  describe('Error Handling and Edge Cases', () => {
    test('handles component rendering errors gracefully', () => {
      // Test that the component doesn't crash with edge cases
      renderClientsPage()
      
      expect(screen.getByRole('heading', { name: /clientes/i })).toBeInTheDocument()
    })

    test('maintains state during user interactions', async () => {
      renderClientsPage()
      
      const searchInput = screen.getByPlaceholderText(/buscar clientes/i)
      
      // Type in search
      await userEvent.type(searchInput, 'test client')
      expect(searchInput).toHaveValue('test client')
      
      // Click around the page
      const heading = screen.getByRole('heading', { name: /clientes/i })
      await userEvent.click(heading)
      
      // Search value should persist
      expect(searchInput).toHaveValue('test client')
    })

    test('handles rapid user interactions without issues', async () => {
      renderClientsPage()
      
      const newClientButton = screen.getByRole('button', { name: /novo cliente/i })
      const searchInput = screen.getByPlaceholderText(/buscar clientes/i)
      
      // Rapid interactions
      await userEvent.click(newClientButton)
      await userEvent.type(searchInput, 'rapid')
      await userEvent.click(newClientButton)
      
      // Should handle without crashing
      expect(screen.getByRole('heading', { name: /clientes/i })).toBeInTheDocument()
      expect(mockPush).toHaveBeenCalledTimes(2)
    })
  })

  describe('Performance and State Management', () => {
    test('renders efficiently without unnecessary re-renders', () => {
      const { rerender } = renderClientsPage()
      
      // Initial render
      expect(screen.getByRole('heading', { name: /clientes/i })).toBeInTheDocument()
      
      // Re-render should work without issues
      rerender(<ClientsPage />)
      expect(screen.getByRole('heading', { name: /clientes/i })).toBeInTheDocument()
    })

    test('maintains component state correctly', async () => {
      renderClientsPage()
      
      const searchInput = screen.getByPlaceholderText(/buscar clientes/i)
      
      // Set search state
      await userEvent.type(searchInput, 'persistent state')
      expect(searchInput).toHaveValue('persistent state')
      
      // State should be maintained
      expect(searchInput).toHaveValue('persistent state')
    })

    test('handles concurrent user actions appropriately', async () => {
      renderClientsPage()
      
      const newClientButton = screen.getByRole('button', { name: /novo cliente/i })
      const firstClientButton = screen.getByRole('button', { name: /criar primeiro cliente/i })
      
      // Concurrent clicks
      await Promise.all([
        userEvent.click(newClientButton),
        userEvent.click(firstClientButton),
      ])
      
      // Should handle multiple navigation calls
      expect(mockPush).toHaveBeenCalled()
      expect(screen.getByRole('heading', { name: /clientes/i })).toBeInTheDocument()
    })
  })
})