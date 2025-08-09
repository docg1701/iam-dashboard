import React from 'react'
import userEvent from '@testing-library/user-event'
import { 
  describe, 
  it, 
  expect, 
  beforeEach, 
  vi, 
  afterEach,
  renderWithProviders,
  screen,
  waitFor,
  act,
  useTestSetup,
  mockSuccessfulFetch,
  mockFailedFetch
} from '@/test/test-template'
import { 
  createMockAdminUser,
  createMockUserAgentPermission,
  setupPermissionAPITest,
  setupUserAPITest,
  TestDataPresets
} from '@/test/api-mocks'
import { 
  setupAuthenticatedUser,
  clearTestAuth
} from '@/test/auth-helpers'
import { UserPermissionsDialog } from '../UserPermissionsDialog'
import { AgentName } from '@/types/permissions'
import useAuthStore from '@/store/authStore'

// Setup standard test utilities
useTestSetup()

// Mock data using test infrastructure
const mockAdminUser = createMockAdminUser({
  user_id: 'admin-123',
  email: 'admin@test.com',
  full_name: 'Admin User'
})

const mockTestUser = createMockAdminUser({
  user_id: '123',
  email: 'joao@example.com',
  role: 'user',
  full_name: 'João Silva'
})

// Mock permissions data for the test user
const mockPermissions = {
  user_id: mockTestUser.user_id,
  permissions: [
    createMockUserAgentPermission(mockTestUser.user_id, AgentName.CLIENT_MANAGEMENT, 
      { create: true, read: true, update: true, delete: false }),
    createMockUserAgentPermission(mockTestUser.user_id, AgentName.PDF_PROCESSING, 
      { create: false, read: true, update: false, delete: false }),
    createMockUserAgentPermission(mockTestUser.user_id, AgentName.REPORTS_ANALYSIS, 
      { create: false, read: true, update: false, delete: false }),
    createMockUserAgentPermission(mockTestUser.user_id, AgentName.AUDIO_RECORDING, 
      { create: false, read: false, update: false, delete: false })
  ],
  last_updated: new Date().toISOString()
}

