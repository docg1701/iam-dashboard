/**
 * Test utilities and helpers for permission system testing
 * 
 * This file provides reusable functions for mocking permission-related 
 * functionality across different test scenarios.
 */

import { vi } from 'vitest'
import { AgentName, UserPermissionMatrix, PermissionOperation } from '@/types/permissions'

/**
 * Creates a mock UserPermissionMatrix with customizable permissions
 */
export const createMockUserPermissionMatrix = (
  userId: string = 'test-user-id',
  customPermissions?: Partial<UserPermissionMatrix['permissions']>
): UserPermissionMatrix => ({
  user_id: userId,
  permissions: {
    [AgentName.CLIENT_MANAGEMENT]: { create: true, read: true, update: true, delete: false },
    [AgentName.PDF_PROCESSING]: { create: false, read: true, update: false, delete: false },
    [AgentName.REPORTS_ANALYSIS]: { create: false, read: true, update: false, delete: false },
    [AgentName.AUDIO_RECORDING]: { create: false, read: false, update: false, delete: false },
    ...customPermissions,
  },
  last_updated: '2024-01-01T00:00:00Z',
})

/**
 * Creates a mock useUserPermissions hook return value
 */
export const createMockUseUserPermissions = (
  permissionMatrix?: UserPermissionMatrix | null,
  overrides?: Record<string, any>
) => ({
  permissions: permissionMatrix?.permissions || null,
  isLoading: false,
  error: null,
  lastUpdated: permissionMatrix ? new Date(permissionMatrix.last_updated) : null,
  hasPermission: vi.fn((agent: AgentName, operation: PermissionOperation) => {
    if (!permissionMatrix?.permissions) return false
    return permissionMatrix.permissions[agent]?.[operation] ?? false
  }),
  hasAgentPermission: vi.fn((agent: AgentName) => {
    if (!permissionMatrix?.permissions) return false
    const agentPerms = permissionMatrix.permissions[agent]
    return Object.values(agentPerms || {}).some(Boolean)
  }),
  getUserMatrix: vi.fn(() => permissionMatrix),
  refetch: vi.fn().mockResolvedValue(permissionMatrix),
  invalidate: vi.fn(),
  ...overrides,
})

/**
 * Mock functions for the PermissionAPI
 */
export const createMockPermissionAPI = () => ({
  User: {
    getUserPermissions: vi.fn(),
    updateUserPermissions: vi.fn(),
    deleteUserPermissions: vi.fn(),
  },
  Template: {
    getTemplates: vi.fn(),
    createTemplate: vi.fn(),
    updateTemplate: vi.fn(),
    deleteTemplate: vi.fn(),
    applyTemplate: vi.fn(),
  },
  Audit: {
    getUserAuditLogs: vi.fn(),
    getAgentAuditLogs: vi.fn(),
  },
  Utils: {
    hasPermission: vi.fn(),
    hasAgentPermission: vi.fn(),
    validatePermissions: vi.fn(),
  },
})

/**
 * Provides mock implementations for all permission-related hooks
 * Use this in tests that need comprehensive permission functionality
 */
export const mockPermissionHooks = (
  userMatrix?: UserPermissionMatrix,
  customMocks?: Record<string, any>
) => {
  const baseMatrix = userMatrix || createMockUserPermissionMatrix()
  
  return {
    useUserPermissions: vi.fn(() => createMockUseUserPermissions(baseMatrix)),
    usePermissionCheck: vi.fn((agent: AgentName, operation: PermissionOperation) => ({
      allowed: baseMatrix.permissions[agent]?.[operation] ?? false,
      isLoading: false,
      error: null,
      agent,
      operation,
    })),
    useAgentAccess: vi.fn((agent: AgentName) => ({
      hasAccess: Object.values(baseMatrix.permissions[agent] || {}).some(Boolean),
      permissions: baseMatrix.permissions[agent] || { create: false, read: false, update: false, delete: false },
      isLoading: false,
      error: null,
      agent,
    })),
    usePermissionMutations: vi.fn(() => ({
      updatePermission: {
        mutate: vi.fn(),
        mutateAsync: vi.fn().mockResolvedValue({}),
        isPending: false,
        isError: false,
        error: null,
        reset: vi.fn(),
      },
      createPermission: {
        mutate: vi.fn(),
        mutateAsync: vi.fn().mockResolvedValue({}),
        isPending: false,
        isError: false,
        error: null,
        reset: vi.fn(),
      },
      deletePermission: {
        mutate: vi.fn(),
        mutateAsync: vi.fn().mockResolvedValue({}),
        isPending: false,
        isError: false,
        error: null,
        reset: vi.fn(),
      },
      isLoading: false,
      error: null,
    })),
    usePermissionTemplates: vi.fn(() => ({
      templates: [
        { template_id: 'template-1', template_name: 'Admin', description: 'Admin template' },
        { template_id: 'template-2', template_name: 'User', description: 'User template' },
      ],
      total: 2,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
      applyTemplate: {
        mutate: vi.fn(),
        mutateAsync: vi.fn().mockResolvedValue({}),
        isPending: false,
        isError: false,
        error: null,
        reset: vi.fn(),
      },
      isApplying: false,
      applyError: null,
    })),
    usePermissionAudit: vi.fn(() => ({
      logs: [],
      total: 0,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    })),
    ...customMocks,
  }
}

/**
 * Test data generators
 */
export const generateTestUsers = (count: number = 3) => {
  return Array.from({ length: count }, (_, i) => ({
    user_id: `user-${i + 1}`,
    name: `Test User ${i + 1}`,
    email: `user${i + 1}@test.com`,
    role: i === 0 ? 'admin' : 'user',
    is_active: true,
  }))
}

export const generateTestAuditLogs = (count: number = 5) => {
  return Array.from({ length: count }, (_, i) => ({
    log_id: `log-${i + 1}`,
    user_id: `user-${(i % 3) + 1}`,
    agent: Object.values(AgentName)[i % 4],
    operation: Object.values(['create', 'read', 'update', 'delete'])[i % 4] as PermissionOperation,
    timestamp: new Date(Date.now() - i * 3600000).toISOString(),
    success: i % 5 !== 0, // 80% success rate
    details: `Test operation ${i + 1}`,
  }))
}

/**
 * Cleanup function for tests
 */
export const cleanupTest = () => {
  vi.clearAllMocks()
  
  // Clean up any DOM elements created during tests
  const testContainers = document.querySelectorAll('[data-testid*="test"]')
  testContainers.forEach(container => {
    if (container.parentNode) {
      container.parentNode.removeChild(container)
    }
  })
}

/**
 * Wait utility for async operations in tests
 */
export const waitForAsync = (ms: number = 100) => 
  new Promise(resolve => setTimeout(resolve, ms))