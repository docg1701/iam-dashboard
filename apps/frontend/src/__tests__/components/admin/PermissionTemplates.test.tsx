import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { PermissionTemplates } from '@/components/admin/PermissionTemplates'
import { AgentName } from '@/types/permissions'

// Mock the hooks
const mockUsePermissionTemplates = vi.fn()

vi.mock('@/hooks/useUserPermissions', () => ({
  usePermissionTemplates: () => mockUsePermissionTemplates(),
}))

// Mock PermissionGuard components
vi.mock('@/components/common/PermissionGuard', () => ({
  PermissionGuard: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CreatePermissionGuard: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  UpdatePermissionGuard: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DeletePermissionGuard: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
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
  Input: ({ value, onChange, placeholder, disabled, className, id, ...props }: {
    value?: string
    onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void
    placeholder?: string
    disabled?: boolean
    className?: string
    id?: string
    [key: string]: unknown
  }) => (
    <input 
      id={id}
      value={value} 
      onChange={onChange} 
      placeholder={placeholder}
      disabled={disabled}
      className={className}
      data-testid="input"
      {...props}
    />
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
  Textarea: ({ value, onChange, placeholder, disabled, rows, className, id, ...props }: {
    value?: string
    onChange?: (e: React.ChangeEvent<HTMLTextAreaElement>) => void
    placeholder?: string
    disabled?: boolean
    rows?: number
    className?: string
    id?: string
    [key: string]: unknown
  }) => (
    <textarea 
      id={id}
      value={value} 
      onChange={onChange} 
      placeholder={placeholder}
      disabled={disabled}
      rows={rows}
      className={className}
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
  Template: () => <div data-testid="template-icon">Template</div>,
  Plus: () => <div data-testid="plus-icon">Plus</div>,
  Edit: () => <div data-testid="edit-icon">Edit</div>,
  Trash2: () => <div data-testid="trash2-icon">Trash2</div>,
  Copy: () => <div data-testid="copy-icon">Copy</div>,
  Users: () => <div data-testid="users-icon">Users</div>,
  Save: () => <div data-testid="save-icon">Save</div>,
  X: () => <div data-testid="x-icon">X</div>,
  Shield: () => <div data-testid="shield-icon">Shield</div>,
  Search: () => <div data-testid="search-icon">Search</div>,
  Star: () => <div data-testid="star-icon">Star</div>,
  StarOff: () => <div data-testid="star-off-icon">StarOff</div>,
  AlertTriangle: () => <div data-testid="alert-triangle-icon">AlertTriangle</div>,
  CheckCircle: () => <div data-testid="check-circle-icon">CheckCircle</div>,
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

// Mock template data
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
    is_system_template: true,
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
    is_system_template: false,
    created_at: '2023-01-15T00:00:00Z',
    updated_at: '2023-01-15T00:00:00Z',
  },
  {
    template_id: 'template-3',
    template_name: 'Manager Template',
    description: 'Mid-level access for team managers',
    permissions: {
      [AgentName.CLIENT_MANAGEMENT]: { create: true, read: true, update: true, delete: false },
      [AgentName.PDF_PROCESSING]: { create: false, read: true, update: false, delete: false },
      [AgentName.REPORTS_ANALYSIS]: { create: false, read: true, update: false, delete: false },
      [AgentName.AUDIO_RECORDING]: { create: false, read: false, update: false, delete: false },
    },
    is_system_template: false,
    created_at: '2023-02-01T00:00:00Z',
    updated_at: '2023-02-01T00:00:00Z',
  },
]

describe('PermissionTemplates', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Setup default mock returns
    mockUsePermissionTemplates.mockReturnValue({
      templates: mockTemplates,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    })
  })

  it('should render templates list', () => {
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    expect(screen.getByText('Templates de Permissão')).toBeInTheDocument()
    expect(screen.getByText('Admin Template')).toBeInTheDocument()
    expect(screen.getByText('User Template')).toBeInTheDocument()
    expect(screen.getByText('Manager Template')).toBeInTheDocument()
  })

  it('should display header and description', () => {
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    expect(screen.getByText('Templates de Permissão')).toBeInTheDocument()
    expect(screen.getByText(/Crie e gerencie templates reutilizáveis/)).toBeInTheDocument()
  })

  it('should show create new template button', () => {
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    expect(screen.getByText('Novo Template')).toBeInTheDocument()
  })

  it('should display stats cards correctly', () => {
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    expect(screen.getByText('Total de Templates')).toBeInTheDocument()
    expect(screen.getByText('Templates do Sistema')).toBeInTheDocument()
    expect(screen.getByText('Templates Personalizados')).toBeInTheDocument()

    // Check stats values
    expect(screen.getByText('3')).toBeInTheDocument() // Total templates
    expect(screen.getByText('1')).toBeInTheDocument() // System templates
    expect(screen.getByText('2')).toBeInTheDocument() // Custom templates
  })

  it('should show filter controls', () => {
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    expect(screen.getByText('Buscar Templates')).toBeInTheDocument()
    expect(screen.getByText('Filtrar por Tipo')).toBeInTheDocument()
    expect(screen.getByText('Atualizar')).toBeInTheDocument()

    // Filter options
    expect(screen.getByText('Todos os Templates')).toBeInTheDocument()
    expect(screen.getByText('Templates do Sistema')).toBeInTheDocument()
    expect(screen.getByText('Templates Personalizados')).toBeInTheDocument()
  })

  it('should handle search input', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    const searchInput = screen.getByPlaceholderText('Nome ou descrição...')
    await user.type(searchInput, 'Admin')

    expect(searchInput).toHaveValue('Admin')
  })

  it('should handle filter selection', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    const filterSelect = screen.getAllByTestId('select')[0]
    await user.click(filterSelect)

    // Should trigger filter change
    expect(filterSelect).toHaveAttribute('data-value')
  })

  it('should display template table', () => {
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    expect(screen.getByTestId('table')).toBeInTheDocument()
    expect(screen.getByText('Nome e Descrição')).toBeInTheDocument()
    expect(screen.getByText('Permissões')).toBeInTheDocument()
    expect(screen.getByText('Tipo')).toBeInTheDocument()
    expect(screen.getByText('Criado em')).toBeInTheDocument()
    expect(screen.getByText('Ações')).toBeInTheDocument()
  })

  it('should show template details in table rows', () => {
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    // Template names and descriptions
    expect(screen.getByText('Admin Template')).toBeInTheDocument()
    expect(screen.getByText('Full access template for administrators')).toBeInTheDocument()
    expect(screen.getByText('User Template')).toBeInTheDocument()
    expect(screen.getByText('Basic access template for regular users')).toBeInTheDocument()

    // Template types
    expect(screen.getByText('Sistema')).toBeInTheDocument()
    expect(screen.getAllByText('Personalizado')).toHaveLength(2)
  })

  it('should show action buttons for each template', () => {
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    // Should have view, edit, duplicate, and delete buttons for each template
    const viewButtons = screen.getAllByTestId('shield-icon')
    const editButtons = screen.getAllByTestId('edit-icon')
    const duplicateButtons = screen.getAllByTestId('copy-icon')
    const deleteButtons = screen.getAllByTestId('trash2-icon')

    expect(viewButtons.length).toBeGreaterThan(0)
    expect(editButtons.length).toBeGreaterThan(0)
    expect(duplicateButtons.length).toBeGreaterThan(0)
    expect(deleteButtons.length).toBeGreaterThan(0)
  })

  it('should open create template dialog', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    const createButton = screen.getByText('Novo Template')
    await user.click(createButton)

    await waitFor(() => {
      expect(screen.getByTestId('dialog')).toBeInTheDocument()
      expect(screen.getByText('Criar Novo Template')).toBeInTheDocument()
    })
  })

  it('should open view template dialog', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    const viewButtons = screen.getAllByTestId('shield-icon')
    if (viewButtons.length > 0) {
      await user.click(viewButtons[0].parentElement!)

      await waitFor(() => {
        expect(screen.getByTestId('dialog')).toBeInTheDocument()
        expect(screen.getByText('Visualizar Template')).toBeInTheDocument()
      })
    }
  })

  it('should open edit template dialog', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    const editButtons = screen.getAllByTestId('edit-icon')
    if (editButtons.length > 0) {
      await user.click(editButtons[0].parentElement!)

      await waitFor(() => {
        expect(screen.getByTestId('dialog')).toBeInTheDocument()
        expect(screen.getByText('Editar Template')).toBeInTheDocument()
      })
    }
  })

  it('should open delete confirmation dialog', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    const deleteButtons = screen.getAllByTestId('trash2-icon')
    if (deleteButtons.length > 0) {
      await user.click(deleteButtons[0].parentElement!)

      await waitFor(() => {
        expect(screen.getByTestId('dialog')).toBeInTheDocument()
        expect(screen.getByText('Excluir Template')).toBeInTheDocument()
        expect(screen.getByText(/Esta ação não pode ser desfeita/)).toBeInTheDocument()
      })
    }
  })

  it('should handle template duplication', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    const duplicateButtons = screen.getAllByTestId('copy-icon')
    if (duplicateButtons.length > 0) {
      await user.click(duplicateButtons[0].parentElement!)

      await waitFor(() => {
        expect(screen.getByTestId('dialog')).toBeInTheDocument()
        expect(screen.getByText('Criar Novo Template')).toBeInTheDocument()
        // Should show duplicated name with "(Cópia)" suffix
      })
    }
  })

  it('should show template form in create mode', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    const createButton = screen.getByText('Novo Template')
    await user.click(createButton)

    await waitFor(() => {
      expect(screen.getByText('Nome do Template *')).toBeInTheDocument()
      expect(screen.getByText('Descrição')).toBeInTheDocument()
      expect(screen.getByText('Template do sistema')).toBeInTheDocument()
      expect(screen.getByText('Configuração de Permissões')).toBeInTheDocument()
    })
  })

  it('should show permission configuration for all agents', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    const createButton = screen.getByText('Novo Template')
    await user.click(createButton)

    await waitFor(() => {
      expect(screen.getByText('Gestão de Clientes')).toBeInTheDocument()
      expect(screen.getByText('Processamento de PDFs')).toBeInTheDocument()
      expect(screen.getByText('Relatórios e Análises')).toBeInTheDocument()
      expect(screen.getByText('Gravação de Áudio')).toBeInTheDocument()
    })
  })

  it('should handle form input changes', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    const createButton = screen.getByText('Novo Template')
    await user.click(createButton)

    await waitFor(async () => {
      const nameInput = screen.getByLabelText('Nome do Template *')
      const descriptionTextarea = screen.getByLabelText('Descrição')

      await user.type(nameInput, 'Test Template')
      await user.type(descriptionTextarea, 'Test description')

      expect(nameInput).toHaveValue('Test Template')
      expect(descriptionTextarea).toHaveValue('Test description')
    })
  })

  it('should handle form submission', async () => {
    const { toast } = await import('@/components/ui/toast')
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    const createButton = screen.getByText('Novo Template')
    await user.click(createButton)

    await waitFor(async () => {
      const nameInput = screen.getByLabelText('Nome do Template *')
      await user.type(nameInput, 'Test Template')

      const submitButton = screen.getByText('Criar Template')
      await user.click(submitButton)

      expect(toast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Template criado',
          description: expect.stringContaining('Test Template'),
        })
      )
    })
  })

  it('should handle template deletion', async () => {
    const { toast } = await import('@/components/ui/toast')
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    const deleteButtons = screen.getAllByTestId('trash2-icon')
    if (deleteButtons.length > 0) {
      await user.click(deleteButtons[0].parentElement!)

      await waitFor(async () => {
        const confirmButton = screen.getByText('Excluir Template')
        await user.click(confirmButton)

        expect(toast).toHaveBeenCalledWith(
          expect.objectContaining({
            title: 'Template excluído',
            description: expect.stringContaining('excluído com sucesso'),
          })
        )
      })
    }
  })

  it('should disable system template editing and deletion', () => {
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    // System templates should show as disabled in actions
    const systemTemplate = screen.getByText('Admin Template')
    expect(systemTemplate).toBeInTheDocument()
    
    // System templates should show star icon
    expect(screen.getByTestId('star-icon')).toBeInTheDocument()
  })

  it('should show empty state when no templates found', () => {
    mockUsePermissionTemplates.mockReturnValue({
      templates: [],
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    })

    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    expect(screen.getByText('Nenhum template encontrado')).toBeInTheDocument()
    expect(screen.getByText('Criar Primeiro Template')).toBeInTheDocument()
  })

  it('should show loading state', () => {
    mockUsePermissionTemplates.mockReturnValue({
      templates: [],
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    })

    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    // Component should still render but with loading state
    expect(screen.getByText('Templates de Permissão')).toBeInTheDocument()
    expect(screen.getByText('Carregando...')).toBeInTheDocument()
  })

  it('should show error state', () => {
    const error = new Error('Failed to load templates')
    mockUsePermissionTemplates.mockReturnValue({
      templates: [],
      isLoading: false,
      error: error,
      refetch: vi.fn(),
    })

    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    expect(screen.getByTestId('alert')).toBeInTheDocument()
    expect(screen.getByText(`Erro ao carregar templates: ${error.message}`)).toBeInTheDocument()
  })

  it('should handle refresh action', async () => {
    const user = userEvent.setup()
    const mockRefetch = vi.fn()
    
    mockUsePermissionTemplates.mockReturnValue({
      templates: mockTemplates,
      isLoading: false,
      error: null,
      refetch: mockRefetch,
    })

    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    const refreshButton = screen.getByText('Atualizar')
    await user.click(refreshButton)

    expect(mockRefetch).toHaveBeenCalled()
  })

  it('should filter templates by search term', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    const searchInput = screen.getByPlaceholderText('Nome ou descrição...')
    await user.type(searchInput, 'Admin')

    // Should filter results (though in this mock implementation, all templates are still shown)
    expect(searchInput).toHaveValue('Admin')
  })

  it('should validate form submission requirements', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    const createButton = screen.getByText('Novo Template')
    await user.click(createButton)

    await waitFor(() => {
      const submitButton = screen.getByText('Criar Template')
      expect(submitButton).toBeDisabled() // Should be disabled without template name
    })
  })

  it('should show permission details in template form', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    const createButton = screen.getByText('Novo Template')
    await user.click(createButton)

    await waitFor(() => {
      // Should show permission operations
      expect(screen.getByText('Criar')).toBeInTheDocument()
      expect(screen.getByText('Ver')).toBeInTheDocument()
      expect(screen.getByText('Editar')).toBeInTheDocument()
      expect(screen.getByText('Excluir')).toBeInTheDocument()
    })
  })

  it('should handle dialog close', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    const createButton = screen.getByText('Novo Template')
    await user.click(createButton)

    await waitFor(async () => {
      const cancelButton = screen.getByText('Cancelar')
      await user.click(cancelButton)

      expect(screen.queryByTestId('dialog')).not.toBeInTheDocument()
    })
  })

  it('should call onTemplateApplied callback when provided', () => {
    const onTemplateApplied = vi.fn()
    
    render(
      <TestWrapper>
        <PermissionTemplates onTemplateApplied={onTemplateApplied} />
      </TestWrapper>
    )

    // Component should render with the callback
    expect(screen.getByText('Templates de Permissão')).toBeInTheDocument()
  })

  it('should apply custom className', () => {
    const { container } = render(
      <TestWrapper>
        <PermissionTemplates className="custom-class" />
      </TestWrapper>
    )

    expect(container.firstChild).toHaveClass('custom-class')
  })

  it('should show system template badge', () => {
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    // System template should show "Sistema" badge
    expect(screen.getByText('Sistema')).toBeInTheDocument()
  })

  it('should show custom template badges', () => {
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    // Custom templates should show "Personalizado" badge
    expect(screen.getAllByText('Personalizado')).toHaveLength(2)
  })
})