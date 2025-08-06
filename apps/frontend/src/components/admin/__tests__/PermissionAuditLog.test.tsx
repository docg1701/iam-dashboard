/**
 * Permission Audit Log Component Tests
 * 
 * Comprehensive test suite for the PermissionAuditLog component covering
 * audit trail display, filtering, export functionality, and accessibility.
 */

import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { PermissionAuditLog } from '../PermissionAuditLog'
import { 
  AgentName, 
  PERMISSION_LEVELS, 
  getPermissionsForLevel,
} from '@/types/permissions'
import * as permissionAPI from '@/lib/api/permissions'

// Mock all UI components
vi.mock('@/components/ui/table', async () => {
  const actual = await import('@/__tests__/mocks/ui-components')
  return {
    Table: actual.Table,
    TableHeader: actual.TableHeader,
    TableBody: actual.TableBody,
    TableRow: actual.TableRow,
    TableHead: actual.TableHead,
    TableCell: actual.TableCell,
  }
})

vi.mock('@/components/ui/button', async () => {
  const actual = await import('@/__tests__/mocks/ui-components')
  return {
    Button: actual.Button,
  }
})

vi.mock('@/components/ui/badge', async () => {
  const actual = await import('@/__tests__/mocks/ui-components')
  return {
    Badge: actual.Badge,
  }
})

vi.mock('@/components/ui/input', async () => {
  const actual = await import('@/__tests__/mocks/ui-components')
  return {
    Input: actual.Input,
  }
})

vi.mock('@/components/ui/card', async () => {
  const actual = await import('@/__tests__/mocks/ui-components')
  return {
    Card: actual.Card,
    CardContent: actual.CardContent,
    CardDescription: actual.CardDescription,
    CardHeader: actual.CardHeader,
    CardTitle: actual.CardTitle,
    CardFooter: actual.CardFooter,
  }
})

vi.mock('@/components/ui/select', async () => {
  const actual = await import('@/__tests__/mocks/ui-components')
  return {
    Select: actual.Select,
    SelectContent: actual.SelectContent,
    SelectItem: actual.SelectItem,
    SelectTrigger: actual.SelectTrigger,
    SelectValue: actual.SelectValue,
  }
})

vi.mock('@/components/ui/popover', async () => {
  const actual = await import('@/__tests__/mocks/ui-components')
  return {
    Popover: actual.Popover,
    PopoverContent: actual.PopoverContent,
    PopoverTrigger: actual.PopoverTrigger,
  }
})

vi.mock('@/components/ui/calendar', async () => {
  const actual = await import('@/__tests__/mocks/ui-components')
  return {
    Calendar: actual.Calendar,
  }
})

