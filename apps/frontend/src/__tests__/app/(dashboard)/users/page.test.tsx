import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import UsersPage from '@/app/(dashboard)/users/page'
import { ToastProvider } from '@/components/ui/toast'
import * as usersAPI from '@/lib/api/users'
import type { User } from '@iam-dashboard/shared'

// Mock the users API
vi.mock('@/lib/api/users', () => ({
  usersAPI: {
    getUsers: vi.fn(),
    deactivateUser: vi.fn(),
    activateUser: vi.fn(),
    resetPassword: vi.fn()
  }
}))

// Mock the toast hook
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
    dismiss: vi.fn(),
    toasts: []
  })
}))

// Mock UserCreateForm and UserEditForm
vi.mock('@/components/forms/UserCreateForm', () => ({
  UserCreateForm: ({ onSuccess, onCancel }: { onSuccess: () => void; onCancel: () => void }) => (
    <div data-testid="user-create-form">
      <button onClick={onSuccess}>Success</button>
      <button onClick={onCancel}>Cancel</button>
    </div>
  )
}))

vi.mock('@/components/forms/UserEditForm', () => ({
  UserEditForm: ({ user, onSuccess, onCancel }: { user: User; onSuccess: () => void; onCancel: () => void }) => (
    <div data-testid="user-edit-form">
      <span>Editing: {user.full_name}</span>
      <button onClick={onSuccess}>Success</button>
      <button onClick={onCancel}>Cancel</button>
    </div>
  )
}))

// Test wrapper component
const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        {children}
      </ToastProvider>
    </QueryClientProvider>
  )
}

