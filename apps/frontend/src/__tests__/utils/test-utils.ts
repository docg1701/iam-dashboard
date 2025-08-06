/**
 * Test Utilities for Permission System Components
 * 
 * Provides common testing utilities, custom matchers, and helper functions
 * for testing permission-related components and functionality.
 */

import { vi } from 'vitest'
import { render, RenderOptions } from '@testing-library/react'
import { TestProviders } from '../mocks/test-providers'
import {
  AgentName,
  UserPermissionMatrix,
  PermissionActions,
  UserAgentPermission,
  PermissionTemplate,
  PermissionAuditLog,
  DEFAULT_PERMISSIONS,
  DEFAULT_AGENT_PERMISSIONS,
} from '@/types/permissions'

// Re-export everything from React Testing Library
export * from '@testing-library/react'

// Custom render function with providers
export const renderWithProviders = (
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => {
  return render(ui, {
    wrapper: TestProviders,
    ...options,
  })
}

// Mock data factories
export const createMockUser = (overrides: any = {}) => ({
  user_id: 'test-user-id',
  email: 'test@example.com',
  full_name: 'Test User',
  role: 'user',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: null,
  ...overrides,
})

export const createMockUsers = (count: number = 3) => {
  return Array.from({ length: count }, (_, index) => createMockUser({
    user_id: `user-${index + 1}`,
    email: `user${index + 1}@example.com`,
    full_name: `User ${index + 1}`,
    role: index === 0 ? 'admin' : 'user',
  }))
}

export const createMockPermissionActions = (overrides: Partial<PermissionActions> = {}): PermissionActions => ({
  ...DEFAULT_PERMISSIONS,
  ...overrides,
})

export const createMockUserPermissionMatrix = (
  userId: string = 'test-user-id',
  overrides: Partial<UserPermissionMatrix> = {}
): UserPermissionMatrix => ({
  user_id: userId,
  permissions: {
    [AgentName.CLIENT_MANAGEMENT]: createMockPermissionActions({ create: true, read: true, update: true }),
    [AgentName.PDF_PROCESSING]: createMockPermissionActions({ read: true }),
    [AgentName.REPORTS_ANALYSIS]: createMockPermissionActions({ read: true }),
    [AgentName.AUDIO_RECORDING]: createMockPermissionActions(),
  },
  last_updated: '2024-01-01T00:00:00Z',
  ...overrides,
})

export const createMockUserAgentPermission = (
  userId: string = 'test-user-id',
  agentName: AgentName = AgentName.CLIENT_MANAGEMENT,
  overrides: Partial<UserAgentPermission> = {}
): UserAgentPermission => ({
  permission_id: `perm-${userId}-${agentName}`,
  user_id: userId,
  agent_name: agentName,
  permissions: createMockPermissionActions({ create: true, read: true, update: true }),
  created_by_user_id: 'admin-user-id',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: null,
  ...overrides,
})

export const createMockPermissionTemplate = (
  templateId: string = 'template-1',
  overrides: Partial<PermissionTemplate> = {}
): PermissionTemplate => ({
  template_id: templateId,
  template_name: 'Standard User',
  description: 'Standard user permissions template',
  permissions: {
    [AgentName.CLIENT_MANAGEMENT]: createMockPermissionActions({ create: true, read: true, update: true }),
    [AgentName.PDF_PROCESSING]: createMockPermissionActions({ read: true }),
    [AgentName.REPORTS_ANALYSIS]: createMockPermissionActions({ read: true }),
    [AgentName.AUDIO_RECORDING]: DEFAULT_PERMISSIONS,
  },
  is_system_template: false,
  created_by_user_id: 'admin-user-id',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: null,
  ...overrides,
})

export const createMockAuditLog = (
  userId: string = 'test-user-id',
  agentName: AgentName = AgentName.CLIENT_MANAGEMENT,
  overrides: Partial<PermissionAuditLog> = {}
): PermissionAuditLog => ({
  audit_id: `audit-${Date.now()}`,
  user_id: userId,
  agent_name: agentName,
  action: 'UPDATE',
  old_permissions: DEFAULT_PERMISSIONS,
  new_permissions: createMockPermissionActions({ create: true, read: true, update: true }),
  changed_by_user_id: 'admin-user-id',
  change_reason: 'Permission update via admin panel',
  created_at: new Date().toISOString(),
  ...overrides,
})

// Test utilities for permission components
export const waitForLoadingToFinish = async () => {
  // Wait for any loading states to complete
  await new Promise(resolve => setTimeout(resolve, 0))
}

export const mockApiResponse = <T>(data: T, delay: number = 0): Promise<T> => {
  return new Promise((resolve) => {
    setTimeout(() => resolve(data), delay)
  })
}

export const mockApiError = (message: string = 'API Error', status: number = 500): Promise<never> => {
  return Promise.reject({
    message,
    status,
    response: {
      status,
      data: { message },
    },
  })
}

// Common test assertions
export const expectElementToBeVisible = (element: HTMLElement) => {
  expect(element).toBeInTheDocument()
  expect(element).toBeVisible()
}

export const expectElementToHaveText = (element: HTMLElement, text: string | RegExp) => {
  expect(element).toBeInTheDocument()
  expect(element).toHaveTextContent(text)
}

export const expectButtonToBeEnabled = (button: HTMLElement) => {
  expect(button).toBeInTheDocument()
  expect(button).toBeEnabled()
}

export const expectButtonToBeDisabled = (button: HTMLElement) => {
  expect(button).toBeInTheDocument()
  expect(button).toBeDisabled()
}

// Permission-specific test utilities
export const expectPermissionMatrixToRender = (container: HTMLElement) => {
  expect(container.querySelector('[data-testid="table"]')).toBeInTheDocument()
}

export const expectDialogToBeOpen = (container: HTMLElement) => {
  expect(container.querySelector('[data-testid="dialog"]')).toBeInTheDocument()
  expect(container.querySelector('[data-testid="dialog-content"]')).toBeInTheDocument()
}

export const expectAlertToBeVisible = (container: HTMLElement, type: 'error' | 'warning' | 'info' = 'error') => {
  const alert = container.querySelector('[data-testid="alert"]')
  expect(alert).toBeInTheDocument()
  expect(alert).toBeVisible()
}

export const expectLoadingSpinnerToBeVisible = (container: HTMLElement) => {
  const spinner = container.querySelector('[data-testid="lucide-icon"]') || 
                   container.querySelector('[data-testid="skeleton"]')
  expect(spinner).toBeInTheDocument()
}

// Form testing utilities
export const fillFormInput = async (input: HTMLElement, value: string) => {
  const { fireEvent } = await import('@testing-library/react')
  fireEvent.change(input, { target: { value } })
}

export const clickButton = async (button: HTMLElement) => {
  const { fireEvent } = await import('@testing-library/react')
  fireEvent.click(button)
}

export const submitForm = async (form: HTMLElement) => {
  const { fireEvent } = await import('@testing-library/react')
  fireEvent.submit(form)
}

// Mock implementations for common hooks
export const createMockUseUserPermissions = (permissions: UserPermissionMatrix | null = null) => {
  return {
    permissions: permissions?.permissions || null,
    isLoading: false,
    error: null,
    lastUpdated: permissions ? new Date(permissions.last_updated) : null,
    hasPermission: vi.fn(() => true),
    hasAgentPermission: vi.fn(() => true),
    getUserMatrix: vi.fn(() => permissions),
    refetch: vi.fn(),
    invalidate: vi.fn(),
  }
}

export const createMockUseMutation = (options: any = {}) => {
  return {
    mutate: vi.fn(),
    mutateAsync: vi.fn().mockResolvedValue({}),
    isLoading: false,
    isPending: false,
    isError: false,
    isSuccess: false,
    error: null,
    data: null,
    reset: vi.fn(),
    ...options,
  }
}

export const createMockUseQuery = (options: any = {}) => {
  return {
    data: null,
    isLoading: false,
    isError: false,
    error: null,
    refetch: vi.fn(),
    isFetching: false,
    isSuccess: true,
    ...options,
  }
}

// Agent names for testing
export const AGENT_NAMES = Object.values(AgentName)

// Common test data sets
export const TEST_USERS = createMockUsers(5)
export const TEST_PERMISSION_MATRIX = createMockUserPermissionMatrix()
export const TEST_PERMISSION_TEMPLATES = [
  createMockPermissionTemplate('template-1', { template_name: 'Admin' }),
  createMockPermissionTemplate('template-2', { template_name: 'User' }),
  createMockPermissionTemplate('template-3', { template_name: 'Read Only' }),
]

// Environment setup for tests
export const setupTestEnvironment = () => {
  // Suppress console errors and warnings in tests
  const originalError = console.error
  const originalWarn = console.warn
  
  beforeEach(() => {
    console.error = vi.fn()
    console.warn = vi.fn()
  })
  
  afterEach(() => {
    console.error = originalError
    console.warn = originalWarn
    vi.clearAllMocks()
  })
}

// Custom matchers (extend jest-dom matchers)
export const customMatchers = {
  toHavePermission: (permissions: PermissionActions, operation: keyof PermissionActions) => {
    const pass = permissions[operation] === true
    return {
      pass,
      message: () => 
        pass 
          ? `Expected permissions to NOT have ${operation} permission`
          : `Expected permissions to have ${operation} permission`
    }
  }
}

// Default export for convenience
export default {
  renderWithProviders,
  createMockUser,
  createMockUsers,
  createMockUserPermissionMatrix,
  createMockPermissionTemplate,
  waitForLoadingToFinish,
  TEST_USERS,
  TEST_PERMISSION_MATRIX,
  TEST_PERMISSION_TEMPLATES,
}