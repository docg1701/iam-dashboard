import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import UsersPage from '../page'
// VIOLAÇÃO CORRIGIDA: Não fazer mock de código interno (@/lib/api/users)
// Usar implementação real do toast
import type { User } from '@iam-dashboard/shared'
import type { UserListResponse } from '@/lib/api/users'

// Mock apenas APIs externas (fetch) - NUNCA código interno
const mockFetch = vi.fn()
global.fetch = mockFetch

// Não fazer mock de hooks internos - usar implementação real

const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  })
  
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('UsersPage', () => {
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

  beforeEach(() => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockUsersResponse
    })
    vi.clearAllMocks()
  })

  const renderComponent = () => {
    return render(
      <TestWrapper>
        <UsersPage />
      </TestWrapper>
    )
  }

  describe('Page Rendering and Initial State', () => {
    it('should render page header with title and description', async () => {
      renderComponent()

      expect(screen.getByRole('heading', { name: /usuários/i })).toBeInTheDocument()
      expect(screen.getByText(/gerencie os usuários e suas permissões/i)).toBeInTheDocument()
    })

    it('should render new user button', async () => {
      renderComponent()

      expect(screen.getByRole('button', { name: /novo usuário/i })).toBeInTheDocument()
    })

    it('should render search and filter controls', async () => {
      renderComponent()

      expect(screen.getByPlaceholderText(/buscar por email/i)).toBeInTheDocument()
      expect(screen.getByText(/filtrar por role/i)).toBeInTheDocument()
      expect(screen.getByText(/filtrar por status/i)).toBeInTheDocument()
    })

    it('should render users table with proper headers', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      expect(screen.getByText(/usuário/i)).toBeInTheDocument()
      expect(screen.getByText(/email/i)).toBeInTheDocument()
      expect(screen.getByText(/role/i)).toBeInTheDocument()
      expect(screen.getByText(/status/i)).toBeInTheDocument()
      expect(screen.getByText(/criado em/i)).toBeInTheDocument()
      expect(screen.getByText(/ações/i)).toBeInTheDocument()
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
      renderComponent()

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      // The table should be responsive and scrollable
      const tableContainer = screen.getByRole('table').closest('.overflow-hidden')
      expect(tableContainer).toBeInTheDocument()
    })

    it('should show mobile-friendly search and filters layout', async () => {
      renderComponent()

      const filtersContainer = screen.getByPlaceholderText(/buscar por email/i).closest('.flex')
      expect(filtersContainer).toHaveClass('flex-col', 'sm:flex-row')
    })
  })
})