/**
 * PermissionTemplates Component Tests
 * 
 * Comprehensive tests for the PermissionTemplates component with CRUD operations
 * Following CLAUDE.md rules: no internal mocking, only external API mocking
 */

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import React from 'react'

import { PermissionTemplates } from '../PermissionTemplates'
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

const mockSystemTemplates = [
  {
    template_id: 'template-system-1',
    template_name: 'Client Specialist',
    description: 'Full access to client management with limited PDF processing',
    permissions: {
      client_management: { create: true, read: true, update: true, delete: false },
      pdf_processing: { create: false, read: true, update: false, delete: false },
      reports_analysis: { create: false, read: true, update: false, delete: false },
      audio_recording: { create: false, read: false, update: false, delete: false }
    },
    is_system_template: true,
    created_by_user_id: 'system',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    usage_count: 12,
    last_used: '2024-01-07T00:00:00Z'
  },
  {
    template_id: 'template-system-2',
    template_name: 'Read Only Access',
    description: 'Read-only access to all agents for monitoring purposes',
    permissions: {
      client_management: { create: false, read: true, update: false, delete: false },
      pdf_processing: { create: false, read: true, update: false, delete: false },
      reports_analysis: { create: false, read: true, update: false, delete: false },
      audio_recording: { create: false, read: true, update: false, delete: false }
    },
    is_system_template: true,
    created_by_user_id: 'system',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    usage_count: 25,
    last_used: '2024-01-06T00:00:00Z'
  }
]

const mockCustomTemplates = [
  {
    template_id: 'template-custom-1',
    template_name: 'Marketing Team',
    description: 'Custom template for marketing team with reports focus',
    permissions: {
      client_management: { create: false, read: true, update: false, delete: false },
      pdf_processing: { create: false, read: false, update: false, delete: false },
      reports_analysis: { create: true, read: true, update: true, delete: false },
      audio_recording: { create: false, read: false, update: false, delete: false }
    },
    is_system_template: false,
    created_by_user_id: 'admin-123',
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-03T00:00:00Z',
    usage_count: 5,
    last_used: '2024-01-05T00:00:00Z'
  },
  {
    template_id: 'template-custom-2',
    template_name: 'Document Processors',
    description: 'Specialized access for document processing team',
    permissions: {
      client_management: { create: false, read: true, update: false, delete: false },
      pdf_processing: { create: true, read: true, update: true, delete: true },
      reports_analysis: { create: false, read: false, update: false, delete: false },
      audio_recording: { create: false, read: false, update: false, delete: false }
    },
    is_system_template: false,
    created_by_user_id: 'admin-123',
    created_at: '2024-01-04T00:00:00Z',
    updated_at: '2024-01-04T00:00:00Z',
    usage_count: 3,
    last_used: null
  }
]

const mockAllTemplates = [...mockSystemTemplates, ...mockCustomTemplates]

const mockFetch = vi.fn()

beforeEach(() => {
  global.fetch = mockFetch
})

afterEach(() => {
  vi.clearAllMocks()
})

