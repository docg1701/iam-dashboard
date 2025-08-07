/**
 * PermissionMatrix Component Tests
 * 
 * Comprehensive tests for the PermissionMatrix admin component including responsive design
 * Following CLAUDE.md rules: no internal mocking, only external API mocking
 */

import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import React from 'react'
import useAuthStore from '../../../store/authStore'

import { PermissionMatrix } from '../PermissionMatrix'
import {
  createMockUser,
  createMockAdminUser,
  createMockUserPermissionMatrix,
  createTestQueryClientConfig,
  setupUserAPITest,
  setupPermissionSaveTest,
  AgentName,
  createMockPermissions,
} from '@/test/api-mocks'
import type { User } from '@/types/auth'

// Test utilities
const createTestQueryClient = () => {
  return new QueryClient(createTestQueryClientConfig())
}

const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = createTestQueryClient()
  
  // Initialize auth store with admin user for testing
  React.useEffect(() => {
    const store = useAuthStore.getState()
    store.setUser(mockAdminUser)
    store.setToken('mock-token')
  }, [])
  
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

// Create consistent test data using mock factories
const mockAdminUser = createMockAdminUser({ full_name: 'Admin User' })
const mockUsers: User[] = [
  createMockUser({
    user_id: 'user-1',
    email: 'user1@test.com',
    full_name: 'User One',
    role: 'user',
    is_active: true,
    totp_enabled: false,
  }),
  createMockUser({
    user_id: 'user-2',
    email: 'user2@test.com', 
    full_name: 'User Two',
    role: 'user',
    is_active: true,
    totp_enabled: true,
  }),
  createMockUser({
    user_id: 'user-3',
    email: 'user3@test.com',
    full_name: 'User Three (Inactive)',
    role: 'admin',
    is_active: false,
    totp_enabled: false,
  })
]

// Create permission matrix data using mock factories
const mockPermissionMatrix = {
  'user-1': createMockUserPermissionMatrix('user-1', {
    [AgentName.CLIENT_MANAGEMENT]: createMockPermissions({ create: true, read: true, update: true, delete: false }),
    [AgentName.PDF_PROCESSING]: createMockPermissions({ create: false, read: true, update: false, delete: false }),
    [AgentName.REPORTS_ANALYSIS]: createMockPermissions({ create: false, read: false, update: false, delete: false }),
    [AgentName.AUDIO_RECORDING]: createMockPermissions({ create: false, read: false, update: false, delete: false }),
  }),
  'user-2': createMockUserPermissionMatrix('user-2', {
    [AgentName.CLIENT_MANAGEMENT]: createMockPermissions({ create: false, read: true, update: false, delete: false }),
    [AgentName.PDF_PROCESSING]: createMockPermissions({ create: true, read: true, update: true, delete: false }),
    [AgentName.REPORTS_ANALYSIS]: createMockPermissions({ create: false, read: true, update: false, delete: false }),
    [AgentName.AUDIO_RECORDING]: createMockPermissions({ create: false, read: false, update: false, delete: false }),
  }),
  'user-3': createMockUserPermissionMatrix('user-3', {
    [AgentName.CLIENT_MANAGEMENT]: createMockPermissions({ create: true, read: true, update: true, delete: true }),
    [AgentName.PDF_PROCESSING]: createMockPermissions({ create: true, read: true, update: true, delete: true }),
    [AgentName.REPORTS_ANALYSIS]: createMockPermissions({ create: true, read: true, update: true, delete: true }),
    [AgentName.AUDIO_RECORDING]: createMockPermissions({ create: false, read: false, update: false, delete: false }),
  })
}

const mockFetch = vi.fn()

// Helper function to setup comprehensive mocks for all API calls
const setupStandardMocks = () => {
  // Clear any previous mock calls
  mockFetch.mockClear()
  
  // Always return success for any API call - comprehensive fallback
  mockFetch.mockImplementation((url: string) => {
    // Permission matrix API calls
    if (url.includes('/api/v1/permissions/user/')) {
      const userId = url.split('/').pop()
      const matrix = mockPermissionMatrix[userId!] || createMockUserPermissionMatrix(userId)
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(matrix)
      } as Response)
    }
    
    // Auth/user API calls
    if (url.includes('/api/v1/auth/me') || url.includes('/api/v1/users/me')) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ user: mockAdminUser })
      } as Response)
    }
    
    // Permission check API calls
    if (url.includes('/api/v1/permissions/check')) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ 
          allowed: true,
          user_id: mockAdminUser.user_id,
          agent: AgentName.CLIENT_MANAGEMENT,
          operation: 'read'
        })
      } as Response)
    }
    
    // Default successful response for any other API call
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ success: true })
    } as Response)
  })
}

