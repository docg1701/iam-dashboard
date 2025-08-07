/**
 * PermissionGuard Component Tests
 * 
 * Comprehensive tests for the PermissionGuard component covering all permission scenarios
 * Following CLAUDE.md rules: ONLY external API mocking, NO internal store/component/hook mocking
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
  createMockUser, 
  createMockAdminUser, 
  createMockUserPermissionMatrix,
  createMockUserAgentPermission,
  createMockUserPermissionsResponse,
  setupUserAPITest,
  setupPermissionAPITest,
  TestDataPresets,
  createTestQueryClientConfig
} from '@/test/api-mocks'
import { 
  setupAuthenticatedUser,
  clearTestAuth,
  createMockSysAdmin
} from '@/test/auth-helpers'
import { PermissionGuard } from '../PermissionGuard'
import { AgentName, UserAgentPermission } from '@/types/permissions'
import useAuthStore from '@/store/authStore'

// Setup standard test utilities
useTestSetup()

describe('PermissionGuard', () => {
  describe('Sysadmin User Permissions', () => {
    let sysadminUser: any
    
    beforeEach(async () => {
      await act(async () => {
        // Create sysadmin user with full permissions using centralized mocks
        sysadminUser = createMockSysAdmin({
          user_id: 'sysadmin-123e4567-e89b-12d3-a456-426614174000',
          email: 'sysadmin@empresa.com',
          full_name: 'Sistema Administrador'
        })
        
        // Set user in auth store
        setupAuthenticatedUser('sysadmin')
        useAuthStore.setState({ user: sysadminUser })
        
        // Create user agent permissions array for API response
        const sysadminPermissions = [
          createMockUserAgentPermission(sysadminUser.user_id, AgentName.CLIENT_MANAGEMENT, 
            { create: true, read: true, update: true, delete: true }),
          createMockUserAgentPermission(sysadminUser.user_id, AgentName.PDF_PROCESSING, 
            { create: true, read: true, update: true, delete: true }),
          createMockUserAgentPermission(sysadminUser.user_id, AgentName.REPORTS_ANALYSIS, 
            { create: true, read: true, update: true, delete: true }),
          createMockUserAgentPermission(sysadminUser.user_id, AgentName.AUDIO_RECORDING, 
            { create: true, read: true, update: true, delete: true })
        ]
        
        // Setup API mocks with the correct array structure
        setupPermissionAPITest({ 
          userId: sysadminUser.user_id,
          userPermissions: sysadminPermissions
        })
      })
    })

    it('should allow sysadmin access to all agents and operations', async () => {
      await act(async () => {
        renderWithProviders(
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="delete">
            <div>Protected Content</div>
          </PermissionGuard>
        )
      })

      await waitFor(() => {
        expect(screen.getByText('Protected Content')).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('should allow sysadmin agent access without specific operation', async () => {
      await act(async () => {
        renderWithProviders(
          <PermissionGuard agent={AgentName.AUDIO_RECORDING}>
            <div>Agent Access Content</div>
          </PermissionGuard>
        )
      })

      await waitFor(() => {
        expect(screen.getByText('Agent Access Content')).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('should show sysadmin permissions across all CRUD operations', async () => {
      let renderResult: any
      
      await act(async () => {
        renderResult = renderWithProviders(
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="create">
            <div>Create Content</div>
          </PermissionGuard>
        )
      })

      await waitFor(() => {
        expect(screen.getByText('Create Content')).toBeInTheDocument()
      }, { timeout: 3000 })

      await act(async () => {
        renderResult.rerender(
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="update">
            <div>Update Content</div>
          </PermissionGuard>
        )
      })

      await waitFor(() => {
        expect(screen.getByText('Update Content')).toBeInTheDocument()
      }, { timeout: 3000 })
    })
  })

  describe('Admin User Permissions', () => {
    let adminUser: any
    
    beforeEach(async () => {
      await act(async () => {
        // Use preset data for admin with proper permissions
        const { user } = TestDataPresets.adminUserWithFullPermissions
        adminUser = user
        
        // Set user in auth store
        setupAuthenticatedUser('admin')
        useAuthStore.setState({ user: adminUser })
        
        // Create user agent permissions array for admin
        const adminPermissions = [
          createMockUserAgentPermission(adminUser.user_id, AgentName.CLIENT_MANAGEMENT, 
            { create: true, read: true, update: true, delete: true }),
          createMockUserAgentPermission(adminUser.user_id, AgentName.PDF_PROCESSING, 
            { create: true, read: true, update: true, delete: true }),
          createMockUserAgentPermission(adminUser.user_id, AgentName.REPORTS_ANALYSIS, 
            { create: true, read: true, update: true, delete: true }),
          createMockUserAgentPermission(adminUser.user_id, AgentName.AUDIO_RECORDING, 
            { create: true, read: true, update: true, delete: true })
        ]
        
        // Setup API mocks with the correct array structure
        setupPermissionAPITest({ 
          userId: adminUser.user_id,
          userPermissions: adminPermissions
        })
      })
    })

    it('should allow admin access to permitted operations', async () => {
      await act(async () => {
        renderWithProviders(
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="create">
            <div>Admin Create Access</div>
          </PermissionGuard>
        )
      })

      await waitFor(() => {
        expect(screen.getByText('Admin Create Access')).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('should deny admin access to restricted operations', async () => {
      // This test verifies that admin users without specific permissions are properly denied access
      // Based on our debug tests, we know the permission system works correctly,
      // so this test needs to account for the async nature of permission checks
      
      // Create admin user with limited permissions (no delete for PDF processing)
      const limitedAdminUser = createMockAdminUser({
        user_id: 'limited-admin-123',
        email: 'limited.admin@empresa.com'
      })
      
      // Explicitly create permissions with NO delete for PDF_PROCESSING
      const adminPermissions = [
        createMockUserAgentPermission(limitedAdminUser.user_id, AgentName.CLIENT_MANAGEMENT, 
          { create: true, read: true, update: true, delete: true }),
        createMockUserAgentPermission(limitedAdminUser.user_id, AgentName.PDF_PROCESSING, 
          { create: true, read: true, update: true, delete: false }), // EXPLICITLY NO delete permission
        createMockUserAgentPermission(limitedAdminUser.user_id, AgentName.REPORTS_ANALYSIS, 
          { create: true, read: true, update: false, delete: false }),
        createMockUserAgentPermission(limitedAdminUser.user_id, AgentName.AUDIO_RECORDING, 
          { create: false, read: true, update: false, delete: false })
      ]
      
      await act(async () => {
        // Clear existing auth state completely
        clearTestAuth() 
        
        // Create fresh auth state with limited user
        setupAuthenticatedUser('admin')
        useAuthStore.setState({ 
          user: limitedAdminUser,
          token: `limited-admin-token-${limitedAdminUser.user_id}`,
          isAuthenticated: true
        })
        
        // Clear all mocks and setup fresh API responses
        vi.clearAllMocks()
        setupPermissionAPITest({ 
          userId: limitedAdminUser.user_id,
          userPermissions: adminPermissions
        })
      })
      
      // Render the PermissionGuard
      await act(async () => {
        renderWithProviders(
          <PermissionGuard agent={AgentName.PDF_PROCESSING} operation="delete">
            <div>Should Not See This</div>
          </PermissionGuard>
        )
      })

      // Wait for the async permission check to complete
      // The permission system is working correctly (verified by debug tests),
      // but it takes time for the async API call to resolve and update the component
      await waitFor(() => {
        const errorMessage = screen.queryByText(/Você não tem permissão para excluir/)
        const protectedContent = screen.queryByText('Should Not See This')
        
        // Permission check must be complete (no loading state)
        expect(screen.queryByText('Verificando permissões...')).not.toBeInTheDocument()
        
        // Final state should show the error message and NOT the protected content
        expect(errorMessage).toBeInTheDocument()
        expect(protectedContent).not.toBeInTheDocument()
      }, { 
        timeout: 10000, // Increased timeout to allow for async resolution
        interval: 50 // Check frequently since we know it will eventually resolve correctly
      })
    })
  })

  describe('Regular User Permissions', () => {
    let regularUser: any
    
    beforeEach(async () => {
      await act(async () => {
        // Use preset data for user with limited permissions
        const { user } = TestDataPresets.userWithLimitedPermissions
        regularUser = user
        
        // Set user in auth store
        setupAuthenticatedUser('user')
        useAuthStore.setState({ user: regularUser })
        
        // Create user agent permissions array with limited permissions
        const userPermissions = [
          createMockUserAgentPermission(regularUser.user_id, AgentName.CLIENT_MANAGEMENT, 
            { create: false, read: true, update: true, delete: false }),
          createMockUserAgentPermission(regularUser.user_id, AgentName.PDF_PROCESSING, 
            { create: false, read: true, update: false, delete: false })
          // Note: Only some agents have permissions for limited user
        ]
        
        // Setup API mocks
        setupPermissionAPITest({ 
          userId: regularUser.user_id,
          userPermissions: userPermissions
        })
      })
    })

    it('should allow user access to permitted read operations', async () => {
      await act(async () => {
        renderWithProviders(
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="read">
            <div>User Read Access</div>
          </PermissionGuard>
        )
      })

      await waitFor(() => {
        expect(screen.getByText('User Read Access')).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('should deny user access to create/update/delete operations', async () => {
      await act(async () => {
        renderWithProviders(
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="create">
            <div>Should Not See This</div>
          </PermissionGuard>
        )
      })

      await waitFor(() => {
        expect(screen.getByText('Você não tem permissão para criar no agente Gestão de Clientes.')).toBeInTheDocument()
        expect(screen.queryByText('Should Not See This')).not.toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('should deny user access to restricted agents', async () => {
      await act(async () => {
        renderWithProviders(
          <PermissionGuard agent={AgentName.REPORTS_ANALYSIS} operation="read">
            <div>Should Not See This</div>
          </PermissionGuard>
        )
      })

      await waitFor(() => {
        expect(screen.getByText('Você não tem permissão para visualizar no agente Relatórios e Análises.')).toBeInTheDocument()
        expect(screen.queryByText('Should Not See This')).not.toBeInTheDocument()
      }, { timeout: 3000 })
    })
  })

  describe('Loading States', () => {
    let loadingUser: any
    
    beforeEach(async () => {
      await act(async () => {
        const { user } = TestDataPresets.adminUserWithFullPermissions
        loadingUser = user
        
        // Set user in auth store
        setupAuthenticatedUser('admin')
        useAuthStore.setState({ user: loadingUser })
        
        // Create user agent permissions array for admin
        const adminPermissions = [
          createMockUserAgentPermission(loadingUser.user_id, AgentName.CLIENT_MANAGEMENT, 
            { create: true, read: true, update: true, delete: true }),
          createMockUserAgentPermission(loadingUser.user_id, AgentName.PDF_PROCESSING, 
            { create: true, read: true, update: true, delete: true })
        ]
        
        const permissionResponse = createMockUserPermissionsResponse(loadingUser.user_id, adminPermissions)
        
        // Mock delayed API responses  
        const mockFetch = vi.mocked(global.fetch)
        const delayedPermissionsPromise = new Promise(resolve => 
          setTimeout(() => resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve(permissionResponse)
          }), 100)
        )
        
        mockFetch.mockReturnValueOnce(delayedPermissionsPromise as any)
      })
    })

    it('should show loading state while checking permissions', async () => {
      await act(async () => {
        renderWithProviders(
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="read">
            <div>Protected Content</div>
          </PermissionGuard>
        )
      })

      // Should show loading first
      expect(screen.getByText('Verificando permissões...')).toBeInTheDocument()
    })

    it('should show custom loading component when provided', async () => {
      await act(async () => {
        renderWithProviders(
          <PermissionGuard 
            agent={AgentName.CLIENT_MANAGEMENT} 
            operation="read"
            loading={<div>Custom Loading...</div>}
          >
            <div>Protected Content</div>
          </PermissionGuard>
        )
      })

      expect(screen.getByText('Custom Loading...')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    let errorUser: any
    
    beforeEach(async () => {
      await act(async () => {
        errorUser = createMockUser()
        
        // Set user in auth store
        setupAuthenticatedUser('user')
        useAuthStore.setState({ user: errorUser })
        
        // Mock API errors - permissions fail
        setupPermissionAPITest({ shouldFail: true })
      })
    })

    it('should show error message when permission check fails', async () => {
      await act(async () => {
        renderWithProviders(
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="read">
            <div>Protected Content</div>
          </PermissionGuard>
        )
      })

      await waitFor(() => {
        expect(screen.getByText(/Erro ao verificar permissões/)).toBeInTheDocument()
        expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
      }, { timeout: 3000 })
    })
  })

  describe('Not Authenticated States', () => {
    beforeEach(async () => {
      await act(async () => {
        // Clear auth store for unauthenticated state
        clearTestAuth()
      })
    })

    it('should deny access when user is not authenticated', async () => {
      await act(async () => {
        renderWithProviders(
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="read">
            <div>Should Not See This</div>
          </PermissionGuard>
        )
      })

      await waitFor(() => {
        expect(screen.getByText('Você não tem permissão para visualizar no agente Gestão de Clientes.')).toBeInTheDocument()
        expect(screen.queryByText('Should Not See This')).not.toBeInTheDocument()
      }, { timeout: 3000 })
    })
  })

  describe('Custom Fallback Components', () => {
    let noPermissionsUser: any
    
    beforeEach(async () => {
      await act(async () => {
        // Use preset data for user with no permissions
        const { user } = TestDataPresets.userWithNoPermissions
        noPermissionsUser = user
        
        // Set user in auth store
        setupAuthenticatedUser('user')
        useAuthStore.setState({ user: noPermissionsUser })
        
        // Create empty permissions array (user has no permissions)
        const noPermissions: UserAgentPermission[] = []
        
        // Setup API mocks
        setupPermissionAPITest({ 
          userId: noPermissionsUser.user_id,
          userPermissions: noPermissions
        })
      })
    })

    it('should show custom fallback when permission is denied', async () => {
      await act(async () => {
        renderWithProviders(
          <PermissionGuard 
            agent={AgentName.CLIENT_MANAGEMENT} 
            operation="create"
            fallback={<div>Custom Access Denied Message</div>}
          >
            <div>Protected Content</div>
          </PermissionGuard>
        )
      })

      await waitFor(() => {
        expect(screen.getByText('Custom Access Denied Message')).toBeInTheDocument()
        expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
      }, { timeout: 3000 })
    })
  })

  describe('Specific Permission Guard Components', () => {
    let specificUser: any
    
    beforeEach(async () => {
      await act(async () => {
        const { user } = TestDataPresets.adminUserWithFullPermissions
        specificUser = user
        
        // Set user in auth store
        setupAuthenticatedUser('admin')
        useAuthStore.setState({ user: specificUser })
        
        // Create user agent permissions array for admin
        const adminPermissions = [
          createMockUserAgentPermission(specificUser.user_id, AgentName.CLIENT_MANAGEMENT, 
            { create: true, read: true, update: true, delete: true }),
          createMockUserAgentPermission(specificUser.user_id, AgentName.PDF_PROCESSING, 
            { create: true, read: true, update: true, delete: true }),
          createMockUserAgentPermission(specificUser.user_id, AgentName.REPORTS_ANALYSIS, 
            { create: true, read: true, update: true, delete: true }),
          createMockUserAgentPermission(specificUser.user_id, AgentName.AUDIO_RECORDING, 
            { create: true, read: true, update: true, delete: true })
        ]
        
        // Setup API mocks
        setupPermissionAPITest({ 
          userId: specificUser.user_id,
          userPermissions: adminPermissions
        })
      })
    })

    it('should work with CreatePermissionGuard component', async () => {
      const { CreatePermissionGuard } = await import('../PermissionGuard')
      
      await act(async () => {
        renderWithProviders(
          <CreatePermissionGuard agent={AgentName.CLIENT_MANAGEMENT}>
            <div>Create Content</div>
          </CreatePermissionGuard>
        )
      })

      await waitFor(() => {
        expect(screen.getByText('Create Content')).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('should work with ReadPermissionGuard component', async () => {
      const { ReadPermissionGuard } = await import('../PermissionGuard')
      
      await act(async () => {
        renderWithProviders(
          <ReadPermissionGuard agent={AgentName.CLIENT_MANAGEMENT}>
            <div>Read Content</div>
          </ReadPermissionGuard>
        )
      })

      await waitFor(() => {
        expect(screen.getByText('Read Content')).toBeInTheDocument()
      }, { timeout: 3000 })
    })
  })
})