/**
 * PermissionAuditLog Component Tests
 * 
 * Comprehensive tests for the PermissionAuditLog component with filtering and real-time updates
 * Following CLAUDE.md rules: no internal mocking, only external API mocking
 */

import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import React from 'react'

import { PermissionAuditLog } from '../PermissionAuditLog'
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

const mockAuditLogs = [
  {
    audit_id: 'audit-1',
    user_id: 'user-123',
    user_name: 'João Silva',
    user_email: 'joao@test.com',
    agent_name: 'client_management',
    action: 'PERMISSION_GRANTED',
    permission_changes: {
      before: { create: false, read: true, update: false, delete: false },
      after: { create: true, read: true, update: true, delete: false }
    },
    reason: 'Promoção para especialista em clientes',
    changed_by_user_id: 'admin-123',
    changed_by_name: 'Admin User',
    created_at: '2024-01-07T10:30:00Z',
    ip_address: '192.168.1.100',
    user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
  },
  {
    audit_id: 'audit-2',
    user_id: 'user-456',
    user_name: 'Maria Santos',
    user_email: 'maria@test.com',
    agent_name: 'pdf_processing',
    action: 'PERMISSION_REVOKED',
    permission_changes: {
      before: { create: true, read: true, update: true, delete: false },
      after: { create: false, read: true, update: false, delete: false }
    },
    reason: 'Mudança de função - não requer mais processamento de documentos',
    changed_by_user_id: 'admin-123',
    changed_by_name: 'Admin User',
    created_at: '2024-01-07T09:15:00Z',
    ip_address: '192.168.1.101',
    user_agent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
  },
  {
    audit_id: 'audit-3',
    user_id: 'user-789',
    user_name: 'Pedro Costa',
    user_email: 'pedro@test.com',
    agent_name: 'reports_analysis',
    action: 'TEMPLATE_APPLIED',
    permission_changes: {
      before: {},
      after: { create: false, read: true, update: false, delete: false }
    },
    reason: 'Aplicação de template "Read Only Access"',
    changed_by_user_id: 'admin-123',
    changed_by_name: 'Admin User',
    created_at: '2024-01-07T08:45:00Z',
    ip_address: '192.168.1.102',
    user_agent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    template_name: 'Read Only Access'
  },
  {
    audit_id: 'audit-4',
    user_id: 'user-321',
    user_name: 'Ana Oliveira',
    user_email: 'ana@test.com',
    agent_name: 'audio_recording',
    action: 'BULK_OPERATION',
    permission_changes: {
      before: { create: false, read: false, update: false, delete: false },
      after: { create: true, read: true, update: false, delete: false }
    },
    reason: 'Operação em lote: habilitando acesso para equipe de suporte',
    changed_by_user_id: 'admin-123',
    changed_by_name: 'Admin User',
    created_at: '2024-01-06T16:20:00Z',
    ip_address: '192.168.1.103',
    user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    bulk_operation_id: 'bulk-op-456'
  },
  {
    audit_id: 'audit-5',
    user_id: 'user-654',
    user_name: 'Carlos Lima',
    user_email: 'carlos@test.com',
    agent_name: 'client_management',
    action: 'PERMISSION_DENIED',
    permission_changes: null,
    reason: 'Tentativa de acesso negada - usuário sem permissão',
    changed_by_user_id: null,
    changed_by_name: null,
    created_at: '2024-01-06T14:10:00Z',
    ip_address: '192.168.1.104',
    user_agent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15',
    access_attempt: true
  }
]

const mockFetch = vi.fn()

beforeEach(() => {
  global.fetch = mockFetch
})

afterEach(() => {
  vi.clearAllMocks()
})

