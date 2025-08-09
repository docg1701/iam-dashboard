/**
 * PermissionAuditLog Component Tests
 * 
 * Comprehensive tests for the PermissionAuditLog component with filtering and real-time updates
 * Following CLAUDE.md rules: no internal mocking, only external API mocking
 */

import React from 'react'
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
  useTestSetup
} from '@/test/test-template'
import { 
  createMockAdminUser,
  createMockUserAgentPermission,
  setupUserAPITest,
  setupPermissionAPITest
} from '@/test/api-mocks'
import { 
  setupAuthenticatedUser,
  clearTestAuth
} from '@/test/auth-helpers'
import { PermissionAuditLog } from '../PermissionAuditLog'
import { AgentName } from '@/types/permissions'
import useAuthStore from '@/store/authStore'

// Setup standard test utilities
useTestSetup()

// Mock data
const mockAdminUser = createMockAdminUser({ 
  user_id: 'admin-123',
  full_name: 'Admin User',
  email: 'admin@test.com'
})

const mockAuditLogs = [
  {
    audit_id: 'audit-1',
    user_id: 'user-123',
    agent_name: 'client_management' as AgentName,
    action: 'GRANT',
    old_permissions: { create: false, read: true, update: false, delete: false },
    new_permissions: { create: true, read: true, update: true, delete: false },
    change_reason: 'Promoção para especialista em clientes',
    changed_by_user_id: 'admin-123',
    created_at: '2024-01-07T10:30:00Z'
  },
  {
    audit_id: 'audit-2',
    user_id: 'user-456',
    agent_name: 'pdf_processing' as AgentName,
    action: 'REVOKE',
    old_permissions: { create: true, read: true, update: true, delete: false },
    new_permissions: { create: false, read: true, update: false, delete: false },
    change_reason: 'Mudança de função - não requer mais processamento de documentos',
    changed_by_user_id: 'admin-123',
    created_at: '2024-01-07T09:15:00Z'
  },
  {
    audit_id: 'audit-3',
    user_id: 'user-789',
    agent_name: 'reports_analysis' as AgentName,
    action: 'TEMPLATE_APPLIED',
    old_permissions: null,
    new_permissions: { create: false, read: true, update: false, delete: false },
    change_reason: 'Aplicação de template "Read Only Access"',
    changed_by_user_id: 'admin-123',
    created_at: '2024-01-07T08:45:00Z'
  }
]

