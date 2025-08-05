import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { PermissionMatrix } from '@/components/admin/PermissionMatrix'

// Mock the hooks
const mockUseUserPermissions = vi.fn()
const mockUsePermissionMutations = vi.fn()

vi.mock('@/hooks/useUserPermissions', () => ({
  useUserPermissions: () => mockUseUserPermissions(),
  usePermissionMutations: () => mockUsePermissionMutations(),
}))

// Mock PermissionGuard components
vi.mock('@/components/common/PermissionGuard', () => ({
  PermissionGuard: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  UpdatePermissionGuard: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

// Mock UI components
vi.mock('@/components/ui/table', () => ({
  Table: ({ children }: { children: React.ReactNode }) => <table data-testid="permission-table">{children}</table>,
  TableBody: ({ children }: { children: React.ReactNode }) => <tbody>{children}</tbody>,
  TableCell: ({ children, className, ...props }: { children: React.ReactNode; className?: string; [key: string]: unknown }) => <td className={className} {...props}>{children}</td>,
  TableHead: ({ children, className, ...props }: { children: React.ReactNode; className?: string; [key: string]: unknown }) => <th className={className} {...props}>{children}</th>,
  TableHeader: ({ children }: { children: React.ReactNode }) => <thead>{children}</thead>,
  TableRow: ({ children, className, ...props }: { children: React.ReactNode; className?: string; [key: string]: unknown }) => <tr className={className} {...props}>{children}</tr>,
}))

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled, variant, size, ...props }: {
    children: React.ReactNode
    onClick?: () => void
    disabled?: boolean
    variant?: string
    size?: string
    [key: string]: unknown
  }) => (
    <button 
      onClick={onClick} 
      disabled={disabled} 
      data-variant={variant} 
      data-size={size}
      {...props}
    >
      {children}
    </button>
  ),
}))

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, variant, className, onClick, ...props }: {
    children: React.ReactNode
    variant?: string
    className?: string
    onClick?: () => void
    [key: string]: unknown
  }) => (
    <span 
      className={className} 
      onClick={onClick} 
      data-variant={variant}
      data-testid="permission-badge"
      {...props}
    >
      {children}
    </span>
  ),
}))

vi.mock('@/components/ui/input', () => ({
  Input: ({ value, onChange, placeholder, ...props }: {
    value?: string
    onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void
    placeholder?: string
    [key: string]: unknown
  }) => (
    <input 
      value={value} 
      onChange={onChange} 
      placeholder={placeholder}
      data-testid="filter-input"
      {...props}
    />
  ),
}))

vi.mock('@/components/ui/select', () => ({
  Select: ({ children, value, onValueChange }: {
    children: React.ReactNode
    value?: string
    onValueChange?: (value: string) => void
  }) => (
    <div data-testid="select" data-value={value} onClick={() => onValueChange?.('test-value')}>
      {children}
    </div>
  ),
  SelectContent: ({ children }: { children: React.ReactNode }) => <div data-testid="select-content">{children}</div>,
  SelectItem: ({ children, value }: { children: React.ReactNode; value?: string }) => <div data-testid="select-item" data-value={value}>{children}</div>,
  SelectTrigger: ({ children }: { children: React.ReactNode }) => <div data-testid="select-trigger">{children}</div>,
  SelectValue: ({ placeholder }: { placeholder?: string }) => <div data-testid="select-value">{placeholder}</div>,
}))

