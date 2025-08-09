/**
 * Users Dashboard Page Tests - CLAUDE.md Compliant
 * 
 * Phase 3: Rewritten following strict CLAUDE.md testing directives:
 * - NEVER mock internal components, pages, or application logic
 * - ONLY mock external APIs (fetch calls, browser APIs)
 * - Test real page rendering and user interactions
 * - Focus on user-facing functionality and business logic
 * - No internal mocks - test actual component behavior
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
  setupUnauthenticatedUser,
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
    }
  ]

  const mockUsersResponse: UserListResponse = {
    users: mockUsers,
    total: 2,
    page: 1,
    per_page: 50,
    total_pages: 1
  }

  const renderUsersPage = (userRole: 'user' | 'admin' | 'sysadmin' = 'admin') => {
    setupAuthenticatedUser(userRole)
    mockSuccessfulFetch('/api/v1/users', mockUsersResponse)
    return renderWithProviders(<UsersPage />)
  }

  describe('Page Structure and Layout', () => {
    test('renders page header with proper structure', async () => {
      renderUsersPage()

      expect(screen.getByRole('heading', { name: /usuários/i })).toBeInTheDocument()
      expect(screen.getByText(/gerencie os usuários/i)).toBeInTheDocument()
    })

    test('renders action buttons when user has permissions', async () => {
      renderUsersPage('admin')

      expect(screen.getByRole('button', { name: /novo usuário/i })).toBeInTheDocument()
    })

    test('renders search and filter controls', async () => {
      renderUsersPage()

      expect(screen.getByPlaceholderText(/buscar por email/i)).toBeInTheDocument()
      expect(screen.getByText(/filtrar por role/i)).toBeInTheDocument()
      expect(screen.getByText(/filtrar por status/i)).toBeInTheDocument()
    })
  })

  describe('Users Data Loading', () => {
    test('displays users data when loaded successfully', async () => {
      renderUsersPage()

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
        expect(screen.getByText('joao@example.com')).toBeInTheDocument()
        expect(screen.getByText('Maria Santos')).toBeInTheDocument()
        expect(screen.getByText('maria@example.com')).toBeInTheDocument()
      })
    })

    test('displays error message when loading fails', async () => {
      setupAuthenticatedUser('admin')
      mockFailedFetch('/api/v1/users', 'Failed to load users')
      
      renderWithProviders(<UsersPage />)

      await waitFor(() => {
        expect(screen.getByText(/erro.*carregar/i)).toBeInTheDocument()
      })
    })
  })

  describe('Authentication and Permissions', () => {
    test('renders for admin users with full functionality', async () => {
      renderUsersPage('admin')

      expect(screen.getByRole('button', { name: /novo usuário/i })).toBeInTheDocument()
      
      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })
    })

    test('renders for sysadmin users with enhanced capabilities', async () => {
      renderUsersPage('sysadmin')

      expect(screen.getByRole('button', { name: /novo usuário/i })).toBeInTheDocument()
      
      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })
    })

    test('handles regular users with limited permissions', async () => {
      renderUsersPage('user')

      // Regular users might see limited functionality
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /usuários/i })).toBeInTheDocument()
      })
    })
  })

  describe('User Interactions', () => {
    test('allows searching users by email', async () => {
      renderUsersPage()

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText(/buscar/i)
      await userEvent.type(searchInput, 'joao@example.com')

      // Search functionality should work with real components
      expect(searchInput).toHaveValue('joao@example.com')
    })

    test('handles new user button click', async () => {
      renderUsersPage('admin')

      const newUserButton = screen.getByRole('button', { name: /novo usuário/i })
      expect(newUserButton).toBeEnabled()

      await userEvent.click(newUserButton)
      
      // Should open the create user dialog
      await waitFor(() => {
        expect(screen.getByRole('dialog', { name: /criar novo usuário/i })).toBeInTheDocument()
      })
      
      // Dialog should contain form fields
      expect(screen.getByRole('textbox', { name: /nome completo/i })).toBeInTheDocument()
      expect(screen.getByRole('textbox', { name: /email/i })).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    test('handles network errors gracefully', async () => {
      setupAuthenticatedUser('admin')
      mockFailedFetch('/api/v1/users', 'Network error', 500)
      
      renderWithProviders(<UsersPage />)

      await waitFor(() => {
        expect(screen.getByText(/erro/i)).toBeInTheDocument()
      })
    })

    test('handles empty user list', async () => {
      setupAuthenticatedUser('admin')
      mockSuccessfulFetch('/api/v1/users', {
        users: [],
        total: 0,
        page: 1,
        per_page: 50,
        total_pages: 1
      })
      
      renderWithProviders(<UsersPage />)

      await waitFor(() => {
        expect(screen.getByText(/nenhum usuário/i) || screen.getByText(/sem usuários/i)).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    test('has proper heading hierarchy', async () => {
      renderUsersPage()

      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/usuários/i)
    })

    test('has accessible form controls', async () => {
      renderUsersPage()

      const searchInput = screen.getByPlaceholderText(/buscar/i)
      expect(searchInput).toBeInTheDocument()
      
      const newUserButton = screen.getByRole('button', { name: /novo usuário/i })
      expect(newUserButton).toBeInTheDocument()
    })
  })
})