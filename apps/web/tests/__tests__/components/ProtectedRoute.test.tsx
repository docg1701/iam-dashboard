import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { AuthProvider } from '@/contexts/AuthContext'
import { ErrorProvider } from '@/components/errors/ErrorContext'
import { setTestNodeEnv } from '../../test-utils'
import {
  ProtectedRoute,
  PermissionGuard,
  RoleGuard,
} from '@/components/auth/ProtectedRoute'

// Mock Next.js router
const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
  }),
}))

// Test components
const ProtectedContent = () => (
  <div data-testid="protected-content">Protected Content</div>
)

// Test wrapper with all required providers
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <ErrorProvider enableGlobalErrorHandler={false}>
    <AuthProvider>{children}</AuthProvider>
  </ErrorProvider>
)
const AdminContent = () => (
  <div data-testid="admin-content">Admin Only Content</div>
)

describe('ProtectedRoute Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn()
    localStorage.clear()
    setTestNodeEnv('development')
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  it('should redirect to login when user is not authenticated', async () => {
    render(
      <TestWrapper>
        <ProtectedRoute>
          <ProtectedContent />
        </ProtectedRoute>
      </TestWrapper>
    )

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login')
    })
  })

  it('should render content when user is authenticated', async () => {
    const mockUser = {
      id: '1',
      email: 'user@example.com',
      role: 'user',
      is_active: true,
      has_2fa: false,
    }

    localStorage.setItem('access_token', 'mock_token')
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => mockUser,
    })

    render(
      <TestWrapper>
        <ProtectedRoute>
          <ProtectedContent />
        </ProtectedRoute>
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByTestId('protected-content')).toBeInTheDocument()
    })
  })

  it('should show access denied for insufficient role', async () => {
    const mockUser = {
      id: '1',
      email: 'user@example.com',
      role: 'user',
      is_active: true,
      has_2fa: false,
    }

    localStorage.setItem('access_token', 'mock_token')
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => mockUser,
    })

    render(
      <TestWrapper>
        <ProtectedRoute requiredRole="admin">
          <AdminContent />
        </ProtectedRoute>
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('Acesso Negado')).toBeInTheDocument()
      expect(screen.queryByTestId('admin-content')).not.toBeInTheDocument()
    })
  })

  it('should allow access with sufficient role', async () => {
    const mockAdmin = {
      id: '1',
      email: 'admin@example.com',
      role: 'admin',
      is_active: true,
      has_2fa: false,
    }

    localStorage.setItem('access_token', 'mock_token')
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => mockAdmin,
    })

    render(
      <TestWrapper>
        <ProtectedRoute requiredRole="admin">
          <AdminContent />
        </ProtectedRoute>
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByTestId('admin-content')).toBeInTheDocument()
    })
  })

  it('should redirect to custom path when specified', async () => {
    render(
      <TestWrapper>
        <ProtectedRoute redirectTo="/custom-login">
          <ProtectedContent />
        </ProtectedRoute>
      </TestWrapper>
    )

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/custom-login')
    })
  })
})

describe('PermissionGuard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn()
    localStorage.clear()
    setTestNodeEnv('development')
  })

  it('should render nothing when user is not authenticated', async () => {
    render(
      <TestWrapper>
        <PermissionGuard>
          <AdminContent />
        </PermissionGuard>
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.queryByTestId('admin-content')).not.toBeInTheDocument()
    })
  })

  it('should render content when user has required role', async () => {
    const mockAdmin = {
      id: '1',
      email: 'admin@example.com',
      role: 'admin',
      is_active: true,
      has_2fa: false,
    }

    localStorage.setItem('access_token', 'mock_token')
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => mockAdmin,
    })

    render(
      <TestWrapper>
        <PermissionGuard requiredRole="admin">
          <AdminContent />
        </PermissionGuard>
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByTestId('admin-content')).toBeInTheDocument()
    })
  })
})

describe('RoleGuard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn()
    localStorage.clear()
    setTestNodeEnv('development')
  })

  it('should render content when user has one of allowed roles', async () => {
    const mockAdmin = {
      id: '1',
      email: 'admin@example.com',
      role: 'admin',
      is_active: true,
      has_2fa: false,
    }

    localStorage.setItem('access_token', 'mock_token')
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => mockAdmin,
    })

    render(
      <TestWrapper>
        <RoleGuard roles={['admin', 'sysadmin']}>
          <AdminContent />
        </RoleGuard>
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByTestId('admin-content')).toBeInTheDocument()
    })
  })

  it('should not render content when user role is not in allowed list', async () => {
    const mockUser = {
      id: '1',
      email: 'user@example.com',
      role: 'user',
      is_active: true,
      has_2fa: false,
    }

    localStorage.setItem('access_token', 'mock_token')
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => mockUser,
    })

    render(
      <TestWrapper>
        <RoleGuard roles={['admin', 'sysadmin']}>
          <AdminContent />
        </RoleGuard>
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.queryByTestId('admin-content')).not.toBeInTheDocument()
    })
  })
})
