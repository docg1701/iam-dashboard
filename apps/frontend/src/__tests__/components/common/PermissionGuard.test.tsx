import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import {
  PermissionGuard,
  CreatePermissionGuard,
  ReadPermissionGuard,
  UpdatePermissionGuard,
  DeletePermissionGuard,
  AgentAccessGuard,
  MultiplePermissionGuard,
  SuspensePermissionGuard,
  withPermissionGuard,
} from '@/components/common/PermissionGuard'
import { AgentName } from '@/types/permissions'

// Mock the hooks directly
const mockUsePermissionCheck = vi.fn()
const mockUseAgentAccess = vi.fn()

vi.mock('@/hooks/useUserPermissions', () => ({
  usePermissionCheck: (...args: unknown[]) => {
    mockUsePermissionCheck(...args)
    return mockUsePermissionCheck.mockReturnValue || {
      allowed: true,
      isLoading: false,
      error: null,
      agent: args[0],
      operation: args[1],
    }
  },
  useAgentAccess: (...args: unknown[]) => {
    mockUseAgentAccess(...args)
    return mockUseAgentAccess.mockReturnValue || {
      hasAccess: true,
      isLoading: false,
      error: null,
      agent: args[0],
      permissions: { create: true, read: true, update: false, delete: false },
    }
  },
}))

// Mock Lucide React icons
vi.mock('lucide-react', () => ({
  Lock: () => <div data-testid="lock-icon">Lock</div>,
  Loader2: () => <div data-testid="loader-icon">Loader2</div>,
  AlertTriangle: () => <div data-testid="alert-triangle-icon">AlertTriangle</div>,
}))