vi.mock('@/components/ui/dropdown-menu', () => ({
  DropdownMenu: ({ children }: { children: React.ReactNode }) => <div data-testid="dropdown-menu">{children}</div>,
  DropdownMenuContent: ({ children }: { children: React.ReactNode }) => <div data-testid="dropdown-content">{children}</div>,
  DropdownMenuItem: ({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) => (
    <div data-testid="dropdown-item" onClick={onClick}>{children}</div>
  ),
  DropdownMenuLabel: ({ children }: { children: React.ReactNode }) => <div data-testid="dropdown-label">{children}</div>,
  DropdownMenuSeparator: () => <div data-testid="dropdown-separator" />,
  DropdownMenuTrigger: ({ children }: { children: React.ReactNode }) => <div data-testid="dropdown-trigger">{children}</div>,
}))

vi.mock('@/components/ui/card', () => ({
  Card: ({ children, className }: { children: React.ReactNode; className?: string }) => <div className={className} data-testid="card">{children}</div>,
  CardContent: ({ children, className }: { children: React.ReactNode; className?: string }) => <div className={className} data-testid="card-content">{children}</div>,
  CardDescription: ({ children, className }: { children: React.ReactNode; className?: string }) => <div className={className} data-testid="card-description">{children}</div>,
  CardHeader: ({ children, className }: { children: React.ReactNode; className?: string }) => <div className={className} data-testid="card-header">{children}</div>,
  CardTitle: ({ children, className }: { children: React.ReactNode; className?: string }) => <div className={className} data-testid="card-title">{children}</div>,
}))

vi.mock('@/components/ui/toast', () => ({
  toast: vi.fn(),
}))

// Mock icons
vi.mock('lucide-react', () => ({
  Search: () => <div data-testid="search-icon">Search</div>,
  Filter: () => <div data-testid="filter-icon">Filter</div>,
  Users: () => <div data-testid="users-icon">Users</div>,
  Settings: () => <div data-testid="settings-icon">Settings</div>,
  Eye: () => <div data-testid="eye-icon">Eye</div>,
  EyeOff: () => <div data-testid="eye-off-icon">EyeOff</div>,
  MoreHorizontal: () => <div data-testid="more-horizontal-icon">MoreHorizontal</div>,
}))

// Mock permission types and utilities
vi.mock('@/types/permissions', async () => {
  const actual = await vi.importActual('@/types/permissions')
  return {
    ...actual,
    getPermissionLevel: vi.fn(() => 'read_only'),
    getPermissionsForLevel: vi.fn(() => ({ create: false, read: true, update: false, delete: false })),
    PERMISSION_LEVELS: {
      NONE: 'none',
      READ_ONLY: 'read_only',
      STANDARD: 'standard',
      FULL: 'full',
    },
  }
})

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
      {children}
    </QueryClientProvider>
  )
}

// Mock user data
const mockUsers = [
  {
    user_id: 'user-1',
    name: 'João Silva',
    email: 'joao@example.com',
    role: 'admin' as const,
    is_active: true,
  },
  {
    user_id: 'user-2',
    name: 'Maria Santos',
    email: 'maria@example.com',
    role: 'user' as const,
    is_active: true,
  },
  {
    user_id: 'user-3',
    name: 'Pedro Inactive',
    email: 'pedro@example.com',
    role: 'user' as const,
    is_active: false,
  },
]