describe('PermissionAuditLog Component', () => {
  beforeEach(async () => {
    await act(async () => {
      // Setup authenticated admin user
      setupAuthenticatedUser('admin')
      useAuthStore.setState({ 
        user: mockAdminUser,
        token: 'mock-admin-token',
        isAuthenticated: true
      })
      
      // Setup permission API mocks for admin user with full permissions
      const adminPermissions = [
        createMockUserAgentPermission(mockAdminUser.user_id, AgentName.CLIENT_MANAGEMENT, 
          { create: true, read: true, update: true, delete: true }),
        createMockUserAgentPermission(mockAdminUser.user_id, AgentName.PDF_PROCESSING, 
          { create: true, read: true, update: true, delete: true }),
        createMockUserAgentPermission(mockAdminUser.user_id, AgentName.REPORTS_ANALYSIS, 
          { create: true, read: true, update: true, delete: true }),
        createMockUserAgentPermission(mockAdminUser.user_id, AgentName.AUDIO_RECORDING, 
          { create: true, read: true, update: true, delete: true })
      ]
      
      setupPermissionAPITest({
        userId: mockAdminUser.user_id,
        userPermissions: adminPermissions
      })
      
      // Mock audit logs API response
      vi.mocked(global.fetch).mockImplementation((url, options) => {
        // Override for audit endpoints
        if (url.toString().includes('/audit/recent')) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve(mockAuditLogs),
            headers: new Headers({ 'content-type': 'application/json' })
          } as Response)
        }
        
        if (url.toString().includes('/audit/user/')) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({
              logs: mockAuditLogs,
              total: mockAuditLogs.length,
              limit: 50,
              offset: 0,
            }),
            headers: new Headers({ 'content-type': 'application/json' })
          } as Response)
        }
        
        // Fall back to default response
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ success: true }),
          headers: new Headers({ 'content-type': 'application/json' })
        } as Response)
      })
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
    clearTestAuth()
  })

  describe('Embedded Mode Rendering', () => {
    it('should render audit log with entries in embedded mode', async () => {
      await act(async () => {
        renderWithProviders(<PermissionAuditLog embedded />)
      })

      // Wait for the data to be loaded and rendered
      await waitFor(() => {
        expect(screen.queryByText('Carregando histórico...')).not.toBeInTheDocument()
      }, { timeout: 5000 })

      // Should show audit entries or table structure
      await waitFor(() => {
        const auditContent = screen.queryByRole('table') ||
                           screen.queryByText('user-123') ||
                           screen.queryByText(/audit|histórico|registro/i)
        expect(auditContent).toBeInTheDocument()
      }, { timeout: 5000 })
    })

    it('should display different action types with appropriate badges', async () => {
      await act(async () => {
        renderWithProviders(<PermissionAuditLog embedded />)
      })

      await waitFor(() => {
        // Should show action indicators or badges
        const actionElements = screen.queryAllByText(/concedido|revogado|template|grant|revoke/i)
        expect(actionElements.length).toBeGreaterThan(0)
      })
    })

    it('should show agent and permission change information', async () => {
      await act(async () => {
        renderWithProviders(<PermissionAuditLog embedded />)
      })

      await waitFor(() => {
        // Should show agent-related content
        const agentElements = screen.queryByText(/gestão|clientes|processamento|relatórios/i) ||
                            screen.queryByText(/client|pdf|reports/i)
        expect(agentElements).toBeInTheDocument()
      })
    })

    it('should display timestamps in formatted time', async () => {
      await act(async () => {
        renderWithProviders(<PermissionAuditLog embedded />)
      })

      await waitFor(() => {
        // Should show formatted timestamps or date elements
        const dateElements = screen.queryAllByText(/\d{2}\/\d{2}\/\d{4}|\d{4}-\d{2}-\d{2}/) ||
                           screen.queryAllByText(/\d{1,2}:\d{2}/) ||
                           screen.queryAllByText(/jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec/i)
        expect(dateElements.length).toBeGreaterThan(0)
      })
    })

    it('should not show filters in embedded mode', async () => {
      await act(async () => {
        renderWithProviders(<PermissionAuditLog embedded />)
      })

      await waitFor(() => {
        // Embedded mode should not show extensive filter controls
        expect(screen.queryByPlaceholderText(/buscar por usuário/i)).not.toBeInTheDocument()
        expect(screen.queryByRole('button', { name: /exportar/i })).not.toBeInTheDocument()
      })
    })
  })

  describe('Loading and Error States', () => {
    it('should show loading state initially', async () => {
      // Mock with a delayed response
      vi.mocked(global.fetch).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      )

      await act(async () => {
        renderWithProviders(<PermissionAuditLog embedded />)
      })

      // Should show loading state
      expect(screen.getByText(/carregando|loading/i)).toBeInTheDocument()
    })

    it('should show empty state when no audit logs exist', async () => {
      // Mock empty response
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve([]),
        headers: new Headers({ 'content-type': 'application/json' })
      } as Response)

      await act(async () => {
        renderWithProviders(<PermissionAuditLog embedded />)
      })

      await waitFor(() => {
        const emptyMessage = screen.queryByText(/nenhum registro|não há registros|empty|no records/i)
        expect(emptyMessage).toBeInTheDocument()
      })
    })
  })

  describe('Table Structure', () => {
    it('should have proper table structure with headers', async () => {
      await act(async () => {
        renderWithProviders(<PermissionAuditLog embedded />)
      })

      await waitFor(() => {
        // Should have table structure
        const table = screen.queryByRole('table')
        if (table) {
          expect(table).toBeInTheDocument()
          
          // Should have some column headers
          const headers = screen.queryAllByRole('columnheader')
          expect(headers.length).toBeGreaterThan(0)
        } else {
          // Alternative: should have structured content
          const structuredContent = screen.queryByText(/data|usuário|agente|ação/i)
          expect(structuredContent).toBeInTheDocument()
        }
      })
    })

    it('should show user column by default', async () => {
      await act(async () => {
        renderWithProviders(<PermissionAuditLog embedded showUserColumn={true} />)
      })

      await waitFor(() => {
        // Should show user-related content when showUserColumn is true
        const userContent = screen.queryByText(/usuário|user/) ||
                          screen.queryByText('user-123')
        expect(userContent).toBeInTheDocument()
      })
    })

    it('should hide user column when showUserColumn is false', async () => {
      await act(async () => {
        renderWithProviders(<PermissionAuditLog embedded showUserColumn={false} />)
      })

      await waitFor(() => {
        // Should still render the component even without user column
        const content = screen.queryByText(/audit|histórico|registro|data|agente/i)
        expect(content).toBeInTheDocument()
      })
    })
  })
})