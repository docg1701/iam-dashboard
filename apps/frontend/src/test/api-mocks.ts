/**
 * Centralized API Mock Helper Utilities
 * 
 * Provides proper API response structures, mock data factories, and setup functions
 * for TanStack Query testing. Only mocks external API responses - never internal components.
 */

import { vi } from 'vitest'
import {
  AgentName,
  PermissionActions,
  UserAgentPermission,
  PermissionTemplate,
  PermissionAuditLog,
  UserPermissionMatrix,
  BulkPermissionAssignResponse,
  PermissionCheckResponse,
  DEFAULT_AGENT_PERMISSIONS,
} from '@/types/permissions'

// Re-export types for convenience in tests
export { AgentName } from '@/types/permissions'

// ============================================================================
// Mock Data Factories
// ============================================================================

/**
 * Create mock user data
 */
export const createMockUser = (overrides?: Partial<any>) => ({
  user_id: '123e4567-e89b-12d3-a456-426614174000',
  email: 'joao.silva@exemplo.com',
  full_name: 'João da Silva',
  role: 'user' as const,
  is_active: true,
  totp_enabled: false,
  created_at: '2024-01-15T10:00:00Z',
  updated_at: '2024-01-15T10:00:00Z',
  ...overrides,
})

/**
 * Create mock admin user data
 */
export const createMockAdminUser = (overrides?: Partial<any>) => ({
  user_id: 'admin-123e4567-e89b-12d3-a456-426614174001',
  email: 'admin@empresa.com',
  full_name: 'Maria Administradora',
  role: 'admin' as const,
  is_active: true,
  totp_enabled: true,
  created_at: '2024-01-01T08:00:00Z',
  updated_at: '2024-01-01T08:00:00Z',
  ...overrides,
})

/**
 * Create mock permission actions
 */
export const createMockPermissions = (overrides?: Partial<PermissionActions>): PermissionActions => ({
  create: false,
  read: true,
  update: false,
  delete: false,
  ...overrides,
})

/**
 * Create full mock user permission matrix
 */
export const createMockUserPermissionMatrix = (
  userId?: string,
  overrides?: Partial<Record<AgentName, PermissionActions>>
): UserPermissionMatrix => ({
  user_id: userId || '123e4567-e89b-12d3-a456-426614174000',
  permissions: {
    [AgentName.CLIENT_MANAGEMENT]: createMockPermissions({ create: true, read: true, update: true }),
    [AgentName.PDF_PROCESSING]: createMockPermissions({ read: true }),
    [AgentName.REPORTS_ANALYSIS]: createMockPermissions({ read: true }),
    [AgentName.AUDIO_RECORDING]: createMockPermissions(),
    ...overrides,
  },
  last_updated: '2024-01-15T14:30:00Z',
})

/**
 * Create mock user agent permission
 */
export const createMockUserAgentPermission = (
  userId?: string,
  agent?: AgentName,
  permissions?: Partial<PermissionActions>
): UserAgentPermission => ({
  permission_id: `perm-${agent || AgentName.CLIENT_MANAGEMENT}-${userId || '123'}`,
  user_id: userId || '123e4567-e89b-12d3-a456-426614174000',
  agent_name: agent || AgentName.CLIENT_MANAGEMENT,
  permissions: createMockPermissions(permissions),
  created_by_user_id: 'admin-123e4567-e89b-12d3-a456-426614174001',
  created_at: '2024-01-15T10:00:00Z',
  updated_at: '2024-01-15T14:30:00Z',
})

/**
 * Create mock permission template
 */
