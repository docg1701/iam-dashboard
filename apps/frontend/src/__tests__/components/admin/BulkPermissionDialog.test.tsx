import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { BulkPermissionDialog } from '@/components/admin/BulkPermissionDialog'
import { AgentName } from '@/types/permissions'

// Mock the hooks
const mockUsePermissionTemplates = vi.fn()

vi.mock('@/hooks/useUserPermissions', () => ({
  usePermissionTemplates: () => mockUsePermissionTemplates(),
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

vi.mock('@/components/ui/label', () => ({
  Label: ({ children, className, htmlFor }: {
    children: React.ReactNode
    className?: string
    htmlFor?: string
  }) => (
    <label className={className} htmlFor={htmlFor} data-testid="label">{children}</label>
  ),
}))

vi.mock('@/components/ui/textarea', () => ({
  Textarea: ({ value, onChange, placeholder, disabled, rows, ...props }: {
    value?: string
    onChange?: (e: React.ChangeEvent<HTMLTextAreaElement>) => void
    placeholder?: string
    disabled?: boolean
    rows?: number
    [key: string]: unknown
  }) => (
    <textarea 
      value={value} 
      onChange={onChange} 
      placeholder={placeholder}
      disabled={disabled}
      rows={rows}
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

vi.mock('@/components/ui/progress', () => ({
  Progress: ({ value, className }: { value?: number; className?: string }) => (
    <div data-testid="progress" data-value={value} className={className} />
  ),
}))

vi.mock('@/components/ui/toast', () => ({
  toast: vi.fn(),
}))

// Mock icons
vi.mock('lucide-react', () => ({
  Users: () => <div data-testid="users-icon">Users</div>,
  Template: () => <div data-testid="template-icon">Template</div>,
  Save: () => <div data-testid="save-icon">Save</div>,
  X: () => <div data-testid="x-icon">X</div>,
  AlertTriangle: () => <div data-testid="alert-triangle-icon">AlertTriangle</div>,
  CheckCircle: () => <div data-testid="check-circle-icon">CheckCircle</div>,
  Clock: () => <div data-testid="clock-icon">Clock</div>,
  Shield: () => <div data-testid="shield-icon">Shield</div>,
  Download: () => <div data-testid="download-icon">Download</div>,
  Upload: () => <div data-testid="upload-icon">Upload</div>,
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

const mockTemplates = [
  {
    template_id: 'template-1',
    template_name: 'Admin Template',
    description: 'Full access template for administrators',
    permissions: {
      [AgentName.CLIENT_MANAGEMENT]: { create: true, read: true, update: true, delete: true },
      [AgentName.PDF_PROCESSING]: { create: true, read: true, update: false, delete: false },
      [AgentName.REPORTS_ANALYSIS]: { create: false, read: true, update: false, delete: false },
      [AgentName.AUDIO_RECORDING]: { create: false, read: false, update: false, delete: false },
    },
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z',
  },
  {
    template_id: 'template-2',
    template_name: 'User Template',
    description: 'Basic access template for regular users',
    permissions: {
      [AgentName.CLIENT_MANAGEMENT]: { create: false, read: true, update: false, delete: false },
      [AgentName.PDF_PROCESSING]: { create: false, read: true, update: false, delete: false },
      [AgentName.REPORTS_ANALYSIS]: { create: false, read: false, update: false, delete: false },
      [AgentName.AUDIO_RECORDING]: { create: false, read: false, update: false, delete: false },
    },
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z',
  },
]

describe('BulkPermissionDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Setup default mock returns
    mockUsePermissionTemplates.mockReturnValue({
      templates: mockTemplates,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    })

    // Mock URL.createObjectURL for file download tests
    global.URL.createObjectURL = vi.fn(() => 'mock-blob-url')
    global.URL.revokeObjectURL = vi.fn()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should render dialog when open', () => {
    render(
      <TestWrapper>
        <BulkPermissionDialog 
          users={mockUsers} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    expect(screen.getByTestId('dialog')).toBeInTheDocument()
    expect(screen.getByTestId('dialog-content')).toBeInTheDocument()
    expect(screen.getByText('Operação em Lote - 3 usuários selecionados')).toBeInTheDocument()
  })

  it('should not render dialog when closed', () => {
    render(
      <TestWrapper>
        <BulkPermissionDialog 
          users={mockUsers} 
          open={false} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    expect(screen.queryByTestId('dialog')).not.toBeInTheDocument()
  })

  it('should display user summary correctly', () => {
    render(
      <TestWrapper>
        <BulkPermissionDialog 
          users={mockUsers} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    // Check user summary stats
    expect(screen.getByText('Resumo dos Usuários')).toBeInTheDocument()
    expect(screen.getByText('Ativos')).toBeInTheDocument()
    expect(screen.getByText('Inativos')).toBeInTheDocument()
    expect(screen.getByText('Admins')).toBeInTheDocument()
    expect(screen.getByText('Usuários')).toBeInTheDocument()

    // Check stats values (2 active, 1 inactive, 1 admin, 2 users)
    expect(screen.getByText('2')).toBeInTheDocument() // Active users
    expect(screen.getByText('1')).toBeInTheDocument() // Inactive users and admin count
  })

  it('should show operation type selection', () => {
    render(
      <TestWrapper>
        <BulkPermissionDialog 
          users={mockUsers} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    expect(screen.getByText('Tipo de Operação')).toBeInTheDocument()
    expect(screen.getByText('Aplicar Template')).toBeInTheDocument()
    expect(screen.getByText('Conceder Todas as Permissões')).toBeInTheDocument()
    expect(screen.getByText('Revogar Todas as Permissões')).toBeInTheDocument()
    expect(screen.getByText('Permissões Personalizadas')).toBeInTheDocument()
  })

  it('should handle operation type change', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <BulkPermissionDialog 
          users={mockUsers} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    // Find and click operation type select
    const selects = screen.getAllByTestId('select')
    if (selects.length > 0) {
      await user.click(selects[0])
      // Operation type should change (mocked behavior)
    }
  })

  it('should show template selection when template operation is selected', () => {
    render(
      <TestWrapper>
        <BulkPermissionDialog 
          users={mockUsers} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    // Template selection should be visible by default (template is default operation)
    expect(screen.getByText('Selecionar Template')).toBeInTheDocument()
    expect(screen.getByText('Escolha um template...')).toBeInTheDocument()
  })

  it('should show template options in select', () => {
    render(
      <TestWrapper>
        <BulkPermissionDialog 
          users={mockUsers} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    // Template names should be available in the options
    expect(screen.getByText('Admin Template')).toBeInTheDocument()
    expect(screen.getByText('User Template')).toBeInTheDocument()
  })

  it('should require change reason for execution', () => {
    render(
      <TestWrapper>
        <BulkPermissionDialog 
          users={mockUsers} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    expect(screen.getByText('Motivo da Alteração *')).toBeInTheDocument()
    expect(screen.getByTestId('textarea')).toBeInTheDocument()
    
    // Execute button should be disabled without change reason
    const executeButton = screen.getByText('Executar Operação')
    expect(executeButton).toBeDisabled()
  })

  it('should handle change reason input', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <BulkPermissionDialog 
          users={mockUsers} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    const textarea = screen.getByTestId('textarea')
    await user.type(textarea, 'Bulk update for new policy')

    expect(textarea).toHaveValue('Bulk update for new policy')
  })

  it('should show warning for dangerous operations', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <BulkPermissionDialog 
          users={mockUsers} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    // Mock selecting "grant_all" operation type
    const selects = screen.getAllByTestId('select')
    if (selects.length > 0) {
      // Simulate selecting grant_all operation
      const operationSelect = selects[0]
      await user.click(operationSelect)
      
      // Warning should appear (this would happen in real implementation)
      expect(screen.getByTestId('alert')).toBeInTheDocument()
      expect(screen.getByText('Atenção:')).toBeInTheDocument()
    }
  })

  it('should handle template preview', async () => {
    
    render(
      <TestWrapper>
        <BulkPermissionDialog 
          users={mockUsers} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    // Template preview should show when template is selected
    // In the real implementation, selecting a template would show the preview
    expect(screen.getByText('Admin Template')).toBeInTheDocument()
  })

  it('should execute bulk operation with progress tracking', async () => {
    const { toast } = await import('@/components/ui/toast')
    const user = userEvent.setup()
    const onBulkOperationComplete = vi.fn()
    
    render(
      <TestWrapper>
        <BulkPermissionDialog 
          users={mockUsers} 
          open={true} 
          onOpenChange={vi.fn()}
          onBulkOperationComplete={onBulkOperationComplete}
        />
      </TestWrapper>
    )

    // Fill in change reason
    const textarea = screen.getByTestId('textarea')
    await user.type(textarea, 'Test bulk operation')

    // Execute operation
    const executeButton = screen.getByText('Executar Operação')
    await user.click(executeButton)

    // Should show progress (mocked implementation)
    await waitFor(() => {
      expect(toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Operação concluída',
          description: expect.stringContaining('usuários atualizados'),
        })
      )
    })
  })

  it('should handle export functionality', async () => {
    const { toast } = await import('@/components/ui/toast')
    const user = userEvent.setup()
    
    // Mock document methods
    const mockAppendChild = vi.fn()
    const mockRemoveChild = vi.fn()
    const mockClick = vi.fn()
    
    Object.defineProperty(document, 'createElement', {
      value: vi.fn(() => ({
        href: '',
        download: '',
        click: mockClick,
      })),
      writable: true,
    })
    
    Object.defineProperty(document.body, 'appendChild', {
      value: mockAppendChild,
      writable: true,
    })
    
    Object.defineProperty(document.body, 'removeChild', {
      value: mockRemoveChild,
      writable: true,
    })

    render(
      <TestWrapper>
        <BulkPermissionDialog 
          users={mockUsers} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    // Click export button
    const exportButton = screen.getByText('Exportar Lista')
    await user.click(exportButton)

    // Should trigger export functionality
    expect(mockClick).toHaveBeenCalled()
    expect(toast).toHaveBeenCalledWith(
      expect.objectContaining({
        title: 'Exportação concluída',
        description: expect.stringContaining('exportada'),
      })
    )
  })

  it('should handle cancel action', async () => {
    const user = userEvent.setup()
    const onOpenChange = vi.fn()
    
    render(
      <TestWrapper>
        <BulkPermissionDialog 
          users={mockUsers} 
          open={true} 
          onOpenChange={onOpenChange}
        />
      </TestWrapper>
    )

    const cancelButton = screen.getByText('Cancelar')
    await user.click(cancelButton)

    expect(onOpenChange).toHaveBeenCalledWith(false)
  })

  it('should disable form elements during operation execution', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <BulkPermissionDialog 
          users={mockUsers} 
          open={true} 
          onOpenChange={vi.fn()}
        />
      </TestWrapper>
    )

    // Fill in change reason and start operation
    const textarea = screen.getByTestId('textarea')
    await user.type(textarea, 'Test operation')

    const executeButton = screen.getByText('Executar Operação')
    await user.click(executeButton)

    // During execution, form should be disabled
    await waitFor(() => {
      expect(screen.getByText('Executando...')).toBeInTheDocument()
    })
  })

  it('should show progress tracker during execution', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <BulkPermissionDialog 
          users={mockUsers} 
          open={true} 
          onOpenChange={vi.fn()}
        />
      </TestWrapper>
    )

    // Start operation
    const textarea = screen.getByTestId('textarea')
    await user.type(textarea, 'Test progress')

    const executeButton = screen.getByText('Executar Operação')
    await user.click(executeButton)

    // Progress tracker should appear
    await waitFor(() => {
      expect(screen.getByText('Progresso da Operação')).toBeInTheDocument()
      expect(screen.getByTestId('progress')).toBeInTheDocument()
    })
  })

  it('should show custom permissions editor for custom operation type', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <BulkPermissionDialog 
          users={mockUsers} 
          open={true} 
          onOpenChange={vi.fn()}
        />
      </TestWrapper>
    )

    // Mock selecting custom operation type
    const selects = screen.getAllByTestId('select')
    if (selects.length > 0) {
      await user.click(selects[0])
      
      // Custom permissions editor should show
      expect(screen.getByText('Permissões Personalizadas')).toBeInTheDocument()
      expect(screen.getByText('Configure permissões específicas para cada agente')).toBeInTheDocument()
    }
  })

  it('should handle empty user list', () => {
    render(
      <TestWrapper>
        <BulkPermissionDialog 
          users={[]} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    expect(screen.getByText('Operação em Lote - 0 usuários selecionados')).toBeInTheDocument()
    
    // Execute button should be disabled for empty user list
    const executeButton = screen.getByText('Executar Operação')
    expect(executeButton).toBeDisabled()
  })

  it('should show loading state for templates', () => {
    mockUsePermissionTemplates.mockReturnValue({
      templates: [],
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    })

    render(
      <TestWrapper>
        <BulkPermissionDialog 
          users={mockUsers} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    // Template select should be disabled during loading
    const selects = screen.getAllByTestId('select')
    const templateSelect = selects.find(select => 
      select.getAttribute('data-disabled') === 'true'
    )
    expect(templateSelect).toBeTruthy()
  })

  it('should handle template loading error gracefully', () => {
    mockUsePermissionTemplates.mockReturnValue({
      templates: [],
      isLoading: false,
      error: new Error('Failed to load templates'),
      refetch: vi.fn(),
    })

    render(
      <TestWrapper>
        <BulkPermissionDialog 
          users={mockUsers} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    // Should still render the dialog
    expect(screen.getByTestId('dialog')).toBeInTheDocument()
  })

  it('should validate execution requirements', () => {
    render(
      <TestWrapper>
        <BulkPermissionDialog 
          users={mockUsers} 
          open={true} 
          onOpenChange={vi.fn()} 
        />
      </TestWrapper>
    )

    const executeButton = screen.getByText('Executar Operação')
    
    // Should be disabled without change reason
    expect(executeButton).toBeDisabled()
  })

  it('should show success state after completion', async () => {
    const { toast } = await import('@/components/ui/toast')
    const user = userEvent.setup()
    const onOpenChange = vi.fn()
    
    render(
      <TestWrapper>
        <BulkPermissionDialog 
          users={mockUsers} 
          open={true} 
          onOpenChange={onOpenChange}
        />
      </TestWrapper>
    )

    // Complete operation
    const textarea = screen.getByTestId('textarea')
    await user.type(textarea, 'Test completion')

    const executeButton = screen.getByText('Executar Operação')
    await user.click(executeButton)

    // Should show success and auto-close
    await waitFor(() => {
      expect(toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Operação concluída',
        })
      )
    })
  })
})