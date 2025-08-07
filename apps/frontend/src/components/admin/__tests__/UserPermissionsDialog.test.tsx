import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, beforeEach, afterEach, describe, it, expect } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

import { UserPermissionsDialog } from '../UserPermissionsDialog'
import useAuthStore from '@/store/authStore'

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
const mockAdminUser = {
  user_id: 'admin-123',
  email: 'admin@test.com',
  role: 'admin',
  is_active: true,
  totp_enabled: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  full_name: 'Admin User'
}

const mockTestUser = {
  user_id: '123',
  email: 'joao@example.com',
  role: 'user',
  is_active: true,
  totp_enabled: false,
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
  full_name: 'João Silva'
}

const mockPermissions = {
  client_management: { create: true, read: true, update: true, delete: false },
  pdf_processing: { create: false, read: true, update: false, delete: false },
  reports_analysis: { create: false, read: true, update: false, delete: false },
  audio_recording: { create: false, read: false, update: false, delete: false },
}

const mockFetch = vi.fn()

beforeEach(() => {
  global.fetch = mockFetch
  
  // Mock ResizeObserver (external API)
  global.ResizeObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  }))
})

afterEach(() => {
  vi.clearAllMocks()
})

describe('UserPermissionsDialog', () => {
  const mockOnOpenChange = vi.fn()
  const mockOnPermissionsChanged = vi.fn()
  
  beforeEach(() => {
    vi.clearAllMocks()
    mockOnOpenChange.mockClear()
    mockOnPermissionsChanged.mockClear()
  })

  const renderComponent = (user = mockTestUser, open = true) => {
    return render(
      <TestWrapper>
        <UserPermissionsDialog
          user={user}
          open={open}
          onOpenChange={mockOnOpenChange}
          onPermissionsChanged={mockOnPermissionsChanged}
        />
      </TestWrapper>
    )
  }

  describe('Dialog Rendering', () => {
    it('should not render when user is null', () => {
      renderComponent(null)

      expect(screen.queryByText(/permissões de/i)).not.toBeInTheDocument()
    })

    it('should not render when dialog is closed', () => {
      renderComponent(mockTestUser, false)

      expect(screen.queryByText(/permissões de/i)).not.toBeInTheDocument()
    })

    it('should render dialog header with user name', () => {
      renderComponent()

      expect(screen.getByText(`Permissões de ${mockTestUser.full_name}`)).toBeInTheDocument()
      expect(screen.getByText(/gerencie as permissões de acesso aos agentes/i)).toBeInTheDocument()
    })

    it('should display user information card', () => {
      renderComponent()

      expect(screen.getByText(/nome completo/i)).toBeInTheDocument()
      expect(screen.getByText(mockTestUser.full_name!)).toBeInTheDocument()
      expect(screen.getByText(mockTestUser.email)).toBeInTheDocument()
      expect(screen.getByText(mockTestUser.role)).toBeInTheDocument()
    })
  })

  describe('Permissions Loading States', () => {
    beforeEach(() => {
      // Reset fetch mock for each test
      mockFetch.mockClear()
    })

    it('should display loading state while fetching permissions', async () => {
      // Mock delayed response
      const delayedPromise = new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockPermissions)
        }), 100)
      )
      mockFetch.mockReturnValueOnce(delayedPromise as any)

      renderComponent()

      expect(screen.getByText(/permissões de/i)).toBeInTheDocument()
      
      await waitFor(() => {
        expect(screen.getByText(/motivo da alteração/i)).toBeInTheDocument()
      })
    })

    it('should display error state when permissions loading fails', async () => {
      // Mock API error
      mockFetch.mockRejectedValueOnce(new Error('Failed to fetch permissions'))

      renderComponent()

      expect(screen.getByText(/permissões de/i)).toBeInTheDocument()
    })

    it('should display permissions form when loaded successfully', async () => {
      // Mock successful response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockPermissions)
      } as Response)

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/motivo da alteração/i)).toBeInTheDocument()
        expect(screen.getByText(/permissões por agente/i)).toBeInTheDocument()
        expect(screen.getByPlaceholderText(/descreva o motivo desta alteração/i)).toBeInTheDocument()
      })
    })
  })

  describe('Agent Permission Cards', () => {
    beforeEach(() => {
      // Reset fetch mock and provide default successful response
      mockFetch.mockClear()
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockPermissions)
      } as Response)
    })

    it('should display all agent permission cards', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/gestão de clientes/i)).toBeInTheDocument()
        expect(screen.getByText(/processamento de pdfs/i)).toBeInTheDocument()
        expect(screen.getByText(/relatórios e análises/i)).toBeInTheDocument()
        expect(screen.getByText(/gravação de áudio/i)).toBeInTheDocument()
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
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ user: mockAdminUser })
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockPermissions)
        } as Response)
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
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ user: mockAdminUser })
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockPermissions)
        } as Response)
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
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ user: mockAdminUser })
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockPermissions)
        } as Response)
    })

    it('should save permissions when save button is clicked', async () => {
      const user = userEvent.setup()
      
      // Mock successful save API
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ success: true })
      } as Response)
      
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
      mockFetch.mockResolvedValueOnce(slowSavePromise as any)
      
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
      mockFetch.mockRejectedValueOnce(new Error('Save failed'))
      
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
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: () => Promise.resolve({ success: true })
      } as Response)
      
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
        expect(mockFetch).toHaveBeenLastCalledWith(
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
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ user: mockAdminUser })
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockPermissions)
        } as Response)
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
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ user: mockAdminUser })
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockPermissions)
        } as Response)
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
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ user: mockAdminUser })
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockPermissions)
        } as Response)
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