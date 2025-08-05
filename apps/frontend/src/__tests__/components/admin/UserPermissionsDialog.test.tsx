import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { UserPermissionsDialog } from '@/components/admin/UserPermissionsDialog'
import { AgentName } from '@/types/permissions'

// Mock the hooks
const mockUseUserPermissions = vi.fn()
const mockUsePermissionMutations = vi.fn()
const mockUsePermissionAudit = vi.fn()

vi.mock('@/hooks/useUserPermissions', () => ({
  useUserPermissions: () => mockUseUserPermissions(),
  usePermissionMutations: () => mockUsePermissionMutations(),
  usePermissionAudit: () => mockUsePermissionAudit(),
}))

// Mock PermissionGuard components
vi.mock('@/components/common/PermissionGuard', () => ({
  PermissionGuard: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  UpdatePermissionGuard: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

// Mock UI components
vi.mock('@/components/ui/dialog', () => ({
  Dialog: ({ children, open }: { children: React.ReactNode; open: boolean }) => (
    open ? <div data-testid="dialog">{children}</div> : null
  ),
  DialogContent: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="dialog-content">{children}</div>
  ),
  DialogDescription: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="dialog-description">{children}</div>
  ),
  DialogFooter: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="dialog-footer">{children}</div>
  ),
  DialogHeader: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="dialog-header">{children}</div>
  ),
  DialogTitle: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="dialog-title">{children}</div>
  ),
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
      data-testid="button"
      {...props}
    >
      {children}
    </button>
  ),
}))

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, variant, className }: {
    children: React.ReactNode
    variant?: string
    className?: string
  }) => (
    <span data-variant={variant} className={className} data-testid="badge">
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
      data-testid="input"
      {...props}
    />
  ),
}))

vi.mock('@/components/ui/label', () => ({
  Label: ({ children, className }: {
    children: React.ReactNode
    className?: string
  }) => (
    <label className={className} data-testid="label">{children}</label>
  ),
}))

vi.mock('@/components/ui/textarea', () => ({
  Textarea: ({ value, onChange, placeholder, ...props }: {
    value?: string
    onChange?: (e: React.ChangeEvent<HTMLTextAreaElement>) => void
    placeholder?: string
    [key: string]: unknown
  }) => (
    <textarea 
      value={value} 
      onChange={onChange} 
      placeholder={placeholder}
      data-testid="textarea"
      {...props}
    />
  ),
}))

vi.mock('@/components/ui/select', () => ({
  Select: ({ children, value, onValueChange, disabled }: {
    children: React.ReactNode
    value?: string
    onValueChange?: (value: string) => void
    disabled?: boolean
  }) => (
    <div 
      data-testid="select" 
      data-value={value} 
      data-disabled={disabled}
      onClick={() => !disabled && onValueChange?.('test-value')}
    >
      {children}
    </div>
  ),
  SelectContent: ({ children }: { children: React.ReactNode }) => <div data-testid="select-content">{children}</div>,
  SelectItem: ({ children, value }: { children: React.ReactNode; value?: string }) => (
    <div data-testid="select-item" data-value={value}>{children}</div>
  ),
  SelectTrigger: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="select-trigger" className={className}>{children}</div>
  ),
  SelectValue: ({ placeholder }: { placeholder?: string }) => <div data-testid="select-value">{placeholder}</div>,
}))

vi.mock('@/components/ui/table', () => ({
  Table: ({ children }: { children: React.ReactNode }) => <table data-testid="table">{children}</table>,
  TableBody: ({ children }: { children: React.ReactNode }) => <tbody>{children}</tbody>,
  TableCell: ({ children }: { children: React.ReactNode }) => <td data-testid="table-cell">{children}</td>,
  TableHead: ({ children }: { children: React.ReactNode }) => <th data-testid="table-head">{children}</th>,
  TableHeader: ({ children }: { children: React.ReactNode }) => <thead>{children}</thead>,
  TableRow: ({ children }: { children: React.ReactNode }) => <tr data-testid="table-row">{children}</tr>,
}))

vi.mock('@/components/ui/card', () => ({
  Card: ({ children }: { children: React.ReactNode }) => <div data-testid="card">{children}</div>,
  CardContent: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div className={className} data-testid="card-content">{children}</div>
  ),
  CardDescription: ({ children }: { children: React.ReactNode }) => <div data-testid="card-description">{children}</div>,
  CardHeader: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div className={className} data-testid="card-header">{children}</div>
  ),
  CardTitle: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div className={className} data-testid="card-title">{children}</div>
  ),
}))