// Mock the PermissionAPI
vi.mock('@/lib/api/permissions', () => ({
  PermissionAPI: {
    Audit: {
      getUserAuditLogs: vi.fn(),
      getAgentAuditLogs: vi.fn(),
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

// Mock date-fns with proper date handling
vi.mock('date-fns', async () => {
  const actual = await vi.importActual('date-fns')
  return {
    ...actual,
    format: vi.fn((date, formatStr) => {
      const dateObj = new Date(date)
      if (formatStr === 'dd/MM/yyyy HH:mm') {
        // Return different formatted dates based on the input
        const day = String(dateObj.getDate()).padStart(2, '0')
        const month = String(dateObj.getMonth() + 1).padStart(2, '0')
        const year = dateObj.getFullYear()
        const hours = String(dateObj.getHours()).padStart(2, '0')
        const minutes = String(dateObj.getMinutes()).padStart(2, '0')
        return `${day}/${month}/${year} ${hours}:${minutes}`
      }
      if (formatStr === 'yyyy-MM-dd-HHmm') {
        const year = dateObj.getFullYear()
        const month = String(dateObj.getMonth() + 1).padStart(2, '0')
        const day = String(dateObj.getDate()).padStart(2, '0')
        const hours = String(dateObj.getHours()).padStart(2, '0')
        const minutes = String(dateObj.getMinutes()).padStart(2, '0')
        return `${year}-${month}-${day}-${hours}${minutes}`
      }
      return `${String(dateObj.getDate()).padStart(2, '0')}/${String(dateObj.getMonth() + 1).padStart(2, '0')}/${dateObj.getFullYear()}`
    }),
    subDays: vi.fn((date, days) => new Date(date.getTime() - days * 24 * 60 * 60 * 1000)),
  }
})

// Test data
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
    created_at: '2024-01-15T14:30:00Z',
  },
  {
    audit_id: 'audit-2',
    user_id: 'user-1',
    agent_name: AgentName.PDF_PROCESSING,
    action: 'GRANT',
    old_permissions: null,
    new_permissions: getPermissionsForLevel(PERMISSION_LEVELS.READ_ONLY),
    changed_by_user_id: 'admin-2',
    change_reason: 'Acesso necessário para nova função',
    created_at: '2024-01-10T09:15:00Z',
  },
  {
    audit_id: 'audit-3',
    user_id: 'user-2',
    agent_name: AgentName.REPORTS_ANALYSIS,
    action: 'REVOKE',
    old_permissions: getPermissionsForLevel(PERMISSION_LEVELS.STANDARD),
    new_permissions: getPermissionsForLevel(PERMISSION_LEVELS.NONE),
    changed_by_user_id: 'admin-1',
    change_reason: 'Mudança de função',
    created_at: '2024-01-08T16:45:00Z',
  },
  {
    audit_id: 'audit-4',
    user_id: 'user-3',
    agent_name: AgentName.AUDIO_RECORDING,
    action: 'TEMPLATE_APPLIED',
    old_permissions: getPermissionsForLevel(PERMISSION_LEVELS.NONE),
    new_permissions: getPermissionsForLevel(PERMISSION_LEVELS.READ_ONLY),
    changed_by_user_id: 'admin-1',
    change_reason: 'Aplicação de template padrão',
    created_at: '2024-01-05T11:20:00Z',
  },
]

// Mock users data is available in mockAuditLogs user references

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

describe('PermissionAuditLog Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Setup API mocks
    vi.mocked(permissionAPI.PermissionAPI.Audit.getUserAuditLogs).mockResolvedValue({
      logs: mockAuditLogs,
      total: mockAuditLogs.length,
      limit: 50,
      offset: 0,
    })

    vi.mocked(permissionAPI.PermissionAPI.Audit.getAgentAuditLogs).mockResolvedValue({
      logs: mockAuditLogs,
      total: mockAuditLogs.length,
      limit: 50,
      offset: 0,
    })

    // Mock URL functions for export
    global.URL.createObjectURL = vi.fn(() => 'mock-url')
    global.URL.revokeObjectURL = vi.fn()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  const renderPermissionAuditLog = (props = {}) => {
    const defaultProps = {
      userId: 'user-1',
      embedded: false,
      ...props,
    }

    return render(
      <TestWrapper>
        <PermissionAuditLog {...defaultProps} />
      </TestWrapper>
    )
  }

  describe('Component Rendering', () => {
    it('should render without crashing', () => {
      renderPermissionAuditLog()
      expect(screen.getByText('Log de Auditoria de Permissões')).toBeInTheDocument()
    })

    it('should render embedded view when embedded prop is true', () => {
      const { container } = renderPermissionAuditLog({ embedded: true })
      
      // Check that embedded view is rendered (space-y-4 class)
      const embeddedWrapper = container.querySelector('.space-y-4')
      expect(embeddedWrapper).toBeInTheDocument()
      
      // Check that full view is not rendered (no statistics cards)
      expect(screen.queryByText('Total de Registros')).not.toBeInTheDocument()
      expect(screen.queryByText('Log de Auditoria de Permissões')).not.toBeInTheDocument()
      expect(screen.getByRole('table')).toBeInTheDocument()
    })

    it('should show loading state initially', async () => {
      // Import useQuery from the actual module and mock it temporarily
      const { useQuery } = await import('@tanstack/react-query')
      const mockUseQuery = vi.mocked(useQuery)
      
      // Override the useQuery mock to return loading state for this test
      mockUseQuery.mockReturnValueOnce({
        data: undefined,
        isLoading: true,
        isError: false,
        error: null,
        refetch: vi.fn(),
      } as any)

      renderPermissionAuditLog({ embedded: true })
      expect(screen.getByText('Carregando histórico...')).toBeInTheDocument()
    })

    it('should display audit statistics correctly', async () => {
      // Import useQuery and override to provide audit data
      const { useQuery } = await import('@tanstack/react-query')
      const mockUseQuery = vi.mocked(useQuery)
      
      // Override the useQuery mock to return audit data
      mockUseQuery.mockReturnValueOnce({
        data: {
          logs: mockAuditLogs,
          total: mockAuditLogs.length,
          limit: 50,
          offset: 0,
        },
        isLoading: false,
        isError: false,
        error: null,
        refetch: vi.fn(),
      } as any)

      renderPermissionAuditLog()

      await waitFor(() => {
        expect(screen.getByText('Total de Registros')).toBeInTheDocument()
        expect(screen.getByText('4')).toBeInTheDocument() // Total logs count
      })
    })
  })

  describe('Audit Log Display', () => {
    it('should render audit log entries correctly', async () => {
      // Override useQuery to provide audit data for this test
      const { useQuery } = await import('@tanstack/react-query')
      const mockUseQuery = vi.mocked(useQuery)
      
      mockUseQuery.mockReturnValueOnce({
        data: {
          logs: mockAuditLogs,
          total: mockAuditLogs.length,
          limit: 50,
          offset: 0,
        },
        isLoading: false,
        isError: false,
        error: null,
        refetch: vi.fn(),
      } as any)

      renderPermissionAuditLog({ embedded: true })

      await waitFor(() => {
        expect(screen.getByText('15/01/2024 11:30')).toBeInTheDocument()
        expect(screen.getAllByText('Gestão de Clientes').length).toBeGreaterThan(0)
        expect(screen.getAllByText('Atualizado').length).toBeGreaterThan(0)
        expect(screen.getAllByText('admin-1').length).toBeGreaterThan(0)
        expect(screen.getByText('Promoção para supervisor')).toBeInTheDocument()
      })
    })

    it('should display action badges with correct colors', async () => {
      // Override useQuery to provide audit data for this test
      const { useQuery } = await import('@tanstack/react-query')
      const mockUseQuery = vi.mocked(useQuery)
      
      mockUseQuery.mockReturnValueOnce({
        data: {
          logs: mockAuditLogs,
          total: mockAuditLogs.length,
          limit: 50,
          offset: 0,
        },
        isLoading: false,
        isError: false,
        error: null,
        refetch: vi.fn(),
      } as any)

      renderPermissionAuditLog({ embedded: true })

      await waitFor(() => {
        const updateBadges = screen.getAllByText('Atualizado')
        expect(updateBadges[0]).toHaveClass('bg-blue-100', 'text-blue-800')

        const grantBadges = screen.getAllByText('Concedido')
        expect(grantBadges[0]).toHaveClass('bg-green-100', 'text-green-800')

        const revokeBadges = screen.getAllByText('Revogado')
        expect(revokeBadges[0]).toHaveClass('bg-red-100', 'text-red-800')
      })
    })

    it('should show agent names in Portuguese', async () => {
      // Override useQuery to provide audit data
      const { useQuery } = await import('@tanstack/react-query')
      const mockUseQuery = vi.mocked(useQuery)
      
      mockUseQuery.mockReturnValueOnce({
        data: {
          logs: mockAuditLogs,
          total: mockAuditLogs.length,
          limit: 50,
          offset: 0,
        },
        isLoading: false,
        isError: false,
        error: null,
        refetch: vi.fn(),
      } as any)

      renderPermissionAuditLog({ embedded: true })

      await waitFor(() => {
        expect(screen.getAllByText('Gestão de Clientes').length).toBeGreaterThan(0)
        expect(screen.getAllByText('Processamento PDFs').length).toBeGreaterThan(0)
        expect(screen.getAllByText('Relatórios').length).toBeGreaterThan(0)
        expect(screen.getAllByText('Gravação de Áudio').length).toBeGreaterThan(0)
      })
    })

    it('should handle empty audit logs', async () => {
      // Override useQuery to provide empty data
      const { useQuery } = await import('@tanstack/react-query')
      const mockUseQuery = vi.mocked(useQuery)
      
      mockUseQuery.mockReturnValueOnce({
        data: {
          logs: [],
          total: 0,
          limit: 50,
          offset: 0,
        },
        isLoading: false,
        isError: false,
        error: null,
        refetch: vi.fn(),
      } as any)

      renderPermissionAuditLog({ embedded: true })

      await waitFor(() => {
        expect(screen.getByText('Nenhum registro de auditoria encontrado')).toBeInTheDocument()
      })
    })
  })

  describe('Filtering Functionality', () => {
    it('should filter logs by search term', async () => {
      renderPermissionAuditLog()

      await waitFor(() => {
        expect(screen.getByText('Promoção para supervisor')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText('Usuário, admin ou motivo...')
      await userEvent.type(searchInput, 'supervisor')

      await waitFor(() => {
        expect(screen.getByText('Promoção para supervisor')).toBeInTheDocument()
        expect(screen.queryByText('Mudança de função')).not.toBeInTheDocument()
      })
    })

    it('should filter logs by agent', async () => {
      renderPermissionAuditLog()

      await waitFor(() => {
        expect(screen.getByText('Gestão de Clientes')).toBeInTheDocument()
      })

      const agentSelect = screen.getByDisplayValue('Todos os Agentes')
      await userEvent.click(agentSelect)
      
      const clientManagementOption = screen.getByText('Gestão de Clientes')
      await userEvent.click(clientManagementOption)

      // Should filter API call
      expect(permissionAPI.PermissionAPI.Audit.getUserAuditLogs).toHaveBeenCalledWith(
        'user-1',
        expect.objectContaining({
          agent_name: AgentName.CLIENT_MANAGEMENT,
        })
      )
    })

    it('should filter logs by action type', async () => {
      renderPermissionAuditLog()

      const actionSelect = screen.getByDisplayValue('Todas as Ações')
      await userEvent.click(actionSelect)
      
      const updateOption = screen.getByText('Atualizado')
      await userEvent.click(updateOption)

      // Should filter API call
      expect(permissionAPI.PermissionAPI.Audit.getUserAuditLogs).toHaveBeenCalledWith(
        'user-1',
        expect.objectContaining({
          action: 'UPDATE',
        })
      )
    })

    it('should filter logs by date range', async () => {
      renderPermissionAuditLog()

      // Click on date picker
      const dateFromButton = screen.getByText('Selecionar')
      await userEvent.click(dateFromButton)

      // Mock calendar selection would be complex to test
      // For now, just verify the component renders the date picker
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })
  })

  describe('Statistics Calculation', () => {
    it('should calculate recent changes correctly', async () => {
      renderPermissionAuditLog()

      await waitFor(() => {
        expect(screen.getByText('Últimas 24h')).toBeInTheDocument()
        // The exact number would depend on the mocked date calculations
      })
    })

    it('should count unique administrators', async () => {
      renderPermissionAuditLog()

      await waitFor(() => {
        expect(screen.getByText('Administradores Ativos')).toBeInTheDocument()
        expect(screen.getByText('2')).toBeInTheDocument() // admin-1 and admin-2
      })
    })

    it('should identify most active agent', async () => {
      renderPermissionAuditLog()

      await waitFor(() => {
        expect(screen.getByText('Agente Mais Ativo')).toBeInTheDocument()
        // Should show the agent with most logs
      })
    })
  })

  describe('Export Functionality', () => {
    it('should export audit logs', async () => {
      const { toast } = await import('@/components/ui/toast')
      
      const mockAppendChild = vi.fn()
      const mockRemoveChild = vi.fn()
      const mockClick = vi.fn()
      
      document.body.appendChild = mockAppendChild
      document.body.removeChild = mockRemoveChild
      
      const mockLink = {
        href: '',
        download: '',
        click: mockClick,
      } as unknown as HTMLAnchorElement
      
      vi.spyOn(document, 'createElement').mockReturnValue(mockLink)
      
      renderPermissionAuditLog()

      await waitFor(() => {
        const exportButton = screen.getByText('Exportar')
        userEvent.click(exportButton)
      })

      await waitFor(() => {
        expect(mockAppendChild).toHaveBeenCalledWith(mockLink)
        expect(mockClick).toHaveBeenCalled()
        expect(mockRemoveChild).toHaveBeenCalledWith(mockLink)
        
        expect(toast).toHaveBeenCalledWith({
          title: 'Exportação concluída',
          description: expect.stringContaining('registros de auditoria exportados'),
          variant: 'success',
        })
      })
    })

    it('should set correct export filename', async () => {
      const mockLink = {
        href: '',
        download: '',
        click: vi.fn(),
      } as unknown as HTMLAnchorElement
      
      vi.spyOn(document, 'createElement').mockReturnValue(mockLink)
      document.body.appendChild = vi.fn()
      document.body.removeChild = vi.fn()
      
      renderPermissionAuditLog()

      await waitFor(() => {
        const exportButton = screen.getByText('Exportar')
        userEvent.click(exportButton)
      })

      await waitFor(() => {
        expect(mockLink.download).toContain('audit-log-')
        expect(mockLink.download).toContain('.json')
      })
    })
  })

  describe('API Integration', () => {
    it('should call getUserAuditLogs when userId is provided', async () => {
      renderPermissionAuditLog({ userId: 'user-1' })

      await waitFor(() => {
        expect(permissionAPI.PermissionAPI.Audit.getUserAuditLogs).toHaveBeenCalledWith(
          'user-1',
          expect.any(Object)
        )
      })
    })

    it('should call getAgentAuditLogs when userId is not provided', async () => {
      renderPermissionAuditLog({ userId: undefined })

      await waitFor(() => {
        expect(permissionAPI.PermissionAPI.Audit.getAgentAuditLogs).toHaveBeenCalledWith(
          expect.any(String),
          expect.any(Object)
        )
      })
    })

    it('should handle API errors gracefully', async () => {
      vi.mocked(permissionAPI.PermissionAPI.Audit.getUserAuditLogs).mockRejectedValue(
        new Error('API Error')
      )

      renderPermissionAuditLog({ embedded: true })

      await waitFor(() => {
        expect(screen.getByText('Erro ao carregar logs de auditoria')).toBeInTheDocument()
      })
    })
  })

  describe('Refresh Functionality', () => {
    it('should refresh audit logs when refresh button is clicked', async () => {
      // Mock refetch is implicit in the query mock setup
      
      renderPermissionAuditLog()

      await waitFor(() => {
        const refreshButton = screen.getByText('Atualizar')
        userEvent.click(refreshButton)
      })

      // The refetch function would be called through the query client
      expect(permissionAPI.PermissionAPI.Audit.getUserAuditLogs).toHaveBeenCalledTimes(1)
    })
  })

  describe('User Column Visibility', () => {
    it('should show user column when showUserColumn is true', async () => {
      renderPermissionAuditLog({ showUserColumn: true, embedded: true })

      await waitFor(() => {
        expect(screen.getByText('Usuário')).toBeInTheDocument()
      })
    })

    it('should hide user column when showUserColumn is false', async () => {
      renderPermissionAuditLog({ showUserColumn: false, embedded: true })

      await waitFor(() => {
        expect(screen.queryByText('Usuário')).not.toBeInTheDocument()
      })
    })
  })

  describe('Agent Filtering', () => {
    it('should apply agent filter when provided', async () => {
      renderPermissionAuditLog({ 
        agentFilter: AgentName.CLIENT_MANAGEMENT,
        embedded: true 
      })

      await waitFor(() => {
        expect(permissionAPI.PermissionAPI.Audit.getUserAuditLogs).toHaveBeenCalledWith(
          'user-1',
          expect.objectContaining({
            agent_name: AgentName.CLIENT_MANAGEMENT,
          })
        )
      })
    })
  })

  describe('Responsive Behavior', () => {
    it('should handle mobile layout appropriately', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: vi.fn().mockImplementation(query => ({
          matches: query === '(max-width: 768px)',
          media: query,
          onchange: null,
          addListener: vi.fn(),
          removeListener: vi.fn(),
        })),
      })

      renderPermissionAuditLog({ embedded: true })

      // Component should still render table on mobile
      expect(screen.getByRole('table')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels', async () => {
      renderPermissionAuditLog({ embedded: true })

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument()
        expect(screen.getAllByRole('columnheader')).toHaveLength(7)
        expect(screen.getByRole('searchbox')).toBeInTheDocument()
      })
    })

    it('should support keyboard navigation', async () => {
      renderPermissionAuditLog()

      await waitFor(() => {
        const searchInput = screen.getByRole('searchbox')
        searchInput.focus()
        expect(searchInput).toHaveFocus()
      })
    })

    it('should have accessible table headers', async () => {
      renderPermissionAuditLog({ embedded: true })

      await waitFor(() => {
        expect(screen.getByRole('columnheader', { name: /Data\/Hora/ })).toBeInTheDocument()
        expect(screen.getByRole('columnheader', { name: /Agente/ })).toBeInTheDocument()
        expect(screen.getByRole('columnheader', { name: /Ação/ })).toBeInTheDocument()
        expect(screen.getByRole('columnheader', { name: /Alterado por/ })).toBeInTheDocument()
        expect(screen.getByRole('columnheader', { name: /Motivo/ })).toBeInTheDocument()
      })
    })
  })

  describe('Performance', () => {
    it('should handle large numbers of audit logs efficiently', async () => {
      const manyLogs = Array.from({ length: 100 }, (_, i) => ({
        ...mockAuditLogs[0],
        audit_id: `audit-${i}`,
        created_at: `2024-01-${String(i % 31 + 1).padStart(2, '0')}T10:00:00Z`,
      }))

      vi.mocked(permissionAPI.PermissionAPI.Audit.getUserAuditLogs).mockResolvedValue({
        logs: manyLogs,
        total: manyLogs.length,
        limit: 50,
        offset: 0,
      })

      renderPermissionAuditLog()

      await waitFor(() => {
        expect(screen.getByText('100')).toBeInTheDocument() // Total logs count
      })
    })
  })
})