export const createMockPermissionTemplate = (overrides?: Partial<PermissionTemplate>): PermissionTemplate => ({
  template_id: 'template-123e4567-e89b-12d3-a456-426614174000',
  template_name: 'Usuário Padrão',
  description: 'Permissões básicas para usuários regulares do sistema',
  permissions: {
    [AgentName.CLIENT_MANAGEMENT]: createMockPermissions({ read: true, update: true }),
    [AgentName.PDF_PROCESSING]: createMockPermissions({ read: true }),
    [AgentName.REPORTS_ANALYSIS]: createMockPermissions({ read: true }),
    [AgentName.AUDIO_RECORDING]: createMockPermissions(),
  },
  is_system_template: false,
  created_by_user_id: 'admin-123e4567-e89b-12d3-a456-426614174001',
  created_at: '2024-01-01T08:00:00Z',
  updated_at: '2024-01-15T16:00:00Z',
  ...overrides,
})

/**
 * Create mock audit log entry
 */
export const createMockAuditLog = (overrides?: Partial<PermissionAuditLog>): PermissionAuditLog => ({
  audit_id: 'audit-123e4567-e89b-12d3-a456-426614174000',
  user_id: '123e4567-e89b-12d3-a456-426614174000',
  agent_name: AgentName.CLIENT_MANAGEMENT,
  action: 'PERMISSION_UPDATED',
  old_permissions: createMockPermissions({ read: true }),
  new_permissions: createMockPermissions({ read: true, update: true }),
  changed_by_user_id: 'admin-123e4567-e89b-12d3-a456-426614174001',
  change_reason: 'Usuário precisa editar clientes para sua função atual',
  created_at: '2024-01-15T14:30:00Z',
  ...overrides,
})

// ============================================================================
// API Response Factories
// ============================================================================

/**
 * Create mock API response structure for user permissions
 */
export const createMockUserPermissionsResponse = (userId?: string, permissions?: UserAgentPermission[]) => ({
  user_id: userId || '123e4567-e89b-12d3-a456-426614174000',
  permissions: permissions || [
    createMockUserAgentPermission(userId, AgentName.CLIENT_MANAGEMENT, { create: true, read: true, update: true }),
    createMockUserAgentPermission(userId, AgentName.PDF_PROCESSING, { read: true }),
  ],
  last_updated: '2024-01-15T14:30:00Z',
})

/**
 * Create mock API response for permission templates
 */
export const createMockTemplatesResponse = (templates?: PermissionTemplate[]) => ({
  templates: templates || [
    createMockPermissionTemplate({ template_name: 'Usuário Básico', is_system_template: true }),
    createMockPermissionTemplate({ 
      template_id: 'template-admin',
      template_name: 'Administrador',
      permissions: {
        [AgentName.CLIENT_MANAGEMENT]: createMockPermissions({ create: true, read: true, update: true, delete: true }),
        [AgentName.PDF_PROCESSING]: createMockPermissions({ create: true, read: true, update: true }),
        [AgentName.REPORTS_ANALYSIS]: createMockPermissions({ create: true, read: true, update: true }),
        [AgentName.AUDIO_RECORDING]: createMockPermissions({ read: true, update: true }),
      },
      is_system_template: true,
    }),
  ],
  total: templates?.length || 2,
})

/**
 * Create mock API response for audit logs
 */
export const createMockAuditLogsResponse = (logs?: PermissionAuditLog[], options?: {
  total?: number
  limit?: number
  offset?: number
}) => ({
  logs: logs || [
    createMockAuditLog({ action: 'PERMISSION_GRANTED' }),
    createMockAuditLog({ 
      action: 'PERMISSION_REVOKED',
      old_permissions: createMockPermissions({ create: true, read: true, update: true }),
      new_permissions: createMockPermissions({ read: true }),
      change_reason: 'Redução de privilégios por mudança de função',
      created_at: '2024-01-14T09:15:00Z',
    }),
    createMockAuditLog({
      action: 'PERMISSION_UPDATED',
      agent_name: AgentName.PDF_PROCESSING,
      old_permissions: null,
      new_permissions: createMockPermissions({ read: true }),
      change_reason: 'Primeira concessão de acesso ao processamento de PDFs',
      created_at: '2024-01-13T11:22:00Z',
    }),
  ],
  total: options?.total || 3,
  limit: options?.limit || 50,
  offset: options?.offset || 0,
})

