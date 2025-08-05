/**
 * Bulk Permission Dialog Component Tests
 * 
 * Comprehensive test suite for the BulkPermissionDialog component covering
 * bulk operations, template application, progress tracking, and error handling.
 */

import React from 'react'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { BulkPermissionDialog } from '../BulkPermissionDialog'
import { 
  AgentName, 
  PERMISSION_LEVELS, 
  getPermissionsForLevel,
} from '@/types/permissions'
import * as useUserPermissions from '@/hooks/useUserPermissions'
import * as permissionAPI from '@/lib/api/permissions'

// Mock the hooks
vi.mock('@/hooks/useUserPermissions')

// Mock the PermissionAPI
vi.mock('@/lib/api/permissions', () => ({
  PermissionAPI: {
    User: {
      bulkAssignPermissions: vi.fn(),
    },
  },
}))

// Mock the PermissionGuard components
vi.mock('@/components/common/PermissionGuard', () => ({
  PermissionGuard: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

// Mock toast notifications
vi.mock('@/components/ui/toast', () => ({
  toast: vi.fn(),
}))

// Test data
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
    name: 'Pedro Costa',
    email: 'pedro@example.com',
    role: 'user' as const,
    is_active: false,
  },
]

const mockTemplates = [
  {
    template_id: 'template-1',
    template_name: 'Operador Básico',
    description: 'Permissões básicas para operadores',
    permissions: {
      [AgentName.CLIENT_MANAGEMENT]: getPermissionsForLevel(PERMISSION_LEVELS.READ_ONLY),
      [AgentName.PDF_PROCESSING]: getPermissionsForLevel(PERMISSION_LEVELS.NONE),
      [AgentName.REPORTS_ANALYSIS]: getPermissionsForLevel(PERMISSION_LEVELS.NONE),
      [AgentName.AUDIO_RECORDING]: getPermissionsForLevel(PERMISSION_LEVELS.NONE),
    },
    is_system_template: true,
    created_by_user_id: 'admin-1',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: null,
  },
  {
    template_id: 'template-2',
    template_name: 'Supervisor',
    description: 'Permissões completas para supervisores',
    permissions: {
      [AgentName.CLIENT_MANAGEMENT]: getPermissionsForLevel(PERMISSION_LEVELS.FULL),
      [AgentName.PDF_PROCESSING]: getPermissionsForLevel(PERMISSION_LEVELS.STANDARD),
      [AgentName.REPORTS_ANALYSIS]: getPermissionsForLevel(PERMISSION_LEVELS.STANDARD),
      [AgentName.AUDIO_RECORDING]: getPermissionsForLevel(PERMISSION_LEVELS.READ_ONLY),
    },
    is_system_template: false,
    created_by_user_id: 'admin-1',
    created_at: '2024-01-02T00:00:00Z',
    updated_at: null,
  },
]

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

describe('BulkPermissionDialog Component', () => {
  const mockOnOpenChange = vi.fn()
  const mockOnBulkOperationComplete = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    
    // Setup hook mocks
    vi.mocked(useUserPermissions.usePermissionTemplates).mockReturnValue({
      templates: mockTemplates,
      total: mockTemplates.length,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      applyTemplate: {
        mutateAsync: vi.fn(),
        isPending: false,
        error: null,
      },
      isApplying: false,
      applyError: null,
    })

    // Setup API mocks
    vi.mocked(permissionAPI.PermissionAPI.User.bulkAssignPermissions).mockResolvedValue({
      success_count: 3,
      error_count: 0,
      errors: [],
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  const renderBulkPermissionDialog = (props = {}) => {
    const defaultProps = {
      users: mockUsers,
      open: true,
      onOpenChange: mockOnOpenChange,
      onBulkOperationComplete: mockOnBulkOperationComplete,
      ...props,
    }

    return render(
      <TestWrapper>
        <BulkPermissionDialog {...defaultProps} />
      </TestWrapper>
    )
  }

  describe('Component Rendering', () => {
    it('should render without crashing when open', () => {
      renderBulkPermissionDialog()
      expect(screen.getByText('Operação em Lote - 3 usuários selecionados')).toBeInTheDocument()
    })

    it('should not render when closed', () => {
      renderBulkPermissionDialog({ open: false })
      expect(screen.queryByText('Operação em Lote')).not.toBeInTheDocument()
    })

    it('should display user summary correctly', () => {
      renderBulkPermissionDialog()
      
      expect(screen.getByText('Resumo dos Usuários')).toBeInTheDocument()
      expect(screen.getByText('2')).toBeInTheDocument() // Active users
      expect(screen.getByText('1')).toBeInTheDocument() // Inactive users
      expect(screen.getByText('1')).toBeInTheDocument() // Admin users
      expect(screen.getByText('2')).toBeInTheDocument() // Regular users
    })

    it('should render operation type selector', () => {
      renderBulkPermissionDialog()
      
      expect(screen.getByText('Tipo de Operação')).toBeInTheDocument()
      expect(screen.getByDisplayValue('Aplicar Template')).toBeInTheDocument()
    })
  })

  describe('Operation Type Selection', () => {
    it('should allow changing operation type', async () => {
      renderBulkPermissionDialog()
      
      const operationSelect = screen.getByDisplayValue('Aplicar Template')
      await userEvent.click(operationSelect)
      
      const grantAllOption = screen.getByText('Conceder Todas as Permissões')
      await userEvent.click(grantAllOption)
      
      expect(screen.getByDisplayValue('Conceder Todas as Permissões')).toBeInTheDocument()
    })

    it('should show template selection when template operation is selected', async () => {
      renderBulkPermissionDialog()
      
      expect(screen.getByText('Selecionar Template')).toBeInTheDocument()
      
      const templateSelect = screen.getByPlaceholderText('Escolha um template...')
      await userEvent.click(templateSelect)
      
      expect(screen.getByText('Operador Básico')).toBeInTheDocument()
      expect(screen.getByText('Supervisor')).toBeInTheDocument()
    })

    it('should show custom permissions editor for custom operation', async () => {
      renderBulkPermissionDialog()
      
      const operationSelect = screen.getByDisplayValue('Aplicar Template')
      await userEvent.click(operationSelect)
      
      const customOption = screen.getByText('Permissões Personalizadas')
      await userEvent.click(customOption)
      
      expect(screen.getByText('Permissões Personalizadas')).toBeInTheDocument()
      expect(screen.getByText('Configure permissões específicas para cada agente')).toBeInTheDocument()
    })

    it('should show warning for dangerous operations', async () => {
      renderBulkPermissionDialog()
      
      const operationSelect = screen.getByDisplayValue('Aplicar Template')
      await userEvent.click(operationSelect)
      
      const revokeAllOption = screen.getByText('Revogar Todas as Permissões')
      await userEvent.click(revokeAllOption)
      
      expect(screen.getByText('Atenção:')).toBeInTheDocument()
      expect(screen.getByText(/Esta operação afetará 3 usuários/)).toBeInTheDocument()
    })
  })

  describe('Template Operations', () => {
    it('should show template preview when template is selected', async () => {
      renderBulkPermissionDialog()
      
      const templateSelect = screen.getByPlaceholderText('Escolha um template...')
      await userEvent.click(templateSelect)
      
      const operatorTemplate = screen.getByText('Operador Básico')
      await userEvent.click(operatorTemplate)
      
      expect(screen.getByText('Pré-visualização do Template')).toBeInTheDocument()
      expect(screen.getByText('Permissões básicas para operadores')).toBeInTheDocument()
    })

    it('should display template permissions correctly in preview', async () => {
      renderBulkPermissionDialog()
      
      const templateSelect = screen.getByPlaceholderText('Escolha um template...')
      await userEvent.click(templateSelect)
      
      const supervisorTemplate = screen.getByText('Supervisor')
      await userEvent.click(supervisorTemplate)
      
      const previewSection = screen.getByText('Pré-visualização do Template').closest('.space-y-2')
      expect(previewSection).toBeInTheDocument()
      
      if (previewSection) {
        expect(within(previewSection).getByText('Gestão de Clientes')).toBeInTheDocument()
        expect(within(previewSection).getByText('Completo')).toBeInTheDocument()
      }
    })
  })

  describe('Custom Permissions', () => {
    it('should allow editing custom permissions', async () => {
      renderBulkPermissionDialog()
      
      // Switch to custom operation
      const operationSelect = screen.getByDisplayValue('Aplicar Template')
      await userEvent.click(operationSelect)
      
      const customOption = screen.getByText('Permissões Personalizadas')
      await userEvent.click(customOption)
      
      // Find and modify a permission dropdown
      const permissionSelects = screen.getAllByRole('combobox')
      const clientManagementSelect = permissionSelects.find(select => 
        select.closest('.space-y-2')?.textContent?.includes('Gestão de Clientes')
      )
      
      if (clientManagementSelect) {
        await userEvent.click(clientManagementSelect)
        const fullOption = screen.getByText('Completo')
        await userEvent.click(fullOption)
      }
    })
  })

  describe('Form Validation', () => {
    it('should require change reason to execute operation', async () => {
      renderBulkPermissionDialog()
      
      // Select a template
      const templateSelect = screen.getByPlaceholderText('Escolha um template...')
      await userEvent.click(templateSelect)
      
      const operatorTemplate = screen.getByText('Operador Básico')
      await userEvent.click(operatorTemplate)
      
      // Execute button should be disabled without reason
      const executeButton = screen.getByText('Executar Operação')
      expect(executeButton).toBeDisabled()
      
      // Add reason
      const reasonTextarea = screen.getByPlaceholderText('Descreva o motivo desta operação em lote...')
      await userEvent.type(reasonTextarea, 'Aplicação de template padrão')
      
      expect(executeButton).not.toBeDisabled()
    })

    it('should show error toast when trying to execute without reason', async () => {
      const { toast } = await import('@/components/ui/toast')
      
      renderBulkPermissionDialog()
      
      // Mock the execute function to trigger validation
      const executeButton = screen.getByText('Executar Operação')
      
      // Force enable the button temporarily
      executeButton.removeAttribute('disabled')
      await userEvent.click(executeButton)
      
      expect(toast).toHaveBeenCalledWith({
        title: 'Motivo obrigatório',
        description: 'Por favor, informe o motivo da alteração.',
        variant: 'error',
      })
    })
  })

  describe('Operation Execution', () => {
    it('should execute bulk operation successfully', async () => {
      const { toast } = await import('@/components/ui/toast')
      
      renderBulkPermissionDialog()
      
      // Select template and add reason
      const templateSelect = screen.getByPlaceholderText('Escolha um template...')
      await userEvent.click(templateSelect)
      
      const operatorTemplate = screen.getByText('Operador Básico')
      await userEvent.click(operatorTemplate)
      
      const reasonTextarea = screen.getByPlaceholderText('Descreva o motivo desta operação em lote...')
      await userEvent.type(reasonTextarea, 'Aplicação de template padrão')
      
      // Execute operation
      const executeButton = screen.getByText('Executar Operação')
      await userEvent.click(executeButton)
      
      await waitFor(() => {
        expect(permissionAPI.PermissionAPI.User.bulkAssignPermissions).toHaveBeenCalledWith({
          user_ids: ['user-1'],
          permissions: expect.any(Object),
          change_reason: 'Aplicação de template padrão',
        })
      })
      
      await waitFor(() => {
        expect(toast).toHaveBeenCalledWith({
          title: 'Operação concluída',
          description: '3 usuários atualizados com sucesso. 0 falhas.',
          variant: 'success',
        })
      })
    })

    it('should show progress during operation execution', async () => {
      // Mock slow API response
      vi.mocked(permissionAPI.PermissionAPI.User.bulkAssignPermissions).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({
          success_count: 1,
          error_count: 0,
          errors: [],
        }), 100))
      )
      
      renderBulkPermissionDialog()
      
      // Setup and execute operation
      const templateSelect = screen.getByPlaceholderText('Escolha um template...')
      await userEvent.click(templateSelect)
      
      const operatorTemplate = screen.getByText('Operador Básico')
      await userEvent.click(operatorTemplate)
      
      const reasonTextarea = screen.getByPlaceholderText('Descreva o motivo desta operação em lote...')
      await userEvent.type(reasonTextarea, 'Teste de progresso')
      
      const executeButton = screen.getByText('Executar Operação')
      await userEvent.click(executeButton)
      
      // Should show progress
      expect(screen.getByText('Executando...')).toBeInTheDocument()
      expect(screen.getByText('Progresso da Operação')).toBeInTheDocument()
    })

    it('should handle operation errors gracefully', async () => {
      const { toast } = await import('@/components/ui/toast')
      
      vi.mocked(permissionAPI.PermissionAPI.User.bulkAssignPermissions).mockRejectedValue(
        new Error('API Error')
      )
      
      renderBulkPermissionDialog()
      
      // Setup and execute operation
      const templateSelect = screen.getByPlaceholderText('Escolha un template...')
      await userEvent.click(templateSelect)
      
      const operatorTemplate = screen.getByText('Operador Básico')
      await userEvent.click(operatorTemplate)
      
      const reasonTextarea = screen.getByPlaceholderText('Descreva o motivo desta operação em lote...')
      await userEvent.type(reasonTextarea, 'Teste de erro')
      
      const executeButton = screen.getByText('Executar Operação')
      await userEvent.click(executeButton)
      
      await waitFor(() => {
        expect(toast).toHaveBeenCalledWith({
          title: 'Erro na operação',
          description: 'Falha ao executar a operação em lote. Tente novamente.',
          variant: 'error',
        })
      })
    })

    it('should show partial success with errors', async () => {
      const { toast } = await import('@/components/ui/toast')
      
      vi.mocked(permissionAPI.PermissionAPI.User.bulkAssignPermissions).mockResolvedValue({
        success_count: 2,
        error_count: 1,
        errors: [
          {
            user_id: 'user-3',
            error: 'User is inactive',
          },
        ],
      })
      
      renderBulkPermissionDialog()
      
      // Setup and execute operation
      const templateSelect = screen.getByPlaceholderText('Escolha un template...')
      await userEvent.click(templateSelect)
      
      const operatorTemplate = screen.getByText('Operador Básico')
      await userEvent.click(operatorTemplate)
      
      const reasonTextarea = screen.getByPlaceholderText('Descreva o motivo desta operação em lote...')
      await userEvent.type(reasonTextarea, 'Teste com erros parciais')
      
      const executeButton = screen.getByText('Executar Operação')
      await userEvent.click(executeButton)
      
      await waitFor(() => {
        expect(toast).toHaveBeenCalledWith({
          title: 'Operação concluída',
          description: '2 usuários atualizados com sucesso. 1 falhas.',
          variant: 'warning',
        })
      })
    })
  })

  describe('Export Functionality', () => {
    it('should export user list', async () => {
      const { toast } = await import('@/components/ui/toast')
      
      // Mock URL.createObjectURL and related functions
      global.URL.createObjectURL = vi.fn(() => 'mock-url')
      global.URL.revokeObjectURL = vi.fn()
      
      const mockAppendChild = vi.fn()
      const mockRemoveChild = vi.fn()
      const mockClick = vi.fn()
      
      document.body.appendChild = mockAppendChild
      document.body.removeChild = mockRemoveChild
      
      const mockLink = {
        href: '',
        download: '',
        click: mockClick,
      }
      
      vi.spyOn(document, 'createElement').mockReturnValue(mockLink as HTMLAnchorElement)
      
      renderBulkPermissionDialog()
      
      const exportButton = screen.getByText('Exportar Lista')
      await userEvent.click(exportButton)
      
      expect(mockAppendChild).toHaveBeenCalledWith(mockLink)
      expect(mockClick).toHaveBeenCalled()
      expect(mockRemoveChild).toHaveBeenCalledWith(mockLink)
      
      expect(toast).toHaveBeenCalledWith({
        title: 'Exportação concluída',
        description: 'Lista de usuários exportada com sucesso.',
        variant: 'success',
      })
    })
  })

  describe('Dialog Management', () => {
    it('should close dialog when cancel is clicked', async () => {
      renderBulkPermissionDialog()
      
      const cancelButton = screen.getByText('Cancelar')
      await userEvent.click(cancelButton)
      
      expect(mockOnOpenChange).toHaveBeenCalledWith(false)
    })

    it('should auto-close dialog after successful operation', async () => {
      vi.useFakeTimers()
      
      renderBulkPermissionDialog()
      
      // Execute successful operation
      const templateSelect = screen.getByPlaceholderText('Escolha un template...')
      await userEvent.click(templateSelect)
      
      const operatorTemplate = screen.getByText('Operador Básico')
      await userEvent.click(operatorTemplate)
      
      const reasonTextarea = screen.getByPlaceholderText('Descreva o motivo desta operação em lote...')
      await userEvent.type(reasonTextarea, 'Auto-close test')
      
      const executeButton = screen.getByText('Executar Operação')
      await userEvent.click(executeButton)
      
      await waitFor(() => {
        expect(mockOnBulkOperationComplete).toHaveBeenCalled()
      })
      
      // Fast-forward time
      vi.advanceTimersByTime(2000)
      
      expect(mockOnOpenChange).toHaveBeenCalledWith(false)
      
      vi.useRealTimers()
    })
  })

  describe('Template Loading', () => {
    it('should show loading state for templates', () => {
      vi.mocked(useUserPermissions.usePermissionTemplates).mockReturnValue({
        templates: [],
        total: 0,
        isLoading: true,
        error: null,
        refetch: vi.fn(),
        applyTemplate: {
          mutateAsync: vi.fn(),
          isPending: false,
          error: null,
        },
        isApplying: false,
        applyError: null,
      })

      renderBulkPermissionDialog()
      
      const templateSelect = screen.getByPlaceholderText('Escolha un template...')
      expect(templateSelect).toBeDisabled()
    })

    it('should handle template loading errors', () => {
      vi.mocked(useUserPermissions.usePermissionTemplates).mockReturnValue({
        templates: [],
        total: 0,
        isLoading: false,
        error: new Error('Failed to load templates'),
        refetch: vi.fn(),
        applyTemplate: {
          mutateAsync: vi.fn(),
          isPending: false,
          error: null,
        },
        isApplying: false,
        applyError: null,
      })

      renderBulkPermissionDialog()
      
      const templateSelect = screen.getByPlaceholderText('Escolha un template...')
      expect(templateSelect).toBeDisabled()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels and roles', () => {
      renderBulkPermissionDialog()
      
      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Cancelar/ })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Executar Operação/ })).toBeInTheDocument()
      expect(screen.getByRole('textbox', { name: /Motivo da Alteração/ })).toBeInTheDocument()
    })

    it('should support keyboard navigation', () => {
      renderBulkPermissionDialog()
      
      const reasonTextarea = screen.getByRole('textbox')
      reasonTextarea.focus()
      expect(reasonTextarea).toHaveFocus()
    })
  })
})