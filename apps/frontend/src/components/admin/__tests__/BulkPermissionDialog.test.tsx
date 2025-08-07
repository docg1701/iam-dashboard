/**
 * BulkPermissionDialog Component Tests
 * 
 * Comprehensive tests for the BulkPermissionDialog with progress tracking and error handling
 * Following CLAUDE.md rules: no internal mocking, only external API mocking
 */

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import React from 'react'

import { BulkPermissionDialog } from '../BulkPermissionDialog'
import useAuthStore from '@/store/authStore'
import type { User } from '@/types/auth'

// Test utilities
const createTestQueryClient = () => {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
      mutations: { retry: false }
    },
    logger: { log: () => {}, warn: () => {}, error: () => {} }
  })
}

const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = createTestQueryClient()
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

// Mock data
const mockAdminUser: User = {
  user_id: 'admin-123',
  email: 'admin@test.com',
  role: 'admin',
  is_active: true,
  totp_enabled: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  full_name: 'Admin User'
}

const mockSelectedUsers = [
  {
    user_id: 'user-1',
    email: 'user1@test.com',
    role: 'user',
    is_active: true,
    totp_enabled: false,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    full_name: 'User One'
  },
  {
    user_id: 'user-2',
    email: 'user2@test.com',
    role: 'user',
    is_active: true,
    totp_enabled: false,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
    full_name: 'User Two'
  },
  {
    user_id: 'user-3',
    email: 'user3@test.com',
    role: 'user',
    is_active: true,
    totp_enabled: true,
    created_at: '2024-01-03T00:00:00Z',
    updated_at: '2024-01-03T00:00:00Z',
    full_name: 'User Three'
  }
]

const mockPermissionTemplates = [
  {
    template_id: 'template-1',
    template_name: 'Client Specialist',
    description: 'Full client management access',
    permissions: {
      client_management: { create: true, read: true, update: true, delete: false },
      pdf_processing: { create: false, read: true, update: false, delete: false },
      reports_analysis: { create: false, read: true, update: false, delete: false },
      audio_recording: { create: false, read: false, update: false, delete: false }
    },
    is_system_template: true,
    created_at: '2024-01-01T00:00:00Z'
  },
  {
    template_id: 'template-2',
    template_name: 'Read Only Access',
    description: 'Read-only access to all agents',
    permissions: {
      client_management: { create: false, read: true, update: false, delete: false },
      pdf_processing: { create: false, read: true, update: false, delete: false },
      reports_analysis: { create: false, read: true, update: false, delete: false },
      audio_recording: { create: false, read: true, update: false, delete: false }
    },
    is_system_template: true,
    created_at: '2024-01-01T00:00:00Z'
  }
]

const mockFetch = vi.fn()
const mockOnClose = vi.fn()
const mockOnComplete = vi.fn()

beforeEach(() => {
  global.fetch = mockFetch
})

afterEach(() => {
  vi.clearAllMocks()
})