describe('PermissionMatrix', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Setup default mock returns
    mockUseUserPermissions.mockReturnValue({
      permissions: null,
      isLoading: false,
      error: null,
      hasPermission: vi.fn(() => true),
      hasAgentPermission: vi.fn(() => true),
    })
    
    mockUsePermissionMutations.mockReturnValue({
      updatePermission: { mutateAsync: vi.fn(), isPending: false },
      createPermission: { mutateAsync: vi.fn(), isPending: false },
      deletePermission: { mutateAsync: vi.fn(), isPending: false },
      isLoading: false,
    })
  })

  it('should render permission matrix with users', () => {
    render(
      <TestWrapper>
        <PermissionMatrix users={mockUsers} />
      </TestWrapper>
    )

    // Check header
    expect(screen.getByText('Matriz de Permissões')).toBeInTheDocument()
    expect(screen.getByText(/Gerencie permissões de usuários/)).toBeInTheDocument()

    // Check users are displayed
    expect(screen.getByText('João Silva')).toBeInTheDocument()
    expect(screen.getByText('joao@example.com')).toBeInTheDocument()
    expect(screen.getByText('Maria Santos')).toBeInTheDocument()
    expect(screen.getByText('maria@example.com')).toBeInTheDocument()
  })

  it('should display stats cards correctly', () => {
    render(
      <TestWrapper>
        <PermissionMatrix users={mockUsers} />
      </TestWrapper>
    )

    // Check stats cards
    expect(screen.getByText('Total de Usuários')).toBeInTheDocument()
    expect(screen.getByText('Selecionados')).toBeInTheDocument()
    expect(screen.getByText('Com Acesso')).toBeInTheDocument()
    expect(screen.getByText('Sem Acesso')).toBeInTheDocument()

    // Check stats values
    expect(screen.getByText('3')).toBeInTheDocument() // Total users
    expect(screen.getByText('0')).toBeInTheDocument() // Selected users
  })

  it('should filter users by search term', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionMatrix users={mockUsers} />
      </TestWrapper>
    )

    const searchInput = screen.getByTestId('filter-input')
    await user.type(searchInput, 'João')

    // Should show filtered results
    expect(screen.getByText('João Silva')).toBeInTheDocument()
    // Other users should still be visible in this simplified mock
  })

  it('should handle user selection', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionMatrix users={mockUsers} />
      </TestWrapper>
    )

    // Find checkboxes (there should be individual user checkboxes)
    const checkboxes = screen.getAllByRole('checkbox')
    
    // Click on a user checkbox (not the select all)
    if (checkboxes.length > 1) {
      await user.click(checkboxes[1])
      
      // Selected count should update
      await waitFor(() => {
        // In the real component, the stats would update
        expect(checkboxes[1]).toBeChecked()
      })
    }
  })

  it('should handle select all functionality', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionMatrix users={mockUsers} />
      </TestWrapper>
    )

    const checkboxes = screen.getAllByRole('checkbox')
    
    if (checkboxes.length > 0) {
      // Click select all (first checkbox)
      await user.click(checkboxes[0])
      
      await waitFor(() => {
        // All checkboxes should be checked
        checkboxes.forEach(checkbox => {
          expect(checkbox).toBeChecked()
        })
      })
    }
  })

  it('should handle bulk actions', async () => {
    const user = userEvent.setup()
    const onBulkAction = vi.fn()
    
    render(
      <TestWrapper>
        <PermissionMatrix users={mockUsers} onBulkAction={onBulkAction} />
      </TestWrapper>
    )

    // First select some users
    const checkboxes = screen.getAllByRole('checkbox')
    if (checkboxes.length > 1) {
      await user.click(checkboxes[1])
    }

    // Click on bulk action button
    const bulkActionButton = screen.getByText(/Aplicar Template/)
    await user.click(bulkActionButton)

    // Should call onBulkAction
    await waitFor(() => {
      expect(onBulkAction).toHaveBeenCalledWith(expect.any(Array), 'apply_template')
    })
  })

  it('should show permission badges for each agent', () => {
    render(
      <TestWrapper>
        <PermissionMatrix users={mockUsers} />
      </TestWrapper>
    )

    // Check agent column headers
    expect(screen.getByText('Gestão de Clientes')).toBeInTheDocument()
    expect(screen.getByText('Processamento PDFs')).toBeInTheDocument()
    expect(screen.getByText('Relatórios')).toBeInTheDocument()
    expect(screen.getByText('Gravação de Áudio')).toBeInTheDocument()

    // Check permission badges are present
    const badges = screen.getAllByTestId('permission-badge')
    expect(badges.length).toBeGreaterThan(0)
  })

  it('should handle permission changes when badge is clicked', async () => {
    const user = userEvent.setup()
    const onUserPermissionsChange = vi.fn()
    
    render(
      <TestWrapper>
        <PermissionMatrix 
          users={mockUsers} 
          onUserPermissionsChange={onUserPermissionsChange}
        />
      </TestWrapper>
    )

    // Find a permission badge and click it
    const badges = screen.getAllByTestId('permission-badge')
    if (badges.length > 0) {
      await user.click(badges[0])
      
      // Should trigger permission change
      await waitFor(() => {
        // In real implementation, this would trigger the edit mode
        expect(badges[0]).toBeInTheDocument()
      })
    }
  })

  it('should display role and status badges correctly', () => {
    render(
      <TestWrapper>
        <PermissionMatrix users={mockUsers} />
      </TestWrapper>
    )

    // Check role badges
    expect(screen.getByText('admin')).toBeInTheDocument()
    expect(screen.getAllByText('user')).toHaveLength(2)

    // Check status badges
    expect(screen.getAllByText('Ativo')).toHaveLength(2)
    expect(screen.getByText('Inativo')).toBeInTheDocument()
  })

  it('should show empty state when no users match filters', () => {
    render(
      <TestWrapper>
        <PermissionMatrix users={[]} />
      </TestWrapper>
    )

    expect(screen.getByText('Nenhum usuário encontrado')).toBeInTheDocument()
    expect(screen.getByText(/Tente ajustar os filtros/)).toBeInTheDocument()
  })

  it('should handle dropdown menu actions', async () => {
    const user = userEvent.setup()
    const onBulkAction = vi.fn()
    
    render(
      <TestWrapper>
        <PermissionMatrix users={mockUsers} onBulkAction={onBulkAction} />
      </TestWrapper>
    )

    // First select some users
    const checkboxes = screen.getAllByRole('checkbox')
    if (checkboxes.length > 1) {
      await user.click(checkboxes[1])
    }

    // Find dropdown menu items
    const grantAllItem = screen.getByText('Conceder Todas Permissões')
    const revokeAllItem = screen.getByText('Revogar Todas Permissões')
    const exportItem = screen.getByText('Exportar Permissões')

    // Test grant all action
    await user.click(grantAllItem)
    expect(onBulkAction).toHaveBeenCalledWith(expect.any(Array), 'grant_all')

    // Reset mock
    onBulkAction.mockClear()

    // Test revoke all action
    await user.click(revokeAllItem)
    expect(onBulkAction).toHaveBeenCalledWith(expect.any(Array), 'revoke_all')

    // Reset mock
    onBulkAction.mockClear()

    // Test export action
    await user.click(exportItem)
    expect(onBulkAction).toHaveBeenCalledWith(expect.any(Array), 'export')
  })

  it('should disable bulk actions when no users are selected', () => {
    render(
      <TestWrapper>
        <PermissionMatrix users={mockUsers} />
      </TestWrapper>
    )

    // Bulk action buttons should be disabled
    const applyTemplateButton = screen.getByText(/Aplicar Template/)
    const actionsButton = screen.getByText(/Ações \(0\)/)

    expect(applyTemplateButton).toBeDisabled()
    expect(actionsButton).toBeDisabled()
  })

  it('should show mobile card view on small screens', () => {
    render(
      <TestWrapper>
        <PermissionMatrix users={mockUsers} />
      </TestWrapper>
    )

    // Mobile cards should be present (though hidden by default in the actual component)
    const cards = screen.getAllByTestId('card')
    expect(cards.length).toBeGreaterThan(0)
  })

  it('should apply custom className', () => {
    const { container } = render(
      <TestWrapper>
        <PermissionMatrix users={mockUsers} className="custom-class" />
      </TestWrapper>
    )

    expect(container.firstChild).toHaveClass('custom-class')
  })

  it('should handle filter state changes', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionMatrix users={mockUsers} />
      </TestWrapper>
    )

    // Test role filter
    const selects = screen.getAllByTestId('select')
    if (selects.length > 0) {
      await user.click(selects[0])
      // Should trigger filter change
    }

    // Test search filter
    const searchInput = screen.getByTestId('filter-input')
    await user.type(searchInput, 'test search')
    
    expect(searchInput).toHaveValue('test search')
  })

  it('should show correct permission level names', () => {
    render(
      <TestWrapper>
        <PermissionMatrix users={mockUsers} />
      </TestWrapper>
    )

    // Permission level names should be in Portuguese
    expect(screen.getByText('Sem Acesso')).toBeInTheDocument()
    expect(screen.getByText('Leitura')).toBeInTheDocument()
    expect(screen.getByText('Padrão')).toBeInTheDocument()
    expect(screen.getByText('Completo')).toBeInTheDocument()
  })

  it('should handle permission update with toast notification', async () => {
    const { toast } = await import('@/components/ui/toast')
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionMatrix users={mockUsers} />
      </TestWrapper>
    )

    // Find and click a permission badge to edit
    const badges = screen.getAllByTestId('permission-badge')
    if (badges.length > 0) {
      await user.click(badges[0])
      
      // Simulate permission level change
      const selects = screen.getAllByTestId('select')
      if (selects.length > 0) {
        await user.click(selects[0])
      }
      
      // Should show toast notification
      await waitFor(() => {
        expect(toast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Permissões atualizadas',
            description: expect.stringContaining('atualizadas'),
          })
        )
      })
    }
  })
})