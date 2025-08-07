/**
 * PermissionGuard Component Tests
 * 
 * Comprehensive tests for the PermissionGuard component covering all permission scenarios
 * Following CLAUDE.md rules: ONLY external API mocking, NO internal store/component/hook mocking
 */

import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import React from 'react'

import { PermissionGuard } from '../PermissionGuard'
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
import { AgentName, UserAgentPermission } from '@/types/permissions'
import useAuthStore from '@/store/authStore'

// Test utilities
const createTestQueryClient = () => {
  return new QueryClient(createTestQueryClientConfig())
}

const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = createTestQueryClient()
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
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
  // Clear auth store state
  useAuthStore.setState({ user: null, token: null, isAuthenticated: false })
})

describe('PermissionGuard', () => {
  describe('Sysadmin User Permissions', () => {
    beforeEach(() => {
      // Create sysadmin user with full permissions using centralized mocks
      const sysadminUser = createMockAdminUser({ 
        role: 'sysadmin',
        user_id: 'sysadmin-123e4567-e89b-12d3-a456-426614174000',
        email: 'sysadmin@empresa.com',
        full_name: 'Sistema Administrador'
      })
      
      // Set user in auth store so hook can access it
      useAuthStore.setState({ 
        user: sysadminUser, 
        token: 'mock-token', 
        isAuthenticated: true 
      })
      
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
      setupUserAPITest({ user: sysadminUser })
      setupPermissionAPITest({ 
        userId: sysadminUser.user_id,
        userPermissions: sysadminPermissions
      })
    })

    it('should allow sysadmin access to all agents and operations', async () => {
      render(
        <TestWrapper>
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="delete">
            <div>Protected Content</div>
          </PermissionGuard>
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Protected Content')).toBeInTheDocument()
      })
    })

    it('should allow sysadmin agent access without specific operation', async () => {
      render(
        <TestWrapper>
          <PermissionGuard agent={AgentName.AUDIO_RECORDING}>
            <div>Agent Access Content</div>
          </PermissionGuard>
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Agent Access Content')).toBeInTheDocument()
      })
    })

    it('should show sysadmin permissions across all CRUD operations', async () => {
      const { rerender } = render(
        <TestWrapper>
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="create">
            <div>Create Content</div>
          </PermissionGuard>
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Create Content')).toBeInTheDocument()
      })

      rerender(
        <TestWrapper>
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="update">
            <div>Update Content</div>
          </PermissionGuard>
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Update Content')).toBeInTheDocument()
      })
    })
  })

  describe('Admin User Permissions', () => {
    beforeEach(() => {
      // Use preset data for admin with proper permissions
      const { user } = TestDataPresets.adminUserWithFullPermissions
      
      // Set user in auth store so hook can access it
      useAuthStore.setState({ 
        user, 
        token: 'mock-token', 
        isAuthenticated: true 
      })
      
      // Create user agent permissions array for admin
      const adminPermissions = [
        createMockUserAgentPermission(user.user_id, AgentName.CLIENT_MANAGEMENT, 
          { create: true, read: true, update: true, delete: true }),
        createMockUserAgentPermission(user.user_id, AgentName.PDF_PROCESSING, 
          { create: true, read: true, update: true, delete: true }),
        createMockUserAgentPermission(user.user_id, AgentName.REPORTS_ANALYSIS, 
          { create: true, read: true, update: true, delete: true }),
        createMockUserAgentPermission(user.user_id, AgentName.AUDIO_RECORDING, 
          { create: true, read: true, update: true, delete: true })
      ]
      
      // Setup API mocks with the correct array structure
      setupUserAPITest({ user })
      setupPermissionAPITest({ 
        userId: user.user_id,
        userPermissions: adminPermissions
      })
    })

    it('should allow admin access to permitted operations', async () => {
      render(
        <TestWrapper>
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="create">
            <div>Admin Create Access</div>
          </PermissionGuard>
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Admin Create Access')).toBeInTheDocument()
      })
    })

    it('should deny admin access to restricted operations', async () => {
      // Create admin user with limited permissions (no delete for PDF processing)
      const adminUser = createMockAdminUser()
      
      // Set user in auth store so hook can access it
      useAuthStore.setState({ 
        user: adminUser, 
        token: 'mock-token', 
        isAuthenticated: true 
      })
      
      const adminPermissions = [
        createMockUserAgentPermission(adminUser.user_id, AgentName.CLIENT_MANAGEMENT, 
          { create: true, read: true, update: true, delete: true }),
        createMockUserAgentPermission(adminUser.user_id, AgentName.PDF_PROCESSING, 
          { create: true, read: true, update: true, delete: false }), // No delete permission
        createMockUserAgentPermission(adminUser.user_id, AgentName.REPORTS_ANALYSIS, 
          { create: true, read: true, update: false, delete: false }),
        createMockUserAgentPermission(adminUser.user_id, AgentName.AUDIO_RECORDING, 
          { create: false, read: true, update: false, delete: false })
      ]
      
      // Setup new mocks for this specific test
      vi.clearAllMocks()
      setupUserAPITest({ user: adminUser })
      setupPermissionAPITest({ 
        userId: adminUser.user_id,
        userPermissions: adminPermissions
      })
      
      render(
        <TestWrapper>
          <PermissionGuard agent={AgentName.PDF_PROCESSING} operation="delete">
            <div>Should Not See This</div>
          </PermissionGuard>
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Você não tem permissão para excluir no agente Processamento de PDFs.')).toBeInTheDocument()
        expect(screen.queryByText('Should Not See This')).not.toBeInTheDocument()
      })
    })
  })

  describe('Regular User Permissions', () => {
    beforeEach(() => {
      // Use preset data for user with limited permissions
      const { user } = TestDataPresets.userWithLimitedPermissions
      
      // Set user in auth store so hook can access it
      useAuthStore.setState({ 
        user, 
        token: 'mock-token', 
        isAuthenticated: true 
      })
      
      // Create user agent permissions array with limited permissions
      const userPermissions = [
        createMockUserAgentPermission(user.user_id, AgentName.CLIENT_MANAGEMENT, 
          { create: false, read: true, update: true, delete: false }),
        createMockUserAgentPermission(user.user_id, AgentName.PDF_PROCESSING, 
          { create: false, read: true, update: false, delete: false })
        // Note: Only some agents have permissions for limited user
      ]
      
      // Setup API mocks
      setupUserAPITest({ user })
      setupPermissionAPITest({ 
        userId: user.user_id,
        userPermissions: userPermissions
      })
    })

    it('should allow user access to permitted read operations', async () => {
      render(
        <TestWrapper>
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="read">
            <div>User Read Access</div>
          </PermissionGuard>
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('User Read Access')).toBeInTheDocument()
      })
    })

    it('should deny user access to create/update/delete operations', async () => {
      render(
        <TestWrapper>
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="create">
            <div>Should Not See This</div>
          </PermissionGuard>
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Você não tem permissão para criar no agente Gestão de Clientes.')).toBeInTheDocument()
        expect(screen.queryByText('Should Not See This')).not.toBeInTheDocument()
      })
    })

    it('should deny user access to restricted agents', async () => {
      render(
        <TestWrapper>
          <PermissionGuard agent={AgentName.REPORTS_ANALYSIS} operation="read">
            <div>Should Not See This</div>
          </PermissionGuard>
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Você não tem permissão para visualizar no agente Relatórios e Análises.')).toBeInTheDocument()
        expect(screen.queryByText('Should Not See This')).not.toBeInTheDocument()
      })
    })
  })

  describe('Loading States', () => {
    beforeEach(() => {
      const { user } = TestDataPresets.adminUserWithFullPermissions
      
      // Set user in auth store so hook can access it
      useAuthStore.setState({ 
        user, 
        token: 'mock-token', 
        isAuthenticated: true 
      })
      
      // Create user agent permissions array for admin
      const adminPermissions = [
        createMockUserAgentPermission(user.user_id, AgentName.CLIENT_MANAGEMENT, 
          { create: true, read: true, update: true, delete: true }),
        createMockUserAgentPermission(user.user_id, AgentName.PDF_PROCESSING, 
          { create: true, read: true, update: true, delete: true })
      ]
      
      const permissionResponse = createMockUserPermissionsResponse(user.user_id, adminPermissions)
      
      // Mock delayed API responses
      const delayedAuthPromise = new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ user })
        }), 100)
      )
      const delayedPermissionsPromise = new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve(permissionResponse)
        }), 100)
      )
      
      mockFetch
        .mockReturnValueOnce(delayedAuthPromise as any)
        .mockReturnValueOnce(delayedPermissionsPromise as any)
    })

    it('should show loading state while checking permissions', () => {
      render(
        <TestWrapper>
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="read">
            <div>Protected Content</div>
          </PermissionGuard>
        </TestWrapper>
      )

      expect(screen.getByText('Verificando permissões...')).toBeInTheDocument()
    })

    it('should show custom loading component when provided', () => {
      render(
        <TestWrapper>
          <PermissionGuard 
            agent={AgentName.CLIENT_MANAGEMENT} 
            operation="read"
            loading={<div>Custom Loading...</div>}
          >
            <div>Protected Content</div>
          </PermissionGuard>
        </TestWrapper>
      )

      expect(screen.getByText('Custom Loading...')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    beforeEach(() => {
      const regularUser = createMockUser()
      
      // Set user in auth store so hook can access it
      useAuthStore.setState({ 
        user: regularUser, 
        token: 'mock-token', 
        isAuthenticated: true 
      })
      
      // Mock API errors - auth succeeds but permissions fail
      setupUserAPITest({ user: regularUser })
      setupPermissionAPITest({ shouldFail: true })
    })

    it('should show error message when permission check fails', async () => {
      render(
        <TestWrapper>
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="read">
            <div>Protected Content</div>
          </PermissionGuard>
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText(/Erro ao verificar permissões/)).toBeInTheDocument()
        expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
      })
    })
  })

  describe('Not Authenticated States', () => {
    beforeEach(() => {
      // Clear auth store for unauthenticated state
      useAuthStore.setState({ user: null, token: null, isAuthenticated: false })
      
      // Mock unauthenticated response
      setupUserAPITest({ shouldFail: true })
    })

    it('should deny access when user is not authenticated', async () => {
      render(
        <TestWrapper>
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="read">
            <div>Should Not See This</div>
          </PermissionGuard>
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Você não tem permissão para visualizar no agente Gestão de Clientes.')).toBeInTheDocument()
        expect(screen.queryByText('Should Not See This')).not.toBeInTheDocument()
      })
    })
  })

  describe('Custom Fallback Components', () => {
    beforeEach(() => {
      // Use preset data for user with no permissions
      const { user } = TestDataPresets.userWithNoPermissions
      
      // Set user in auth store so hook can access it
      useAuthStore.setState({ 
        user, 
        token: 'mock-token', 
        isAuthenticated: true 
      })
      
      // Create empty permissions array (user has no permissions)
      const noPermissions: UserAgentPermission[] = []
      
      // Setup API mocks
      setupUserAPITest({ user })
      setupPermissionAPITest({ 
        userId: user.user_id,
        userPermissions: noPermissions
      })
    })

    it('should show custom fallback when permission is denied', async () => {
      render(
        <TestWrapper>
          <PermissionGuard 
            agent={AgentName.CLIENT_MANAGEMENT} 
            operation="create"
            fallback={<div>Custom Access Denied Message</div>}
          >
            <div>Protected Content</div>
          </PermissionGuard>
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Custom Access Denied Message')).toBeInTheDocument()
        expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
      })
    })
  })

  describe('Specific Permission Guard Components', () => {
    beforeEach(() => {
      const { user } = TestDataPresets.adminUserWithFullPermissions
      
      // Set user in auth store so hook can access it
      useAuthStore.setState({ 
        user, 
        token: 'mock-token', 
        isAuthenticated: true 
      })
      
      // Create user agent permissions array for admin
      const adminPermissions = [
        createMockUserAgentPermission(user.user_id, AgentName.CLIENT_MANAGEMENT, 
          { create: true, read: true, update: true, delete: true }),
        createMockUserAgentPermission(user.user_id, AgentName.PDF_PROCESSING, 
          { create: true, read: true, update: true, delete: true }),
        createMockUserAgentPermission(user.user_id, AgentName.REPORTS_ANALYSIS, 
          { create: true, read: true, update: true, delete: true }),
        createMockUserAgentPermission(user.user_id, AgentName.AUDIO_RECORDING, 
          { create: true, read: true, update: true, delete: true })
      ]
      
      // Setup API mocks
      setupUserAPITest({ user })
      setupPermissionAPITest({ 
        userId: user.user_id,
        userPermissions: adminPermissions
      })
    })

    it('should work with CreatePermissionGuard component', async () => {
      const { CreatePermissionGuard } = await import('../PermissionGuard')
      
      render(
        <TestWrapper>
          <CreatePermissionGuard agent={AgentName.CLIENT_MANAGEMENT}>
            <div>Create Content</div>
          </CreatePermissionGuard>
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Create Content')).toBeInTheDocument()
      })
    })

    it('should work with ReadPermissionGuard component', async () => {
      const { ReadPermissionGuard } = await import('../PermissionGuard')
      
      render(
        <TestWrapper>
          <ReadPermissionGuard agent={AgentName.CLIENT_MANAGEMENT}>
            <div>Read Content</div>
          </ReadPermissionGuard>
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Read Content')).toBeInTheDocument()
      })
    })
  })
})