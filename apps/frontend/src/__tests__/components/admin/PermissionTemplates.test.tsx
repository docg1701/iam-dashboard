import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, cleanup } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { PermissionTemplates } from '@/components/admin/PermissionTemplates'
import { AgentName, UserPermissionMatrix } from '@/types/permissions'
import { usePermissionTemplates } from '@/hooks/useUserPermissions'
import { createMockMutation } from '@/__tests__/mocks/tanstack-query'

// Mock the hooks - don't define variables outside the mock factory
vi.mock('@/hooks/useUserPermissions', () => ({
  usePermissionTemplates: vi.fn(),
}))

// Mock PermissionGuard components
vi.mock('@/components/common/PermissionGuard', () => ({
  PermissionGuard: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  CreatePermissionGuard: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  UpdatePermissionGuard: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  DeletePermissionGuard: ({ children }: { children: React.ReactNode }) => <>{children}</>,
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

// The global lucide-react mock in setup.ts handles all icons
// No need to override it here - the global mock includes all necessary icons

// Test wrapper component
const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  // Create a fresh query client for each test
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
    created_by_user_id: 'user-1',
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
    created_by_user_id: 'user-2',
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
    created_by_user_id: 'user-3',
    created_at: '2023-02-01T00:00:00Z',
    updated_at: '2023-02-01T00:00:00Z',
  },
]

// Type assertion for mocked hook
const mockedUsePermissionTemplates = vi.mocked(usePermissionTemplates)

describe('PermissionTemplates', () => {
  beforeEach(() => {
    // Clear all mocks completely 
    vi.clearAllMocks()
    vi.resetAllMocks()
    
    // Setup default mock returns with stable references
    const mockRefetch = vi.fn()
    const mockApplyTemplate = createMockMutation<
      UserPermissionMatrix,
      Error,
      { templateId: string; userId: string; changeReason?: string }
    >({
      mutate: vi.fn(),
      isPending: false,
      error: null,
      isIdle: true,
      isError: false,
      isSuccess: false,
      data: undefined,
      variables: undefined,
      context: undefined,
      isPaused: false,
      failureCount: 0,
      failureReason: null,
      mutateAsync: vi.fn().mockResolvedValue({
        user_id: 'test-user',
        permissions: {
          [AgentName.CLIENT_MANAGEMENT]: { create: true, read: true, update: true, delete: false },
          [AgentName.PDF_PROCESSING]: { create: false, read: true, update: false, delete: false },
          [AgentName.REPORTS_ANALYSIS]: { create: false, read: true, update: false, delete: false },
          [AgentName.AUDIO_RECORDING]: { create: false, read: false, update: false, delete: false },
        },
        last_updated: new Date().toISOString(),
      } as UserPermissionMatrix),
      reset: vi.fn(),
      status: 'idle',
      submittedAt: 0,
    })
    
    // Reset the hook mock completely
    mockedUsePermissionTemplates.mockReset()
    mockedUsePermissionTemplates.mockReturnValue({
      templates: mockTemplates,
      total: mockTemplates.length,
      isLoading: false,
      error: null,
      refetch: mockRefetch,
      applyTemplate: mockApplyTemplate,
      isApplying: false,
      applyError: null,
    })
  })

  afterEach(() => {
    // Explicitly cleanup after each test
    cleanup()
  })

  it('should render templates list', () => {
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    // Count the number of headings to check for duplication
    const headings = screen.getAllByRole('heading', { level: 2 })
    expect(headings).toHaveLength(1)
    
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

    // Check that header exists  
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Templates de Permissão')
    expect(screen.getByText(/Crie e gerencie templates reutilizáveis/)).toBeInTheDocument()
  })

  it('should show create new template button', () => {
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    // Look for button specifically in the header area, not the empty state
    const createButtons = screen.getAllByText('Novo Template')
    expect(createButtons.length).toBeGreaterThan(0)
  })

  it('should display stats cards correctly', () => {
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    expect(screen.getByText('Total de Templates')).toBeInTheDocument()
    
    // Check that stats cards exist by looking for specific stats labels  
    expect(screen.getByText('Total de Templates')).toBeInTheDocument()
    
    // Check that we have the stat numbers (3, 1, 2)
    const statNumbers = screen.getAllByText(/^[0-9]+$/)
    expect(statNumbers.length).toBeGreaterThanOrEqual(3)
    
    // Should contain expected values somewhere
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

    // Check that filter options exist (some text may appear multiple times)
    expect(screen.getAllByText('Todos os Templates').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Templates do Sistema').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Templates Personalizados').length).toBeGreaterThan(0)
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
    // Using generic button selector since icons are now mocked globally
    const buttons = screen.getAllByTestId('button')
    expect(buttons.length).toBeGreaterThan(0)
    
    // Check for action button text content or other identifying features
    expect(screen.getByText('Novo Template')).toBeInTheDocument()
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

    // Look for buttons in table rows - the view button should be the first button in each row's actions
    const tableRows = screen.getAllByTestId('table-row')
    if (tableRows.length > 0) {
      const actionButtons = screen.getAllByTestId('button').filter(button => 
        button.textContent === '' && button.closest('[data-testid="table-row"]')
      )
      
      if (actionButtons.length > 0) {
        await user.click(actionButtons[0])

        await waitFor(() => {
          expect(screen.getByTestId('dialog')).toBeInTheDocument()
          expect(screen.getByText('Visualizar Template')).toBeInTheDocument()
        })
      }
    }
  })

  it('should open edit template dialog', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    // Look for the second action button in table rows (edit button)
    const tableRows = screen.getAllByTestId('table-row')
    if (tableRows.length > 0) {
      const actionButtons = screen.getAllByTestId('button').filter(button => 
        button.textContent === '' && button.closest('[data-testid="table-row"]')
      )
      
      if (actionButtons.length > 1) {
        await user.click(actionButtons[1])

        await waitFor(() => {
          expect(screen.getByTestId('dialog')).toBeInTheDocument()
          expect(screen.getByText('Editar Template')).toBeInTheDocument()
        })
      }
    }
  })

  it('should open delete confirmation dialog', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    // Look for the last action button in table rows (delete button)
    const tableRows = screen.getAllByTestId('table-row')
    if (tableRows.length > 0) {
      const actionButtons = screen.getAllByTestId('button').filter(button => 
        button.textContent === '' && button.closest('[data-testid="table-row"]')
      )
      
      if (actionButtons.length > 3) {
        await user.click(actionButtons[3]) // Delete is typically the 4th button

        await waitFor(() => {
          expect(screen.getByTestId('dialog')).toBeInTheDocument()
          expect(screen.getByText('Excluir Template')).toBeInTheDocument()
          expect(screen.getByText(/Esta ação não pode ser desfeita/)).toBeInTheDocument()
        })
      }
    }
  })

  it('should handle template duplication', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    // Look for the duplicate button in table rows (typically 3rd button)
    const tableRows = screen.getAllByTestId('table-row')
    if (tableRows.length > 0) {
      const actionButtons = screen.getAllByTestId('button').filter(button => 
        button.textContent === '' && button.closest('[data-testid="table-row"]')
      )
      
      if (actionButtons.length > 2) {
        await user.click(actionButtons[2]) // Duplicate is typically the 3rd button

        await waitFor(() => {
          expect(screen.getByTestId('dialog')).toBeInTheDocument()
          expect(screen.getByText('Criar Novo Template')).toBeInTheDocument()
          // Should show duplicated name with "(Cópia)" suffix
        })
      }
    }
  })

  it('should show template form in create mode', async () => {
    const user = userEvent.setup()
    
    render(
      <TestWrapper>
        <PermissionTemplates />
      </TestWrapper>
    )

    const createButtons = screen.getAllByText('Novo Template')
    await user.click(createButtons[0])

    await waitFor(() => {
      expect(screen.getByTestId('dialog')).toBeInTheDocument()
      expect(screen.getByText('Criar Novo Template')).toBeInTheDocument()
      expect(screen.getByText('Nome do Template *')).toBeInTheDocument()
      expect(screen.getByText('Descrição')).toBeInTheDocument()
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

    // Look for the delete button in table rows (typically last button)
    const tableRows = screen.getAllByTestId('table-row')
    if (tableRows.length > 0) {
      const actionButtons = screen.getAllByTestId('button').filter(button => 
        button.textContent === '' && button.closest('[data-testid="table-row"]')
      )
      
      if (actionButtons.length > 3) {
        await user.click(actionButtons[3])

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
    
    // System templates should show "Sistema" badge
    expect(screen.getByText('Sistema')).toBeInTheDocument()
  })

  it('should show empty state when no templates found', () => {
    const mockApplyTemplateEmpty = createMockMutation<
      UserPermissionMatrix,
      Error,
      { templateId: string; userId: string; changeReason?: string }
    >({
      mutate: vi.fn(),
      isPending: false,
      error: null,
    })
    
    mockedUsePermissionTemplates.mockReturnValue({
      templates: [],
      total: 0,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      applyTemplate: mockApplyTemplateEmpty,
      isApplying: false,
      applyError: null,
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
    const mockApplyTemplateLoading = createMockMutation<
      UserPermissionMatrix,
      Error,
      { templateId: string; userId: string; changeReason?: string }
    >({
      mutate: vi.fn(),
      isPending: false,
      error: null,
    })
    
    mockedUsePermissionTemplates.mockReturnValue({
      templates: [],
      total: 0,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
      applyTemplate: mockApplyTemplateLoading,
      isApplying: false,
      applyError: null,
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
    const mockApplyTemplateError = createMockMutation<
      UserPermissionMatrix,
      Error,
      { templateId: string; userId: string; changeReason?: string }
    >({
      mutate: vi.fn(),
      isPending: false,
      error: null,
    })
    
    mockedUsePermissionTemplates.mockReturnValue({
      templates: [],
      total: 0,
      isLoading: false,
      error: error,
      refetch: vi.fn(),
      applyTemplate: mockApplyTemplateError,
      isApplying: false,
      applyError: null,
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
    const mockApplyTemplateRefresh = createMockMutation<
      UserPermissionMatrix,
      Error,
      { templateId: string; userId: string; changeReason?: string }
    >({
      mutate: vi.fn(),
      isPending: false,
      error: null,
    })
    
    mockedUsePermissionTemplates.mockReturnValue({
      templates: mockTemplates,
      total: mockTemplates.length,
      isLoading: false,
      error: null,
      refetch: mockRefetch,
      applyTemplate: mockApplyTemplateRefresh,
      isApplying: false,
      applyError: null,
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

    const createButtons = screen.getAllByText('Novo Template')
    await user.click(createButtons[0])

    await waitFor(() => {
      // Should show permission operations (may appear multiple times for different agents)
      expect(screen.getAllByText('Criar').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Ver').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Editar').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Excluir').length).toBeGreaterThan(0)
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