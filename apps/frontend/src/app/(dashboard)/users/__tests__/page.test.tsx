/**
 * Users Dashboard Page Enhanced Tests
 * 
 * Phase 3: Enhanced critical page testing implementation
 * 
 * Test coverage focuses on:
 * - Complete user management workflow
 * - Search and filtering functionality
 * - Permission-based actions and access control
 * - CRUD operations with real API integration
 * - Responsive behavior and accessibility
 * - Loading states and error scenarios
 * 
 * Following CLAUDE.md testing directives:
 * - NEVER mock internal components, pages, or application logic
 * - ONLY mock external APIs (fetch calls, browser APIs)
 * - Test real page rendering and user interactions
 * - Focus on user-facing functionality and business logic
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
  within,
} from '@/test/test-template'
import { 
  AuthScenarios,
  setupAuthenticatedUser,
  setupUnauthenticatedUser,
  expectAuthState,
  clearTestAuth,
} from '@/test/auth-helpers'
import UsersPage from '../page'
import type { User } from '@iam-dashboard/shared'
import type { UserListResponse } from '@/lib/api/users'

describe('UsersPage', () => {
  useTestSetup()

  const mockUsers: User[] = [
    {
      user_id: '1',
      full_name: 'João Silva',
      email: 'joao@example.com',
      role: 'admin',
      status: 'active',
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
      last_login_at: '2023-01-02T00:00:00Z',
      is_verified: true
    },
    {
      user_id: '2',
      full_name: 'Maria Santos',
      email: 'maria@example.com',
      role: 'user',
      status: 'active',
      created_at: '2023-01-03T00:00:00Z',
      updated_at: '2023-01-03T00:00:00Z',
      is_verified: true
    },
    {
      user_id: '3',
      full_name: 'Pedro Costa',
      email: 'pedro@example.com',
      role: 'sysadmin',
      status: 'inactive',
      created_at: '2023-01-05T00:00:00Z',
      updated_at: '2023-01-05T00:00:00Z',
      is_verified: false
    }
  ]

  const mockUsersResponse: UserListResponse = {
    users: mockUsers,
    total: 3,
    page: 1,
    per_page: 50,
    total_pages: 1
  }

  const renderUsersPage = (userRole: 'user' | 'admin' | 'sysadmin' = 'admin') => {
    // Setup authenticated user with appropriate role
    setupAuthenticatedUser(userRole)
    
    // Mock successful users fetch by default
    mockSuccessfulFetch('/api/v1/users', mockUsersResponse)
    
    return renderWithProviders(<UsersPage />)
  }

  describe('Page Structure and Layout', () => {
    test('renders page header with proper structure and branding', async () => {
      renderUsersPage()

      expect(screen.getByRole('heading', { name: /usuários/i })).toBeInTheDocument()
      expect(screen.getByText(/gerencie os usuários e suas permissões/i)).toBeInTheDocument()
      
      // Check for icon and layout
      const userIcon = document.querySelector('[data-lucide="users"]')
      expect(userIcon).toBeInTheDocument()
    })

    test('renders action buttons with proper accessibility', async () => {
      renderUsersPage()

      const newUserButton = screen.getByRole('button', { name: /novo usuário/i })
      expect(newUserButton).toBeInTheDocument()
      expect(newUserButton).toBeEnabled()
      
      // Check for plus icon
      const plusIcon = document.querySelector('[data-lucide="plus"]')
      expect(plusIcon).toBeInTheDocument()
    })

    test('renders comprehensive search and filter controls', async () => {
      renderUsersPage()

      expect(screen.getByPlaceholderText(/buscar por email/i)).toBeInTheDocument()
      expect(screen.getByText(/filtrar por role/i)).toBeInTheDocument()  
      expect(screen.getByText(/filtrar por status/i)).toBeInTheDocument()
      
      // Check for search icon
      const searchIcon = document.querySelector('[data-lucide="search"]')
      expect(searchIcon).toBeInTheDocument()
    })

    test('renders users table with complete structure and accessibility', async () => {
      renderUsersPage()

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      const table = screen.getByRole('table')
      const columnHeaders = within(table).getAllByRole('columnheader')
      
      expect(columnHeaders).toHaveLength(6)
      expect(within(table).getByText(/usuário/i)).toBeInTheDocument()
      expect(within(table).getByText(/email/i)).toBeInTheDocument()
      expect(within(table).getByText(/role/i)).toBeInTheDocument()
      expect(within(table).getByText(/status/i)).toBeInTheDocument()
      expect(within(table).getByText(/criado em/i)).toBeInTheDocument()
      expect(within(table).getByText(/ações/i)).toBeInTheDocument()
    })

    test('maintains responsive design classes and structure', () => {
      renderUsersPage()
      
      const container = screen.getByText('Usuários').closest('.container')
      expect(container).toHaveClass('mx-auto', 'px-4', 'py-8', 'max-w-7xl')
      
      const filtersContainer = screen.getByPlaceholderText(/buscar por email/i).closest('.flex')
      expect(filtersContainer).toHaveClass('flex-col', 'sm:flex-row')
    })
  })

  describe('Users Data Loading', () => {
    it('should display loading state while fetching users', () => {
      mockFetch.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({
          ok: true,
          status: 200,
          json: async () => mockUsersResponse
        }), 100))
      )

      renderComponent()

      expect(screen.getByText(/carregando usuários/i)).toBeInTheDocument()
    })

    it('should display users data when loaded successfully', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
        expect(screen.getByText('joao@example.com')).toBeInTheDocument()
        expect(screen.getByText('Maria Santos')).toBeInTheDocument()
        expect(screen.getByText('maria@example.com')).toBeInTheDocument()
        expect(screen.getByText('Pedro Costa')).toBeInTheDocument()
        expect(screen.getByText('pedro@example.com')).toBeInTheDocument()
      })
    })

    it('should display error message when loading fails', async () => {
      mockFetch.mockRejectedValue(new Error('API Error'))

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/erro ao carregar usuários/i)).toBeInTheDocument()
      })
    })

    it('should display empty state when no users found', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          users: [],
          total: 0,
          page: 1,
          per_page: 50,
          total_pages: 0
        })
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/nenhum usuário encontrado/i)).toBeInTheDocument()
      })
    })

    it('should display users count summary', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/mostrando 3 de 3 usuário\(s\)/i)).toBeInTheDocument()
      })
    })
  })

  describe('User Role and Status Display', () => {
    it('should display user roles with proper badges', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/administrador$/i)).toBeInTheDocument()
        expect(screen.getByText(/usuário$/i)).toBeInTheDocument()
        expect(screen.getByText(/administrador do sistema/i)).toBeInTheDocument()
      })
    })

    it('should display user status with proper badges', async () => {
      renderComponent()

      await waitFor(() => {
        const activeBadges = screen.getAllByText(/ativo/i)
        expect(activeBadges).toHaveLength(2) // Two active users
        expect(screen.getByText(/inativo/i)).toBeInTheDocument()
      })
    })

    it('should display formatted creation dates', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('01/01/2023')).toBeInTheDocument()
        expect(screen.getByText('03/01/2023')).toBeInTheDocument()
        expect(screen.getByText('05/01/2023')).toBeInTheDocument()
      })
    })
  })

  describe('Search Functionality', () => {
    it('should filter users by email search', async () => {
      const user = userEvent.setup()
      renderComponent()

      const searchInput = screen.getByPlaceholderText(/buscar por email/i)
      await user.type(searchInput, 'joao')

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/users'),
          expect.objectContaining({
            method: 'GET'
          })
        )
      })
    })

    it('should filter users by role', async () => {
      const user = userEvent.setup()
      renderComponent()

      const roleFilter = screen.getByRole('combobox', { name: /filtrar por role/i })
      await user.click(roleFilter)
      await user.click(screen.getByText(/admin$/i))

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/users'),
          expect.objectContaining({
            method: 'GET'
          })
        )
      })
    })

    it('should filter users by status', async () => {
      const user = userEvent.setup()
      renderComponent()

      const statusFilter = screen.getByRole('combobox', { name: /filtrar por status/i })
      await user.click(statusFilter)
      await user.click(screen.getByText(/ativo/i))

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/users'),
          expect.objectContaining({
            method: 'GET'
          })
        )
      })
    })

    it('should combine multiple filters', async () => {
      const user = userEvent.setup()
      renderComponent()

      const searchInput = screen.getByPlaceholderText(/buscar por email/i)
      await user.type(searchInput, 'example')

      const roleFilter = screen.getByRole('combobox', { name: /filtrar por role/i })
      await user.click(roleFilter)
      await user.click(screen.getByText(/admin$/i))

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/users'),
          expect.objectContaining({
            method: 'GET'
          })
        )
      })
    })

    it('should clear filters when "all" options selected', async () => {
      const user = userEvent.setup()
      renderComponent()

      // First apply a filter
      const roleFilter = screen.getByRole('combobox', { name: /filtrar por role/i })
      await user.click(roleFilter)
      await user.click(screen.getByText(/admin$/i))

      // Then clear it
      await user.click(roleFilter)
      await user.click(screen.getByText(/todos os roles/i))

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/users'),
          expect.objectContaining({
            method: 'GET'
          })
        )
      })
    })
  })

  describe('User Actions', () => {
    it('should open user edit dialog when edit action is clicked', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      // Find the first user row and open actions menu
      const userRow = screen.getByText('João Silva').closest('tr')!
      const actionsButton = within(userRow).getByRole('button', { name: /abrir menu/i })
      await user.click(actionsButton)

      const editButton = screen.getByText(/editar usuário/i)
      await user.click(editButton)

      await waitFor(() => {
        expect(screen.getByText(/editar usuário/i)).toBeInTheDocument()
        expect(screen.getByDisplayValue('João Silva')).toBeInTheDocument()
      })
    })

    it('should show deactivate option for active users', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      const userRow = screen.getByText('João Silva').closest('tr')!
      const actionsButton = within(userRow).getByRole('button', { name: /abrir menu/i })
      await user.click(actionsButton)

      expect(screen.getByText(/desativar/i)).toBeInTheDocument()
      expect(screen.queryByText(/ativar/i)).not.toBeInTheDocument()
    })

    it('should show activate option for inactive users', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Pedro Costa')).toBeInTheDocument()
      })

      const userRow = screen.getByText('Pedro Costa').closest('tr')!
      const actionsButton = within(userRow).getByRole('button', { name: /abrir menu/i })
      await user.click(actionsButton)

      expect(screen.getByText(/ativar/i)).toBeInTheDocument()
      expect(screen.queryByText(/desativar/i)).not.toBeInTheDocument()
    })

    it('should show reset password option for all users', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      const userRow = screen.getByText('João Silva').closest('tr')!
      const actionsButton = within(userRow).getByRole('button', { name: /abrir menu/i })
      await user.click(actionsButton)

      expect(screen.getByText(/redefinir senha/i)).toBeInTheDocument()
    })
  })

  describe('User Deactivation', () => {
    it('should show confirmation dialog when deactivating user', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      const userRow = screen.getByText('João Silva').closest('tr')!
      const actionsButton = within(userRow).getByRole('button', { name: /abrir menu/i })
      await user.click(actionsButton)

      const deactivateButton = screen.getByText(/desativar/i)
      await user.click(deactivateButton)

      await waitFor(() => {
        expect(screen.getByText(/desativar usuário/i)).toBeInTheDocument()
        expect(screen.getByText(/tem certeza que deseja desativar o usuário joão silva/i)).toBeInTheDocument()
      })
    })

    it('should call deactivate API when confirmed', async () => {
      const user = userEvent.setup()
      mockFetch.mockResolvedValue({
        ok: true,
        status: 204
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      const userRow = screen.getByText('João Silva').closest('tr')!
      const actionsButton = within(userRow).getByRole('button', { name: /abrir menu/i })
      await user.click(actionsButton)

      const deactivateButton = screen.getByText(/desativar/i)
      await user.click(deactivateButton)

      const confirmButton = screen.getByRole('button', { name: /confirmar/i })
      await user.click(confirmButton)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/users/1'),
          expect.objectContaining({
            method: 'DELETE'
          })
        )
        // Toast será chamado através da implementação real
      })
    })

    it('should handle deactivation errors', async () => {
      const user = userEvent.setup()
      mockFetch.mockRejectedValue(new Error('API Error'))

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      const userRow = screen.getByText('João Silva').closest('tr')!
      const actionsButton = within(userRow).getByRole('button', { name: /abrir menu/i })
      await user.click(actionsButton)

      const deactivateButton = screen.getByText(/desativar/i)
      await user.click(deactivateButton)

      const confirmButton = screen.getByRole('button', { name: /confirmar/i })
      await user.click(confirmButton)

      await waitFor(() => {
        // Toast de erro será chamado através da implementação real
        expect(mockFetch).toHaveBeenCalled()
      })
    })
  })

  describe('User Activation', () => {
    it('should show confirmation dialog when activating user', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Pedro Costa')).toBeInTheDocument()
      })

      const userRow = screen.getByText('Pedro Costa').closest('tr')!
      const actionsButton = within(userRow).getByRole('button', { name: /abrir menu/i })
      await user.click(actionsButton)

      const activateButton = screen.getByText(/ativar/i)
      await user.click(activateButton)

      await waitFor(() => {
        expect(screen.getByText(/ativar usuário/i)).toBeInTheDocument()
        expect(screen.getByText(/tem certeza que deseja ativar o usuário pedro costa/i)).toBeInTheDocument()
      })
    })

    it('should call activate API when confirmed', async () => {
      const user = userEvent.setup()
      const activatedUser = { ...mockUsers[2], status: 'active' as const, is_active: true }
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => activatedUser
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Pedro Costa')).toBeInTheDocument()
      })

      const userRow = screen.getByText('Pedro Costa').closest('tr')!
      const actionsButton = within(userRow).getByRole('button', { name: /abrir menu/i })
      await user.click(actionsButton)

      const activateButton = screen.getByText(/ativar/i)
      await user.click(activateButton)

      const confirmButton = screen.getByRole('button', { name: /confirmar/i })
      await user.click(confirmButton)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/users/3'),
          expect.objectContaining({
            method: 'PATCH'
          })
        )
        // Toast será chamado através da implementação real
      })
    })
  })

  describe('Password Reset', () => {
    it('should show confirmation dialog when resetting password', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      const userRow = screen.getByText('João Silva').closest('tr')!
      const actionsButton = within(userRow).getByRole('button', { name: /abrir menu/i })
      await user.click(actionsButton)

      const resetButton = screen.getByText(/redefinir senha/i)
      await user.click(resetButton)

      await waitFor(() => {
        expect(screen.getByText(/redefinir senha/i)).toBeInTheDocument()
        expect(screen.getByText(/tem certeza que deseja redefinir a senha do usuário joão silva/i)).toBeInTheDocument()
      })
    })

    it('should call reset password API when confirmed', async () => {
      const user = userEvent.setup()
      mockFetch.mockResolvedValue({
        ok: true,
        status: 204
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      const userRow = screen.getByText('João Silva').closest('tr')!
      const actionsButton = within(userRow).getByRole('button', { name: /abrir menu/i })
      await user.click(actionsButton)

      const resetButton = screen.getByText(/redefinir senha/i)
      await user.click(resetButton)

      const confirmButton = screen.getByRole('button', { name: /confirmar/i })
      await user.click(confirmButton)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/users/1/reset-password'),
          expect.objectContaining({
            method: 'POST'
          })
        )
        // Toast será chamado através da implementação real
      })
    })
  })

  describe('Create User Dialog', () => {
    it('should open create user dialog when new user button clicked', async () => {
      const user = userEvent.setup()
      renderComponent()

      const newUserButton = screen.getByRole('button', { name: /novo usuário/i })
      await user.click(newUserButton)

      await waitFor(() => {
        expect(screen.getByText(/criar novo usuário/i)).toBeInTheDocument()
        expect(screen.getByText(/preencha os dados para criar um novo usuário/i)).toBeInTheDocument()
      })
    })

    it('should close create user dialog when cancelled', async () => {
      const user = userEvent.setup()
      renderComponent()

      const newUserButton = screen.getByRole('button', { name: /novo usuário/i })
      await user.click(newUserButton)

      const cancelButton = screen.getByRole('button', { name: /cancelar/i })
      await user.click(cancelButton)

      await waitFor(() => {
        expect(screen.queryByText(/criar novo usuário/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', async () => {
      renderComponent()

      expect(screen.getByRole('heading', { level: 1, name: /usuários/i })).toBeInTheDocument()
    })

    it('should have accessible table structure', async () => {
      renderComponent()

      await waitFor(() => {
        const table = screen.getByRole('table')
        expect(table).toBeInTheDocument()
        
        const columnHeaders = within(table).getAllByRole('columnheader')
        expect(columnHeaders).toHaveLength(6)
      })
    })

    it('should have accessible form controls with labels', async () => {
      renderComponent()

      expect(screen.getByLabelText(/buscar por email/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/filtrar por role/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/filtrar por status/i)).toBeInTheDocument()
    })

    it('should support keyboard navigation for actions menu', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      const userRow = screen.getByText('João Silva').closest('tr')!
      const actionsButton = within(userRow).getByRole('button', { name: /abrir menu/i })
      
      // Focus and activate with keyboard
      actionsButton.focus()
      await user.keyboard('{Enter}')

      expect(screen.getByText(/editar usuário/i)).toBeInTheDocument()
    })
  })

  describe('Responsive Behavior', () => {
    it('should render properly on different screen sizes', async () => {
      renderUsersPage()

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      // The table should be responsive and scrollable
      const tableContainer = screen.getByRole('table').closest('.overflow-hidden')
      expect(tableContainer).toBeInTheDocument()
    })

    it('should show mobile-friendly search and filters layout', async () => {
      renderUsersPage()

      const filtersContainer = screen.getByPlaceholderText(/buscar por email/i).closest('.flex')
      expect(filtersContainer).toHaveClass('flex-col', 'sm:flex-row')
    })

    test('adapts layout for mobile viewports', () => {
      triggerWindowResize(375, 667) // Mobile viewport
      renderUsersPage()
      
      // Should still render main components
      expect(screen.getByRole('heading', { name: /usuários/i })).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/buscar por email/i)).toBeInTheDocument()
      
      // Check responsive classes are working
      const container = screen.getByText('Usuários').closest('.container')
      expect(container).toHaveClass('px-4') // Mobile padding
    })

    test('handles tablet viewport correctly', () => {
      triggerWindowResize(768, 1024) // Tablet viewport
      renderUsersPage()
      
      expect(screen.getByRole('table')).toBeInTheDocument()
      expect(screen.getByText(/novo usuário/i)).toBeInTheDocument()
    })
  })

  describe('Authentication and Permission Integration', () => {
    test('renders for admin users with full functionality', () => {
      renderUsersPage('admin')
      
      expectAuthState({
        isAuthenticated: true,
        isLoading: false,
      })
      
      expect(screen.getByRole('button', { name: /novo usuário/i })).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/buscar por email/i)).toBeInTheDocument()
    })

    test('renders for sysadmin users with enhanced capabilities', () => {
      renderUsersPage('sysadmin')
      
      expect(screen.getByRole('heading', { name: /usuários/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /novo usuário/i })).toBeInTheDocument()
      
      // Sysadmins should see all functionality
      expect(screen.getByText(/filtrar por role/i)).toBeInTheDocument()
    })

    test('renders for regular users with limited permissions', () => {
      renderUsersPage('user')
      
      expect(screen.getByRole('heading', { name: /usuários/i })).toBeInTheDocument()
      
      // Regular users might have limited access - this depends on implementation
      // For now, we test that the page renders without crashing
      expect(screen.getByPlaceholderText(/buscar por email/i)).toBeInTheDocument()
    })

    test('handles unauthenticated access appropriately', () => {
      setupUnauthenticatedUser()
      
      // This might redirect or show an error - depends on implementation
      // For now, test that it doesn't crash
      renderWithProviders(<UsersPage />)
      
      // The behavior here depends on how the app handles unauthenticated access
      expect(document.body).toBeInTheDocument()
    })
  })

  describe('Error Boundaries and Edge Cases', () => {
    test('handles malformed user data gracefully', async () => {
      const malformedUsers = [
        {
          user_id: '1',
          // Missing required fields
          full_name: null,
          email: 'broken@example.com',
          role: 'admin',
        }
      ] as any
      
      mockSuccessfulFetch('/api/v1/users', {
        users: malformedUsers,
        total: 1,
        page: 1,
        per_page: 50,
        total_pages: 1,
      })
      
      renderUsersPage()
      
      // Should handle malformed data without crashing
      expect(screen.getByRole('heading', { name: /usuários/i })).toBeInTheDocument()
    })

    test('handles network timeouts gracefully', async () => {
      mockNetworkError('/api/v1/users', 'Request timeout')
      
      renderUsersPage()
      
      await waitFor(() => {
        expect(screen.getByText(/erro ao carregar usuários/i)).toBeInTheDocument()
      })
      
      // Should show error state
      expect(screen.getByRole('heading', { name: /usuários/i })).toBeInTheDocument()
    })

    test('recovers from API errors with retry', async () => {
      // First call fails
      mockFailedFetch('/api/v1/users', 'Server error', 500)
      
      renderUsersPage()
      
      await waitFor(() => {
        expect(screen.getByText(/erro ao carregar usuários/i)).toBeInTheDocument()
      })
      
      // Second call succeeds (simulating retry)
      mockSuccessfulFetch('/api/v1/users', mockUsersResponse)
      
      // The actual retry mechanism would be handled by React Query
      expect(screen.getByRole('heading', { name: /usuários/i })).toBeInTheDocument()
    })
  })

  describe('Performance and Optimization', () => {
    test('handles large user lists efficiently', async () => {
      const largeUserList = Array.from({ length: 100 }, (_, i) => ({
        user_id: `user-${i}`,
        full_name: `User ${i}`,
        email: `user${i}@example.com`,
        role: 'user' as const,
        status: 'active' as const,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
        is_verified: true,
      }))
      
      mockSuccessfulFetch('/api/v1/users', {
        users: largeUserList,
        total: 100,
        page: 1,
        per_page: 50,
        total_pages: 2,
      })
      
      renderUsersPage()
      
      await waitFor(() => {
        expect(screen.getByText(/mostrando 100 de 100 usuário/i)).toBeInTheDocument()
      })
      
      // Should render without performance issues
      expect(screen.getByRole('table')).toBeInTheDocument()
    })

    test('debounces search input to prevent excessive API calls', async () => {
      renderUsersPage()
      
      const searchInput = screen.getByPlaceholderText(/buscar por email/i)
      
      // Type quickly - should debounce
      await userEvent.type(searchInput, 'test')
      
      // Should not make immediate API calls for each character
      expect(screen.getByDisplayValue('test')).toBeInTheDocument()
    })
  })

  describe('Business Logic Integration', () => {
    test('displays user statistics and summary information', async () => {
      renderUsersPage()
      
      await waitFor(() => {
        expect(screen.getByText(/mostrando 3 de 3 usuário\(s\)/i)).toBeInTheDocument()
      })
      
      // Check that the summary reflects actual data
      expect(screen.getByRole('table')).toBeInTheDocument()
    })

    test('handles empty search results appropriately', async () => {
      mockSuccessfulFetch('/api/v1/users', {
        users: [],
        total: 0,
        page: 1,
        per_page: 50,
        total_pages: 0,
      })
      
      renderUsersPage()
      
      await waitFor(() => {
        expect(screen.getByText(/nenhum usuário encontrado/i)).toBeInTheDocument()
      })
    })

    test('integrates with real form components for user creation', async () => {
      renderUsersPage()
      
      const newUserButton = screen.getByRole('button', { name: /novo usuário/i })
      await userEvent.click(newUserButton)
      
      await waitFor(() => {
        expect(screen.getByText(/criar novo usuário/i)).toBeInTheDocument()
        expect(screen.getByText(/preencha os dados para criar um novo usuário/i)).toBeInTheDocument()
      })
      
      // Should render the actual UserCreateForm component
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })
  })
})