beforeEach(() => {
  global.fetch = mockFetch
  
  // Initialize auth store with admin user for all tests
  const store = useAuthStore.getState()
  store.setUser(mockAdminUser)
  store.setToken('mock-test-token')
  
  // Mock ResizeObserver (browser API - external boundary)
  global.ResizeObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  }))

  // Mock WebSocket (external API)
  global.WebSocket = vi.fn().mockImplementation(() => ({
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    send: vi.fn(),
    close: vi.fn(),
    readyState: WebSocket.OPEN
  }))
})

afterEach(() => {
  vi.clearAllMocks()
})

describe('PermissionMatrix Component', () => {
  describe('Basic Rendering', () => {
    it('should render permission matrix table with users and agents', async () => {
      setupStandardMocks()

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      // Should show user information
      expect(screen.getByText('User One')).toBeInTheDocument()
      expect(screen.getByText('user1@test.com')).toBeInTheDocument()
      expect(screen.getByText('User Two')).toBeInTheDocument()
      expect(screen.getByText('user2@test.com')).toBeInTheDocument()

      // Should show agent columns
      expect(screen.getByText('Gestão de Clientes')).toBeInTheDocument()
      expect(screen.getByText('Processamento PDF')).toBeInTheDocument()
      expect(screen.getByText('Relatórios')).toBeInTheDocument()
      expect(screen.getByText('Gravação de Áudio')).toBeInTheDocument()
    })

    it('should render permission badges for each user-agent combination', async () => {
      setupStandardMocks()

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        // Should show permission level badges
        expect(screen.getByText('Padrão')).toBeInTheDocument() // User 1 - Client Management
        expect(screen.getByText('Leitura')).toBeInTheDocument() // User 1 - PDF Processing  
        expect(screen.getByText('Sem Acesso')).toBeInTheDocument() // Various no-access permissions
      })
    })

    it('should show user status indicators', async () => {
      setupStandardMocks()

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        // Should show active/inactive status
        expect(screen.getByText('Ativo')).toBeInTheDocument()
        expect(screen.getByText('Inativo')).toBeInTheDocument()
      })
    })
  })

  describe('Loading States', () => {
    it('should show loading skeleton while fetching data', () => {
      // Mock delayed responses
      const delayedAuthPromise = new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ user: mockAdminUser })
        }), 100)
      )
      const delayedUsersPromise = new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ users: mockUsers })
        }), 100)
      )
      
      mockFetch
        .mockReturnValueOnce(delayedAuthPromise as any)
        .mockReturnValueOnce(delayedUsersPromise as any)

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      // Should show loading skeleton
      expect(screen.getAllByTestId('user-row-skeleton')).toHaveLength(3) // Default skeleton rows
    })

    it('should show loading state for permission updates', async () => {
      setupStandardMocks()

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      // Mock updating permission response
      setupPermissionSaveTest()

      // Click on a permission badge to update
      const user = userEvent.setup()
      const permissionBadge = screen.getAllByRole('button', { name: /sem acesso|leitura|padrão|completo/i })[0]
      await user.click(permissionBadge)

      // Should show loading indicator
      expect(screen.getByTestId('permission-updating-indicator')).toBeInTheDocument()
    })
  })

  describe('Search and Filtering', () => {
    beforeEach(async () => {
      // Reset mocks before each test
      mockFetch.mockClear()
    })

    it('should filter users by search query', async () => {
      const user = userEvent.setup()
      setupStandardMocks()

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText(/buscar usuários/i)
      await user.type(searchInput, 'User One')

      await waitFor(() => {
        expect(screen.getByText('User One')).toBeInTheDocument()
        expect(screen.queryByText('User Two')).not.toBeInTheDocument()
        expect(screen.queryByText('User Three (Inactive)')).not.toBeInTheDocument()
      })
    })

    it('should filter by user role', async () => {
      const user = userEvent.setup()
      setupStandardMocks()

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      const roleFilter = screen.getByRole('combobox', { name: /filtrar por função/i })
      await user.click(roleFilter)
      await user.click(screen.getByText('Admin'))

      await waitFor(() => {
        expect(screen.getByText('User Three (Inactive)')).toBeInTheDocument()
        expect(screen.queryByText('User One')).not.toBeInTheDocument()
        expect(screen.queryByText('User Two')).not.toBeInTheDocument()
      })
    })

    it('should filter by user status', async () => {
      const user = userEvent.setup()
      setupStandardMocks()

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      const statusFilter = screen.getByRole('combobox', { name: /filtrar por status/i })
      await user.click(statusFilter)
      await user.click(screen.getByText('Inativo'))

      await waitFor(() => {
        expect(screen.getByText('User Three (Inactive)')).toBeInTheDocument()
        expect(screen.queryByText('User One')).not.toBeInTheDocument()
        expect(screen.queryByText('User Two')).not.toBeInTheDocument()
      })
    })

    it('should combine multiple filters', async () => {
      const user = userEvent.setup()
      setupStandardMocks()

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      // Search for "user" AND filter by active status
      const searchInput = screen.getByPlaceholderText(/buscar usuários/i)
      await user.type(searchInput, 'user')

      const statusFilter = screen.getByRole('combobox', { name: /filtrar por status/i })
      await user.click(statusFilter)
      await user.click(screen.getByText('Ativo'))

      await waitFor(() => {
        expect(screen.getByText('User One')).toBeInTheDocument()
        expect(screen.getByText('User Two')).toBeInTheDocument()
        expect(screen.queryByText('User Three (Inactive)')).not.toBeInTheDocument()
      })
    })
  })

  describe('Permission Editing', () => {
    beforeEach(async () => {
      // Reset mocks before each test
      mockFetch.mockClear()
    })

    it('should allow clicking permission badges to edit', async () => {
      const user = userEvent.setup()
      setupStandardMocks()

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      // Find and click a permission badge
      const nonePermissionBadge = screen.getAllByText('Sem Acesso')[0]
      await user.click(nonePermissionBadge)

      // Should open permission level selection
      expect(screen.getByRole('menu')).toBeInTheDocument()
      expect(screen.getByText('Leitura')).toBeInTheDocument()
      expect(screen.getByText('Padrão')).toBeInTheDocument()
      expect(screen.getByText('Completo')).toBeInTheDocument()
    })

    it('should update permission when new level is selected', async () => {
      const user = userEvent.setup()
      setupStandardMocks()
      
      // Mock permission update response
      setupPermissionSaveTest()

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      // Click a "Sem Acesso" permission to change it
      const nonePermissionBadge = screen.getAllByText('Sem Acesso')[0]
      await user.click(nonePermissionBadge)

      // Select "Leitura" level
      await user.click(screen.getByText('Leitura'))

      // Should call API to update permission
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/permissions/'),
          expect.objectContaining({
            method: 'PUT',
            headers: expect.objectContaining({
              'Content-Type': 'application/json'
            }),
            body: expect.stringContaining('read')
          })
        )
      })
    })

    it('should show confirmation dialog for destructive permission changes', async () => {
      const user = userEvent.setup()
      setupStandardMocks()

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      // Click a "Completo" permission to remove it
      const fullPermissionBadge = screen.getAllByText('Completo')[0]
      await user.click(fullPermissionBadge)

      // Select "Sem Acesso" to remove all permissions
      await user.click(screen.getByText('Sem Acesso'))

      // Should show confirmation dialog
      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByText(/tem certeza que deseja remover/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /confirmar/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /cancelar/i })).toBeInTheDocument()
    })

    it('should handle permission update errors', async () => {
      const user = userEvent.setup()
      setupStandardMocks()
      
      // Mock API error
      setupPermissionSaveTest({ shouldFail: true })

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      // Try to update permission
      const nonePermissionBadge = screen.getAllByText('Sem Acesso')[0]
      await user.click(nonePermissionBadge)
      await user.click(screen.getByText('Padrão'))

      // Should show error message
      await waitFor(() => {
        expect(screen.getByText(/erro ao atualizar permissões/i)).toBeInTheDocument()
      })
    })
  })

  describe('Bulk Selection', () => {
    beforeEach(async () => {
      // Reset mocks before each test
      mockFetch.mockClear()
    })

    it('should allow selecting multiple users with checkboxes', async () => {
      const user = userEvent.setup()
      setupStandardMocks()

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      // Select individual users
      const userCheckboxes = screen.getAllByRole('checkbox', { name: /selecionar usuário/i })
      await user.click(userCheckboxes[0])
      await user.click(userCheckboxes[1])

      // Should show bulk actions bar
      expect(screen.getByText(/2 usuários selecionados/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /operações em lote/i })).toBeInTheDocument()
    })

    it('should allow selecting all users with header checkbox', async () => {
      const user = userEvent.setup()
      setupStandardMocks()

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      // Click select all checkbox
      const selectAllCheckbox = screen.getByRole('checkbox', { name: /selecionar todos/i })
      await user.click(selectAllCheckbox)

      // Should select all visible users
      expect(screen.getByText(/3 usuários selecionados/i)).toBeInTheDocument()
    })

    it('should open bulk operations dialog when bulk button is clicked', async () => {
      const user = userEvent.setup()
      setupStandardMocks()

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      // Select users
      const userCheckboxes = screen.getAllByRole('checkbox', { name: /selecionar usuário/i })
      await user.click(userCheckboxes[0])
      await user.click(userCheckboxes[1])

      // Click bulk operations
      const bulkButton = screen.getByRole('button', { name: /operações em lote/i })
      await user.click(bulkButton)

      // Should open bulk permissions dialog
      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByText(/operações em lote para 2 usuários/i)).toBeInTheDocument()
    })
  })

  describe('Responsive Design', () => {
    beforeEach(async () => {
      // Reset mocks before each test
      mockFetch.mockClear()
    })

    it('should display horizontally scrollable table on mobile', async () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375, // Mobile width
      })

      setupStandardMocks()

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      // Table container should be scrollable
      const tableContainer = screen.getByTestId('permission-matrix-container')
      expect(tableContainer).toHaveClass('overflow-x-auto')
    })

    it('should show collapsible agent columns on tablet', async () => {
      // Mock tablet viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768, // Tablet width
      })

      const user = userEvent.setup()
      setupStandardMocks()

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      // Should have column visibility controls
      expect(screen.getByRole('button', { name: /mostrar\/ocultar colunas/i })).toBeInTheDocument()

      // Click to open column selector
      const columnButton = screen.getByRole('button', { name: /mostrar\/ocultar colunas/i })
      await user.click(columnButton)

      // Should show agent column toggles
      expect(screen.getByText('Gestão de Clientes')).toBeInTheDocument()
      expect(screen.getByText('Processamento PDF')).toBeInTheDocument()
    })

    it('should use card layout on mobile for better readability', async () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 320, // Small mobile width
      })

      setupStandardMocks()

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        // Should show card layout instead of table on very small screens
        expect(screen.getByTestId('permission-matrix-cards')).toBeInTheDocument()
      })

      // Each user should be in a card
      expect(screen.getByText('User One')).toBeInTheDocument()
      expect(screen.getByText('User Two')).toBeInTheDocument()

      // Permission badges should be in card format
      const userOneCard = screen.getByTestId('user-card-user-1')
      expect(within(userOneCard).getByText('Padrão')).toBeInTheDocument()
    })

    it('should maintain functionality across different screen sizes', async () => {
      const user = userEvent.setup()

      // Start with desktop
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1024,
      })

      setupStandardMocks()

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      // Should be able to edit permissions on desktop
      const permissionBadge = screen.getAllByText('Sem Acesso')[0]
      await user.click(permissionBadge)
      expect(screen.getByRole('menu')).toBeInTheDocument()

      // Switch to mobile view
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      })
      
      // Trigger resize
      window.dispatchEvent(new Event('resize'))

      await waitFor(() => {
        // Should switch to mobile layout but maintain functionality
        expect(screen.getByTestId('permission-matrix-container')).toHaveClass('overflow-x-auto')
      })

      // Permission editing should still work
      const mobileBadge = screen.getAllByText('Sem Acesso')[0]
      await user.click(mobileBadge)
      expect(screen.getByRole('menu')).toBeInTheDocument()
    })
  })

  describe('Real-time Updates', () => {
    beforeEach(async () => {
      // Reset mocks before each test
      mockFetch.mockClear()
    })

    it('should update UI when permissions change via WebSocket', async () => {
      setupStandardMocks()

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      // Initial state - user-1 should have "Padrão" for client_management
      expect(screen.getByText('Padrão')).toBeInTheDocument()

      // Mock updated permissions from WebSocket
      const updatedMatrix = createMockUserPermissionMatrix('user-1', {
        [AgentName.CLIENT_MANAGEMENT]: createMockPermissions({ create: true, read: true, update: true, delete: true })
      })

      // Simulate WebSocket permission update
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(updatedMatrix)
      } as Response)

      // Trigger permission refetch (simulating WebSocket event)
      const refreshButton = screen.getByRole('button', { name: /atualizar/i })
      await userEvent.setup().click(refreshButton)

      await waitFor(() => {
        expect(screen.getByText('Completo')).toBeInTheDocument()
      })
    })

    it('should show real-time notification when permissions are updated', async () => {
      setupStandardMocks()

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      // Simulate receiving WebSocket notification
      const mockNotification = {
        type: 'permission_updated',
        userId: 'user-1',
        agent: 'client_management',
        changes: { delete: true }
      }

      // This would normally come through WebSocket
      window.dispatchEvent(new CustomEvent('permission-update', { detail: mockNotification }))

      await waitFor(() => {
        expect(screen.getByText(/permissões atualizadas em tempo real/i)).toBeInTheDocument()
      })
    })
  })

  describe('Performance and Virtualization', () => {
    it('should handle large number of users with virtual scrolling', async () => {
      // Generate large user list
      const largeUserList = Array.from({ length: 500 }, (_, i) => 
        createMockUser({
          user_id: `user-${i}`,
          email: `user${i}@test.com`,
          full_name: `User ${i}`,
        })
      )

      // Setup authentication mock
      setupUserAPITest({ user: mockAdminUser })
      
      // Setup large users list mock
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ users: largeUserList })
      } as Response)

      // Setup empty permissions for large list
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({})
      } as Response)

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={largeUserList}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      // Should only render visible rows (virtual scrolling)
      const userRows = screen.getAllByTestId(/user-row-/)
      expect(userRows.length).toBeLessThan(500) // Should not render all 500 rows
      expect(userRows.length).toBeGreaterThan(10) // Should render a reasonable number

      // Should show virtual scroll indicators
      expect(screen.getByTestId('virtual-scroll-container')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    beforeEach(async () => {
      // Reset mocks before each test
      mockFetch.mockClear()
    })

    it('should have proper ARIA labels and roles', async () => {
      setupStandardMocks()

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      // Table should have proper accessibility attributes
      const table = screen.getByRole('table')
      expect(table).toHaveAttribute('aria-label', 'Matriz de Permissões de Usuários')

      // Column headers should be properly labeled
      expect(screen.getByRole('columnheader', { name: /usuário/i })).toBeInTheDocument()
      expect(screen.getByRole('columnheader', { name: /gestão de clientes/i })).toBeInTheDocument()

      // Permission buttons should have descriptive labels
      const permissionButtons = screen.getAllByRole('button', { name: /alterar permissão/i })
      expect(permissionButtons.length).toBeGreaterThan(0)
    })

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup()
      setupStandardMocks()

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      // Should be able to tab through permission buttons
      await user.tab()
      expect(screen.getAllByRole('button')[0]).toHaveFocus()

      await user.tab()
      expect(screen.getAllByRole('button')[1]).toHaveFocus()

      // Should be able to activate with Enter/Space
      await user.keyboard('{Enter}')
      expect(screen.getByRole('menu')).toBeInTheDocument()
    })

    it('should announce changes to screen readers', async () => {
      const user = userEvent.setup()
      setupStandardMocks()
      
      // Mock permission update response
      setupPermissionSaveTest()

      render(
        <TestWrapper>
          <PermissionMatrix 
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
      })

      // Update a permission
      const permissionBadge = screen.getAllByText('Sem Acesso')[0]
      await user.click(permissionBadge)
      await user.click(screen.getByText('Leitura'))

      await waitFor(() => {
        // Should have live region with update announcement
        expect(screen.getByRole('status')).toHaveTextContent(/permissão atualizada com sucesso/i)
      })
    })
  })
})