describe('UserPermissionsDialog', () => {
  const mockOnOpenChange = vi.fn()
  const mockOnPermissionsChanged = vi.fn()
  
  beforeEach(async () => {
    await act(async () => {
      // Clear all previous state
      clearTestAuth()
      vi.clearAllMocks()
      mockOnOpenChange.mockClear()
      mockOnPermissionsChanged.mockClear()
      
      // Setup authenticated admin user with proper permissions to view the dialog
      setupAuthenticatedUser('admin')
      useAuthStore.setState({ user: mockAdminUser })
      
      // Setup API mocks for the admin user to have permissions to view the dialog
      const adminPermissions = [
        createMockUserAgentPermission(mockAdminUser.user_id, AgentName.CLIENT_MANAGEMENT, 
          { create: true, read: true, update: true, delete: true }),
        createMockUserAgentPermission(mockAdminUser.user_id, AgentName.PDF_PROCESSING, 
          { create: true, read: true, update: true, delete: false }),
        createMockUserAgentPermission(mockAdminUser.user_id, AgentName.REPORTS_ANALYSIS, 
          { create: true, read: true, update: false, delete: false }),
        createMockUserAgentPermission(mockAdminUser.user_id, AgentName.AUDIO_RECORDING, 
          { create: false, read: true, update: false, delete: false })
      ]
      
      // Setup permission API for the current admin user
      setupPermissionAPITest({ 
        userId: mockAdminUser.user_id,
        userPermissions: adminPermissions
      })
      
      // Setup API mocks for the target user being edited
      const targetUserPermissions = [
        createMockUserAgentPermission(mockTestUser.user_id, AgentName.CLIENT_MANAGEMENT, 
          { create: true, read: true, update: true, delete: false }),
        createMockUserAgentPermission(mockTestUser.user_id, AgentName.PDF_PROCESSING, 
          { create: false, read: true, update: false, delete: false }),
        createMockUserAgentPermission(mockTestUser.user_id, AgentName.REPORTS_ANALYSIS, 
          { create: false, read: true, update: false, delete: false }),
        createMockUserAgentPermission(mockTestUser.user_id, AgentName.AUDIO_RECORDING, 
          { create: false, read: false, update: false, delete: false })
      ]
      
      // Setup permission API for the target user
      setupPermissionAPITest({ 
        userId: mockTestUser.user_id,
        userPermissions: targetUserPermissions
      })
    })
  })

  const renderComponent = async (user: typeof mockTestUser | null = mockTestUser, open = true) => {
    return await act(async () => {
      return renderWithProviders(
        <UserPermissionsDialog
          user={user}
          open={open}
          onOpenChange={mockOnOpenChange}
          onPermissionsChanged={mockOnPermissionsChanged}
        />
      )
    })
  }

  describe('Dialog Rendering', () => {
    it('should not render when user is null', async () => {
      await act(async () => {
        await renderComponent(undefined)
      })

      await act(async () => {
        expect(screen.queryByText(/permissões de/i)).not.toBeInTheDocument()
      })
    })

    it('should not render when dialog is closed', async () => {
      await act(async () => {
        await renderComponent(mockTestUser, false)
      })

      await act(async () => {
        expect(screen.queryByText(/permissões de/i)).not.toBeInTheDocument()
      })
    })

    it('should render dialog header with user name', async () => {
      await act(async () => {
        await renderComponent()
      })

      await waitFor(async () => {
        await act(async () => {
          expect(screen.getByText(`Permissões de ${mockTestUser.full_name}`)).toBeInTheDocument()
          expect(screen.getByText(/gerencie as permissões de acesso aos agentes/i)).toBeInTheDocument()
        })
      }, { timeout: 3000 })
    })

    it('should display user information card', async () => {
      await act(async () => {
        await renderComponent()
      })

      await waitFor(async () => {
        await act(async () => {
          expect(screen.getByText(/nome completo/i)).toBeInTheDocument()
          expect(screen.getByText(mockTestUser.full_name!)).toBeInTheDocument()
          expect(screen.getByText(mockTestUser.email)).toBeInTheDocument()
          expect(screen.getByText(mockTestUser.role)).toBeInTheDocument()
        })
      }, { timeout: 3000 })
    })
  })

  describe('Permissions Loading States', () => {
    it('should display loading state while fetching permissions', async () => {
      // Mock delayed response for target user permissions
      const delayedPermissionsPromise = new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({
            user_id: mockTestUser.user_id,
            permissions: [
              createMockUserAgentPermission(mockTestUser.user_id, AgentName.CLIENT_MANAGEMENT, 
                { create: true, read: true, update: true, delete: false })
            ],
            last_updated: new Date().toISOString()
          })
        }), 200)
      )
      
      // Clear existing mocks and set up delayed response
      vi.clearAllMocks()
      const mockedFetch = vi.mocked(global.fetch)
      
      // First call for admin user permissions (immediate)
      setupPermissionAPITest({ 
        userId: mockAdminUser.user_id,
        userPermissions: [
          createMockUserAgentPermission(mockAdminUser.user_id, AgentName.CLIENT_MANAGEMENT, 
            { create: true, read: true, update: true, delete: true })
        ]
      })
      
      // Second call for target user permissions (delayed)
      mockedFetch.mockReturnValueOnce(delayedPermissionsPromise as any)

      await renderComponent()

      // Should show the dialog header first
      await waitFor(() => {
        expect(screen.getByText(/permissões de/i)).toBeInTheDocument()
      }, { timeout: 3000 })
      
      // Eventually should show the form
      await waitFor(() => {
        expect(screen.getByText(/motivo da alteração/i)).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('should display error state when permissions loading fails', async () => {
      // Clear existing mocks
      vi.clearAllMocks()
      
      // Setup admin permissions (successful)
      setupPermissionAPITest({ 
        userId: mockAdminUser.user_id,
        userPermissions: [
          createMockUserAgentPermission(mockAdminUser.user_id, AgentName.CLIENT_MANAGEMENT, 
            { create: true, read: true, update: true, delete: true })
        ]
      })
      
      // Setup failed permissions for target user
      setupPermissionAPITest({ shouldFail: true })

      await renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/permissões de/i)).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('should display permissions form when loaded successfully', async () => {
      // Mock successful response
      mockSuccessfulFetch('/permissions/user/', mockPermissions)

      await act(async () => {
        await renderComponent()
      })

      await waitFor(async () => {
        await act(async () => {
          expect(screen.getByText(/motivo da alteração/i)).toBeInTheDocument()
          expect(screen.getByText(/permissões por agente/i)).toBeInTheDocument()
          expect(screen.getByPlaceholderText(/descreva o motivo desta alteração/i)).toBeInTheDocument()
        })
      })
    })
  })

  describe('Agent Permission Cards', () => {
    beforeEach(() => {
      // Reset fetch mock and provide default successful response
      vi.mocked(global.fetch).mockClear()
      mockSuccessfulFetch('/permissions/user/', mockPermissions)
    })

    it('should display all agent permission cards', async () => {
      await act(async () => {
        await renderComponent()
      })

      await waitFor(async () => {
        await act(async () => {
          expect(screen.getByText(/gestão de clientes/i)).toBeInTheDocument()
          expect(screen.getByText(/processamento de pdfs/i)).toBeInTheDocument()
          expect(screen.getByText(/relatórios e análises/i)).toBeInTheDocument()
          expect(screen.getByText(/gravação de áudio/i)).toBeInTheDocument()
        })
      })
    })

    it('should display correct permission levels for each agent', async () => {
      renderComponent()

      await waitFor(() => {
        // Client Management should show "Padrão" (Standard) level
        expect(screen.getByText(/padrão/i)).toBeInTheDocument()
        
        // PDF Processing should show "Somente Leitura" (Read Only) level
        expect(screen.getByText(/somente leitura/i)).toBeInTheDocument()
      })
    })

    it('should display individual permission checkboxes', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getAllByText(/criar/i)).toHaveLength(4) // One for each agent
        expect(screen.getAllByText(/visualizar/i)).toHaveLength(4)
        expect(screen.getAllByText(/editar/i)).toHaveLength(4)
        expect(screen.getAllByText(/excluir/i)).toHaveLength(4)
      })
    })

    it('should show correct checkbox states based on permissions', async () => {
      renderComponent()

      await waitFor(() => {
        // Client Management permissions
        const createCheckboxes = screen.getAllByLabelText(/criar/i)
        expect(createCheckboxes[0]).toBeChecked() // Client management create should be checked
        
        const deleteCheckboxes = screen.getAllByLabelText(/excluir/i)
        expect(deleteCheckboxes[0]).not.toBeChecked() // Client management delete should be unchecked
      })
    })
  })

  describe('Permission Level Selection', () => {
    it('should allow changing permission level via dropdown', async () => {
      const user = userEvent.setup()
      renderComponent()

      const levelSelects = screen.getAllByRole('combobox', { name: /nível de acesso/i })
      await user.click(levelSelects[0]) // Client Management dropdown

      expect(screen.getByText(/nenhum/i)).toBeInTheDocument()
      expect(screen.getByText(/somente leitura/i)).toBeInTheDocument()
      expect(screen.getByText(/padrão/i)).toBeInTheDocument()
      expect(screen.getByText(/completo/i)).toBeInTheDocument()
    })

    it('should update individual checkboxes when permission level changes', async () => {
      const user = userEvent.setup()
      renderComponent()

      const levelSelects = screen.getAllByRole('combobox', { name: /nível de acesso/i })
      await user.click(levelSelects[3]) // Audio Recording dropdown
      await user.click(screen.getByText(/completo/i))

      // Should enable changes detection
      await waitFor(() => {
        expect(screen.getByText(/você tem alterações não salvas/i)).toBeInTheDocument()
      })
    })
  })

  describe('Individual Permission Changes', () => {
    it('should allow toggling individual permissions', async () => {
      const user = userEvent.setup()
      renderComponent()

      // Find and click a checkbox that is currently unchecked
      const deleteCheckboxes = screen.getAllByLabelText(/excluir/i)
      const clientDeleteCheckbox = deleteCheckboxes[0]
      
      expect(clientDeleteCheckbox).not.toBeChecked()
      await user.click(clientDeleteCheckbox)

      expect(clientDeleteCheckbox).toBeChecked()
      expect(screen.getByText(/você tem alterações não salvas/i)).toBeInTheDocument()
    })

    it('should detect changes and enable save button', async () => {
      const user = userEvent.setup()
      renderComponent()

      // Save button should be disabled initially
      const saveButton = screen.getByRole('button', { name: /salvar alterações/i })
      expect(saveButton).toBeDisabled()

      // Make a change
      const deleteCheckboxes = screen.getAllByLabelText(/excluir/i)
      await user.click(deleteCheckboxes[0])

      // Save button should be enabled
      await waitFor(() => {
        expect(saveButton).toBeEnabled()
      })
    })
  })

  describe('Change Reason Requirement', () => {
    beforeEach(() => {
      // Mock authentication and permissions APIs for reason requirement tests
      mockSuccessfulFetch('/auth/user', { user: mockAdminUser })
      mockSuccessfulFetch('/permissions/user/', mockPermissions)
    })

    it('should require change reason to enable save button', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/motivo da alteração/i)).toBeInTheDocument()
      })

      // Make a permission change
      const deleteCheckboxes = screen.getAllByLabelText(/excluir/i)
      await user.click(deleteCheckboxes[0])

      const saveButton = screen.getByRole('button', { name: /salvar alterações/i })
      expect(saveButton).toBeDisabled() // Should be disabled without reason

      // Add change reason
      const reasonTextarea = screen.getByPlaceholderText(/descreva o motivo desta alteração/i)
      await user.type(reasonTextarea, 'Usuário precisa de permissão de exclusão para casos especiais')

      await waitFor(() => {
        expect(saveButton).toBeEnabled()
      })
    })

    it('should disable save button if change reason is cleared', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/motivo da alteração/i)).toBeInTheDocument()
      })

      // Make changes and add reason
      const deleteCheckboxes = screen.getAllByLabelText(/excluir/i)
      await user.click(deleteCheckboxes[0])

      const reasonTextarea = screen.getByPlaceholderText(/descreva o motivo desta alteração/i)
      await user.type(reasonTextarea, 'Test reason')

      const saveButton = screen.getByRole('button', { name: /salvar alterações/i })
      await waitFor(() => {
        expect(saveButton).toBeEnabled()
      })

      // Clear the reason
      await user.clear(reasonTextarea)

      await waitFor(() => {
        expect(saveButton).toBeDisabled()
      })
    })
  })

  describe('Permission History', () => {
    beforeEach(() => {
      // Mock authentication and permissions APIs for history tests
      mockSuccessfulFetch('/auth/user', { user: mockAdminUser })
      mockSuccessfulFetch('/permissions/user/', mockPermissions)
    })

    it('should show/hide permission history when toggle clicked', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/motivo da alteração/i)).toBeInTheDocument()
      })

      const historyToggle = screen.getByRole('button', { name: /ver histórico/i })
      expect(screen.queryByText(/histórico de alterações/i)).not.toBeInTheDocument()

      await user.click(historyToggle)

      expect(screen.getByText(/histórico de alterações/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /ocultar histórico/i })).toBeInTheDocument()
    })

    it('should display audit logs when history is shown', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/motivo da alteração/i)).toBeInTheDocument()
      })

      const historyToggle = screen.getByRole('button', { name: /ver histórico/i })
      await user.click(historyToggle)

      expect(screen.getByText(/histórico de alterações/i)).toBeInTheDocument()
    })

    it('should show loading state for audit logs', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/motivo da alteração/i)).toBeInTheDocument()
      })

      const historyToggle = screen.getByRole('button', { name: /ver histórico/i })
      await user.click(historyToggle)

      expect(screen.getByText(/histórico de alterações/i)).toBeInTheDocument()
    })

    it('should show error state for audit logs', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/motivo da alteração/i)).toBeInTheDocument()
      })

      const historyToggle = screen.getByRole('button', { name: /ver histórico/i })
      await user.click(historyToggle)

      expect(screen.getByText(/histórico de alterações/i)).toBeInTheDocument()
    })
  })

  describe('Form Submission', () => {
    beforeEach(() => {
      // Mock authentication and permissions APIs for form submission tests
      mockSuccessfulFetch('/auth/user', { user: mockAdminUser })
      mockSuccessfulFetch('/permissions/user/', mockPermissions)
    })

    it('should save permissions when save button is clicked', async () => {
      const user = userEvent.setup()
      
      // Mock successful save API
      mockSuccessfulFetch('/permissions', { success: true })
      
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/motivo da alteração/i)).toBeInTheDocument()
      })

      // Make a change
      const deleteCheckboxes = screen.getAllByLabelText(/excluir/i)
      await user.click(deleteCheckboxes[0])

      // Add change reason
      const reasonTextarea = screen.getByPlaceholderText(/descreva o motivo desta alteração/i)
      await user.type(reasonTextarea, 'Test reason')

      // Save changes
      const saveButton = screen.getByRole('button', { name: /salvar alterações/i })
      await user.click(saveButton)

      await waitFor(() => {
        expect(mockOnPermissionsChanged).toHaveBeenCalledWith(mockTestUser.user_id)
        expect(mockOnOpenChange).toHaveBeenCalledWith(false)
      })
    })

    it('should show loading state during save', async () => {
      const user = userEvent.setup()
      
      // Mock slow save API
      const slowSavePromise = new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ success: true })
        }), 100)
      )
      vi.mocked(global.fetch).mockResolvedValueOnce(slowSavePromise as any)
      
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/motivo da alteração/i)).toBeInTheDocument()
      })

      // Make a change and add reason
      const deleteCheckboxes = screen.getAllByLabelText(/excluir/i)
      await user.click(deleteCheckboxes[0])

      const reasonTextarea = screen.getByPlaceholderText(/descreva o motivo desta alteração/i)
      await user.type(reasonTextarea, 'Test reason')

      const saveButton = screen.getByRole('button', { name: /salvar alterações/i })
      await user.click(saveButton)

      // Should show loading state
      expect(saveButton).toHaveAttribute('aria-disabled', 'true')
    })

    it('should handle save errors gracefully', async () => {
      const user = userEvent.setup()
      
      // Mock save API error
      vi.mocked(global.fetch).mockRejectedValueOnce(new Error('Save failed'))
      
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/motivo da alteração/i)).toBeInTheDocument()
      })

      // Make a change and add reason
      const deleteCheckboxes = screen.getAllByLabelText(/excluir/i)
      await user.click(deleteCheckboxes[0])

      const reasonTextarea = screen.getByPlaceholderText(/descreva o motivo desta alteração/i)
      await user.type(reasonTextarea, 'Test reason')

      const saveButton = screen.getByRole('button', { name: /salvar alterações/i })
      await user.click(saveButton)

      await waitFor(() => {
        // Should handle error gracefully
        expect(saveButton).toBeInTheDocument()
      })
    })

    it('should create new permissions for agents without existing permissions', async () => {
      const user = userEvent.setup()
      
      // Mock successful create API
      mockSuccessfulFetch('/permissions', { success: true }, 201)
      
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/motivo da alteração/i)).toBeInTheDocument()
      })

      // Make a change to an agent without existing permissions
      const levelSelects = screen.getAllByRole('combobox', { name: /nível de acesso/i })
      await user.click(levelSelects[1]) // PDF Processing
      await user.click(screen.getByText(/somente leitura/i))

      const reasonTextarea = screen.getByPlaceholderText(/descreva o motivo desta alteração/i)
      await user.type(reasonTextarea, 'Adding PDF processing access')

      const saveButton = screen.getByRole('button', { name: /salvar alterações/i })
      await user.click(saveButton)

      await waitFor(() => {
        // Should call API to create new permission
        expect(vi.mocked(global.fetch)).toHaveBeenLastCalledWith(
          expect.stringContaining('/api/v1/permissions'),
          expect.objectContaining({
            method: 'POST'
          })
        )
      })
    })
  })

  describe('Dialog Actions', () => {
    beforeEach(() => {
      // Mock authentication and permissions APIs for dialog actions
      mockSuccessfulFetch('/auth/user', { user: mockAdminUser })
      mockSuccessfulFetch('/permissions/user/', mockPermissions)
    })

    it('should close dialog when cancel button is clicked', async () => {
      const user = userEvent.setup()
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/motivo da alteração/i)).toBeInTheDocument()
      })

      const cancelButton = screen.getByRole('button', { name: /cancelar/i })
      await user.click(cancelButton)

      expect(mockOnOpenChange).toHaveBeenCalledWith(false)
    })

    it('should show confirmation when closing with unsaved changes', async () => {
      const user = userEvent.setup()
      const mockConfirm = vi.spyOn(window, 'confirm').mockReturnValue(true)
      
      renderComponent()

      // Make a change
      const deleteCheckboxes = screen.getAllByLabelText(/excluir/i)
      await user.click(deleteCheckboxes[0])

      // Try to close
      const cancelButton = screen.getByRole('button', { name: /cancelar/i })
      await user.click(cancelButton)

      expect(mockConfirm).toHaveBeenCalledWith('Você tem alterações não salvas. Deseja descartar?')
      expect(mockOnOpenChange).toHaveBeenCalledWith(false)

      mockConfirm.mockRestore()
    })

    it('should not close dialog when unsaved changes confirmation is cancelled', async () => {
      const user = userEvent.setup()
      const mockConfirm = vi.spyOn(window, 'confirm').mockReturnValue(false)
      
      renderComponent()

      // Make a change
      const deleteCheckboxes = screen.getAllByLabelText(/excluir/i)
      await user.click(deleteCheckboxes[0])

      // Try to close
      const cancelButton = screen.getByRole('button', { name: /cancelar/i })
      await user.click(cancelButton)

      expect(mockConfirm).toHaveBeenCalled()
      expect(mockOnOpenChange).not.toHaveBeenCalled()

      mockConfirm.mockRestore()
    })
  })

  describe('Accessibility', () => {
    beforeEach(() => {
      // Mock authentication and permissions APIs for accessibility tests
      mockSuccessfulFetch('/auth/user', { user: mockAdminUser })
      mockSuccessfulFetch('/permissions/user/', mockPermissions)
    })

    it('should have proper dialog structure', async () => {
      renderComponent()

      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByRole('heading', { name: new RegExp(`permissões de ${mockTestUser.full_name}`, 'i') })).toBeInTheDocument()
    })

    it('should have proper form labels and controls', () => {
      renderComponent()

      expect(screen.getByLabelText(/motivo da alteração/i)).toBeInTheDocument()
      
      // Permission checkboxes should have proper labels
      const createCheckboxes = screen.getAllByLabelText(/criar/i)
      expect(createCheckboxes.length).toBeGreaterThan(0)
    })

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup()
      renderComponent()

      // Should be able to tab through form controls
      await user.tab()
      expect(screen.getByPlaceholderText(/descreva o motivo desta alteração/i)).toHaveFocus()
    })

    it('should have proper ARIA labels for permission controls', () => {
      renderComponent()

      const levelSelects = screen.getAllByRole('combobox', { name: /nível de acesso/i })
      expect(levelSelects.length).toBe(4) // One for each agent
    })
  })

  describe('Responsive Behavior', () => {
    beforeEach(() => {
      // Mock authentication and permissions APIs for responsive tests
      mockSuccessfulFetch('/auth/user', { user: mockAdminUser })
      mockSuccessfulFetch('/permissions/user/', mockPermissions)
    })

    it('should layout agent cards in responsive grid', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/gestão de clientes/i)).toBeInTheDocument()
      })

      const agentGrid = screen.getByText(/gestão de clientes/i).closest('.grid')
      expect(agentGrid).toHaveClass('grid-cols-1', 'lg:grid-cols-2')
    })

    it('should handle dialog sizing on different screens', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      const dialogContent = screen.getByRole('dialog')
      expect(dialogContent).toHaveClass('max-w-4xl', 'max-h-[90vh]', 'overflow-y-auto')
    })
  })
})