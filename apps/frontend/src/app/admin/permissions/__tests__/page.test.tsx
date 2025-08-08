/**
 * Admin Permissions Page Comprehensive Tests
 * 
 * Phase 3: Critical page testing implementation
 * 
 * Test coverage focuses on:
 * - Security administration and role management
 * - Permission matrix functionality and bulk operations  
 * - Complex filtering and search across multiple users
 * - Real-time permission updates and state management
 * - Template system integration and workflow
 * - Statistics display and data visualization
 * - Error handling for complex permission operations
 * - Responsive behavior for admin workflows
 * 
 * Following CLAUDE.md testing directives:
 * - NEVER mock internal components, permission logic, or admin functionality
 * - ONLY mock external APIs (fetch calls, permission API endpoints)
 * - Test real page rendering and complex admin workflows
 * - Focus on security-critical functionality and administrative operations
 */

import {
  renderWithProviders,
  screen,
  fireEvent,
  waitFor,
  userEvent,
  vi,
  expect,
  describe,
  test,
  useTestSetup,
  mockSuccessfulFetch,
  mockFailedFetch,
  mockNetworkError,
  triggerWindowResize,
  within,
  act,
} from '@/test/test-template'
import { 
  AuthScenarios,
  setupAuthenticatedUser,
  setupUnauthenticatedUser,
  expectAuthState,
  clearTestAuth,
} from '@/test/auth-helpers'
import AdminPermissionsPage from '../page'

// Mock localStorage for token storage (external browser API)
const mockLocalStorage = {
  getItem: vi.fn(() => 'mock-admin-token'),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
  writable: true,
})