describe('PermissionAuditLog Component', () => {
  describe('Basic Rendering', () => {
    beforeEach(() => {
      // Mock authentication API for rendering tests
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ user: mockAdminUser })
      } as Response)
    })

    it('should render audit log with entries', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          logs: mockAuditLogs,
          total: mockAuditLogs.length,
          page: 1,
          per_page: 20
        })
      } as Response)

      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Log de Auditoria de Permissões')).toBeInTheDocument()
        expect(screen.getByText('Histórico completo de todas as alterações de permissão')).toBeInTheDocument()
      })

      // Should show audit entries
      expect(screen.getByText('João Silva')).toBeInTheDocument()
      expect(screen.getByText('Maria Santos')).toBeInTheDocument()
      expect(screen.getByText('Pedro Costa')).toBeInTheDocument()
      expect(screen.getByText('Ana Oliveira')).toBeInTheDocument()
      expect(screen.getByText('Carlos Lima')).toBeInTheDocument()
    })

    it('should display different action types with appropriate badges', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          logs: mockAuditLogs,
          total: mockAuditLogs.length,
          page: 1,
          per_page: 20
        })
      } as Response)

      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        // Should show different action badges with appropriate colors
        expect(screen.getByText('Permissão Concedida')).toBeInTheDocument()
        expect(screen.getByText('Permissão Revogada')).toBeInTheDocument()
        expect(screen.getByText('Template Aplicado')).toBeInTheDocument()
        expect(screen.getByText('Operação em Lote')).toBeInTheDocument()
        expect(screen.getByText('Acesso Negado')).toBeInTheDocument()
      })
    })

    it('should show agent and permission change information', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          logs: mockAuditLogs,
          total: mockAuditLogs.length,
          page: 1,
          per_page: 20
        })
      } as Response)

      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        // Should show agent names
        expect(screen.getByText('Gestão de Clientes')).toBeInTheDocument()
        expect(screen.getByText('Processamento PDF')).toBeInTheDocument()
        expect(screen.getByText('Relatórios e Análises')).toBeInTheDocument()
        expect(screen.getByText('Gravação de Áudio')).toBeInTheDocument()

        // Should show reasons
        expect(screen.getByText('Promoção para especialista em clientes')).toBeInTheDocument()
        expect(screen.getByText('Mudança de função - não requer mais processamento de documentos')).toBeInTheDocument()
      })
    })

    it('should display timestamps in relative format', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          logs: mockAuditLogs,
          total: mockAuditLogs.length,
          page: 1,
          per_page: 20
        })
      } as Response)

      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        // Should show relative timestamps (mocked dates should show as relative)
        expect(screen.getAllByText(/há \d+/)).toHaveLength(mockAuditLogs.length)
      })
    })
  })

  describe('Filtering', () => {
    beforeEach(() => {
      // Mock authentication and audit logs APIs for filtering tests
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ user: mockAdminUser })
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            logs: mockAuditLogs,
            total: mockAuditLogs.length,
            page: 1,
            per_page: 20
          })
        } as Response)
    })

    it('should filter by user search', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      // Search for specific user
      const searchInput = screen.getByPlaceholderText(/buscar por usuário/i)
      await user.type(searchInput, 'João')

      // Mock filtered API response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          logs: [mockAuditLogs[0]], // Only João's entry
          total: 1,
          page: 1,
          per_page: 20
        })
      } as Response)

      // Trigger search
      await user.keyboard('{Enter}')

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/permissions/audit'),
          expect.objectContaining({
            method: 'GET'
          })
        )
        expect(mockFetch).toHaveBeenLastCalledWith(
          expect.stringContaining('user_search=João'),
          expect.any(Object)
        )
      })
    })

    it('should filter by action type', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      // Select action filter
      const actionFilter = screen.getByRole('combobox', { name: /filtrar por ação/i })
      await user.click(actionFilter)
      await user.click(screen.getByText('Permissão Concedida'))

      // Mock filtered API response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          logs: [mockAuditLogs[0]], // Only granted permission entries
          total: 1,
          page: 1,
          per_page: 20
        })
      } as Response)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenLastCalledWith(
          expect.stringContaining('action=PERMISSION_GRANTED'),
          expect.any(Object)
        )
      })
    })

    it('should filter by agent', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      // Select agent filter
      const agentFilter = screen.getByRole('combobox', { name: /filtrar por agente/i })
      await user.click(agentFilter)
      await user.click(screen.getByText('Gestão de Clientes'))

      // Mock filtered API response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          logs: [mockAuditLogs[0], mockAuditLogs[4]], // Client management entries
          total: 2,
          page: 1,
          per_page: 20
        })
      } as Response)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenLastCalledWith(
          expect.stringContaining('agent=client_management'),
          expect.any(Object)
        )
      })
    })

    it('should filter by date range', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      // Set date filter
      const fromDateInput = screen.getByLabelText(/data inicial/i)
      const toDateInput = screen.getByLabelText(/data final/i)

      await user.type(fromDateInput, '2024-01-06')
      await user.type(toDateInput, '2024-01-07')

      // Mock filtered API response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          logs: mockAuditLogs.slice(0, 3), // Entries within date range
          total: 3,
          page: 1,
          per_page: 20
        })
      } as Response)

      // Apply filter
      const applyButton = screen.getByRole('button', { name: /aplicar filtros/i })
      await user.click(applyButton)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenLastCalledWith(
          expect.stringContaining('from_date=2024-01-06'),
          expect.any(Object)
        )
        expect(mockFetch).toHaveBeenLastCalledWith(
          expect.stringContaining('to_date=2024-01-07'),
          expect.any(Object)
        )
      })
    })

    it('should clear all filters', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      // Apply some filters first
      const searchInput = screen.getByPlaceholderText(/buscar por usuário/i)
      await user.type(searchInput, 'João')

      const actionFilter = screen.getByRole('combobox', { name: /filtrar por ação/i })
      await user.click(actionFilter)
      await user.click(screen.getByText('Permissão Concedida'))

      // Clear all filters
      const clearButton = screen.getByRole('button', { name: /limpar filtros/i })
      await user.click(clearButton)

      // Mock original API response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          logs: mockAuditLogs,
          total: mockAuditLogs.length,
          page: 1,
          per_page: 20
        })
      } as Response)

      await waitFor(() => {
        expect(searchInput).toHaveValue('')
        expect(screen.getByText('Todas as Ações')).toBeInTheDocument() // Default option
      })
    })
  })

  describe('Detailed View', () => {
    beforeEach(() => {
      // Mock authentication and audit logs APIs for detailed view tests
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ user: mockAdminUser })
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            logs: mockAuditLogs,
            total: mockAuditLogs.length,
            page: 1,
            per_page: 20
          })
        } as Response)
    })

    it('should show detailed view when log entry is clicked', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      // Click on a log entry
      const logEntry = screen.getByText('João Silva').closest('[data-testid^="audit-entry"]')!
      await user.click(logEntry)

      // Should show detailed dialog
      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByText('Detalhes da Auditoria')).toBeInTheDocument()

      // Should show detailed information
      expect(screen.getByText('João Silva')).toBeInTheDocument()
      expect(screen.getByText('joao@test.com')).toBeInTheDocument()
      expect(screen.getByText('Gestão de Clientes')).toBeInTheDocument()
      expect(screen.getByText('Permissão Concedida')).toBeInTheDocument()
      expect(screen.getByText('Promoção para especialista em clientes')).toBeInTheDocument()
      expect(screen.getByText('Admin User')).toBeInTheDocument()

      // Should show before/after permissions comparison
      expect(screen.getByText('Antes')).toBeInTheDocument()
      expect(screen.getByText('Depois')).toBeInTheDocument()

      // Should show technical details
      expect(screen.getByText('192.168.1.100')).toBeInTheDocument()
      expect(screen.getByText(/Mozilla\/5\.0.*Windows/)).toBeInTheDocument()
    })

    it('should show permission changes comparison', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      // Click on a log entry with permission changes
      const logEntry = screen.getByText('João Silva').closest('[data-testid^="audit-entry"]')!
      await user.click(logEntry)

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      // Should show before/after comparison
      const beforeSection = screen.getByText('Antes').closest('.permission-comparison')!
      const afterSection = screen.getByText('Depois').closest('.permission-comparison')!

      expect(within(beforeSection).getByText('Criar: Não')).toBeInTheDocument()
      expect(within(beforeSection).getByText('Visualizar: Sim')).toBeInTheDocument()
      expect(within(beforeSection).getByText('Editar: Não')).toBeInTheDocument()

      expect(within(afterSection).getByText('Criar: Sim')).toBeInTheDocument()
      expect(within(afterSection).getByText('Visualizar: Sim')).toBeInTheDocument()
      expect(within(afterSection).getByText('Editar: Sim')).toBeInTheDocument()
    })

    it('should show special information for template applications', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Pedro Costa')).toBeInTheDocument()
      })

      // Click on template application entry
      const templateEntry = screen.getByText('Pedro Costa').closest('[data-testid^="audit-entry"]')!
      await user.click(templateEntry)

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      // Should show template information
      expect(screen.getByText('Template Aplicado: Read Only Access')).toBeInTheDocument()
      expect(screen.getByText('Aplicação de template "Read Only Access"')).toBeInTheDocument()
    })

    it('should show bulk operation information', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Ana Oliveira')).toBeInTheDocument()
      })

      // Click on bulk operation entry
      const bulkEntry = screen.getByText('Ana Oliveira').closest('[data-testid^="audit-entry"]')!
      await user.click(bulkEntry)

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      // Should show bulk operation information
      expect(screen.getByText('Operação em Lote')).toBeInTheDocument()
      expect(screen.getByText('ID da Operação: bulk-op-456')).toBeInTheDocument()
      expect(screen.getByText('Operação em lote: habilitando acesso para equipe de suporte')).toBeInTheDocument()
    })

    it('should handle access denied entries differently', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Carlos Lima')).toBeInTheDocument()
      })

      // Click on access denied entry
      const deniedEntry = screen.getByText('Carlos Lima').closest('[data-testid^="audit-entry"]')!
      await user.click(deniedEntry)

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument()
      })

      // Should show access denied information
      expect(screen.getByText('Acesso Negado')).toBeInTheDocument()
      expect(screen.getByText('Tentativa de acesso negada - usuário sem permissão')).toBeInTheDocument()
      expect(screen.getByText('Sistema')).toBeInTheDocument() // No user made this change

      // Should not show permission changes for denied access
      expect(screen.queryByText('Antes')).not.toBeInTheDocument()
      expect(screen.queryByText('Depois')).not.toBeInTheDocument()
    })
  })

  describe('Export Functionality', () => {
    beforeEach(() => {
      // Mock authentication and audit logs APIs for export tests
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ user: mockAdminUser })
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            logs: mockAuditLogs,
            total: mockAuditLogs.length,
            page: 1,
            per_page: 20
          })
        } as Response)
    })

    it('should allow exporting audit logs to CSV', async () => {
      const user = userEvent.setup()

      // Mock export API
      mockFetch.mockResolvedValueOnce({
        ok: true,
        blob: () => Promise.resolve(new Blob(['CSV content'], { type: 'text/csv' }))
      } as Response)

      // Mock URL.createObjectURL
      const createObjectURLSpy = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:mock-url')
      const revokeObjectURLSpy = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {})

      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      // Click export button
      const exportButton = screen.getByRole('button', { name: /exportar/i })
      await user.click(exportButton)

      // Should show export options
      expect(screen.getByRole('menu')).toBeInTheDocument()
      expect(screen.getByText('Exportar como CSV')).toBeInTheDocument()
      expect(screen.getByText('Exportar como Excel')).toBeInTheDocument()

      // Click CSV export
      const csvOption = screen.getByText('Exportar como CSV')
      await user.click(csvOption)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenLastCalledWith(
          expect.stringContaining('/api/v1/permissions/audit/export'),
          expect.objectContaining({
            method: 'GET',
            headers: expect.objectContaining({
              'Accept': 'text/csv'
            })
          })
        )
      })

      createObjectURLSpy.mockRestore()
      revokeObjectURLSpy.mockRestore()
    })

    it('should show export progress for large datasets', async () => {
      const user = userEvent.setup()

      // Mock slow export API
      const slowExportPromise = new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          blob: () => Promise.resolve(new Blob(['CSV content'], { type: 'text/csv' }))
        }), 100)
      )
      mockFetch.mockReturnValueOnce(slowExportPromise as any)

      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      const exportButton = screen.getByRole('button', { name: /exportar/i })
      await user.click(exportButton)

      const csvOption = screen.getByText('Exportar como CSV')
      await user.click(csvOption)

      // Should show loading indicator
      expect(screen.getByText(/preparando exportação/i)).toBeInTheDocument()

      await waitFor(() => {
        expect(screen.queryByText(/preparando exportação/i)).not.toBeInTheDocument()
      }, { timeout: 1000 })
    })
  })

  describe('Real-time Updates', () => {
    beforeEach(() => {
      // Mock authentication and audit logs APIs for real-time tests
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ user: mockAdminUser })
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            logs: mockAuditLogs,
            total: mockAuditLogs.length,
            page: 1,
            per_page: 20
          })
        } as Response)
    })

    it('should receive and display real-time audit updates via WebSocket', async () => {
      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      // Simulate receiving a new audit log via WebSocket
      const newAuditLog = {
        audit_id: 'audit-new',
        user_id: 'user-new',
        user_name: 'Novo Usuário',
        user_email: 'novo@test.com',
        agent_name: 'client_management',
        action: 'PERMISSION_GRANTED',
        permission_changes: {
          before: {},
          after: { create: false, read: true, update: false, delete: false }
        },
        reason: 'Novo funcionário - acesso inicial',
        changed_by_user_id: 'admin-123',
        changed_by_name: 'Admin User',
        created_at: new Date().toISOString(),
        ip_address: '192.168.1.200',
        user_agent: 'Mozilla/5.0'
      }

      // Simulate WebSocket message
      window.dispatchEvent(new CustomEvent('audit-log-update', { 
        detail: { type: 'new_entry', log: newAuditLog } 
      }))

      await waitFor(() => {
        expect(screen.getByText('Novo Usuário')).toBeInTheDocument()
        expect(screen.getByText('novo@test.com')).toBeInTheDocument()
        expect(screen.getByText('Novo funcionário - acesso inicial')).toBeInTheDocument()
      })
    })

    it('should show notification when new audit entries are received', async () => {
      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      const newAuditLog = {
        audit_id: 'audit-notification',
        user_id: 'user-notification',
        user_name: 'Test User',
        action: 'PERMISSION_REVOKED'
      }

      // Simulate WebSocket notification
      window.dispatchEvent(new CustomEvent('audit-log-update', { 
        detail: { type: 'new_entry', log: newAuditLog } 
      }))

      await waitFor(() => {
        expect(screen.getByText(/nova entrada no log de auditoria/i)).toBeInTheDocument()
      })
    })

    it('should auto-refresh audit log when significant changes occur', async () => {
      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      // Mock refresh API call
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          logs: [...mockAuditLogs, {
            audit_id: 'audit-refresh',
            user_name: 'Auto Refreshed Entry',
            action: 'BULK_OPERATION'
          }],
          total: mockAuditLogs.length + 1,
          page: 1,
          per_page: 20
        })
      } as Response)

      // Simulate bulk operation completion event
      window.dispatchEvent(new CustomEvent('bulk-operation-complete', { 
        detail: { operation_id: 'bulk-456' } 
      }))

      await waitFor(() => {
        expect(screen.getByText('Auto Refreshed Entry')).toBeInTheDocument()
      })
    })
  })

  describe('Pagination', () => {
    beforeEach(() => {
      // Mock authentication and audit logs APIs for pagination tests
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ user: mockAdminUser })
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            logs: mockAuditLogs,
            total: 100, // More than current page
            page: 1,
            per_page: 20
          })
        } as Response)
    })

    it('should show pagination controls when there are multiple pages', async () => {
      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      // Should show pagination
      expect(screen.getByRole('navigation', { name: /paginação/i })).toBeInTheDocument()
      expect(screen.getByText('Página 1 de 5')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /próxima página/i })).toBeInTheDocument()
    })

    it('should load next page when pagination is used', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      // Mock next page API call
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          logs: [
            {
              audit_id: 'audit-page-2-1',
              user_name: 'Page 2 User 1',
              action: 'PERMISSION_GRANTED'
            }
          ],
          total: 100,
          page: 2,
          per_page: 20
        })
      } as Response)

      // Click next page
      const nextButton = screen.getByRole('button', { name: /próxima página/i })
      await user.click(nextButton)

      await waitFor(() => {
        expect(screen.getByText('Page 2 User 1')).toBeInTheDocument()
        expect(screen.getByText('Página 2 de 5')).toBeInTheDocument()
      })
    })

    it('should allow changing page size', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      // Change page size
      const pageSizeSelect = screen.getByRole('combobox', { name: /itens por página/i })
      await user.click(pageSizeSelect)
      await user.click(screen.getByText('50'))

      // Mock API call with new page size
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          logs: mockAuditLogs,
          total: 100,
          page: 1,
          per_page: 50
        })
      } as Response)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenLastCalledWith(
          expect.stringContaining('per_page=50'),
          expect.any(Object)
        )
      })
    })
  })

  describe('Loading and Error States', () => {
    it('should show loading skeleton while fetching logs', () => {
      // Mock authentication API
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ user: mockAdminUser })
      } as Response)
      
      const delayedPromise = new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve({
            logs: mockAuditLogs,
            total: mockAuditLogs.length,
            page: 1,
            per_page: 20
          })
        }), 100)
      )
      mockFetch.mockReturnValueOnce(delayedPromise as any)

      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      // Should show loading skeletons
      expect(screen.getAllByTestId('audit-entry-skeleton')).toHaveLength(5) // Default skeleton count
    })

    it('should show empty state when no audit logs exist', async () => {
      // Mock authentication API
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ user: mockAdminUser })
      } as Response)
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          logs: [],
          total: 0,
          page: 1,
          per_page: 20
        })
      } as Response)

      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText(/nenhuma entrada de auditoria encontrada/i)).toBeInTheDocument()
        expect(screen.getByText(/não há alterações de permissão registradas/i)).toBeInTheDocument()
      })
    })

    it('should handle API errors gracefully', async () => {
      // Mock authentication API success then audit logs API failure
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ user: mockAdminUser })
        } as Response)
        .mockRejectedValueOnce(new Error('Failed to load audit logs'))

      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText(/erro ao carregar log de auditoria/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /tentar novamente/i })).toBeInTheDocument()
      })
    })

    it('should allow retrying failed requests', async () => {
      const user = userEvent.setup()

      // Mock initial failure
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText(/erro ao carregar log de auditoria/i)).toBeInTheDocument()
      })

      // Mock successful retry
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          logs: mockAuditLogs,
          total: mockAuditLogs.length,
          page: 1,
          per_page: 20
        })
      } as Response)

      // Click retry
      const retryButton = screen.getByRole('button', { name: /tentar novamente/i })
      await user.click(retryButton)

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })
    })
  })

  describe('Embedded Mode', () => {
    it('should render in embedded mode when embedded prop is true', async () => {
      // Mock authentication API
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ user: mockAdminUser })
      } as Response)
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          logs: mockAuditLogs.slice(0, 3), // Limited for embedded view
          total: mockAuditLogs.length,
          page: 1,
          per_page: 5
        })
      } as Response)

      render(
        <TestWrapper>
          <PermissionAuditLog embedded />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Atividade Recente')).toBeInTheDocument()
      })

      // Should show limited entries
      expect(screen.getAllByTestId(/audit-entry-/)).toHaveLength(3)

      // Should show "Ver Todos" link
      expect(screen.getByRole('link', { name: /ver todos os logs/i })).toBeInTheDocument()
    })

    it('should hide filters and export in embedded mode', async () => {
      // Mock authentication API
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ user: mockAdminUser })
      } as Response)
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          logs: mockAuditLogs.slice(0, 3),
          total: mockAuditLogs.length,
          page: 1,
          per_page: 5
        })
      } as Response)

      render(
        <TestWrapper>
          <PermissionAuditLog embedded />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Atividade Recente')).toBeInTheDocument()
      })

      // Should not show filter controls
      expect(screen.queryByPlaceholderText(/buscar por usuário/i)).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /exportar/i })).not.toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    beforeEach(() => {
      // Mock authentication and audit logs APIs for accessibility tests
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ user: mockAdminUser })
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            logs: mockAuditLogs,
            total: mockAuditLogs.length,
            page: 1,
            per_page: 20
          })
        } as Response)
    })

    it('should have proper ARIA labels and structure', async () => {
      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /log de auditoria de permissões/i })).toBeInTheDocument()
      })

      // Should have proper regions
      expect(screen.getByRole('main')).toBeInTheDocument()
      expect(screen.getByRole('search')).toBeInTheDocument()

      // Should have proper table structure
      expect(screen.getByRole('table')).toBeInTheDocument()
      expect(screen.getAllByRole('row')).toHaveLength(mockAuditLogs.length + 1) // +1 for header
    })

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      // Should be able to tab through audit entries
      await user.tab()
      const firstEntry = screen.getAllByTestId(/audit-entry-/)[0]
      expect(firstEntry).toHaveFocus()

      await user.tab()
      const secondEntry = screen.getAllByTestId(/audit-entry-/)[1]
      expect(secondEntry).toHaveFocus()

      // Should be able to activate with Enter
      await user.keyboard('{Enter}')
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    it('should announce updates to screen readers', async () => {
      render(
        <TestWrapper>
          <PermissionAuditLog />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('João Silva')).toBeInTheDocument()
      })

      // Simulate new audit entry
      const newAuditLog = {
        audit_id: 'audit-announce',
        user_name: 'Announced User',
        action: 'PERMISSION_GRANTED'
      }

      window.dispatchEvent(new CustomEvent('audit-log-update', { 
        detail: { type: 'new_entry', log: newAuditLog } 
      }))

      await waitFor(() => {
        // Should have live region announcement
        expect(screen.getByRole('status')).toHaveTextContent(/nova entrada no log/i)
      })
    })
  })
})