describe('BulkPermissionDialog', () => {
  describe('Dialog Rendering', () => {
    beforeEach(() => {
      // Mock authentication API for rendering tests
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ user: mockAdminUser })
      } as Response)
    })

    it('should not render when not open', () => {
      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={false}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      expect(screen.queryByText(/operações em lote/i)).not.toBeInTheDocument()
    })

    it('should not render when no users selected', () => {
      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={[]}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      expect(screen.queryByText(/operações em lote/i)).not.toBeInTheDocument()
    })

    it('should render dialog header with selected user count', async () => {
      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Operações em Lote')).toBeInTheDocument()
      })
      
      expect(screen.getByText('Gerenciar permissões para 3 usuários selecionados')).toBeInTheDocument()
    })

    it('should display selected users list', async () => {
      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Usuários Selecionados')).toBeInTheDocument()
      })
      
      expect(screen.getByText('User One')).toBeInTheDocument()
      expect(screen.getByText('user1@test.com')).toBeInTheDocument()
      expect(screen.getByText('User Two')).toBeInTheDocument()
      expect(screen.getByText('User Three')).toBeInTheDocument()
    })
  })

  describe('Operation Type Selection', () => {
    beforeEach(() => {
      // Mock authentication API for operation type tests
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ user: mockAdminUser })
      } as Response)
    })

    it('should display operation type options', async () => {
      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Tipo de Operação')).toBeInTheDocument()
      })
      
      expect(screen.getByRole('radio', { name: /aplicar template/i })).toBeInTheDocument()
      expect(screen.getByRole('radio', { name: /conceder permissões/i })).toBeInTheDocument()
      expect(screen.getByRole('radio', { name: /revogar permissões/i })).toBeInTheDocument()
      expect(screen.getByRole('radio', { name: /personalizado/i })).toBeInTheDocument()
    })

    it('should show template selector when "Apply Template" is selected', async () => {
      const user = userEvent.setup()

      // Mock authentication and templates APIs
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ user: mockAdminUser })
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ templates: mockPermissionTemplates })
        } as Response)

      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Tipo de Operação')).toBeInTheDocument()
      })

      const applyTemplateRadio = screen.getByRole('radio', { name: /aplicar template/i })
      await user.click(applyTemplateRadio)

      await waitFor(() => {
        expect(screen.getByText('Selecionar Template')).toBeInTheDocument()
        expect(screen.getByText('Client Specialist')).toBeInTheDocument()
        expect(screen.getByText('Read Only Access')).toBeInTheDocument()
      })
    })

    it('should show permission checkboxes when "Grant Permissions" is selected', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      const grantPermissionsRadio = screen.getByRole('radio', { name: /conceder permissões/i })
      await user.click(grantPermissionsRadio)

      expect(screen.getByText('Selecionar Permissões para Conceder')).toBeInTheDocument()
      expect(screen.getByText('Gestão de Clientes')).toBeInTheDocument()
      expect(screen.getByText('Processamento PDF')).toBeInTheDocument()
      expect(screen.getByText('Relatórios e Análises')).toBeInTheDocument()
      expect(screen.getByText('Gravação de Áudio')).toBeInTheDocument()

      // Should show operation checkboxes for each agent
      expect(screen.getAllByLabelText(/criar/i)).toHaveLength(4)
      expect(screen.getAllByLabelText(/visualizar/i)).toHaveLength(4)
      expect(screen.getAllByLabelText(/editar/i)).toHaveLength(4)
      expect(screen.getAllByLabelText(/excluir/i)).toHaveLength(4)
    })

    it('should show permission checkboxes when "Revoke Permissions" is selected', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      const revokePermissionsRadio = screen.getByRole('radio', { name: /revogar permissões/i })
      await user.click(revokePermissionsRadio)

      expect(screen.getByText('Selecionar Permissões para Revogar')).toBeInTheDocument()
      expect(screen.getByText('Gestão de Clientes')).toBeInTheDocument()
    })

    it('should show custom permission matrix when "Custom" is selected', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      const customRadio = screen.getByRole('radio', { name: /personalizado/i })
      await user.click(customRadio)

      expect(screen.getByText('Configuração Personalizada')).toBeInTheDocument()
      expect(screen.getByText(/defina permissões específicas para cada agente/i)).toBeInTheDocument()
    })
  })

  describe('Change Reason Requirement', () => {
    it('should require change reason for all operations', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      expect(screen.getByText('Motivo da Alteração')).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/descreva o motivo desta operação/i)).toBeInTheDocument()

      // Apply button should be disabled without reason
      const applyButton = screen.getByRole('button', { name: /aplicar alterações/i })
      expect(applyButton).toBeDisabled()

      // Add reason
      const reasonTextarea = screen.getByPlaceholderText(/descreva o motivo desta operação/i)
      await user.type(reasonTextarea, 'Atualizando permissões conforme nova política de acesso')

      // Select operation type and make changes
      const grantPermissionsRadio = screen.getByRole('radio', { name: /conceder permissões/i })
      await user.click(grantPermissionsRadio)

      const createCheckboxes = screen.getAllByLabelText(/criar/i)
      await user.click(createCheckboxes[0]) // Grant create permission for client management

      await waitFor(() => {
        expect(applyButton).toBeEnabled()
      })
    })

    it('should disable apply button if reason is cleared', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      // Add reason and make changes
      const reasonTextarea = screen.getByPlaceholderText(/descreva o motivo desta operação/i)
      await user.type(reasonTextarea, 'Test reason')

      const grantPermissionsRadio = screen.getByRole('radio', { name: /conceder permissões/i })
      await user.click(grantPermissionsRadio)

      const createCheckboxes = screen.getAllByLabelText(/criar/i)
      await user.click(createCheckboxes[0])

      const applyButton = screen.getByRole('button', { name: /aplicar alterações/i })
      await waitFor(() => {
        expect(applyButton).toBeEnabled()
      })

      // Clear the reason
      await user.clear(reasonTextarea)

      await waitFor(() => {
        expect(applyButton).toBeDisabled()
      })
    })
  })

  describe('Template Application', () => {
    beforeEach(() => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ templates: mockPermissionTemplates })
      } as Response)
    })

    it('should show template preview when template is selected', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      const applyTemplateRadio = screen.getByRole('radio', { name: /aplicar template/i })
      await user.click(applyTemplateRadio)

      await waitFor(() => {
        expect(screen.getByText('Client Specialist')).toBeInTheDocument()
      })

      // Select template
      const templateCard = screen.getByText('Client Specialist').closest('.cursor-pointer')!
      await user.click(templateCard)

      // Should show preview
      expect(screen.getByText('Preview das Permissões')).toBeInTheDocument()
      expect(screen.getByText('Gestão de Clientes: Padrão')).toBeInTheDocument()
      expect(screen.getByText('Processamento PDF: Somente Leitura')).toBeInTheDocument()
    })

    it('should apply template to all selected users', async () => {
      const user = userEvent.setup()

      // Mock bulk operation API
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          results: [
            { user_id: 'user-1', status: 'success' },
            { user_id: 'user-2', status: 'success' },
            { user_id: 'user-3', status: 'success' }
          ]
        })
      } as Response)

      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      // Select apply template
      const applyTemplateRadio = screen.getByRole('radio', { name: /aplicar template/i })
      await user.click(applyTemplateRadio)

      await waitFor(() => {
        expect(screen.getByText('Client Specialist')).toBeInTheDocument()
      })

      // Select template
      const templateCard = screen.getByText('Client Specialist').closest('.cursor-pointer')!
      await user.click(templateCard)

      // Add reason
      const reasonTextarea = screen.getByPlaceholderText(/descreva o motivo desta operação/i)
      await user.type(reasonTextarea, 'Aplicando template de especialista em clientes')

      // Apply changes
      const applyButton = screen.getByRole('button', { name: /aplicar alterações/i })
      await user.click(applyButton)

      // Should show progress
      expect(screen.getByText('Aplicando Alterações')).toBeInTheDocument()
      expect(screen.getByRole('progressbar')).toBeInTheDocument()

      await waitFor(() => {
        expect(screen.getByText('Operação Concluída')).toBeInTheDocument()
        expect(screen.getByText(/3 usuários atualizados com sucesso/i)).toBeInTheDocument()
      })
    })
  })

  describe('Permission Granting and Revoking', () => {
    it('should grant selected permissions to all users', async () => {
      const user = userEvent.setup()

      // Mock bulk operation API
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          results: [
            { user_id: 'user-1', status: 'success' },
            { user_id: 'user-2', status: 'success' },
            { user_id: 'user-3', status: 'success' }
          ]
        })
      } as Response)

      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      // Select grant permissions
      const grantPermissionsRadio = screen.getByRole('radio', { name: /conceder permissões/i })
      await user.click(grantPermissionsRadio)

      // Select permissions to grant
      const createCheckboxes = screen.getAllByLabelText(/criar/i)
      const readCheckboxes = screen.getAllByLabelText(/visualizar/i)
      
      await user.click(createCheckboxes[0]) // Client management create
      await user.click(readCheckboxes[1]) // PDF processing read

      // Add reason
      const reasonTextarea = screen.getByPlaceholderText(/descreva o motivo desta operação/i)
      await user.type(reasonTextarea, 'Concedendo novas permissões para equipe')

      // Apply changes
      const applyButton = screen.getByRole('button', { name: /aplicar alterações/i })
      await user.click(applyButton)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/permissions/bulk'),
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              'Content-Type': 'application/json'
            }),
            body: expect.stringContaining('grant')
          })
        )
      })
    })

    it('should revoke selected permissions from all users', async () => {
      const user = userEvent.setup()

      // Mock bulk operation API
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          results: [
            { user_id: 'user-1', status: 'success' },
            { user_id: 'user-2', status: 'success' },
            { user_id: 'user-3', status: 'success' }
          ]
        })
      } as Response)

      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      // Select revoke permissions
      const revokePermissionsRadio = screen.getByRole('radio', { name: /revogar permissões/i })
      await user.click(revokePermissionsRadio)

      // Select permissions to revoke
      const deleteCheckboxes = screen.getAllByLabelText(/excluir/i)
      await user.click(deleteCheckboxes[0]) // Revoke delete permission for client management

      // Add reason
      const reasonTextarea = screen.getByPlaceholderText(/descreva o motivo desta operação/i)
      await user.type(reasonTextarea, 'Removendo permissões de exclusão por segurança')

      // Apply changes
      const applyButton = screen.getByRole('button', { name: /aplicar alterações/i })
      await user.click(applyButton)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/permissions/bulk'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('revoke')
          })
        )
      })
    })

    it('should show confirmation dialog for revoke operations', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      // Select revoke permissions
      const revokePermissionsRadio = screen.getByRole('radio', { name: /revogar permissões/i })
      await user.click(revokePermissionsRadio)

      // Select all permissions for client management
      const clientCheckboxes = screen.getAllByLabelText(/criar|visualizar|editar|excluir/i).slice(0, 4)
      for (const checkbox of clientCheckboxes) {
        await user.click(checkbox)
      }

      // Add reason
      const reasonTextarea = screen.getByPlaceholderText(/descreva o motivo desta operação/i)
      await user.type(reasonTextarea, 'Removendo acesso completo')

      // Try to apply - should show confirmation
      const applyButton = screen.getByRole('button', { name: /aplicar alterações/i })
      await user.click(applyButton)

      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByText(/tem certeza que deseja revogar/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /confirmar/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /cancelar/i })).toBeInTheDocument()
    })
  })

  describe('Progress Tracking', () => {
    it('should show progress bar during bulk operations', async () => {
      const user = userEvent.setup()

      // Mock slow bulk operation
      const slowPromise = new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({
            results: [
              { user_id: 'user-1', status: 'success' },
              { user_id: 'user-2', status: 'success' },
              { user_id: 'user-3', status: 'success' }
            ]
          })
        }), 100)
      )
      mockFetch.mockReturnValueOnce(slowPromise as any)

      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      // Setup and apply changes
      const grantPermissionsRadio = screen.getByRole('radio', { name: /conceder permissões/i })
      await user.click(grantPermissionsRadio)

      const createCheckboxes = screen.getAllByLabelText(/criar/i)
      await user.click(createCheckboxes[0])

      const reasonTextarea = screen.getByPlaceholderText(/descreva o motivo desta operação/i)
      await user.type(reasonTextarea, 'Test operation')

      const applyButton = screen.getByRole('button', { name: /aplicar alterações/i })
      await user.click(applyButton)

      // Should show progress UI
      expect(screen.getByText('Aplicando Alterações')).toBeInTheDocument()
      expect(screen.getByRole('progressbar')).toBeInTheDocument()
      expect(screen.getByText(/processando 3 usuários/i)).toBeInTheDocument()

      await waitFor(() => {
        expect(screen.getByText('Operação Concluída')).toBeInTheDocument()
      }, { timeout: 1000 })
    })

    it('should show individual user progress with status indicators', async () => {
      const user = userEvent.setup()

      // Mock partial success response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          results: [
            { user_id: 'user-1', status: 'success' },
            { user_id: 'user-2', status: 'error', error: 'Permission conflict' },
            { user_id: 'user-3', status: 'success' }
          ]
        })
      } as Response)

      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      // Setup and apply changes
      const grantPermissionsRadio = screen.getByRole('radio', { name: /conceder permissões/i })
      await user.click(grantPermissionsRadio)

      const createCheckboxes = screen.getAllByLabelText(/criar/i)
      await user.click(createCheckboxes[0])

      const reasonTextarea = screen.getByPlaceholderText(/descreva o motivo desta operação/i)
      await user.type(reasonTextarea, 'Test operation with errors')

      const applyButton = screen.getByRole('button', { name: /aplicar alterações/i })
      await user.click(applyButton)

      await waitFor(() => {
        expect(screen.getByText('Operação Concluída')).toBeInTheDocument()
        
        // Should show individual results
        expect(screen.getByText('User One')).toBeInTheDocument()
        expect(screen.getByText('✓')).toBeInTheDocument() // Success indicator
        expect(screen.getByText('User Two')).toBeInTheDocument()
        expect(screen.getByText('✗')).toBeInTheDocument() // Error indicator
        expect(screen.getByText('Permission conflict')).toBeInTheDocument()
      })
    })

    it('should allow canceling bulk operations', async () => {
      const user = userEvent.setup()

      // Mock cancellable operation
      const cancelablePromise = new Promise((resolve, reject) => {
        setTimeout(() => reject(new Error('Operation cancelled')), 1000)
      })
      mockFetch.mockReturnValueOnce(cancelablePromise as any)

      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      // Start operation
      const grantPermissionsRadio = screen.getByRole('radio', { name: /conceder permissões/i })
      await user.click(grantPermissionsRadio)

      const createCheckboxes = screen.getAllByLabelText(/criar/i)
      await user.click(createCheckboxes[0])

      const reasonTextarea = screen.getByPlaceholderText(/descreva o motivo desta operação/i)
      await user.type(reasonTextarea, 'Cancellable operation')

      const applyButton = screen.getByRole('button', { name: /aplicar alterações/i })
      await user.click(applyButton)

      // Should show cancel button
      expect(screen.getByRole('button', { name: /cancelar operação/i })).toBeInTheDocument()

      // Cancel the operation
      const cancelButton = screen.getByRole('button', { name: /cancelar operação/i })
      await user.click(cancelButton)

      await waitFor(() => {
        expect(screen.getByText('Operação Cancelada')).toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('should handle bulk operation API errors', async () => {
      const user = userEvent.setup()

      // Mock API error
      mockFetch.mockRejectedValueOnce(new Error('Bulk operation failed'))

      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      // Setup and apply changes
      const grantPermissionsRadio = screen.getByRole('radio', { name: /conceder permissões/i })
      await user.click(grantPermissionsRadio)

      const createCheckboxes = screen.getAllByLabelText(/criar/i)
      await user.click(createCheckboxes[0])

      const reasonTextarea = screen.getByPlaceholderText(/descreva o motivo desta operação/i)
      await user.type(reasonTextarea, 'Test operation')

      const applyButton = screen.getByRole('button', { name: /aplicar alterações/i })
      await user.click(applyButton)

      await waitFor(() => {
        expect(screen.getByText('Erro na Operação')).toBeInTheDocument()
        expect(screen.getByText(/falha ao aplicar alterações em lote/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /tentar novamente/i })).toBeInTheDocument()
      })
    })

    it('should handle template loading errors', async () => {
      // Mock template API error
      mockFetch.mockRejectedValueOnce(new Error('Failed to load templates'))

      const user = userEvent.setup()

      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      const applyTemplateRadio = screen.getByRole('radio', { name: /aplicar template/i })
      await user.click(applyTemplateRadio)

      await waitFor(() => {
        expect(screen.getByText(/erro ao carregar templates/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /tentar novamente/i })).toBeInTheDocument()
      })
    })

    it('should allow retrying failed operations', async () => {
      const user = userEvent.setup()

      // Mock initial failure then success
      mockFetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            results: [
              { user_id: 'user-1', status: 'success' },
              { user_id: 'user-2', status: 'success' },
              { user_id: 'user-3', status: 'success' }
            ]
          })
        } as Response)

      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      // Setup and apply changes
      const grantPermissionsRadio = screen.getByRole('radio', { name: /conceder permissões/i })
      await user.click(grantPermissionsRadio)

      const createCheckboxes = screen.getAllByLabelText(/criar/i)
      await user.click(createCheckboxes[0])

      const reasonTextarea = screen.getByPlaceholderText(/descreva o motivo desta operação/i)
      await user.type(reasonTextarea, 'Test retry operation')

      const applyButton = screen.getByRole('button', { name: /aplicar alterações/i })
      await user.click(applyButton)

      await waitFor(() => {
        expect(screen.getByText('Erro na Operação')).toBeInTheDocument()
      })

      // Retry the operation
      const retryButton = screen.getByRole('button', { name: /tentar novamente/i })
      await user.click(retryButton)

      await waitFor(() => {
        expect(screen.getByText('Operação Concluída')).toBeInTheDocument()
        expect(screen.getByText(/3 usuários atualizados com sucesso/i)).toBeInTheDocument()
      })
    })
  })

  describe('Dialog Actions', () => {
    it('should close dialog when cancel button is clicked', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      const cancelButton = screen.getByRole('button', { name: /cancelar/i })
      await user.click(cancelButton)

      expect(mockOnClose).toHaveBeenCalled()
    })

    it('should call onComplete when operation finishes successfully', async () => {
      const user = userEvent.setup()

      // Mock successful operation
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          results: [
            { user_id: 'user-1', status: 'success' },
            { user_id: 'user-2', status: 'success' },
            { user_id: 'user-3', status: 'success' }
          ]
        })
      } as Response)

      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      // Complete operation
      const grantPermissionsRadio = screen.getByRole('radio', { name: /conceder permissões/i })
      await user.click(grantPermissionsRadio)

      const createCheckboxes = screen.getAllByLabelText(/criar/i)
      await user.click(createCheckboxes[0])

      const reasonTextarea = screen.getByPlaceholderText(/descreva o motivo desta operação/i)
      await user.type(reasonTextarea, 'Test completion')

      const applyButton = screen.getByRole('button', { name: /aplicar alterações/i })
      await user.click(applyButton)

      await waitFor(() => {
        expect(screen.getByText('Operação Concluída')).toBeInTheDocument()
      })

      // Click done button
      const doneButton = screen.getByRole('button', { name: /concluir/i })
      await user.click(doneButton)

      expect(mockOnComplete).toHaveBeenCalledWith(['user-1', 'user-2', 'user-3'])
    })
  })

  describe('Accessibility', () => {
    it('should have proper dialog structure and ARIA labels', () => {
      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByRole('heading', { name: /operações em lote/i })).toBeInTheDocument()
      expect(screen.getByLabelText(/motivo da alteração/i)).toBeInTheDocument()
    })

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={mockSelectedUsers}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      // Should be able to tab through radio buttons
      await user.tab()
      expect(screen.getByRole('radio', { name: /aplicar template/i })).toHaveFocus()

      await user.tab()
      expect(screen.getByRole('radio', { name: /conceder permissões/i })).toHaveFocus()

      // Should be able to select with Enter/Space
      await user.keyboard('{Enter}')
      expect(screen.getByRole('radio', { name: /conceder permissões/i })).toBeChecked()
    })

    it('should announce progress updates to screen readers', async () => {
      const user = userEvent.setup()

      // Mock slow operation
      const slowPromise = new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({
            results: [{ user_id: 'user-1', status: 'success' }]
          })
        }), 100)
      )
      mockFetch.mockReturnValueOnce(slowPromise as any)

      render(
        <TestWrapper>
          <BulkPermissionDialog
            selectedUsers={[mockSelectedUsers[0]]}
            open={true}
            onClose={mockOnClose}
            onComplete={mockOnComplete}
          />
        </TestWrapper>
      )

      // Setup and start operation
      const grantPermissionsRadio = screen.getByRole('radio', { name: /conceder permissões/i })
      await user.click(grantPermissionsRadio)

      const createCheckboxes = screen.getAllByLabelText(/criar/i)
      await user.click(createCheckboxes[0])

      const reasonTextarea = screen.getByPlaceholderText(/descreva o motivo desta operação/i)
      await user.type(reasonTextarea, 'Test accessibility')

      const applyButton = screen.getByRole('button', { name: /aplicar alterações/i })
      await user.click(applyButton)

      // Should have progress announcement
      expect(screen.getByRole('status')).toHaveTextContent(/processando/i)

      await waitFor(() => {
        expect(screen.getByRole('status')).toHaveTextContent(/operação concluída/i)
      }, { timeout: 1000 })
    })
  })
})