/**
 * Create mock bulk permission assign response
 */
export const createMockBulkAssignResponse = (
  successCount?: number,
  errorCount?: number
): BulkPermissionAssignResponse => ({
  success_count: successCount || 5,
  error_count: errorCount || 0,
  errors: errorCount ? [
    { user_id: 'user-error-1', error: 'Usuário não encontrado' },
    { user_id: 'user-error-2', error: 'Permissão inválida para este usuário' },
  ] : [],
})

/**
 * Create mock permission check response
 */
export const createMockPermissionCheckResponse = (
  allowed?: boolean,
  userId?: string,
  agent?: AgentName,
  operation?: keyof PermissionActions
): PermissionCheckResponse => ({
  allowed: allowed !== false,
  user_id: userId || '123e4567-e89b-12d3-a456-426614174000',
  agent_name: agent || AgentName.CLIENT_MANAGEMENT,
  operation: operation || 'read',
})

// ============================================================================
// Mock Setup Functions
// ============================================================================

/**
 * Setup mocks for permission API tests
 */
export const setupPermissionAPITest = (options?: {
  userId?: string
  userPermissions?: UserAgentPermission[]
  shouldFail?: boolean
  customResponse?: any
}) => {
  const mockFetch = vi.mocked(global.fetch)
  
  if (options?.shouldFail) {
    mockFetch.mockRejectedValueOnce(new Error('Failed to fetch permissions'))
    return
  }

  const response = options?.customResponse || 
    createMockUserPermissionsResponse(options?.userId, options?.userPermissions)

  mockFetch.mockResolvedValueOnce({
    ok: true,
    status: 200,
    json: () => Promise.resolve(response),
  } as Response)
}

/**
 * Setup mocks for user API tests
 */
export const setupUserAPITest = (options?: {
  user?: any
  shouldFail?: boolean
  customResponse?: any
}) => {
  const mockFetch = vi.mocked(global.fetch)
  
  if (options?.shouldFail) {
    mockFetch.mockRejectedValueOnce(new Error('Failed to fetch user'))
    return
  }

  const response = options?.customResponse || { user: options?.user || createMockAdminUser() }

  mockFetch.mockResolvedValueOnce({
    ok: true,
    status: 200,
    json: () => Promise.resolve(response),
  } as Response)
}

/**
 * Setup mocks for permission template API tests
 */
export const setupTemplateAPITest = (options?: {
  templates?: PermissionTemplate[]
  shouldFail?: boolean
  customResponse?: any
}) => {
  const mockFetch = vi.mocked(global.fetch)
  
  if (options?.shouldFail) {
    mockFetch.mockRejectedValueOnce(new Error('Failed to fetch templates'))
    return
  }

  const response = options?.customResponse || createMockTemplatesResponse(options?.templates)

  mockFetch.mockResolvedValueOnce({
    ok: true,
    status: 200,
    json: () => Promise.resolve(response),
  } as Response)
}

/**
 * Setup mocks for audit log API tests
 */
export const setupAuditAPITest = (options?: {
  logs?: PermissionAuditLog[]
  shouldFail?: boolean
  customResponse?: any
  total?: number
  limit?: number
  offset?: number
}) => {
  const mockFetch = vi.mocked(global.fetch)
  
  if (options?.shouldFail) {
    mockFetch.mockRejectedValueOnce(new Error('Failed to fetch audit logs'))
    return
  }

  const response = options?.customResponse || 
    createMockAuditLogsResponse(options?.logs, {
      total: options?.total,
      limit: options?.limit,
      offset: options?.offset,
    })

  mockFetch.mockResolvedValueOnce({
    ok: true,
    status: 200,
    json: () => Promise.resolve(response),
  } as Response)
}

/**
 * Setup mock for successful permission save
 */
