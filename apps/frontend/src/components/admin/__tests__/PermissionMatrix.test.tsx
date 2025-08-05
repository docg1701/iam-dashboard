/**
 * Permission Matrix Component Tests
 * 
 * Comprehensive test suite for the PermissionMatrix component covering
 * all user interactions, responsive behavior, and permission management.
 */

import React from 'react'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { PermissionMatrix } from '../PermissionMatrix'
import { 
  AgentName, 
  PERMISSION_LEVELS, 
  getPermissionsForLevel,
  DEFAULT_AGENT_PERMISSIONS,
} from '@/types/permissions'
import * as permissionAPI from '@/lib/api/permissions'

// Mock the PermissionAPI
vi.mock('@/lib/api/permissions', () => ({
  PermissionAPI: {
    User: {
      getUserPermissions: vi.fn(),
      updateUserPermission: vi.fn(),
      createUserPermission: vi.fn(),
    },
    Utils: {
      hasPermission: vi.fn(),
      hasAgentPermission: vi.fn(),
    },
  },
}))

// Mock the PermissionGuard components
vi.mock('@/components/common/PermissionGuard', () => ({
  PermissionGuard: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  UpdatePermissionGuard: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

// Mock toast notifications
vi.mock('@/components/ui/toast', () => ({
  toast: vi.fn(),
}))

// Mock ResizeObserver for responsive testing
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Test data
const mockUsers = [
  {
    user_id: 'user-1',
    name: 'João Silva',
    email: 'joao@example.com',
    role: 'admin' as const,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    user_id: 'user-2', 
    name: 'Maria Santos',
    email: 'maria@example.com',
    role: 'user' as const,
    is_active: true,
    created_at: '2024-01-02T00:00:00Z',
  },
  {
    user_id: 'user-3',
    name: 'Pedro Costa',
    email: 'pedro@example.com',
    role: 'user' as const,
    is_active: false,
    created_at: '2024-01-03T00:00:00Z',
  },
]

const mockUserPermissions = {
  'user-1': {
    user_id: 'user-1',
    permissions: {
      [AgentName.CLIENT_MANAGEMENT]: getPermissionsForLevel(PERMISSION_LEVELS.FULL),
      [AgentName.PDF_PROCESSING]: getPermissionsForLevel(PERMISSION_LEVELS.STANDARD),
      [AgentName.REPORTS_ANALYSIS]: getPermissionsForLevel(PERMISSION_LEVELS.READ_ONLY),
      [AgentName.AUDIO_RECORDING]: getPermissionsForLevel(PERMISSION_LEVELS.NONE),
    },
    last_updated: '2024-01-01T00:00:00Z',
  },
  'user-2': {
    user_id: 'user-2',
    permissions: {
      [AgentName.CLIENT_MANAGEMENT]: getPermissionsForLevel(PERMISSION_LEVELS.READ_ONLY),
      [AgentName.PDF_PROCESSING]: getPermissionsForLevel(PERMISSION_LEVELS.NONE),
      [AgentName.REPORTS_ANALYSIS]: getPermissionsForLevel(PERMISSION_LEVELS.NONE),
      [AgentName.AUDIO_RECORDING]: getPermissionsForLevel(PERMISSION_LEVELS.NONE),
    },
    last_updated: '2024-01-02T00:00:00Z',
  },
  'user-3': {
    user_id: 'user-3',
    permissions: DEFAULT_AGENT_PERMISSIONS,
    last_updated: '2024-01-03T00:00:00Z',
  },
}

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('PermissionMatrix Component', () => {
  const mockOnUserPermissionsChange = vi.fn()
  const mockOnBulkAction = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    
    // Setup API mocks
    vi.mocked(permissionAPI.PermissionAPI.User.getUserPermissions).mockImplementation(
      (userId: string) => Promise.resolve(mockUserPermissions[userId])
    )
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  const renderPermissionMatrix = (props = {}) => {
    const defaultProps = {
      users: mockUsers,
      onUserPermissionsChange: mockOnUserPermissionsChange,
      onBulkAction: mockOnBulkAction,
      ...props,
    }

    return render(
      <TestWrapper>
        <PermissionMatrix {...defaultProps} />
      </TestWrapper>
    )
  }

  describe('Component Rendering', () => {
    it('should render without crashing', () => {
      renderPermissionMatrix()
      expect(screen.getByText('Matriz de Permissões')).toBeInTheDocument()
    })

    it('should display loading state initially', () => {
      renderPermissionMatrix()
      expect(screen.getByText('Carregando permissões...')).toBeInTheDocument()
    })

    it('should render user statistics correctly', async () => {
      renderPermissionMatrix()

      await waitFor(() => {
        expect(screen.getByText('Total de Usuários')).toBeInTheDocument()
        expect(screen.getByText('3')).toBeInTheDocument() // Total users count
      })
    })

    it('should render all agent columns in desktop view', async () => {
      renderPermissionMatrix()

      await waitFor(() => {
        expect(screen.getByText('Gestão de Clientes')).toBeInTheDocument()
        expect(screen.getByText('Processamento PDFs')).toBeInTheDocument()
        expect(screen.getByText('Relatórios')).toBeInTheDocument()
        expect(screen.getByText('Gravação de Áudio')).toBeInTheDocument()
      })
    })

    it('should render user information correctly', async () => {
      renderPermissionMatrix()

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
        expect(screen.getByText('joao@example.com')).toBeInTheDocument()
        expect(screen.getByText('Maria Santos')).toBeInTheDocument()
        expect(screen.getByText('maria@example.com')).toBeInTheDocument()
      })
    })
  })

  describe('Filtering Functionality', () => {
    it('should filter users by search term', async () => {
      renderPermissionMatrix()

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText('Buscar usuários...')
      await userEvent.type(searchInput, 'João')

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
        expect(screen.queryByText('Maria Santos')).not.toBeInTheDocument()
      })
    })

    it('should filter users by role', async () => {
      renderPermissionMatrix()

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      const roleSelect = screen.getByDisplayValue('Todos os Cargos')
      await userEvent.click(roleSelect)
      await userEvent.click(screen.getByText('Administrador'))

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
        expect(screen.queryByText('Maria Santos')).not.toBeInTheDocument()
      })
    })

    it('should filter users by status', async () => {
      renderPermissionMatrix()

      await waitFor(() => {
        expect(screen.getByText('Pedro Costa')).toBeInTheDocument()
      })

      const statusSelect = screen.getByDisplayValue('Todos')
      await userEvent.click(statusSelect)
      await userEvent.click(screen.getByText('Inativos'))

      await waitFor(() => {
        expect(screen.getByText('Pedro Costa')).toBeInTheDocument()
        expect(screen.queryByText('João Silva')).not.toBeInTheDocument()
        expect(screen.queryByText('Maria Santos')).not.toBeInTheDocument()
      })
    })
  })

  describe('Permission Level Display', () => {
    it('should display correct permission levels for users', async () => {
      renderPermissionMatrix()

      await waitFor(() => {
        // Check João Silva's permissions (user-1)
        const joaoRow = screen.getByText('João Silva').closest('tr')
        expect(joaoRow).toBeInTheDocument()
        
        if (joaoRow) {
          expect(within(joaoRow).getByText('Completo')).toBeInTheDocument() // CLIENT_MANAGEMENT
          expect(within(joaoRow).getByText('Padrão')).toBeInTheDocument()   // PDF_PROCESSING
          expect(within(joaoRow).getByText('Leitura')).toBeInTheDocument()  // REPORTS_ANALYSIS
          expect(within(joaoRow).getByText('Sem Acesso')).toBeInTheDocument() // AUDIO_RECORDING
        }
      })
    })

    it('should display permission badges with correct colors', async () => {
      renderPermissionMatrix()

      await waitFor(() => {
        const completeBadge = screen.getByText('Completo')
        expect(completeBadge).toHaveClass('bg-purple-100', 'text-purple-800')

        const readOnlyBadge = screen.getByText('Leitura')
        expect(readOnlyBadge).toHaveClass('bg-blue-100', 'text-blue-800')
      })
    })
  })

  describe('User Selection', () => {
    it('should handle individual user selection', async () => {
      renderPermissionMatrix()

      await waitFor(() => {
        const checkboxes = screen.getAllByRole('checkbox')
        expect(checkboxes).toHaveLength(4) // 3 users + select all
      })

      const userCheckbox = screen.getAllByRole('checkbox')[1] // First user checkbox
      await userEvent.click(userCheckbox)

      expect(userCheckbox).toBeChecked()
    })

    it('should handle select all functionality', async () => {
      renderPermissionMatrix()

      await waitFor(() => {
        const selectAllCheckbox = screen.getAllByRole('checkbox')[0]
        await userEvent.click(selectAllCheckbox)

        const userCheckboxes = screen.getAllByRole('checkbox').slice(1)
        userCheckboxes.forEach(checkbox => {
          expect(checkbox).toBeChecked()
        })
      })
    })

    it('should enable bulk actions when users are selected', async () => {
      renderPermissionMatrix()

      await waitFor(() => {
        const bulkActionsButton = screen.getByText(/Ações \(0\)/)
        expect(bulkActionsButton).toBeDisabled()
      })

      const userCheckbox = screen.getAllByRole('checkbox')[1]
      await userEvent.click(userCheckbox)

      await waitFor(() => {
        const bulkActionsButton = screen.getByText(/Ações \(1\)/)
        expect(bulkActionsButton).not.toBeDisabled()
      })
    })
  })

  describe('Bulk Actions', () => {
    it('should trigger bulk actions when button is clicked', async () => {
      renderPermissionMatrix()

      await waitFor(() => {
        const userCheckbox = screen.getAllByRole('checkbox')[1]
        userEvent.click(userCheckbox)
      })

      await waitFor(() => {
        const bulkActionsButton = screen.getByText(/Ações \(1\)/)
        userEvent.click(bulkActionsButton)
      })

      await waitFor(() => {
        const grantAllOption = screen.getByText('Conceder Todas Permissões')
        userEvent.click(grantAllOption)
      })

      expect(mockOnBulkAction).toHaveBeenCalledWith(['user-1'], 'grant_all')
    })

    it('should show error toast when no users are selected for bulk action', async () => {
      const { toast } = await import('@/components/ui/toast')
      renderPermissionMatrix()

      await waitFor(() => {
        const applyTemplateButton = screen.getByText('Aplicar Template')
        userEvent.click(applyTemplateButton)
      })

      expect(toast).toHaveBeenCalledWith({
        title: 'Nenhum usuário selecionado',
        description: 'Selecione pelo menos um usuário para executar ações em lote.',
        variant: 'error',
      })
    })
  })

  describe('Permission Editing', () => {
    it('should allow inline permission editing', async () => {
      renderPermissionMatrix()

      await waitFor(() => {
        const permissionBadge = screen.getByText('Completo')
        userEvent.click(permissionBadge)
      })

      await waitFor(() => {
        const selectDropdown = screen.getByRole('combobox')
        expect(selectDropdown).toBeInTheDocument()
      })
    })

    it('should update permission level when changed', async () => {
      renderPermissionMatrix()

      await waitFor(() => {
        const permissionBadge = screen.getByText('Completo')
        userEvent.click(permissionBadge)
      })

      await waitFor(() => {
        const selectDropdown = screen.getByRole('combobox')
        userEvent.click(selectDropdown)
        
        const readOnlyOption = screen.getByText('Leitura')
        userEvent.click(readOnlyOption)
      })

      // Should trigger permission update
      await waitFor(() => {
        expect(mockOnUserPermissionsChange).toHaveBeenCalled()
      })
    })
  })

  describe('Responsive Behavior', () => {
    it('should show mobile card view on small screens', () => {
      // Mock window.matchMedia for mobile
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: vi.fn().mockImplementation(query => ({
          matches: query === '(max-width: 768px)',
          media: query,
          onchange: null,
          addListener: vi.fn(),
          removeListener: vi.fn(),
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          dispatchEvent: vi.fn(),
        })),
      })

      renderPermissionMatrix()

      // Mobile view should show cards instead of table
      expect(screen.queryByRole('table')).not.toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      vi.mocked(permissionAPI.PermissionAPI.User.getUserPermissions).mockRejectedValue(
        new Error('API Error')
      )

      renderPermissionMatrix()

      await waitFor(() => {
        // Should show user data even if permissions fail to load
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })
    })

    it('should show default permissions when user permissions are not found', async () => {
      vi.mocked(permissionAPI.PermissionAPI.User.getUserPermissions).mockResolvedValue({
        user_id: 'user-1',
        permissions: DEFAULT_AGENT_PERMISSIONS,
        last_updated: '2024-01-01T00:00:00Z',
      })

      renderPermissionMatrix()

      await waitFor(() => {
        const semAcessoBadges = screen.getAllByText('Sem Acesso')
        expect(semAcessoBadges).toHaveLength(4) // All agents should show no access
      })
    })
  })

  describe('Performance', () => {
    it('should handle large numbers of users efficiently', async () => {
      const manyUsers = Array.from({ length: 100 }, (_, i) => ({
        user_id: `user-${i}`,
        name: `User ${i}`,
        email: `user${i}@example.com`,
        role: 'user' as const,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
      }))

      renderPermissionMatrix({ users: manyUsers })

      await waitFor(() => {
        expect(screen.getByText('100')).toBeInTheDocument() // Total users count
      })
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels', async () => {
      renderPermissionMatrix()

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
        expect(screen.getAllByRole('checkbox')).toHaveLength(4)
        expect(screen.getByRole('searchbox')).toBeInTheDocument()
      })
    })

    it('should support keyboard navigation', async () => {
      renderPermissionMatrix()

      await waitFor(() => {
        const searchInput = screen.getByRole('searchbox')
        searchInput.focus()
        expect(searchInput).toHaveFocus()
      })
    })
  })
})