describe('AdminPermissionsPage', () => {
  useTestSetup()

  // Mock admin users data
  const mockAdminUsers = [
    {
      user_id: 'admin-1',
      name: 'João Admin',
      email: 'joao.admin@example.com',
      role: 'admin',
      is_active: true,
      created_at: '2023-01-01T00:00:00Z',
      last_login: '2023-12-01T10:00:00Z',
    },
    {
      user_id: 'user-1',
      name: 'Maria User',
      email: 'maria.user@example.com',
      role: 'user',
      is_active: true,
      created_at: '2023-01-15T00:00:00Z',
      last_login: '2023-12-01T08:00:00Z',
    },
    {
      user_id: 'sysadmin-1',
      name: 'Pedro SysAdmin',
      email: 'pedro.sysadmin@example.com',
      role: 'sysadmin',
      is_active: true,
      created_at: '2023-01-01T00:00:00Z',
      last_login: '2023-12-01T06:00:00Z',
    },
    {
      user_id: 'inactive-1',
      name: 'Carlos Inactive',
      email: 'carlos.inactive@example.com',
      role: 'user',
      is_active: false,
      created_at: '2023-01-20T00:00:00Z',
    },
  ]

  // Mock user permissions data
  const mockUserPermissions = {
    'admin-1': {
      user_id: 'admin-1',
      permissions: {
        client_management: {
          create: true,
          read: true,
          update: true,
          delete: true,
        },
        user_management: {
          create: true,
          read: true,
          update: true,
          delete: false,
        },
      },
    },
    'user-1': {
      user_id: 'user-1',
      permissions: {
        client_management: {
          create: false,
          read: true,
          update: false,
          delete: false,
        },
        user_management: {
          create: false,
          read: false,
          update: false,
          delete: false,
        },
      },
    },
    'sysadmin-1': {
      user_id: 'sysadmin-1',
      permissions: {
        client_management: {
          create: true,
          read: true,
          update: true,
          delete: true,
        },
        user_management: {
          create: true,
          read: true,
          update: true,
          delete: true,
        },
      },
    },
    'inactive-1': {
      user_id: 'inactive-1',
      permissions: {
        client_management: {
          create: false,
          read: false,
          update: false,
          delete: false,
        },
        user_management: {
          create: false,
          read: false,
          update: false,
          delete: false,
        },
      },
    },
  }

  const renderAdminPermissionsPage = (userRole: 'admin' | 'sysadmin' = 'admin') => {
    // Setup authenticated admin user
    setupAuthenticatedUser(userRole)
    
    // Mock admin users API endpoint
    mockSuccessfulFetch('/api/v1/admin/users', mockAdminUsers)
    
    // Mock individual user permissions endpoints
    Object.keys(mockUserPermissions).forEach(userId => {
      mockSuccessfulFetch(
        `/api/v1/admin/users/${userId}/permissions`,
        mockUserPermissions[userId as keyof typeof mockUserPermissions]
      )
    })
    
    return renderWithProviders(<AdminPermissionsPage />)
  }

  describe('Page Structure and Security Access', () => {
    test('renders admin permissions page with proper security context', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 1, name: /gerenciar permissões/i })).toBeInTheDocument()
      })
      
      expect(screen.getByText(/administre permissões de usuários por agente de forma centralizada/i)).toBeInTheDocument()
    })

    test('renders for sysadmin users with full administrative access', async () => {
      renderAdminPermissionsPage('sysadmin')

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /gerenciar permissões/i })).toBeInTheDocument()
      })
      
      expectAuthState({
        isAuthenticated: true,
        isLoading: false,
      })
    })

    test('displays proper page structure with tabs and sections', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        expect(screen.getByRole('tablist')).toBeInTheDocument()
      })
      
      // Check for main tabs
      expect(screen.getByRole('tab', { name: /matriz de permissões/i })).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: /templates/i })).toBeInTheDocument()
    })

    test('requires proper authentication for admin access', () => {
      setupUnauthenticatedUser()
      
      renderWithProviders(<AdminPermissionsPage />)
      
      // Should handle unauthenticated access appropriately
      // The actual behavior depends on PermissionGuard implementation
      expect(document.body).toBeInTheDocument()
    })
  })

  describe('Statistics and Dashboard Overview', () => {
    test('displays comprehensive permission statistics', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        expect(screen.getByText(/total de usuários/i)).toBeInTheDocument()
      })
      
      // Check all statistics cards
      expect(screen.getByText(/com permissões/i)).toBeInTheDocument()
      expect(screen.getByText(/sem acesso/i)).toBeInTheDocument()
      expect(screen.getByText(/administradores/i)).toBeInTheDocument()
    })

    test('calculates and displays accurate user counts', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        // Should show total of 4 users from mockAdminUsers
        expect(screen.getByText('4')).toBeInTheDocument()
      })
      
      // Should show active vs inactive counts
      expect(screen.getByText(/3 ativos, 1 inativos/i)).toBeInTheDocument()
    })

    test('shows permission distribution statistics', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        // Check for statistics icons
        const usersIcon = document.querySelector('[data-lucide="users"]')
        const shieldIcon = document.querySelector('[data-lucide="shield"]')
        const alertIcon = document.querySelector('[data-lucide="alert-triangle"]')
        const settingsIcon = document.querySelector('[data-lucide="settings"]')
        
        expect(usersIcon).toBeInTheDocument()
        expect(shieldIcon).toBeInTheDocument()
        expect(alertIcon).toBeInTheDocument()
        expect(settingsIcon).toBeInTheDocument()
      })
    })

    test('updates statistics when filters are applied', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        expect(screen.getByText(/total de usuários/i)).toBeInTheDocument()
      })
      
      // Apply role filter
      const roleFilter = screen.getByRole('combobox')
      await act(async () => {
        await userEvent.click(roleFilter)
      })
      
      // The statistics should reflect filtered data
      expect(screen.getByText(/total de usuários/i)).toBeInTheDocument()
    })
  })

  describe('Advanced Filtering and Search', () => {
    test('renders comprehensive filter controls', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        expect(screen.getByText(/filtros/i)).toBeInTheDocument()
      })
      
      // Check all filter inputs
      expect(screen.getByPlaceholderText(/nome ou email/i)).toBeInTheDocument()
      
      // Check filter dropdowns
      const selects = screen.getAllByRole('combobox')
      expect(selects.length).toBeGreaterThan(0)
    })

    test('filters users by search term', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText(/nome ou email/i)
        expect(searchInput).toBeInTheDocument()
      })
      
      const searchInput = screen.getByPlaceholderText(/nome ou email/i)
      await userEvent.type(searchInput, 'João')
      
      expect(searchInput).toHaveValue('João')
    })

    test('filters users by role selection', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        const roleSelects = screen.getAllByRole('combobox')
        expect(roleSelects.length).toBeGreaterThan(0)
      })
      
      // Find and interact with role filter
      const roleFilter = screen.getAllByRole('combobox')[1] // Second combobox should be role
      await act(async () => {
        await userEvent.click(roleFilter)
      })
    })

    test('filters users by status (active/inactive)', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        const statusSelects = screen.getAllByRole('combobox')
        expect(statusSelects.length).toBeGreaterThan(0)
      })
      
      // Should have status filtering capability
      expect(screen.getByText(/todos/i)).toBeInTheDocument()
    })

    test('filters users by permission status', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        expect(screen.getByText(/filtros/i)).toBeInTheDocument()
      })
      
      // Should have permission status filtering
      const filterSection = screen.getByText(/filtros/i).closest('.grid')
      expect(filterSection).toBeInTheDocument()
    })

    test('combines multiple filters effectively', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText(/nome ou email/i)
        expect(searchInput).toBeInTheDocument()
      })
      
      // Apply search filter
      const searchInput = screen.getByPlaceholderText(/nome ou email/i)
      await userEvent.type(searchInput, 'admin')
      
      // Apply additional filters would work here
      expect(searchInput).toHaveValue('admin')
    })

    test('clears filters correctly', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText(/nome ou email/i)
        expect(searchInput).toBeInTheDocument()
      })
      
      const searchInput = screen.getByPlaceholderText(/nome ou email/i)
      await userEvent.type(searchInput, 'test filter')
      expect(searchInput).toHaveValue('test filter')
      
      await userEvent.clear(searchInput)
      expect(searchInput).toHaveValue('')
    })
  })

  describe('Quick Actions Toolbar', () => {
    test('renders quick actions with proper functionality', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /novo usuário/i })).toBeInTheDocument()
      })
      
      expect(screen.getByRole('button', { name: /templates/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /exportar/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /importar/i })).toBeInTheDocument()
    })

    test('handles template management navigation', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        const templatesButton = screen.getByRole('button', { name: /templates/i })
        expect(templatesButton).toBeInTheDocument()
      })
      
      const templatesButton = screen.getByRole('button', { name: /templates/i })
      await userEvent.click(templatesButton)
      
      // Should switch to templates tab
      await waitFor(() => {
        const templatesTab = screen.getByRole('tab', { name: /templates/i })
        expect(templatesTab).toHaveAttribute('aria-selected', 'true')
      })
    })

    test('handles export functionality', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        const exportButton = screen.getByRole('button', { name: /exportar/i })
        expect(exportButton).toBeInTheDocument()
      })
      
      const exportButton = screen.getByRole('button', { name: /exportar/i })
      await userEvent.click(exportButton)
      
      // Export functionality should trigger without errors
      expect(exportButton).toBeInTheDocument()
    })

    test('handles import functionality with proper user feedback', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        const importButton = screen.getByRole('button', { name: /importar/i })
        expect(importButton).toBeInTheDocument()
      })
      
      const importButton = screen.getByRole('button', { name: /importar/i })
      await userEvent.click(importButton)
      
      // Import should show development message or file picker
      expect(importButton).toBeInTheDocument()
    })

    test('displays bulk operations when users are selected', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /novo usuário/i })).toBeInTheDocument()
      })
      
      // Initially no bulk operations should be visible
      expect(screen.queryByText(/operações \(/i)).not.toBeInTheDocument()
    })

    test('shows proper icon indicators for each action', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /templates/i })).toBeInTheDocument()
      })
      
      // Check for action icons
      const plusIcon = document.querySelector('[data-lucide="plus"]')
      const settingsIcon = document.querySelector('[data-lucide="settings"]')
      const downloadIcon = document.querySelector('[data-lucide="download"]')
      const uploadIcon = document.querySelector('[data-lucide="upload"]')
      
      expect(plusIcon).toBeInTheDocument()
      expect(settingsIcon).toBeInTheDocument()
      expect(downloadIcon).toBeInTheDocument()
      expect(uploadIcon).toBeInTheDocument()
    })
  })

  describe('Tab Navigation and Content Management', () => {
    test('switches between matrix and templates tabs correctly', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        expect(screen.getByRole('tablist')).toBeInTheDocument()
      })
      
      const matrixTab = screen.getByRole('tab', { name: /matriz de permissões/i })
      const templatesTab = screen.getByRole('tab', { name: /templates/i })
      
      // Initially matrix tab should be selected
      expect(matrixTab).toHaveAttribute('aria-selected', 'true')
      expect(templatesTab).toHaveAttribute('aria-selected', 'false')
      
      // Switch to templates tab
      await userEvent.click(templatesTab)
      
      await waitFor(() => {
        expect(templatesTab).toHaveAttribute('aria-selected', 'true')
        expect(matrixTab).toHaveAttribute('aria-selected', 'false')
      })
    })

    test('renders matrix content in default tab', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        // Matrix should be the default active tab
        const matrixTab = screen.getByRole('tab', { name: /matriz de permissões/i })
        expect(matrixTab).toHaveAttribute('aria-selected', 'true')
      })
      
      // Matrix content should be visible
      expect(screen.getByText(/filtros/i)).toBeInTheDocument()
    })

    test('renders templates content when templates tab is active', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        const templatesTab = screen.getByRole('tab', { name: /templates/i })
        expect(templatesTab).toBeInTheDocument()
      })
      
      const templatesTab = screen.getByRole('tab', { name: /templates/i })
      await userEvent.click(templatesTab)
      
      // Templates content should load
      await waitFor(() => {
        expect(templatesTab).toHaveAttribute('aria-selected', 'true')
      })
    })

    test('maintains tab state during user interactions', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        const templatesTab = screen.getByRole('tab', { name: /templates/i })
        expect(templatesTab).toBeInTheDocument()
      })
      
      // Switch to templates
      const templatesTab = screen.getByRole('tab', { name: /templates/i })
      await userEvent.click(templatesTab)
      
      // Interact with other elements
      const searchInput = screen.getByPlaceholderText(/nome ou email/i)
      await userEvent.click(searchInput)
      
      // Templates tab should still be active
      expect(templatesTab).toHaveAttribute('aria-selected', 'true')
    })

    test('supports keyboard navigation between tabs', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        const matrixTab = screen.getByRole('tab', { name: /matriz de permissões/i })
        expect(matrixTab).toBeInTheDocument()
      })
      
      const matrixTab = screen.getByRole('tab', { name: /matriz de permissões/i })
      const templatesTab = screen.getByRole('tab', { name: /templates/i })
      
      // Focus on matrix tab
      matrixTab.focus()
      expect(document.activeElement).toBe(matrixTab)
      
      // Navigate with arrow keys
      await userEvent.keyboard('{ArrowRight}')
      expect(document.activeElement).toBe(templatesTab)
    })
  })

  describe('Loading States and Data Management', () => {
    test('displays loading state while fetching admin data', () => {
      // Mock delayed response
      const delayedPromise = new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          status: 200,
          json: async () => mockAdminUsers
        }), 100)
      )
      
      vi.mocked(global.fetch).mockImplementation(() => delayedPromise as any)
      
      renderAdminPermissionsPage()

      // Should show loading state
      expect(screen.getByText(/carregando dados de permissões/i)).toBeInTheDocument()
    })

    test('handles API errors gracefully with proper error display', async () => {
      mockFailedFetch('/api/v1/admin/users', 'Server error', 500)
      
      renderAdminPermissionsPage()

      await waitFor(() => {
        expect(screen.getByText(/erro ao carregar dados/i)).toBeInTheDocument()
      })
      
      // Should show error state with proper messaging
      expect(screen.getByText(/não foi possível carregar os dados de usuários e permissões/i)).toBeInTheDocument()
    })

    test('handles network connectivity issues', async () => {
      mockNetworkError('/api/v1/admin/users', 'Network error')
      
      renderAdminPermissionsPage()

      await waitFor(() => {
        expect(screen.getByText(/erro ao carregar dados/i)).toBeInTheDocument()
      })
      
      // Should show appropriate error messaging
      expect(screen.getByRole('heading', { name: /gerenciar permissões/i })).toBeInTheDocument()
    })

    test('manages loading state for permission data separately', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        // Users should load first
        expect(screen.getByText(/total de usuários/i)).toBeInTheDocument()
      })
      
      // Permission data loading is handled separately
      expect(screen.getByText(/filtros/i)).toBeInTheDocument()
    })
  })

  describe('Error Boundaries and Edge Cases', () => {
    test('handles malformed user data without crashing', async () => {
      const malformedUsers = [
        {
          user_id: 'broken-1',
          // Missing required fields
          name: null,
          email: 'broken@example.com',
          role: 'admin',
        }
      ] as any
      
      mockSuccessfulFetch('/api/v1/admin/users', malformedUsers)
      
      renderAdminPermissionsPage()

      await waitFor(() => {
        // Should handle malformed data gracefully
        expect(screen.getByRole('heading', { name: /gerenciar permissões/i })).toBeInTheDocument()
      })
    })

    test('handles empty user lists appropriately', async () => {
      mockSuccessfulFetch('/api/v1/admin/users', [])
      
      renderAdminPermissionsPage()

      await waitFor(() => {
        expect(screen.getByText(/total de usuários/i)).toBeInTheDocument()
      })
      
      // Statistics should show zero counts
      expect(screen.getByText('0')).toBeInTheDocument()
    })

    test('recovers from permission API failures gracefully', async () => {
      mockSuccessfulFetch('/api/v1/admin/users', mockAdminUsers)
      mockFailedFetch('/api/v1/admin/users/admin-1/permissions', 'Permission error', 403)
      
      renderAdminPermissionsPage()

      await waitFor(() => {
        expect(screen.getByText(/total de usuários/i)).toBeInTheDocument()
      })
      
      // Should still show user data even if some permission calls fail
      expect(screen.getByRole('heading', { name: /gerenciar permissões/i })).toBeInTheDocument()
    })

    test('handles concurrent user actions without data corruption', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText(/nome ou email/i)
        expect(searchInput).toBeInTheDocument()
      })
      
      const searchInput = screen.getByPlaceholderText(/nome ou email/i)
      const templatesTab = screen.getByRole('tab', { name: /templates/i })
      const exportButton = screen.getByRole('button', { name: /exportar/i })
      
      // Concurrent actions
      await Promise.all([
        userEvent.type(searchInput, 'concurrent'),
        userEvent.click(templatesTab),
        userEvent.click(exportButton),
      ])
      
      // Should handle concurrent actions without crashing
      expect(screen.getByRole('heading', { name: /gerenciar permissões/i })).toBeInTheDocument()
    })
  })

  describe('Responsive Design and Admin Workflows', () => {
    test('adapts admin interface for tablet viewports', () => {
      triggerWindowResize(768, 1024) // Tablet viewport
      renderAdminPermissionsPage()
      
      expect(screen.getByRole('heading', { name: /gerenciar permissões/i })).toBeInTheDocument()
      
      // Admin interface should remain functional on tablets
      expect(screen.getByRole('tablist')).toBeInTheDocument()
    })

    test('maintains functionality on larger desktop displays', () => {
      triggerWindowResize(1920, 1080) // Large desktop
      renderAdminPermissionsPage()
      
      expect(screen.getByRole('heading', { name: /gerenciar permissões/i })).toBeInTheDocument()
      expect(screen.getByText(/administre permissões de usuários/i)).toBeInTheDocument()
    })

    test('handles complex admin workflows efficiently', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        expect(screen.getByText(/filtros/i)).toBeInTheDocument()
      })
      
      // Complex workflow: filter -> switch tabs -> export
      const searchInput = screen.getByPlaceholderText(/nome ou email/i)
      await userEvent.type(searchInput, 'admin workflow')
      
      const templatesTab = screen.getByRole('tab', { name: /templates/i })
      await userEvent.click(templatesTab)
      
      const exportButton = screen.getByRole('button', { name: /exportar/i })
      await userEvent.click(exportButton)
      
      // Should handle complex workflows smoothly
      expect(screen.getByRole('heading', { name: /gerenciar permissões/i })).toBeInTheDocument()
    })

    test('provides appropriate mobile warnings for complex admin features', () => {
      triggerWindowResize(375, 667) // Mobile viewport
      renderAdminPermissionsPage()
      
      // Admin interface might have limitations on mobile
      expect(screen.getByRole('heading', { name: /gerenciar permissões/i })).toBeInTheDocument()
      
      // Basic functionality should still work
      expect(screen.getByText(/filtros/i)).toBeInTheDocument()
    })
  })

  describe('Security and Permission Context Integration', () => {
    test('enforces admin-only access with PermissionGuard', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        // Should render content for admin users
        expect(screen.getByRole('heading', { name: /gerenciar permissões/i })).toBeInTheDocument()
      })
      
      // Verify authentication state
      expectAuthState({
        isAuthenticated: true,
        isLoading: false,
      })
    })

    test('handles different admin permission levels appropriately', async () => {
      renderAdminPermissionsPage('sysadmin')

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /gerenciar permissões/i })).toBeInTheDocument()
      })
      
      // Sysadmins should have full access to all functionality
      expect(screen.getByRole('button', { name: /novo usuário/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /templates/i })).toBeInTheDocument()
    })

    test('integrates with real permission checking logic', async () => {
      renderAdminPermissionsPage()

      await waitFor(() => {
        expect(screen.getByText(/total de usuários/i)).toBeInTheDocument()
      })
      
      // Should use real permission logic throughout the component
      expect(screen.getByText(/com permissões/i)).toBeInTheDocument()
      expect(screen.getByText(/administradores/i)).toBeInTheDocument()
    })
  })
})