export const setupPermissionSaveTest = (options?: {
  shouldFail?: boolean
  customResponse?: any
  method?: 'POST' | 'PUT'
}) => {
  const mockFetch = vi.mocked(global.fetch)
  
  if (options?.shouldFail) {
    mockFetch.mockRejectedValueOnce(new Error('Failed to save permission'))
    return
  }

  const response = options?.customResponse || { success: true }

  mockFetch.mockResolvedValueOnce({
    ok: true,
    status: options?.method === 'POST' ? 201 : 200,
    json: () => Promise.resolve(response),
  } as Response)
}

/**
 * Setup comprehensive mocks for permission matrix component
 */
export const setupPermissionMatrixTest = (options?: {
  users?: any[]
  userPermissions?: Record<string, UserPermissionMatrix>
  shouldFailUsers?: boolean
  shouldFailPermissions?: boolean
}) => {
  const mockFetch = vi.mocked(global.fetch)
  
  // Setup authentication mock first
  if (!options?.shouldFailUsers) {
    setupUserAPITest({ user: createMockAdminUser() })
  } else {
    setupUserAPITest({ shouldFail: true })
  }

  // Setup permissions mock for each user
  const users = options?.users || [createMockUser()]
  users.forEach((user, index) => {
    if (!options?.shouldFailPermissions) {
      const userMatrix = options?.userPermissions?.[user.user_id] || 
        createMockUserPermissionMatrix(user.user_id)
      
      // Mock the permission matrix API call for this user
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(createMockUserPermissionsResponse(user.user_id, [
          createMockUserAgentPermission(user.user_id, AgentName.CLIENT_MANAGEMENT, userMatrix.permissions[AgentName.CLIENT_MANAGEMENT]),
          createMockUserAgentPermission(user.user_id, AgentName.PDF_PROCESSING, userMatrix.permissions[AgentName.PDF_PROCESSING]),
          createMockUserAgentPermission(user.user_id, AgentName.REPORTS_ANALYSIS, userMatrix.permissions[AgentName.REPORTS_ANALYSIS]),
          createMockUserAgentPermission(user.user_id, AgentName.AUDIO_RECORDING, userMatrix.permissions[AgentName.AUDIO_RECORDING]),
        ])),
      } as Response)
    } else {
      mockFetch.mockRejectedValueOnce(new Error(`Failed to fetch permissions for user ${user.user_id}`))
    }
  })
}

/**
 * Setup mocks for bulk permission operations
 */
export const setupBulkPermissionTest = (options?: {
  shouldFail?: boolean
  successCount?: number
  errorCount?: number
  customResponse?: any
}) => {
  const mockFetch = vi.mocked(global.fetch)
  
  if (options?.shouldFail) {
    mockFetch.mockRejectedValueOnce(new Error('Bulk operation failed'))
    return
  }

  const response = options?.customResponse || 
    createMockBulkAssignResponse(options?.successCount, options?.errorCount)

  mockFetch.mockResolvedValueOnce({
    ok: true,
    status: 200,
    json: () => Promise.resolve(response),
  } as Response)
}

// ============================================================================
// TanStack Query Key Helpers
// ============================================================================

/**
 * Standard query keys used by the application
 */
export const QueryKeys = {
  // User permissions
  userPermissions: (userId: string) => ['user-permissions', userId],
  userAgentPermission: (userId: string, agent: AgentName) => ['user-permissions', userId, 'agents', agent],
  permissionMatrix: (userIds: string[]) => ['permission-matrix', userIds],
  
  // Templates
  permissionTemplates: () => ['permission-templates'],
  permissionTemplate: (templateId: string) => ['permission-templates', templateId],
  
  // Audit logs
  userAuditLogs: (userId: string) => ['permission-audit', 'users', userId],
  agentAuditLogs: (agent: AgentName) => ['permission-audit', 'agents', agent],
  recentAuditLogs: () => ['permission-audit', 'recent'],
  
  // Permission checks
  permissionCheck: (userId: string, agent: AgentName, operation: keyof PermissionActions) => 
    ['permission-check', userId, agent, operation],
} as const

/**
 * Mock query client configuration for tests
 */