// Test wrapper component
const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('PermissionGuard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    cleanup()
  })

  describe('Basic Permission Guard', () => {
    it('should render children when permission is granted', () => {
      mockUsePermissionCheck.mockReturnValue = {
        allowed: true,
        isLoading: false,
        error: null,
        agent: AgentName.CLIENT_MANAGEMENT,
        operation: 'create',
      }

      render(
        <TestWrapper>
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="create">
            <div data-testid="protected-content">Protected Content</div>
          </PermissionGuard>
        </TestWrapper>
      )

      expect(screen.getByTestId('protected-content')).toBeInTheDocument()
      expect(screen.getByText('Protected Content')).toBeInTheDocument()
    })

    it('should show default fallback when permission is denied', () => {
      mockUsePermissionCheck.mockReturnValue = {
        allowed: false,
        isLoading: false,
        error: null,
        agent: AgentName.CLIENT_MANAGEMENT,
        operation: 'create',
      }

      render(
        <TestWrapper>
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="create">
            <div data-testid="protected-content">Protected Content</div>
          </PermissionGuard>
        </TestWrapper>
      )

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
      expect(screen.getByTestId('lock-icon')).toBeInTheDocument()
      expect(screen.getByText(/não tem permissão para criar/)).toBeInTheDocument()
    })

    it('should show custom fallback when permission is denied', () => {
      mockUsePermissionCheck.mockReturnValue = {
        allowed: false,
        isLoading: false,
        error: null,
        agent: AgentName.CLIENT_MANAGEMENT,
        operation: 'create',
      }

      const customFallback = <div data-testid="custom-fallback">Access Denied</div>

      render(
        <TestWrapper>
          <PermissionGuard 
            agent={AgentName.CLIENT_MANAGEMENT} 
            operation="create" 
            fallback={customFallback}
          >
            <div data-testid="protected-content">Protected Content</div>
          </PermissionGuard>
        </TestWrapper>
      )

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
      expect(screen.getByTestId('custom-fallback')).toBeInTheDocument()
      expect(screen.getByText('Access Denied')).toBeInTheDocument()
    })

    it('should show loading state', () => {
      mockUsePermissionCheck.mockReturnValue = {
        allowed: false,
        isLoading: true,
        error: null,
        agent: AgentName.CLIENT_MANAGEMENT,
        operation: 'create',
      }

      render(
        <TestWrapper>
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="create">
            <div data-testid="protected-content">Protected Content</div>
          </PermissionGuard>
        </TestWrapper>
      )

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
      expect(screen.getByTestId('loader-icon')).toBeInTheDocument()
      expect(screen.getByText('Verificando permissões...')).toBeInTheDocument()
    })

    it('should show custom loading component', () => {
      mockUsePermissionCheck.mockReturnValue = {
        allowed: false,
        isLoading: true,
        error: null,
        agent: AgentName.CLIENT_MANAGEMENT,
        operation: 'create',
      }

      const customLoading = <div data-testid="custom-loading">Loading...</div>

      render(
        <TestWrapper>
          <PermissionGuard 
            agent={AgentName.CLIENT_MANAGEMENT} 
            operation="create" 
            loading={customLoading}
          >
            <div data-testid="protected-content">Protected Content</div>
          </PermissionGuard>
        </TestWrapper>
      )

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
      expect(screen.getByTestId('custom-loading')).toBeInTheDocument()
      expect(screen.getByText('Loading...')).toBeInTheDocument()
    })

    it('should show error state', () => {
      const error = new Error('Permission check failed')
      mockUsePermissionCheck.mockReturnValue = {
        allowed: false,
        isLoading: false,
        error: error,
        agent: AgentName.CLIENT_MANAGEMENT,
        operation: 'create',
      }

      render(
        <TestWrapper>
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="create">
            <div data-testid="protected-content">Protected Content</div>
          </PermissionGuard>
        </TestWrapper>
      )

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
      expect(screen.getByTestId('alert-triangle-icon')).toBeInTheDocument()
      expect(screen.getByText(/Permission check failed/)).toBeInTheDocument()
    })
  })

  describe('Agent Access Guard', () => {
    it('should render children when agent access is granted', () => {
      mockUseAgentAccess.mockReturnValue = {
        hasAccess: true,
        isLoading: false,
        error: null,
        agent: AgentName.CLIENT_MANAGEMENT,
        permissions: { create: true, read: true, update: false, delete: false },
      }

      render(
        <TestWrapper>
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT}>
            <div data-testid="protected-content">Protected Content</div>
          </PermissionGuard>
        </TestWrapper>
      )

      expect(screen.getByTestId('protected-content')).toBeInTheDocument()
    })

    it('should show fallback when agent access is denied', () => {
      mockUseAgentAccess.mockReturnValue = {
        hasAccess: false,
        isLoading: false,
        error: null,
        agent: AgentName.CLIENT_MANAGEMENT,
        permissions: null,
      }

      render(
        <TestWrapper>
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT}>
            <div data-testid="protected-content">Protected Content</div>
          </PermissionGuard>
        </TestWrapper>
      )

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
      expect(screen.getByText(/não tem acesso ao agente/)).toBeInTheDocument()
    })
  })

  describe('Specific Permission Guards', () => {
    it('should render CreatePermissionGuard correctly', () => {
      mockUsePermissionCheck.mockReturnValue = {
        allowed: true,
        isLoading: false,
        error: null,
        agent: AgentName.CLIENT_MANAGEMENT,
        operation: 'create',
      }

      render(
        <TestWrapper>
          <CreatePermissionGuard agent={AgentName.CLIENT_MANAGEMENT}>
            <div data-testid="create-content">Create Content</div>
          </CreatePermissionGuard>
        </TestWrapper>
      )

      expect(screen.getByTestId('create-content')).toBeInTheDocument()
      expect(mockUsePermissionCheck).toHaveBeenCalledWith(
        AgentName.CLIENT_MANAGEMENT,
        'create',
        undefined
      )
    })

    it('should render ReadPermissionGuard correctly', () => {
      mockUsePermissionCheck.mockReturnValue = {
        allowed: true,
        isLoading: false,
        error: null,
        agent: AgentName.PDF_PROCESSING,
        operation: 'read',
      }

      render(
        <TestWrapper>
          <ReadPermissionGuard agent={AgentName.PDF_PROCESSING}>
            <div data-testid="read-content">Read Content</div>
          </ReadPermissionGuard>
        </TestWrapper>
      )

      expect(screen.getByTestId('read-content')).toBeInTheDocument()
      expect(mockUsePermissionCheck).toHaveBeenCalledWith(
        AgentName.PDF_PROCESSING,
        'read',
        undefined
      )
    })

    it('should render UpdatePermissionGuard correctly', () => {
      mockUsePermissionCheck.mockReturnValue = {
        allowed: true,
        isLoading: false,
        error: null,
        agent: AgentName.REPORTS_ANALYSIS,
        operation: 'update',
      }

      render(
        <TestWrapper>
          <UpdatePermissionGuard agent={AgentName.REPORTS_ANALYSIS}>
            <div data-testid="update-content">Update Content</div>
          </UpdatePermissionGuard>
        </TestWrapper>
      )

      expect(screen.getByTestId('update-content')).toBeInTheDocument()
      expect(mockUsePermissionCheck).toHaveBeenCalledWith(
        AgentName.REPORTS_ANALYSIS,
        'update',
        undefined
      )
    })

    it('should render DeletePermissionGuard correctly', () => {
      mockUsePermissionCheck.mockReturnValue = {
        allowed: true,
        isLoading: false,
        error: null,
        agent: AgentName.AUDIO_RECORDING,
        operation: 'delete',
      }

      render(
        <TestWrapper>
          <DeletePermissionGuard agent={AgentName.AUDIO_RECORDING}>
            <div data-testid="delete-content">Delete Content</div>
          </DeletePermissionGuard>
        </TestWrapper>
      )

      expect(screen.getByTestId('delete-content')).toBeInTheDocument()
      expect(mockUsePermissionCheck).toHaveBeenCalledWith(
        AgentName.AUDIO_RECORDING,
        'delete',
        undefined
      )
    })

    it('should render AgentAccessGuard correctly', () => {
      mockUseAgentAccess.mockReturnValue = {
        hasAccess: true,
        isLoading: false,
        error: null,
        agent: AgentName.CLIENT_MANAGEMENT,
        permissions: { create: true, read: true, update: false, delete: false },
      }

      render(
        <TestWrapper>
          <AgentAccessGuard agent={AgentName.CLIENT_MANAGEMENT}>
            <div data-testid="agent-content">Agent Content</div>
          </AgentAccessGuard>
        </TestWrapper>
      )

      expect(screen.getByTestId('agent-content')).toBeInTheDocument()
      expect(mockUseAgentAccess).toHaveBeenCalledWith(
        AgentName.CLIENT_MANAGEMENT,
        undefined
      )
    })
  })

  describe('MultiplePermissionGuard', () => {
    it('should render children when any permission is granted', () => {
      // Mock first permission granted
      mockUsePermissionCheck.mockReturnValue = {
        allowed: true,
        isLoading: false,
        error: null,
        agent: AgentName.CLIENT_MANAGEMENT,
        operation: 'delete',
      }

      render(
        <TestWrapper>
          <MultiplePermissionGuard
            permissions={[
              { agent: AgentName.CLIENT_MANAGEMENT, operation: 'delete' },
              { agent: AgentName.PDF_PROCESSING, operation: 'read' },
            ]}
          >
            <div data-testid="multiple-content">Multiple Permission Content</div>
          </MultiplePermissionGuard>
        </TestWrapper>
      )

      expect(screen.getByTestId('multiple-content')).toBeInTheDocument()
    })

    it('should show fallback when no permissions are granted', () => {
      mockUsePermissionCheck.mockReturnValue = {
        allowed: false,
        isLoading: false,
        error: null,
        agent: AgentName.CLIENT_MANAGEMENT,
        operation: 'delete',
      }

      render(
        <TestWrapper>
          <MultiplePermissionGuard
            permissions={[
              { agent: AgentName.CLIENT_MANAGEMENT, operation: 'delete' },
            ]}
          >
            <div data-testid="multiple-content">Multiple Permission Content</div>
          </MultiplePermissionGuard>
        </TestWrapper>
      )

      expect(screen.queryByTestId('multiple-content')).not.toBeInTheDocument()
      // MultiplePermissionGuard currently uses PermissionGuard fallback
      expect(screen.getByText(/não tem permissão para excluir/)).toBeInTheDocument()
    })

    it('should show loading when any permission is loading', () => {
      mockUsePermissionCheck.mockReturnValue = {
        allowed: false,
        isLoading: true,
        error: null,
        agent: AgentName.CLIENT_MANAGEMENT,
        operation: 'create',
      }

      render(
        <TestWrapper>
          <MultiplePermissionGuard
            permissions={[
              { agent: AgentName.CLIENT_MANAGEMENT, operation: 'create' },
              { agent: AgentName.PDF_PROCESSING, operation: 'read' },
            ]}
          >
            <div data-testid="multiple-content">Multiple Permission Content</div>
          </MultiplePermissionGuard>
        </TestWrapper>
      )

      expect(screen.queryByTestId('multiple-content')).not.toBeInTheDocument()
      expect(screen.getByTestId('loader-icon')).toBeInTheDocument()
    })

    it('should show error when any permission has error', () => {
      const error = new Error('Permission error')
      mockUsePermissionCheck.mockReturnValue = {
        allowed: false,
        isLoading: false,
        error: error,
        agent: AgentName.CLIENT_MANAGEMENT,
        operation: 'create',
      }

      render(
        <TestWrapper>
          <MultiplePermissionGuard
            permissions={[
              { agent: AgentName.CLIENT_MANAGEMENT, operation: 'create' },
              { agent: AgentName.PDF_PROCESSING, operation: 'read' },
            ]}
          >
            <div data-testid="multiple-content">Multiple Permission Content</div>
          </MultiplePermissionGuard>
        </TestWrapper>
      )

      expect(screen.queryByTestId('multiple-content')).not.toBeInTheDocument()
      expect(screen.getByTestId('alert-triangle-icon')).toBeInTheDocument()
      expect(screen.getByText(/Permission error/)).toBeInTheDocument()
    })

    it('should handle mixed permission and agent access checks', () => {
      // Set first permission to allowed since MultiplePermissionGuard only checks first permission
      mockUsePermissionCheck.mockReturnValue = {
        allowed: true,
        isLoading: false,
        error: null,
        agent: AgentName.CLIENT_MANAGEMENT,
        operation: 'delete',
      }

      mockUseAgentAccess.mockReturnValue = {
        hasAccess: true,
        isLoading: false,
        error: null,
        agent: AgentName.PDF_PROCESSING,
        permissions: { create: false, read: true, update: false, delete: false },
      }

      render(
        <TestWrapper>
          <MultiplePermissionGuard
            permissions={[
              { agent: AgentName.CLIENT_MANAGEMENT, operation: 'delete' },
              { agent: AgentName.PDF_PROCESSING }, // No operation = agent access
            ]}
          >
            <div data-testid="mixed-content">Mixed Permission Content</div>
          </MultiplePermissionGuard>
        </TestWrapper>
      )

      expect(screen.getByTestId('mixed-content')).toBeInTheDocument()
    })
  })

  describe('SuspensePermissionGuard', () => {
    it('should render with suspense wrapper', () => {
      mockUsePermissionCheck.mockReturnValue = {
        allowed: true,
        isLoading: false,
        error: null,
        agent: AgentName.CLIENT_MANAGEMENT,
        operation: 'read',
      }

      render(
        <TestWrapper>
          <SuspensePermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="read">
            <div data-testid="suspense-content">Suspense Content</div>
          </SuspensePermissionGuard>
        </TestWrapper>
      )

      expect(screen.getByTestId('suspense-content')).toBeInTheDocument()
    })
  })

  describe('withPermissionGuard HOC', () => {
    it('should wrap component with permission check', () => {
      const TestComponent = ({ message }: { message: string }) => (
        <div data-testid="hoc-content">{message}</div>
      )

      const WrappedComponent = withPermissionGuard(TestComponent, {
        agent: AgentName.CLIENT_MANAGEMENT,
        operation: 'create',
      })

      mockUsePermissionCheck.mockReturnValue = {
        allowed: true,
        isLoading: false,
        error: null,
        agent: AgentName.CLIENT_MANAGEMENT,
        operation: 'create',
      }

      render(
        <TestWrapper>
          <WrappedComponent message="HOC Test" />
        </TestWrapper>
      )

      expect(screen.getByTestId('hoc-content')).toBeInTheDocument()
      expect(screen.getByText('HOC Test')).toBeInTheDocument()
    })

    it('should show fallback when permission denied in HOC', () => {
      const TestComponent = ({ message }: { message: string }) => (
        <div data-testid="hoc-content">{message}</div>
      )

      const WrappedComponent = withPermissionGuard(TestComponent, {
        agent: AgentName.CLIENT_MANAGEMENT,
        operation: 'delete',
        fallback: <div data-testid="hoc-fallback">Access Denied</div>,
      })

      mockUsePermissionCheck.mockReturnValue = {
        allowed: false,
        isLoading: false,
        error: null,
        agent: AgentName.CLIENT_MANAGEMENT,
        operation: 'delete',
      }

      render(
        <TestWrapper>
          <WrappedComponent message="HOC Test" />
        </TestWrapper>
      )

      expect(screen.queryByTestId('hoc-content')).not.toBeInTheDocument()
      expect(screen.getByTestId('hoc-fallback')).toBeInTheDocument()
      expect(screen.getByText('Access Denied')).toBeInTheDocument()
    })

    it('should have correct displayName', () => {
      const TestComponent = ({ message }: { message: string }) => (
        <div>{message}</div>
      )
      TestComponent.displayName = 'TestComponent'

      const WrappedComponent = withPermissionGuard(TestComponent, {
        agent: AgentName.CLIENT_MANAGEMENT,
        operation: 'read',
      })

      expect(WrappedComponent.displayName).toBe('withPermissionGuard(TestComponent)')
    })
  })

  describe('User ID handling', () => {
    it('should pass userId to hooks', () => {
      mockUsePermissionCheck.mockReturnValue = {
        allowed: true,
        isLoading: false,
        error: null,
        agent: AgentName.CLIENT_MANAGEMENT,
        operation: 'create',
      }

      render(
        <TestWrapper>
          <PermissionGuard 
            agent={AgentName.CLIENT_MANAGEMENT} 
            operation="create" 
            userId="specific-user-id"
          >
            <div data-testid="user-content">User Content</div>
          </PermissionGuard>
        </TestWrapper>
      )

      expect(mockUsePermissionCheck).toHaveBeenCalledWith(
        AgentName.CLIENT_MANAGEMENT,
        'create',
        'specific-user-id'
      )
    })
  })

  describe('Agent text mapping', () => {
    it('should display correct Portuguese agent names in fallback', () => {
      mockUsePermissionCheck.mockReturnValue = {
        allowed: false,
        isLoading: false,
        error: null,
        agent: AgentName.CLIENT_MANAGEMENT,
        operation: 'create',
      }

      render(
        <TestWrapper>
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="create">
            <div>Content</div>
          </PermissionGuard>
        </TestWrapper>
      )

      expect(screen.getByText(/Gestão de Clientes/)).toBeInTheDocument()
    })

    it('should display correct Portuguese operation names in fallback', () => {
      mockUsePermissionCheck.mockReturnValue = {
        allowed: false,
        isLoading: false,
        error: null,
        agent: AgentName.PDF_PROCESSING,
        operation: 'delete',
      }

      render(
        <TestWrapper>
          <PermissionGuard agent={AgentName.PDF_PROCESSING} operation="delete">
            <div>Content</div>
          </PermissionGuard>
        </TestWrapper>
      )

      expect(screen.getByText(/excluir.*Processamento de PDFs/)).toBeInTheDocument()
    })
  })

  describe('Error scenarios', () => {
    it('should handle undefined operation gracefully', () => {
      mockUseAgentAccess.mockReturnValue = {
        hasAccess: true,
        isLoading: false,
        error: null,
        agent: AgentName.CLIENT_MANAGEMENT,
        permissions: { create: true, read: true, update: false, delete: false },
      }

      render(
        <TestWrapper>
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT}>
            <div data-testid="no-operation-content">No Operation Content</div>
          </PermissionGuard>
        </TestWrapper>
      )

      expect(screen.getByTestId('no-operation-content')).toBeInTheDocument()
    })

    it('should handle null permissions in agent access', () => {
      mockUseAgentAccess.mockReturnValue = {
        hasAccess: false,
        isLoading: false,
        error: null,
        agent: AgentName.CLIENT_MANAGEMENT,
        permissions: null,
      }

      render(
        <TestWrapper>
          <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT}>
            <div data-testid="null-permissions-content">Content</div>
          </PermissionGuard>
        </TestWrapper>
      )

      expect(screen.queryByTestId('null-permissions-content')).not.toBeInTheDocument()
      expect(screen.getByText(/não tem acesso ao agente/)).toBeInTheDocument()
    })
  })
})