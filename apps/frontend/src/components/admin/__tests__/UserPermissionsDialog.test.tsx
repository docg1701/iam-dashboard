/**
 * User Permissions Dialog Component Tests
 * 
 * Comprehensive test suite for the UserPermissionsDialog component covering
 * form validation, permission editing, audit history, and accessibility.
 */

import React from 'react'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { UserPermissionsDialog } from '../UserPermissionsDialog'
import { 
  AgentName, 
  PERMISSION_LEVELS, 
  getPermissionsForLevel,
} from '@/types/permissions'
import * as useUserPermissions from '@/hooks/useUserPermissions'

// Mock the hooks
vi.mock('@/hooks/useUserPermissions')

// Mock the PermissionGuard components
vi.mock('@/components/common/PermissionGuard', () => ({
  PermissionGuard: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  UpdatePermissionGuard: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

// Mock toast notifications
vi.mock('@/components/ui/toast', () => ({
  toast: vi.fn(),
}))

// Test data
const mockUser = {
  user_id: 'user-1',
  name: 'João Silva',
  email: 'joao@example.com',
  role: 'admin' as const,
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  last_login: '2024-01-15T10:30:00Z',
}

const mockCurrentPermissions = {
  [AgentName.CLIENT_MANAGEMENT]: getPermissionsForLevel(PERMISSION_LEVELS.FULL),
  [AgentName.PDF_PROCESSING]: getPermissionsForLevel(PERMISSION_LEVELS.STANDARD),
  [AgentName.REPORTS_ANALYSIS]: getPermissionsForLevel(PERMISSION_LEVELS.READ_ONLY),
  [AgentName.AUDIO_RECORDING]: getPermissionsForLevel(PERMISSION_LEVELS.NONE),
}

const mockAuditLogs = [
  {
    audit_id: 'audit-1',
    user_id: 'user-1',
    agent_name: AgentName.CLIENT_MANAGEMENT,
    action: 'UPDATE',
    old_permissions: getPermissionsForLevel(PERMISSION_LEVELS.STANDARD),
    new_permissions: getPermissionsForLevel(PERMISSION_LEVELS.FULL),
    changed_by_user_id: 'admin-1',
    change_reason: 'Promoção para supervisor',
    created_at: '2024-01-10T14:30:00Z',
  },
  {
    audit_id: 'audit-2',
    user_id: 'user-1',
    agent_name: AgentName.PDF_PROCESSING,
    action: 'GRANT',
    old_permissions: null,
    new_permissions: getPermissionsForLevel(PERMISSION_LEVELS.STANDARD),
    changed_by_user_id: 'admin-1',
    change_reason: 'Acesso necessário para nova função',
    created_at: '2024-01-08T09:15:00Z',
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

describe('UserPermissionsDialog Component', () => {
  const mockOnOpenChange = vi.fn()
  const mockOnPermissionsChanged = vi.fn()
  const mockUpdatePermission = vi.fn()
  const mockCreatePermission = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    
    // Setup hook mocks
    vi.mocked(useUserPermissions.useUserPermissions).mockReturnValue({
      permissions: mockCurrentPermissions,
      isLoading: false,
      error: null,
      lastUpdated: new Date('2024-01-15T10:30:00Z'),
      hasPermission: vi.fn().mockReturnValue(true),
      hasAgentPermission: vi.fn().mockReturnValue(true),
      getUserMatrix: vi.fn().mockReturnValue({
        user_id: 'user-1',
        permissions: mockCurrentPermissions,
        last_updated: '2024-01-15T10:30:00Z',
      }),
      refetch: vi.fn(),
      invalidate: vi.fn(),
    })

    vi.mocked(useUserPermissions.usePermissionMutations).mockReturnValue({
      updatePermission: {
        mutateAsync: mockUpdatePermission,
        isPending: false,
        error: null,
      },
      createPermission: {
        mutateAsync: mockCreatePermission,
        isPending: false,
        error: null,
      },
      deletePermission: {
        mutateAsync: vi.fn(),
        isPending: false,
        error: null,
      },
      isLoading: false,
      error: null,
    })

    vi.mocked(useUserPermissions.usePermissionAudit).mockReturnValue({
      logs: mockAuditLogs,
      total: mockAuditLogs.length,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  const renderUserPermissionsDialog = (props = {}) => {
    const defaultProps = {
      user: mockUser,
      open: true,
      onOpenChange: mockOnOpenChange,
      onPermissionsChanged: mockOnPermissionsChanged,
      ...props,
    }

    return render(
      <TestWrapper>
        <UserPermissionsDialog {...defaultProps} />
      </TestWrapper>
    )
  }

  describe('Component Rendering', () => {
    it('should render without crashing when open', () => {
      renderUserPermissionsDialog()
      expect(screen.getByText('Permissões de João Silva')).toBeInTheDocument()
    })

    it('should not render when closed', () => {
      renderUserPermissionsDialog({ open: false })
      expect(screen.queryByText('Permissões de João Silva')).not.toBeInTheDocument()
    })

    it('should not render when user is null', () => {
      renderUserPermissionsDialog({ user: null })
      expect(screen.queryByText('Permissões de')).not.toBeInTheDocument()
    })

    it('should display user information correctly', () => {
      renderUserPermissionsDialog()
      
      expect(screen.getByText('João Silva')).toBeInTheDocument()
      expect(screen.getByText('joao@example.com')).toBeInTheDocument()
      expect(screen.getByText('admin')).toBeInTheDocument()
    })

    it('should render all agent permission sections', () => {
      renderUserPermissionsDialog()
      
      expect(screen.getByText('Gestão de Clientes')).toBeInTheDocument()
      expect(screen.getByText('Processamento de PDFs')).toBeInTheDocument()
      expect(screen.getByText('Relatórios e Análises')).toBeInTheDocument()
      expect(screen.getByText('Gravação de Áudio')).toBeInTheDocument()
    })
  })

  describe('Loading States', () => {
    it('should show loading state when permissions are loading', () => {
      vi.mocked(useUserPermissions.useUserPermissions).mockReturnValue({
        permissions: null,
        isLoading: true,
        error: null,
        lastUpdated: null,
        hasPermission: vi.fn(),
        hasAgentPermission: vi.fn(),
        getUserMatrix: vi.fn(),
        refetch: vi.fn(),
        invalidate: vi.fn(),
      })

      renderUserPermissionsDialog()
      expect(screen.getByText('Carregando permissões...')).toBeInTheDocument()
    })

    it('should show error state when permissions fail to load', () => {
      vi.mocked(useUserPermissions.useUserPermissions).mockReturnValue({
        permissions: null,
        isLoading: false,
        error: new Error('Failed to load permissions'),
        lastUpdated: null,
        hasPermission: vi.fn(),
        hasAgentPermission: vi.fn(),
        getUserMatrix: vi.fn(),
        refetch: vi.fn(),
        invalidate: vi.fn(),
      })

      renderUserPermissionsDialog()
      expect(screen.getByText('Erro ao carregar permissões: Failed to load permissions')).toBeInTheDocument()
    })
  })

  describe('Permission Editing', () => {
    it('should allow editing permission levels', async () => {
      renderUserPermissionsDialog()
      
      // Find the Client Management permission dropdown
      const clientManagementSection = screen.getByText('Gestão de Clientes').closest('.space-y-4')
      expect(clientManagementSection).toBeInTheDocument()
      
      if (clientManagementSection) {
        const permissionSelect = within(clientManagementSection).getByRole('combobox')
        await userEvent.click(permissionSelect)
        
        const standardOption = screen.getByText('Padrão')
        await userEvent.click(standardOption)
        
        // Should update form data and mark as changed
        expect(screen.getByText('Você tem alterações não salvas')).toBeInTheDocument()
      }
    })

    it('should allow editing individual permissions', async () => {
      renderUserPermissionsDialog()
      
      const createCheckbox = screen.getByLabelText('Criar')
      await userEvent.click(createCheckbox)
      
      expect(screen.getByText('Você tem alterações não salvas')).toBeInTheDocument()
    })

    it('should require change reason to save', async () => {
      renderUserPermissionsDialog()
      
      // Make a change
      const createCheckbox = screen.getByLabelText('Criar')
      await userEvent.click(createCheckbox)
      
      // Try to save without reason
      const saveButton = screen.getByText('Salvar Alterações')
      expect(saveButton).toBeDisabled()
      
      // Add reason
      const reasonTextarea = screen.getByPlaceholderText('Descreva o motivo desta alteração de permissões...')
      await userEvent.type(reasonTextarea, 'Atualização necessária')
      
      expect(saveButton).not.toBeDisabled()
    })
  })

  describe('Form Submission', () => {
    it('should save permissions when form is submitted', async () => {
      mockUpdatePermission.mockResolvedValue({})
      
      renderUserPermissionsDialog()
      
      // Make a change
      const createCheckbox = screen.getByLabelText('Criar')
      await userEvent.click(createCheckbox)
      
      // Add reason
      const reasonTextarea = screen.getByPlaceholderText('Descreva o motivo desta alteração de permissões...')
      await userEvent.type(reasonTextarea, 'Teste de atualização')
      
      // Save
      const saveButton = screen.getByText('Salvar Alterações')
      await userEvent.click(saveButton)
      
      await waitFor(() => {
        expect(mockUpdatePermission).toHaveBeenCalled()
      })
    })

    it('should create new permissions for agents without existing permissions', async () => {
      // Mock permissions without PDF processing
      const permissionsWithoutPDF = { ...mockCurrentPermissions }
      delete permissionsWithoutPDF[AgentName.PDF_PROCESSING]
      
      vi.mocked(useUserPermissions.useUserPermissions).mockReturnValue({
        permissions: permissionsWithoutPDF,
        isLoading: false,
        error: null,
        lastUpdated: new Date(),
        hasPermission: vi.fn(),
        hasAgentPermission: vi.fn(),
        getUserMatrix: vi.fn(),
        refetch: vi.fn(),
        invalidate: vi.fn(),
      })

      mockCreatePermission.mockResolvedValue({})
      
      renderUserPermissionsDialog()
      
      // Make a change to PDF processing
      const pdfSection = screen.getByText('Processamento de PDFs').closest('.space-y-4')
      if (pdfSection) {
        const permissionSelect = within(pdfSection).getByRole('combobox')
        await userEvent.click(permissionSelect)
        
        const readOnlyOption = screen.getByText('Leitura')
        await userEvent.click(readOnlyOption)
      }
      
      // Add reason and save
      const reasonTextarea = screen.getByPlaceholderText('Descreva o motivo desta alteração de permissões...')
      await userEvent.type(reasonTextarea, 'Nova permissão')
      
      const saveButton = screen.getByText('Salvar Alterações')
      await userEvent.click(saveButton)
      
      await waitFor(() => {
        expect(mockCreatePermission).toHaveBeenCalled()
      })
    })

    it('should handle save errors gracefully', async () => {
      const { toast } = await import('@/components/ui/toast')
      mockUpdatePermission.mockRejectedValue(new Error('Save failed'))
      
      renderUserPermissionsDialog()
      
      // Make a change
      const createCheckbox = screen.getByLabelText('Criar')
      await userEvent.click(createCheckbox)
      
      // Add reason and save
      const reasonTextarea = screen.getByPlaceholderText('Descreva o motivo desta alteração de permissões...')
      await userEvent.type(reasonTextarea, 'Teste de erro')
      
      const saveButton = screen.getByText('Salvar Alterações')
      await userEvent.click(saveButton)
      
      await waitFor(() => {
        expect(toast).toHaveBeenCalledWith({
          title: 'Erro ao salvar',
          description: 'Não foi possível atualizar as permissões. Tente novamente.',
          variant: 'error',
        })
      })
    })
  })

  describe('Permission History', () => {
    it('should toggle history visibility', async () => {
      renderUserPermissionsDialog()
      
      const toggleHistoryButton = screen.getByText('Ver Histórico')
      await userEvent.click(toggleHistoryButton)
      
      expect(screen.getByText('Histórico de Alterações')).toBeInTheDocument()
      expect(screen.getByText('Promoção para supervisor')).toBeInTheDocument()
      
      const hideHistoryButton = screen.getByText('Ocultar Histórico')
      await userEvent.click(hideHistoryButton)
      
      expect(screen.queryByText('Histórico de Alterações')).not.toBeInTheDocument()
    })

    it('should display audit logs correctly', async () => {
      renderUserPermissionsDialog()
      
      const toggleHistoryButton = screen.getByText('Ver Histórico')
      await userEvent.click(toggleHistoryButton)
      
      expect(screen.getByText('Gestão de Clientes - UPDATE')).toBeInTheDocument()
      expect(screen.getByText('Processamento de PDFs - GRANT')).toBeInTheDocument()
      expect(screen.getByText('Promoção para supervisor')).toBeInTheDocument()
      expect(screen.getByText('Acesso necessário para nova função')).toBeInTheDocument()
    })

    it('should handle history loading state', async () => {
      vi.mocked(useUserPermissions.usePermissionAudit).mockReturnValue({
        logs: [],
        total: 0,
        isLoading: true,
        error: null,
        refetch: vi.fn(),
      })

      renderUserPermissionsDialog()
      
      const toggleHistoryButton = screen.getByText('Ver Histórico')
      await userEvent.click(toggleHistoryButton)
      
      expect(screen.getByText('Carregando histórico...')).toBeInTheDocument()
    })

    it('should handle history error state', async () => {
      vi.mocked(useUserPermissions.usePermissionAudit).mockReturnValue({
        logs: [],
        total: 0,
        isLoading: false,
        error: new Error('Failed to load history'),
        refetch: vi.fn(),
      })

      renderUserPermissionsDialog()
      
      const toggleHistoryButton = screen.getByText('Ver Histórico')
      await userEvent.click(toggleHistoryButton)
      
      expect(screen.getByText('Erro ao carregar histórico de permissões: Failed to load history')).toBeInTheDocument()
    })
  })

  describe('Dialog Management', () => {
    it('should close dialog when cancel is clicked', async () => {
      renderUserPermissionsDialog()
      
      const cancelButton = screen.getByText('Cancelar')
      await userEvent.click(cancelButton)
      
      expect(mockOnOpenChange).toHaveBeenCalledWith(false)
    })

    it('should show confirmation when closing with unsaved changes', async () => {
      // Mock window.confirm
      const mockConfirm = vi.spyOn(window, 'confirm').mockReturnValue(true)
      
      renderUserPermissionsDialog()
      
      // Make a change
      const createCheckbox = screen.getByLabelText('Criar')
      await userEvent.click(createCheckbox)
      
      // Try to close
      const cancelButton = screen.getByText('Cancelar')
      await userEvent.click(cancelButton)
      
      expect(mockConfirm).toHaveBeenCalledWith('Você tem alterações não salvas. Deseja descartar?')
      expect(mockOnOpenChange).toHaveBeenCalledWith(false)
      
      mockConfirm.mockRestore()
    })

    it('should not close dialog when confirmation is denied', async () => {
      // Mock window.confirm to return false
      const mockConfirm = vi.spyOn(window, 'confirm').mockReturnValue(false)
      
      renderUserPermissionsDialog()
      
      // Make a change
      const createCheckbox = screen.getByLabelText('Criar')
      await userEvent.click(createCheckbox)
      
      // Try to close
      const cancelButton = screen.getByText('Cancelar')
      await userEvent.click(cancelButton)
      
      expect(mockConfirm).toHaveBeenCalled()
      expect(mockOnOpenChange).not.toHaveBeenCalled()
      
      mockConfirm.mockRestore()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels and roles', () => {
      renderUserPermissionsDialog()
      
      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Cancelar/ })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Salvar Alterações/ })).toBeInTheDocument()
      expect(screen.getByRole('textbox', { name: /Motivo da Alteração/ })).toBeInTheDocument()
    })

    it('should support keyboard navigation', async () => {
      renderUserPermissionsDialog()
      
      // Tab to first interactive element
      const reasonTextarea = screen.getByRole('textbox')
      reasonTextarea.focus()
      expect(reasonTextarea).toHaveFocus()
      
      // Tab to next element
      fireEvent.keyDown(reasonTextarea, { key: 'Tab' })
      // Next focusable element should receive focus
    })

    it('should have proper form labels', () => {
      renderUserPermissionsDialog()
      
      expect(screen.getByLabelText('Motivo da Alteração')).toBeInTheDocument()
      expect(screen.getByLabelText('Criar')).toBeInTheDocument()
      expect(screen.getByLabelText('Visualizar')).toBeInTheDocument()
      expect(screen.getByLabelText('Editar')).toBeInTheDocument()
      expect(screen.getByLabelText('Excluir')).toBeInTheDocument()
    })
  })

  describe('Loading and Saving States', () => {
    it('should show loading state when saving', async () => {
      vi.mocked(useUserPermissions.usePermissionMutations).mockReturnValue({
        updatePermission: {
          mutateAsync: mockUpdatePermission,
          isPending: true,
          error: null,
        },
        createPermission: {
          mutateAsync: mockCreatePermission,
          isPending: false,
          error: null,
        },
        deletePermission: {
          mutateAsync: vi.fn(),
          isPending: false,
          error: null,
        },
        isLoading: true,
        error: null,
      })

      renderUserPermissionsDialog()
      
      const saveButton = screen.getByText('Salvando...')
      expect(saveButton).toBeDisabled()
      expect(screen.getByRole('button', { name: /Cancelar/ })).toBeDisabled()
    })

    it('should disable form elements when saving', async () => {
      vi.mocked(useUserPermissions.usePermissionMutations).mockReturnValue({
        updatePermission: {
          mutateAsync: mockUpdatePermission,
          isPending: true,
          error: null,
        },
        createPermission: {
          mutateAsync: mockCreatePermission,
          isPending: false,
          error: null,
        },
        deletePermission: {
          mutateAsync: vi.fn(),
          isPending: false,
          error: null,
        },
        isLoading: true,
        error: null,
      })

      renderUserPermissionsDialog()
      
      // All form elements should be disabled
      const checkboxes = screen.getAllByRole('checkbox')
      checkboxes.forEach(checkbox => {
        expect(checkbox).toBeDisabled()
      })
      
      const comboboxes = screen.getAllByRole('combobox')
      comboboxes.forEach(combobox => {
        expect(combobox).toBeDisabled()
      })
    })
  })
})