describe('PermissionTemplates Component', () => {
  describe('Basic Rendering', () => {
    beforeEach(() => {
      // Mock authentication API for rendering tests
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ user: mockAdminUser })
      } as Response)
    })

    it('should render templates list with system and custom sections', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ templates: mockAllTemplates })
      } as Response)

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Templates de Permissão')).toBeInTheDocument()
        expect(screen.getByText('Gerencie templates reutilizáveis para configurações de permissão')).toBeInTheDocument()
      })

      // Should show system templates section
      expect(screen.getByText('Templates do Sistema')).toBeInTheDocument()
      expect(screen.getByText('Client Specialist')).toBeInTheDocument()
      expect(screen.getByText('Read Only Access')).toBeInTheDocument()

      // Should show custom templates section
      expect(screen.getByText('Templates Personalizados')).toBeInTheDocument()
      expect(screen.getByText('Marketing Team')).toBeInTheDocument()
      expect(screen.getByText('Document Processors')).toBeInTheDocument()
    })

    it('should display template information correctly', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ templates: mockAllTemplates })
      } as Response)

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        // Should show template descriptions
        expect(screen.getByText('Full access to client management with limited PDF processing')).toBeInTheDocument()
        expect(screen.getByText('Custom template for marketing team with reports focus')).toBeInTheDocument()
        
        // Should show usage statistics
        expect(screen.getByText('12 usuários')).toBeInTheDocument()
        expect(screen.getByText('25 usuários')).toBeInTheDocument()
        expect(screen.getByText('5 usuários')).toBeInTheDocument()
        expect(screen.getByText('3 usuários')).toBeInTheDocument()
        
        // Should show last used dates
        expect(screen.getByText(/usado há 1 dia/i)).toBeInTheDocument()
        expect(screen.getByText(/nunca usado/i)).toBeInTheDocument()
      })
    })

    it('should show create template button', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ templates: mockAllTemplates })
      } as Response)

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /novo template/i })).toBeInTheDocument()
      })
    })
  })

  describe('Loading States', () => {
    beforeEach(() => {
      // Mock authentication API for loading state tests
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ user: mockAdminUser })
      } as Response)
    })

    it('should show loading skeleton while fetching templates', () => {
      const delayedPromise = new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({ templates: mockAllTemplates })
        }), 100)
      )
      mockFetch.mockReturnValueOnce(delayedPromise as any)

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      // Should show loading skeletons
      expect(screen.getAllByTestId('template-skeleton')).toHaveLength(3) // Default skeleton count
    })

    it('should show empty state when no templates exist', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ templates: [] })
      } as Response)

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText(/nenhum template encontrado/i)).toBeInTheDocument()
        expect(screen.getByText(/crie o primeiro template/i)).toBeInTheDocument()
      })
    })
  })

  describe('Template Creation', () => {
    beforeEach(() => {
      // Mock authentication and templates APIs for creation tests
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ user: mockAdminUser })
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ templates: mockAllTemplates })
        } as Response)
    })

    it('should open create template dialog when new template button is clicked', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /novo template/i })).toBeInTheDocument()
      })

      const createButton = screen.getByRole('button', { name: /novo template/i })
      await user.click(createButton)

      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByText('Criar Novo Template')).toBeInTheDocument()
      expect(screen.getByLabelText(/nome do template/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/descrição/i)).toBeInTheDocument()
    })

    it('should validate template form fields', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /novo template/i })).toBeInTheDocument()
      })

      const createButton = screen.getByRole('button', { name: /novo template/i })
      await user.click(createButton)

      // Try to save without required fields
      const saveButton = screen.getByRole('button', { name: /criar template/i })
      expect(saveButton).toBeDisabled()

      // Add template name only
      const nameInput = screen.getByLabelText(/nome do template/i)
      await user.type(nameInput, 'Test Template')

      // Should still be disabled without description
      expect(saveButton).toBeDisabled()

      // Add description
      const descriptionInput = screen.getByLabelText(/descrição/i)
      await user.type(descriptionInput, 'Test template description')

      // Should still be disabled without permissions
      expect(saveButton).toBeDisabled()

      // Add at least one permission
      const clientReadCheckbox = screen.getByLabelText(/gestão de clientes.*visualizar/i)
      await user.click(clientReadCheckbox)

      await waitFor(() => {
        expect(saveButton).toBeEnabled()
      })
    })

    it('should create new template with selected permissions', async () => {
      const user = userEvent.setup()

      // Mock create template API
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          template_id: 'new-template-123',
          template_name: 'Sales Team',
          description: 'Custom template for sales team',
          permissions: {
            client_management: { create: true, read: true, update: true, delete: false },
            pdf_processing: { create: false, read: false, update: false, delete: false },
            reports_analysis: { create: false, read: true, update: false, delete: false },
            audio_recording: { create: false, read: false, update: false, delete: false }
          },
          is_system_template: false
        })
      } as Response)

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /novo template/i })).toBeInTheDocument()
      })

      const createButton = screen.getByRole('button', { name: /novo template/i })
      await user.click(createButton)

      // Fill form
      const nameInput = screen.getByLabelText(/nome do template/i)
      await user.type(nameInput, 'Sales Team')

      const descriptionInput = screen.getByLabelText(/descrição/i)
      await user.type(descriptionInput, 'Custom template for sales team')

      // Set permissions
      const clientCreateCheckbox = screen.getByLabelText(/gestão de clientes.*criar/i)
      const clientReadCheckbox = screen.getByLabelText(/gestão de clientes.*visualizar/i)
      const clientUpdateCheckbox = screen.getByLabelText(/gestão de clientes.*editar/i)
      const reportsReadCheckbox = screen.getByLabelText(/relatórios.*visualizar/i)

      await user.click(clientCreateCheckbox)
      await user.click(clientReadCheckbox)
      await user.click(clientUpdateCheckbox)
      await user.click(reportsReadCheckbox)

      // Create template
      const saveButton = screen.getByRole('button', { name: /criar template/i })
      await user.click(saveButton)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/permissions/templates'),
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              'Content-Type': 'application/json'
            }),
            body: expect.stringContaining('Sales Team')
          })
        )
      })
    })
  })

  describe('Template Management', () => {
    beforeEach(async () => {
      // Mock authentication and templates APIs for management tests
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ user: mockAdminUser })
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ templates: mockAllTemplates })
        } as Response)
    })

    it('should show template actions menu for custom templates', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Marketing Team')).toBeInTheDocument()
      })

      // Find and click actions button for custom template
      const templateCards = screen.getAllByTestId(/template-card-/)
      const customTemplateCard = templateCards.find(card => 
        card.textContent?.includes('Marketing Team')
      )!

      const actionsButton = customTemplateCard.querySelector('[aria-label="Ações do template"]')!
      await user.click(actionsButton)

      // Should show action menu
      expect(screen.getByRole('menu')).toBeInTheDocument()
      expect(screen.getByText('Editar')).toBeInTheDocument()
      expect(screen.getByText('Duplicar')).toBeInTheDocument()
      expect(screen.getByText('Excluir')).toBeInTheDocument()
      expect(screen.getByText('Aplicar a Usuários')).toBeInTheDocument()
    })

    it('should not show edit/delete actions for system templates', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Client Specialist')).toBeInTheDocument()
      })

      // Find and click actions button for system template
      const templateCards = screen.getAllByTestId(/template-card-/)
      const systemTemplateCard = templateCards.find(card => 
        card.textContent?.includes('Client Specialist')
      )!

      const actionsButton = systemTemplateCard.querySelector('[aria-label="Ações do template"]')!
      await user.click(actionsButton)

      // Should only show view and apply actions for system templates
      expect(screen.getByRole('menu')).toBeInTheDocument()
      expect(screen.getByText('Visualizar')).toBeInTheDocument()
      expect(screen.getByText('Duplicar')).toBeInTheDocument()
      expect(screen.getByText('Aplicar a Usuários')).toBeInTheDocument()
      
      // Should not show edit/delete for system templates
      expect(screen.queryByText('Editar')).not.toBeInTheDocument()
      expect(screen.queryByText('Excluir')).not.toBeInTheDocument()
    })

    it('should edit custom template when edit action is clicked', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Marketing Team')).toBeInTheDocument()
      })

      // Open actions menu for custom template
      const templateCards = screen.getAllByTestId(/template-card-/)
      const customTemplateCard = templateCards.find(card => 
        card.textContent?.includes('Marketing Team')
      )!

      const actionsButton = customTemplateCard.querySelector('[aria-label="Ações do template"]')!
      await user.click(actionsButton)

      // Click edit
      const editButton = screen.getByText('Editar')
      await user.click(editButton)

      // Should open edit dialog
      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByText('Editar Template')).toBeInTheDocument()
      expect(screen.getByDisplayValue('Marketing Team')).toBeInTheDocument()
      expect(screen.getByDisplayValue('Custom template for marketing team with reports focus')).toBeInTheDocument()
    })

    it('should duplicate template when duplicate action is clicked', async () => {
      const user = userEvent.setup()

      // Mock duplicate API
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          template_id: 'duplicated-template-456',
          template_name: 'Client Specialist (Cópia)',
          description: 'Full access to client management with limited PDF processing',
          permissions: mockSystemTemplates[0].permissions,
          is_system_template: false
        })
      } as Response)

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Client Specialist')).toBeInTheDocument()
      })

      // Open actions menu for system template
      const templateCards = screen.getAllByTestId(/template-card-/)
      const systemTemplateCard = templateCards.find(card => 
        card.textContent?.includes('Client Specialist')
      )!

      const actionsButton = systemTemplateCard.querySelector('[aria-label="Ações do template"]')!
      await user.click(actionsButton)

      // Click duplicate
      const duplicateButton = screen.getByText('Duplicar')
      await user.click(duplicateButton)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/permissions/templates/template-system-1/duplicate'),
          expect.objectContaining({
            method: 'POST'
          })
        )
      })
    })

    it('should delete custom template with confirmation', async () => {
      const user = userEvent.setup()
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)

      // Mock delete API
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true })
      } as Response)

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Marketing Team')).toBeInTheDocument()
      })

      // Open actions menu for custom template
      const templateCards = screen.getAllByTestId(/template-card-/)
      const customTemplateCard = templateCards.find(card => 
        card.textContent?.includes('Marketing Team')
      )!

      const actionsButton = customTemplateCard.querySelector('[aria-label="Ações do template"]')!
      await user.click(actionsButton)

      // Click delete
      const deleteButton = screen.getByText('Excluir')
      await user.click(deleteButton)

      expect(confirmSpy).toHaveBeenCalledWith('Tem certeza que deseja excluir o template "Marketing Team"? Esta ação não pode ser desfeita.')

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/permissions/templates/template-custom-1'),
          expect.objectContaining({
            method: 'DELETE'
          })
        )
      })

      confirmSpy.mockRestore()
    })
  })

  describe('Template Application', () => {
    beforeEach(async () => {
      // Mock authentication and templates APIs for application tests
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ user: mockAdminUser })
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ templates: mockAllTemplates })
        } as Response)
    })

    it('should open user selection dialog when apply to users is clicked', async () => {
      const user = userEvent.setup()

      // Mock users API
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          users: [
            { user_id: 'user-1', full_name: 'User One', email: 'user1@test.com', role: 'user' },
            { user_id: 'user-2', full_name: 'User Two', email: 'user2@test.com', role: 'user' }
          ]
        })
      } as Response)

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Client Specialist')).toBeInTheDocument()
      })

      // Open actions menu
      const templateCards = screen.getAllByTestId(/template-card-/)
      const templateCard = templateCards.find(card => 
        card.textContent?.includes('Client Specialist')
      )!

      const actionsButton = templateCard.querySelector('[aria-label="Ações do template"]')!
      await user.click(actionsButton)

      // Click apply to users
      const applyButton = screen.getByText('Aplicar a Usuários')
      await user.click(applyButton)

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
        expect(screen.getByText('Aplicar Template a Usuários')).toBeInTheDocument()
        expect(screen.getByText('Client Specialist')).toBeInTheDocument()
        expect(screen.getByText('User One')).toBeInTheDocument()
        expect(screen.getByText('User Two')).toBeInTheDocument()
      })
    })

    it('should apply template to selected users', async () => {
      const user = userEvent.setup()

      // Mock users API
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          users: [
            { user_id: 'user-1', full_name: 'User One', email: 'user1@test.com', role: 'user' },
            { user_id: 'user-2', full_name: 'User Two', email: 'user2@test.com', role: 'user' }
          ]
        })
      } as Response)

      // Mock apply template API
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          results: [
            { user_id: 'user-1', status: 'success' },
            { user_id: 'user-2', status: 'success' }
          ]
        })
      } as Response)

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Client Specialist')).toBeInTheDocument()
      })

      // Open actions menu and click apply
      const templateCards = screen.getAllByTestId(/template-card-/)
      const templateCard = templateCards.find(card => 
        card.textContent?.includes('Client Specialist')
      )!

      const actionsButton = templateCard.querySelector('[aria-label="Ações do template"]')!
      await user.click(actionsButton)

      const applyButton = screen.getByText('Aplicar a Usuários')
      await user.click(applyButton)

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      // Select users
      const userCheckboxes = screen.getAllByRole('checkbox', { name: /selecionar usuário/i })
      await user.click(userCheckboxes[0])
      await user.click(userCheckboxes[1])

      // Add reason
      const reasonTextarea = screen.getByPlaceholderText(/motivo da aplicação/i)
      await user.type(reasonTextarea, 'Aplicando template padrão para novos especialistas')

      // Apply template
      const confirmApplyButton = screen.getByRole('button', { name: /aplicar template/i })
      await user.click(confirmApplyButton)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/permissions/templates/template-system-1/apply'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('user-1')
          })
        )
      })
    })
  })

  describe('Search and Filtering', () => {
    beforeEach(async () => {
      // Mock authentication and templates APIs for search tests
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ user: mockAdminUser })
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ templates: mockAllTemplates })
        } as Response)
    })

    it('should filter templates by search query', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Client Specialist')).toBeInTheDocument()
        expect(screen.getByText('Marketing Team')).toBeInTheDocument()
      })

      // Search for "Marketing"
      const searchInput = screen.getByPlaceholderText(/buscar templates/i)
      await user.type(searchInput, 'Marketing')

      await waitFor(() => {
        expect(screen.getByText('Marketing Team')).toBeInTheDocument()
        expect(screen.queryByText('Client Specialist')).not.toBeInTheDocument()
        expect(screen.queryByText('Document Processors')).not.toBeInTheDocument()
      })
    })

    it('should filter templates by type (system vs custom)', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Client Specialist')).toBeInTheDocument()
        expect(screen.getByText('Marketing Team')).toBeInTheDocument()
      })

      // Filter by system templates only
      const typeFilter = screen.getByRole('combobox', { name: /filtrar por tipo/i })
      await user.click(typeFilter)
      await user.click(screen.getByText('Sistema'))

      await waitFor(() => {
        expect(screen.getByText('Client Specialist')).toBeInTheDocument()
        expect(screen.getByText('Read Only Access')).toBeInTheDocument()
        expect(screen.queryByText('Marketing Team')).not.toBeInTheDocument()
      })
    })

    it('should sort templates by usage count', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Client Specialist')).toBeInTheDocument()
      })

      // Change sort to usage count descending
      const sortSelect = screen.getByRole('combobox', { name: /ordenar por/i })
      await user.click(sortSelect)
      await user.click(screen.getByText('Mais Usados'))

      await waitFor(() => {
        const templateCards = screen.getAllByTestId(/template-card-/)
        // Read Only Access (25 users) should be first
        expect(templateCards[0]).toHaveTextContent('Read Only Access')
        expect(templateCards[0]).toHaveTextContent('25 usuários')
      })
    })
  })

  describe('Error Handling', () => {
    it('should handle template loading errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Failed to load templates'))

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText(/erro ao carregar templates/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /tentar novamente/i })).toBeInTheDocument()
      })
    })

    it('should handle template creation errors', async () => {
      const user = userEvent.setup()

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ templates: mockAllTemplates })
        } as Response)
        .mockRejectedValueOnce(new Error('Template name already exists'))

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /novo template/i })).toBeInTheDocument()
      })

      // Open create dialog
      const createButton = screen.getByRole('button', { name: /novo template/i })
      await user.click(createButton)

      // Fill form
      const nameInput = screen.getByLabelText(/nome do template/i)
      await user.type(nameInput, 'Duplicate Name')

      const descriptionInput = screen.getByLabelText(/descrição/i)
      await user.type(descriptionInput, 'Test description')

      const clientReadCheckbox = screen.getByLabelText(/gestão de clientes.*visualizar/i)
      await user.click(clientReadCheckbox)

      // Try to save
      const saveButton = screen.getByRole('button', { name: /criar template/i })
      await user.click(saveButton)

      await waitFor(() => {
        expect(screen.getByText(/erro ao criar template/i)).toBeInTheDocument()
      })
    })

    it('should handle template deletion errors', async () => {
      const user = userEvent.setup()
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)

      mockFetch.mockRejectedValueOnce(new Error('Cannot delete template in use'))

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Marketing Team')).toBeInTheDocument()
      })

      // Try to delete template
      const templateCards = screen.getAllByTestId(/template-card-/)
      const customTemplateCard = templateCards.find(card => 
        card.textContent?.includes('Marketing Team')
      )!

      const actionsButton = customTemplateCard.querySelector('[aria-label="Ações do template"]')!
      await user.click(actionsButton)

      const deleteButton = screen.getByText('Excluir')
      await user.click(deleteButton)

      await waitFor(() => {
        expect(screen.getByText(/erro ao excluir template/i)).toBeInTheDocument()
      })

      confirmSpy.mockRestore()
    })
  })

  describe('Accessibility', () => {
    beforeEach(async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ templates: mockAllTemplates })
      } as Response)
    })

    it('should have proper ARIA labels and structure', async () => {
      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /templates de permissão/i })).toBeInTheDocument()
      })

      // Should have proper regions
      expect(screen.getByRole('region', { name: /templates do sistema/i })).toBeInTheDocument()
      expect(screen.getByRole('region', { name: /templates personalizados/i })).toBeInTheDocument()

      // Template cards should have proper labels
      const templateCards = screen.getAllByRole('article')
      expect(templateCards.length).toBeGreaterThan(0)

      // Action buttons should be properly labeled
      const actionButtons = screen.getAllByLabelText(/ações do template/i)
      expect(actionButtons.length).toBeGreaterThan(0)
    })

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /novo template/i })).toBeInTheDocument()
      })

      // Should be able to tab to create button
      await user.tab()
      expect(screen.getByRole('button', { name: /novo template/i })).toHaveFocus()

      // Should be able to tab to action buttons
      await user.tab()
      const actionButtons = screen.getAllByLabelText(/ações do template/i)
      expect(actionButtons[0]).toHaveFocus()

      // Should be able to activate with Enter
      await user.keyboard('{Enter}')
      expect(screen.getByRole('menu')).toBeInTheDocument()
    })

    it('should announce template actions to screen readers', async () => {
      const user = userEvent.setup()

      // Mock successful delete
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true })
      } as Response)

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Marketing Team')).toBeInTheDocument()
      })

      // Delete template
      const templateCards = screen.getAllByTestId(/template-card-/)
      const customTemplateCard = templateCards.find(card => 
        card.textContent?.includes('Marketing Team')
      )!

      const actionsButton = customTemplateCard.querySelector('[aria-label="Ações do template"]')!
      await user.click(actionsButton)

      const deleteButton = screen.getByText('Excluir')
      await user.click(deleteButton)

      await waitFor(() => {
        // Should announce successful deletion
        expect(screen.getByRole('status')).toHaveTextContent(/template excluído com sucesso/i)
      })

      confirmSpy.mockRestore()
    })
  })

  describe('Template Details and Preview', () => {
    beforeEach(async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ templates: mockAllTemplates })
      } as Response)
    })

    it('should show template details when template card is clicked', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Client Specialist')).toBeInTheDocument()
      })

      // Click on template card
      const templateCard = screen.getByText('Client Specialist').closest('[data-testid^="template-card"]')!
      await user.click(templateCard)

      // Should show template details dialog
      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByText('Detalhes do Template')).toBeInTheDocument()
      expect(screen.getByText('Client Specialist')).toBeInTheDocument()
      expect(screen.getByText('Full access to client management with limited PDF processing')).toBeInTheDocument()

      // Should show permission breakdown
      expect(screen.getByText('Gestão de Clientes: Padrão')).toBeInTheDocument()
      expect(screen.getByText('Processamento PDF: Somente Leitura')).toBeInTheDocument()
      expect(screen.getByText('Relatórios: Somente Leitura')).toBeInTheDocument()
      expect(screen.getByText('Gravação de Áudio: Nenhum')).toBeInTheDocument()

      // Should show usage statistics
      expect(screen.getByText('Usado por 12 usuários')).toBeInTheDocument()
      expect(screen.getByText('Última utilização: há 1 dia')).toBeInTheDocument()
    })

    it('should show permission level indicators correctly', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <PermissionTemplates />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Marketing Team')).toBeInTheDocument()
      })

      // Click on custom template with reports focus
      const templateCard = screen.getByText('Marketing Team').closest('[data-testid^="template-card"]')!
      await user.click(templateCard)

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      // Should show correct permission levels for marketing team template
      expect(screen.getByText('Gestão de Clientes: Somente Leitura')).toBeInTheDocument()
      expect(screen.getByText('Processamento PDF: Nenhum')).toBeInTheDocument()
      expect(screen.getByText('Relatórios: Padrão')).toBeInTheDocument()
      expect(screen.getByText('Gravação de Áudio: Nenhum')).toBeInTheDocument()
    })
  })
})