export const createTestQueryClientConfig = () => ({
  defaultOptions: {
    queries: {
      retry: false,
      gcTime: 0,
      staleTime: 0,
    },
    mutations: {
      retry: false,
    },
  },
  logger: {
    log: () => {},
    warn: () => {},
    error: () => {},
  },
})

// ============================================================================
// Error Response Helpers
// ============================================================================

/**
 * Create mock API error response
 */
export const createMockErrorResponse = (
  status: number,
  message: string,
  details?: Record<string, any>
) => {
  const mockFetch = vi.mocked(global.fetch)
  
  mockFetch.mockResolvedValueOnce({
    ok: false,
    status,
    json: () => Promise.resolve({
      detail: message,
      ...details,
    }),
  } as Response)
}

/**
 * Create mock network error
 */
export const createMockNetworkError = (message = 'Network error') => {
  const mockFetch = vi.mocked(global.fetch)
  mockFetch.mockRejectedValueOnce(new Error(message))
}

// ============================================================================
// Test Data Presets
// ============================================================================

/**
 * Preset data for common test scenarios
 */
export const TestDataPresets = {
  // User with full admin permissions
  adminUserWithFullPermissions: {
    user: createMockAdminUser(),
    permissions: createMockUserPermissionMatrix(undefined, {
      [AgentName.CLIENT_MANAGEMENT]: createMockPermissions({ create: true, read: true, update: true, delete: true }),
      [AgentName.PDF_PROCESSING]: createMockPermissions({ create: true, read: true, update: true, delete: true }),
      [AgentName.REPORTS_ANALYSIS]: createMockPermissions({ create: true, read: true, update: true, delete: true }),
      [AgentName.AUDIO_RECORDING]: createMockPermissions({ create: true, read: true, update: true, delete: true }),
    }),
  },
  
  // Regular user with limited permissions
  userWithLimitedPermissions: {
    user: createMockUser(),
    permissions: createMockUserPermissionMatrix(undefined, {
      [AgentName.CLIENT_MANAGEMENT]: createMockPermissions({ read: true, update: true }),
      [AgentName.PDF_PROCESSING]: createMockPermissions({ read: true }),
      [AgentName.REPORTS_ANALYSIS]: createMockPermissions({ read: true }),
      [AgentName.AUDIO_RECORDING]: createMockPermissions(),
    }),
  },
  
  // User with no permissions
  userWithNoPermissions: {
    user: createMockUser({ role: 'user' }),
    permissions: createMockUserPermissionMatrix(undefined, DEFAULT_AGENT_PERMISSIONS),
  },
  
  // Multiple users for matrix testing
  multipleUsersForMatrix: [
    createMockUser({ user_id: 'user-1', full_name: 'Ana Santos', email: 'ana@empresa.com' }),
    createMockUser({ user_id: 'user-2', full_name: 'Carlos Silva', email: 'carlos@empresa.com', role: 'admin' }),
    createMockUser({ user_id: 'user-3', full_name: 'Diana Costa', email: 'diana@empresa.com', is_active: false }),
  ],
} as const

export default {
  // Factories
  createMockUser,
  createMockAdminUser,
  createMockPermissions,
  createMockUserPermissionMatrix,
  createMockUserAgentPermission,
  createMockPermissionTemplate,
  createMockAuditLog,
  
  // Response factories
  createMockUserPermissionsResponse,
  createMockTemplatesResponse,
  createMockAuditLogsResponse,
  createMockBulkAssignResponse,
  createMockPermissionCheckResponse,
  
  // Setup functions
  setupPermissionAPITest,
  setupUserAPITest,
  setupTemplateAPITest,
  setupAuditAPITest,
  setupPermissionSaveTest,
  setupPermissionMatrixTest,
  setupBulkPermissionTest,
  
  // Utilities
  QueryKeys,
  createTestQueryClientConfig,
  createMockErrorResponse,
  createMockNetworkError,
  TestDataPresets,
}