describe('UsersPage', () => {
  const mockGetUsers = vi.mocked(usersAPI.usersAPI.getUsers)
  const mockDeactivateUser = vi.mocked(usersAPI.usersAPI.deactivateUser)
  const mockActivateUser = vi.mocked(usersAPI.usersAPI.activateUser)
  const mockResetPassword = vi.mocked(usersAPI.usersAPI.resetPassword)

  const mockUsers: User[] = [
    {
      user_id: '1',
      email: 'admin@example.com',
      full_name: 'System Admin',
      role: 'sysadmin',
      status: 'active',
      created_at: '2023-01-01T00:00:00Z',
      updated_at: '2023-01-01T00:00:00Z',
      is_verified: true
    },
    {
      user_id: '2',
      email: 'john.doe@example.com',
      full_name: 'John Doe',
      role: 'admin',
      status: 'active',
      created_at: '2023-02-01T00:00:00Z',
      updated_at: '2023-02-01T00:00:00Z',
      is_verified: true
    },
    {
      user_id: '3',
      email: 'jane.smith@example.com',
      full_name: 'Jane Smith',
      role: 'user',
      status: 'inactive',
      created_at: '2023-03-01T00:00:00Z',
      updated_at: '2023-03-01T00:00:00Z',
      is_verified: false
    }
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    mockGetUsers.mockResolvedValue({
      users: mockUsers,
      total: mockUsers.length,
      page: 1,
      per_page: 50,
      total_pages: 1
    })
  })

  const renderUsersPage = () => {
    return render(
      <TestWrapper>
        <UsersPage />
      </TestWrapper>
    )
  }

  it('renders page header and navigation correctly', async () => {
    renderUsersPage()

    expect(screen.getByText('Usuários')).toBeInTheDocument()
    expect(screen.getByText('Gerencie os usuários e suas permissões no sistema')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /novo usuário/i })).toBeInTheDocument()
  })

  it('renders search and filter controls', async () => {
    renderUsersPage()

    expect(screen.getByPlaceholderText(/buscar por email/i)).toBeInTheDocument()
    expect(screen.getByText(/filtrar por role/i)).toBeInTheDocument()
    expect(screen.getByText(/filtrar por status/i)).toBeInTheDocument()
  })

  it('loads and displays users in table', async () => {
    renderUsersPage()

    await waitFor(() => {
      expect(screen.getByText('System Admin')).toBeInTheDocument()
      expect(screen.getByText('admin@example.com')).toBeInTheDocument()
      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.getByText('jane.smith@example.com')).toBeInTheDocument()
    })

    expect(mockGetUsers).toHaveBeenCalledWith({
      query: undefined,
      role: undefined,
      is_active: undefined,
      page: 1,
      limit: 50
    })
  })

  it('displays correct role badges', async () => {
    renderUsersPage()

    await waitFor(() => {
      expect(screen.getByText('Administrador do Sistema')).toBeInTheDocument()
      expect(screen.getByText('Administrador')).toBeInTheDocument()
      expect(screen.getByText('Usuário')).toBeInTheDocument()
    })
  })

  it('displays correct status badges', async () => {
    renderUsersPage()

    await waitFor(() => {
      const activeBadges = screen.getAllByText('Ativo')
      const inactiveBadge = screen.getByText('Inativo')
      
      expect(activeBadges).toHaveLength(2)
      expect(inactiveBadge).toBeInTheDocument()
    })
  })

  it('formats dates correctly', async () => {
    renderUsersPage()

    await waitFor(() => {
      expect(screen.getByText('01/01/2023')).toBeInTheDocument()
      expect(screen.getByText('01/02/2023')).toBeInTheDocument()
      expect(screen.getByText('01/03/2023')).toBeInTheDocument()
    })
  })

  it('shows user count summary', async () => {
    renderUsersPage()

    await waitFor(() => {
      expect(screen.getByText(/mostrando 3 de 3 usuário\(s\)/i)).toBeInTheDocument()
    })
  })

  it('filters users by email search', async () => {
    const user = userEvent.setup()
    renderUsersPage()

    const searchInput = screen.getByPlaceholderText(/buscar por email/i)
    await user.type(searchInput, 'john')

    await waitFor(() => {
      expect(mockGetUsers).toHaveBeenLastCalledWith({
        query: 'john',
        role: undefined,
        is_active: undefined,
        page: 1,
        limit: 50
      })
    })
  })

  it('filters users by role', async () => {
    const user = userEvent.setup()
    renderUsersPage()

    const roleFilter = screen.getByText(/filtrar por role/i)
    await user.click(roleFilter)
    
    const adminOption = screen.getByText('Admin')
    await user.click(adminOption)

    await waitFor(() => {
      expect(mockGetUsers).toHaveBeenLastCalledWith({
        query: undefined,
        role: 'admin',
        is_active: undefined,
        page: 1,
        limit: 50
      })
    })
  })

  it('filters users by status', async () => {
    const user = userEvent.setup()
    renderUsersPage()

    const statusFilter = screen.getByText(/filtrar por status/i)
    await user.click(statusFilter)
    
    const inactiveOption = screen.getByText('Inativo')
    await user.click(inactiveOption)

    await waitFor(() => {
      expect(mockGetUsers).toHaveBeenLastCalledWith({
        query: undefined,
        role: undefined,
        is_active: false,
        page: 1,
        limit: 50
      })
    })
  })

  it('opens create user dialog when novo usuário button is clicked', async () => {
    const user = userEvent.setup()
    renderUsersPage()

    const createButton = screen.getByRole('button', { name: /novo usuário/i })
    await user.click(createButton)

    await waitFor(() => {
      expect(screen.getByText('Criar Novo Usuário')).toBeInTheDocument()
      expect(screen.getByTestId('user-create-form')).toBeInTheDocument()
    })
  })

  it('opens edit user dialog when edit action is clicked', async () => {
    const user = userEvent.setup()
    renderUsersPage()

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    // Find and click the actions dropdown for John Doe
    const johnRow = screen.getByText('John Doe').closest('tr')
    const actionsButton = within(johnRow!).getByRole('button', { name: /abrir menu/i })
    await user.click(actionsButton)

    const editButton = screen.getByText(/editar usuário/i)
    await user.click(editButton)

    await waitFor(() => {
      expect(screen.getByText('Editar Usuário')).toBeInTheDocument()
      expect(screen.getByText('Editing: John Doe')).toBeInTheDocument()
    })
  })

  it('shows deactivate option for active users', async () => {
    const user = userEvent.setup()
    renderUsersPage()

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    const johnRow = screen.getByText('John Doe').closest('tr')
    const actionsButton = within(johnRow!).getByRole('button', { name: /abrir menu/i })
    await user.click(actionsButton)

    expect(screen.getByText(/desativar/i)).toBeInTheDocument()
  })

  it('shows activate option for inactive users', async () => {
    const user = userEvent.setup()
    renderUsersPage()

    await waitFor(() => {
      expect(screen.getByText('Jane Smith')).toBeInTheDocument()
    })

    const janeRow = screen.getByText('Jane Smith').closest('tr')
    const actionsButton = within(janeRow!).getByRole('button', { name: /abrir menu/i })
    await user.click(actionsButton)

    expect(screen.getByText(/ativar/i)).toBeInTheDocument()
  })

  it('shows reset password option for all users', async () => {
    const user = userEvent.setup()
    renderUsersPage()

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    const johnRow = screen.getByText('John Doe').closest('tr')
    const actionsButton = within(johnRow!).getByRole('button', { name: /abrir menu/i })
    await user.click(actionsButton)

    expect(screen.getByText(/redefinir senha/i)).toBeInTheDocument()
  })

  it('deactivates user with confirmation dialog', async () => {
    const user = userEvent.setup()
    mockDeactivateUser.mockResolvedValueOnce(undefined)
    renderUsersPage()

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    // Open actions dropdown
    const johnRow = screen.getByText('John Doe').closest('tr')
    const actionsButton = within(johnRow!).getByRole('button', { name: /abrir menu/i })
    await user.click(actionsButton)

    // Click deactivate
    const deactivateButton = screen.getByText(/desativar/i)
    await user.click(deactivateButton)

    // Confirm in dialog
    await waitFor(() => {
      expect(screen.getByText(/desativar usuário/i)).toBeInTheDocument()
      expect(screen.getByText(/tem certeza que deseja desativar o usuário john doe/i)).toBeInTheDocument()
    })

    const confirmButton = screen.getByRole('button', { name: /confirmar/i })
    await user.click(confirmButton)

    await waitFor(() => {
      expect(mockDeactivateUser).toHaveBeenCalledWith('2')
    })
  })

  it('activates user with confirmation dialog', async () => {
    const user = userEvent.setup()
    mockActivateUser.mockResolvedValueOnce({
      ...mockUsers[2],
      status: 'active'
    })
    renderUsersPage()

    await waitFor(() => {
      expect(screen.getByText('Jane Smith')).toBeInTheDocument()
    })

    // Open actions dropdown
    const janeRow = screen.getByText('Jane Smith').closest('tr')
    const actionsButton = within(janeRow!).getByRole('button', { name: /abrir menu/i })
    await user.click(actionsButton)

    // Click activate
    const activateButton = screen.getByText(/ativar/i)
    await user.click(activateButton)

    // Confirm in dialog
    await waitFor(() => {
      expect(screen.getByText(/ativar usuário/i)).toBeInTheDocument()
    })

    const confirmButton = screen.getByRole('button', { name: /confirmar/i })
    await user.click(confirmButton)

    await waitFor(() => {
      expect(mockActivateUser).toHaveBeenCalledWith('3')
    })
  })

  it('resets user password with confirmation dialog', async () => {
    const user = userEvent.setup()
    mockResetPassword.mockResolvedValueOnce(undefined)
    renderUsersPage()

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    // Open actions dropdown
    const johnRow = screen.getByText('John Doe').closest('tr')
    const actionsButton = within(johnRow!).getByRole('button', { name: /abrir menu/i })
    await user.click(actionsButton)

    // Click reset password
    const resetButton = screen.getByText(/redefinir senha/i)
    await user.click(resetButton)

    // Confirm in dialog
    await waitFor(() => {
      expect(screen.getByText(/redefinir senha/i)).toBeInTheDocument()
    })

    const confirmButton = screen.getByRole('button', { name: /confirmar/i })
    await user.click(confirmButton)

    await waitFor(() => {
      expect(mockResetPassword).toHaveBeenCalledWith('2', expect.stringMatching(/^Temp.+!$/))
    })
  })

  it('displays loading state while fetching users', () => {
    mockGetUsers.mockReturnValueOnce(new Promise(() => {})) // Never resolves
    renderUsersPage()

    expect(screen.getByText(/carregando usuários/i)).toBeInTheDocument()
  })

  it('displays error state when users fetch fails', async () => {
    mockGetUsers.mockRejectedValueOnce(new Error('Network error'))
    renderUsersPage()

    await waitFor(() => {
      expect(screen.getByText(/erro ao carregar usuários/i)).toBeInTheDocument()
    })
  })

  it('displays empty state when no users found', async () => {
    mockGetUsers.mockResolvedValueOnce({
      users: [],
      total: 0,
      page: 1,
      per_page: 50,
      total_pages: 0
    })
    renderUsersPage()

    await waitFor(() => {
      expect(screen.getByText(/nenhum usuário encontrado/i)).toBeInTheDocument()
    })
  })

  it('closes dialogs when forms call onCancel', async () => {
    const user = userEvent.setup()
    renderUsersPage()

    // Open create dialog
    const createButton = screen.getByRole('button', { name: /novo usuário/i })
    await user.click(createButton)

    await waitFor(() => {
      expect(screen.getByTestId('user-create-form')).toBeInTheDocument()
    })

    // Cancel form
    const cancelButton = screen.getByText('Cancel')
    await user.click(cancelButton)

    await waitFor(() => {
      expect(screen.queryByTestId('user-create-form')).not.toBeInTheDocument()
    })
  })

  it('refreshes user list when forms call onSuccess', async () => {
    const user = userEvent.setup()
    renderUsersPage()

    // Open create dialog
    const createButton = screen.getByRole('button', { name: /novo usuário/i })
    await user.click(createButton)

    await waitFor(() => {
      expect(screen.getByTestId('user-create-form')).toBeInTheDocument()
    })

    // Clear previous calls
    mockGetUsers.mockClear()

    // Success form
    const successButton = screen.getByText('Success')
    await user.click(successButton)

    await waitFor(() => {
      expect(mockGetUsers).toHaveBeenCalled()
      expect(screen.queryByTestId('user-create-form')).not.toBeInTheDocument()
    })
  })
})