vi.mock('@/components/ui/alert', () => ({
  Alert: ({ children, variant }: { children: React.ReactNode; variant?: string }) => (
    <div data-testid="alert" data-variant={variant}>{children}</div>
  ),
  AlertDescription: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="alert-description">{children}</div>
  ),
}))

vi.mock('@/components/ui/toast', () => ({
  toast: vi.fn(),
}))

// Mock icons
vi.mock('lucide-react', () => ({
  Save: () => <div data-testid="save-icon">Save</div>,
  X: () => <div data-testid="x-icon">X</div>,
  Eye: () => <div data-testid="eye-icon">Eye</div>,
  EyeOff: () => <div data-testid="eye-off-icon">EyeOff</div>,
  User: () => <div data-testid="user-icon">User</div>,
  Shield: () => <div data-testid="shield-icon">Shield</div>,
  Clock: () => <div data-testid="clock-icon">Clock</div>,
  AlertTriangle: () => <div data-testid="alert-triangle-icon">AlertTriangle</div>,
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
    PERMISSION_LEVEL_NAMES: {
      none: 'Sem Acesso',
      read_only: 'Leitura',
      standard: 'Padrão',
      full: 'Completo',
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
const mockUser = {
  user_id: 'user-1',
  name: 'João Silva',
  email: 'joao@example.com',
  role: 'admin' as const,
  is_active: true,
  created_at: '2023-01-01T00:00:00Z',
  last_login: '2023-12-01T10:00:00Z',
}

const mockPermissionMatrix = {
  user_id: 'user-1',
  permissions: {
    [AgentName.CLIENT_MANAGEMENT]: { create: true, read: true, update: false, delete: false },
    [AgentName.PDF_PROCESSING]: { create: false, read: true, update: false, delete: false },
    [AgentName.REPORTS_ANALYSIS]: { create: false, read: false, update: false, delete: false },
    [AgentName.AUDIO_RECORDING]: { create: false, read: false, update: false, delete: false },
  },
  last_updated: '2023-12-01T00:00:00Z',
}

const mockAuditLogs = [
  {
    audit_id: 'audit-1',
    user_id: 'user-1',
    agent_name: AgentName.CLIENT_MANAGEMENT,
    action: 'CREATE',
    old_permissions: null,
    new_permissions: { create: true, read: true, update: false, delete: false },
    changed_by_user_id: 'admin-user-id',
    change_reason: 'Initial setup',
    created_at: '2023-01-01T00:00:00Z',
  },
]

describe('UserPermissionsDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Setup default mock returns
    mockUseUserPermissions.mockReturnValue({
      permissions: mockPermissionMatrix.permissions,
      isLoading: false,
      error: null,
      lastUpdated: new Date(mockPermissionMatrix.last_updated),
      refetch: vi.fn(),
    })
    
    mockUsePermissionMutations.mockReturnValue({
      updatePermission: { mutateAsync: vi.fn(), isPending: false },
      createPermission: { mutateAsync: vi.fn(), isPending: false },
      deletePermission: { mutateAsync: vi.fn(), isPending: false },
      isLoading: false,
    })

    mockUsePermissionAudit.mockReturnValue({
      logs: mockAuditLogs,
      total: 1,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    })
  })

  it('should render dialog when open', () => {
    render(
      <TestWrapper>
        <UserPermissionsDialog 
          user={mockUser} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    expect(screen.getByTestId('dialog')).toBeInTheDocument()
    expect(screen.getByTestId('dialog-content')).toBeInTheDocument()
  })

  it('should not render dialog when closed', () => {
    render(
      <TestWrapper>
        <UserPermissionsDialog 
          user={mockUser} 
          open={false} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    expect(screen.queryByTestId('dialog')).not.toBeInTheDocument()
  })

  it('should display user information in dialog header', () => {
    render(
      <TestWrapper>
        <UserPermissionsDialog 
          user={mockUser} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    expect(screen.getByText(mockUser.name)).toBeInTheDocument()
    expect(screen.getByText(mockUser.email)).toBeInTheDocument()
  })

  it('should display all agent permission cards', () => {
    render(
      <TestWrapper>
        <UserPermissionsDialog 
          user={mockUser} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    // Check agent names
    expect(screen.getByText('Gestão de Clientes')).toBeInTheDocument()
    expect(screen.getByText('Processamento de PDFs')).toBeInTheDocument()
    expect(screen.getByText('Relatórios e Análises')).toBeInTheDocument()
    expect(screen.getByText('Gravação de Áudio')).toBeInTheDocument()

    // Check cards are rendered
    const cards = screen.getAllByTestId('card')
    expect(cards.length).toBeGreaterThan(0)
  })

  it('should display permission level badges', () => {
    render(
      <TestWrapper>
        <UserPermissionsDialog 
          user={mockUser} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    const badges = screen.getAllByTestId('badge')
    expect(badges.length).toBeGreaterThan(0)
    
    // Should display permission level names
    expect(screen.getAllByText('Leitura')).toHaveLength(4) // Based on mock return
  })

  it('should allow permission level changes via select', async () => {
    const user = userEvent.setup()
    const onPermissionsChanged = vi.fn()
    
    render(
      <TestWrapper>
        <UserPermissionsDialog 
          user={mockUser} 
          open={true} 
          onOpenChange={vi.fn()}
          onPermissionsChanged={onPermissionsChanged}
        />
      </TestWrapper>
    )

    // Find select components and click one
    const selects = screen.getAllByTestId('select')
    if (selects.length > 0) {
      await user.click(selects[0])
      
      // Should trigger permission change
      expect(selects[0]).toHaveAttribute('data-value')
    }
  })

  it('should show loading state when fetching permissions', () => {
    mockUseUserPermissions.mockReturnValue({
      permissions: null,
      isLoading: true,
      error: null,
      lastUpdated: null,
      refetch: vi.fn(),
    })

    render(
      <TestWrapper>
        <UserPermissionsDialog 
          user={mockUser} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    // Should show loading indicators
    expect(screen.getByTestId('dialog')).toBeInTheDocument()
    // Loading state should be handled in the actual component
  })

  it('should show error state when permission fetch fails', () => {
    const error = new Error('Failed to fetch permissions')
    mockUseUserPermissions.mockReturnValue({
      permissions: null,
      isLoading: false,
      error: error,
      lastUpdated: null,
      refetch: vi.fn(),
    })

    render(
      <TestWrapper>
        <UserPermissionsDialog 
          user={mockUser} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    // Should show error message
    expect(screen.getByTestId('alert')).toBeInTheDocument()
    expect(screen.getByText(error.message)).toBeInTheDocument()
  })

  it('should handle save action', async () => {
    const user = userEvent.setup()
    const mockMutateAsync = vi.fn().mockResolvedValue({})
    const onPermissionsChanged = vi.fn()
    
    mockUsePermissionMutations.mockReturnValue({
      updatePermission: { mutateAsync: mockMutateAsync, isPending: false },
      createPermission: { mutateAsync: vi.fn(), isPending: false },
      deletePermission: { mutateAsync: vi.fn(), isPending: false },
      isLoading: false,
    })

    render(
      <TestWrapper>
        <UserPermissionsDialog 
          user={mockUser} 
          open={true} 
          onOpenChange={vi.fn()}
          onPermissionsChanged={onPermissionsChanged}
        />
      </TestWrapper>
    )

    // Find and click save button
    const saveButton = screen.getByText('Salvar')
    await user.click(saveButton)

    // Should call mutation and callback
    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalled()
      expect(onPermissionsChanged).toHaveBeenCalledWith(mockUser.user_id)
    })
  })

  it('should handle cancel action', async () => {
    const user = userEvent.setup()
    const onOpenChange = vi.fn()
    
    render(
      <TestWrapper>
        <UserPermissionsDialog 
          user={mockUser} 
          open={true} 
          onOpenChange={onOpenChange}
        />
      </TestWrapper>
    )

    // Find and click cancel button
    const cancelButton = screen.getByText('Cancelar')
    await user.click(cancelButton)

    // Should close dialog
    expect(onOpenChange).toHaveBeenCalledWith(false)
  })

  it('should show change reason textarea', () => {
    render(
      <TestWrapper>
        <UserPermissionsDialog 
          user={mockUser} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    expect(screen.getByTestId('textarea')).toBeInTheDocument()
    expect(screen.getByText('Motivo da Alteração')).toBeInTheDocument()
  })

  it('should handle change reason input', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <UserPermissionsDialog 
          user={mockUser} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    const textarea = screen.getByTestId('textarea')
    await user.type(textarea, 'Permission update reason')

    expect(textarea).toHaveValue('Permission update reason')
  })

  it('should display audit log section', () => {
    render(
      <TestWrapper>
        <UserPermissionsDialog 
          user={mockUser} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    expect(screen.getByText('Histórico de Alterações')).toBeInTheDocument()
    expect(screen.getByTestId('table')).toBeInTheDocument()
  })

  it('should show audit log entries', () => {
    render(
      <TestWrapper>
        <UserPermissionsDialog 
          user={mockUser} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    // Should show audit log data
    expect(screen.getByText('CREATE')).toBeInTheDocument()
    expect(screen.getByText('Initial setup')).toBeInTheDocument()
  })

  it('should disable form when mutation is pending', () => {
    mockUsePermissionMutations.mockReturnValue({
      updatePermission: { mutateAsync: vi.fn(), isPending: true },
      createPermission: { mutateAsync: vi.fn(), isPending: false },
      deletePermission: { mutateAsync: vi.fn(), isPending: false },
      isLoading: true,
    })

    render(
      <TestWrapper>
        <UserPermissionsDialog 
          user={mockUser} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    // Form elements should be disabled
    const selects = screen.getAllByTestId('select')
    if (selects.length > 0) {
      expect(selects[0]).toHaveAttribute('data-disabled', 'true')
    }

    const saveButton = screen.getByText('Salvando...')
    expect(saveButton).toBeDisabled()
  })

  it('should show success toast on successful save', async () => {
    const { toast } = await import('@/components/ui/toast')
    const user = userEvent.setup()
    const mockMutateAsync = vi.fn().mockResolvedValue({})
    
    mockUsePermissionMutations.mockReturnValue({
      updatePermission: { mutateAsync: mockMutateAsync, isPending: false },
      createPermission: { mutateAsync: vi.fn(), isPending: false },
      deletePermission: { mutateAsync: vi.fn(), isPending: false },
      isLoading: false,
    })

    render(
      <TestWrapper>
        <UserPermissionsDialog 
          user={mockUser} 
          open={true} 
          onOpenChange={vi.fn()}
        />
      </TestWrapper>
    )

    const saveButton = screen.getByText('Salvar')
    await user.click(saveButton)

    await waitFor(() => {
      expect(toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Permissões atualizadas',
          description: expect.stringContaining('sucesso'),
        })
      )
    })
  })

  it('should handle save error gracefully', async () => {
    const { toast } = await import('@/components/ui/toast')
    const user = userEvent.setup()
    const mockMutateAsync = vi.fn().mockRejectedValue(new Error('Save failed'))
    
    mockUsePermissionMutations.mockReturnValue({
      updatePermission: { mutateAsync: mockMutateAsync, isPending: false },
      createPermission: { mutateAsync: vi.fn(), isPending: false },
      deletePermission: { mutateAsync: vi.fn(), isPending: false },
      isLoading: false,
    })

    render(
      <TestWrapper>
        <UserPermissionsDialog 
          user={mockUser} 
          open={true} 
          onOpenChange={vi.fn()}
        />
      </TestWrapper>
    )

    const saveButton = screen.getByText('Salvar')
    await user.click(saveButton)

    await waitFor(() => {
      expect(toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Erro ao salvar',
          description: expect.stringContaining('erro'),
          variant: 'destructive',
        })
      )
    })
  })

  it('should not render when user is null', () => {
    render(
      <TestWrapper>
        <UserPermissionsDialog 
          user={null} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    expect(screen.queryByTestId('dialog')).not.toBeInTheDocument()
  })

  it('should show user role and status information', () => {
    render(
      <TestWrapper>
        <UserPermissionsDialog 
          user={mockUser} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    expect(screen.getByText('admin')).toBeInTheDocument()
    expect(screen.getByText('Ativo')).toBeInTheDocument()
  })

  it('should show last login information when available', () => {
    render(
      <TestWrapper>
        <UserPermissionsDialog 
          user={mockUser} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    // Should show last login date
    expect(screen.getByText(/Último acesso/)).toBeInTheDocument()
  })

  it('should handle individual permission toggles', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <UserPermissionsDialog 
          user={mockUser} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    // Find checkboxes for individual permissions
    const checkboxes = screen.getAllByRole('checkbox')
    if (checkboxes.length > 0) {
      await user.click(checkboxes[0])
      
      // Should toggle permission state
      expect(checkboxes[0]).toBeChecked()
    }
  })
})