/**
 * Centralized API mocking for frontend tests
 * 
 * Provides consistent mock implementations for all API functions,
 * eliminating ECONNREFUSED errors from real HTTP calls during testing.
 */

import { vi } from 'vitest'
import {
  AgentName,
  UserPermissionMatrix,
  UserAgentPermission,
  PermissionTemplate,
  PermissionAuditLog,
  PermissionCheckResponse,
  BulkPermissionAssignResponse,
  DEFAULT_AGENT_PERMISSIONS,
  DEFAULT_PERMISSIONS,
} from '@/types/permissions'

// Mock data factories
export const createMockUserPermission = (
  userId: string = 'test-user-id',
  agentName: AgentName = AgentName.CLIENT_MANAGEMENT,
  overrides: Partial<UserAgentPermission> = {}
): UserAgentPermission => ({
  permission_id: 'perm-123',
  user_id: userId,
  agent_name: agentName,
  permissions: {
    create: true,
    read: true,
    update: false,
    delete: false,
  },
  created_by_user_id: 'admin-user-id',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: null,
  ...overrides,
})

export const createMockPermissionMatrix = (
  userId: string = 'test-user-id',
  overrides: Partial<UserPermissionMatrix> = {}
): UserPermissionMatrix => ({
  user_id: userId,
  permissions: {
    [AgentName.CLIENT_MANAGEMENT]: {
      create: true,
      read: true,
      update: true,
      delete: false,
    },
    [AgentName.PDF_PROCESSING]: {
      create: false,
      read: true,
      update: false,
      delete: false,
    },
    [AgentName.REPORTS_ANALYSIS]: {
      create: false,
      read: true,
      update: false,
      delete: false,
    },
    [AgentName.AUDIO_RECORDING]: {
      create: false,
      read: false,
      update: false,
      delete: false,
    },
  },
  last_updated: '2024-01-01T00:00:00Z',
  ...overrides,
})

export const createMockPermissionTemplate = (
  templateId: string = 'template-123',
  overrides: Partial<PermissionTemplate> = {}
): PermissionTemplate => ({
  template_id: templateId,
  template_name: 'Standard User',
  description: 'Standard user permissions template',
  permissions: {
    [AgentName.CLIENT_MANAGEMENT]: {
      create: true,
      read: true,
      update: true,
      delete: false,
    },
    [AgentName.PDF_PROCESSING]: {
      create: false,
      read: true,
      update: false,
      delete: false,
    },
    [AgentName.REPORTS_ANALYSIS]: DEFAULT_PERMISSIONS,
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
  audit_id: 'audit-123',
  user_id: userId,
  agent_name: agentName,
  action: 'UPDATE',
  old_permissions: DEFAULT_PERMISSIONS,
  new_permissions: {
    create: true,
    read: true,
    update: true,
    delete: false,
  },
  changed_by_user_id: 'admin-user-id',
  change_reason: 'Permission update via admin panel',
  created_at: '2024-01-01T00:00:00Z',
  ...overrides,
})

// API Client Mock
export const createMockApiClient = () => {
  return {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    patch: vi.fn(),
    setAuthToken: vi.fn(),
    removeAuthToken: vi.fn(),
  }
}

// Permission API Mocks
export const createMockUserPermissionAPI = () => {
  const mockGetUserPermissions = vi.fn().mockResolvedValue(createMockPermissionMatrix())
  const mockGetUserAgentPermission = vi.fn().mockResolvedValue(createMockUserPermission())
  const mockCreateUserPermission = vi.fn().mockResolvedValue(createMockUserPermission())
  const mockUpdateUserPermission = vi.fn().mockResolvedValue(createMockUserPermission())
  const mockDeleteUserPermission = vi.fn().mockResolvedValue(undefined)
  const mockCheckPermission = vi.fn().mockResolvedValue({
    allowed: true,
    user_id: 'test-user-id',
    agent_name: AgentName.CLIENT_MANAGEMENT,
    operation: 'create',
  } as PermissionCheckResponse)
  const mockBulkAssignPermissions = vi.fn().mockResolvedValue({
    success_count: 5,
    error_count: 0,
    errors: [],
  } as BulkPermissionAssignResponse)

  return {
    getUserPermissions: mockGetUserPermissions,
    getUserAgentPermission: mockGetUserAgentPermission,
    createUserPermission: mockCreateUserPermission,
    updateUserPermission: mockUpdateUserPermission,
    deleteUserPermission: mockDeleteUserPermission,
    checkPermission: mockCheckPermission,
    bulkAssignPermissions: mockBulkAssignPermissions,
  }
}

export const createMockPermissionTemplateAPI = () => {
  const mockGetTemplates = vi.fn().mockResolvedValue([
    createMockPermissionTemplate('template-1', { template_name: 'Admin' }),
    createMockPermissionTemplate('template-2', { template_name: 'User' }),
  ])
  const mockGetTemplate = vi.fn().mockResolvedValue(createMockPermissionTemplate())
  const mockCreateTemplate = vi.fn().mockResolvedValue(createMockPermissionTemplate())
  const mockUpdateTemplate = vi.fn().mockResolvedValue(createMockPermissionTemplate())
  const mockDeleteTemplate = vi.fn().mockResolvedValue(undefined)
  const mockApplyTemplateToUser = vi.fn().mockResolvedValue(createMockPermissionMatrix())

  return {
    getTemplates: mockGetTemplates,
    getTemplate: mockGetTemplate,
    createTemplate: mockCreateTemplate,
    updateTemplate: mockUpdateTemplate,
    deleteTemplate: mockDeleteTemplate,
    applyTemplateToUser: mockApplyTemplateToUser,
  }
}

export const createMockPermissionAuditAPI = () => {
  const mockGetUserAuditLogs = vi.fn().mockResolvedValue({
    logs: [createMockAuditLog()],
    total: 1,
    limit: 50,
    offset: 0,
  })
  const mockGetAgentAuditLogs = vi.fn().mockResolvedValue({
    logs: [createMockAuditLog()],
    total: 1,
    limit: 50,
    offset: 0,
  })
  const mockGetRecentChanges = vi.fn().mockResolvedValue([createMockAuditLog()])

  return {
    getUserAuditLogs: mockGetUserAuditLogs,
    getAgentAuditLogs: mockGetAgentAuditLogs,
    getRecentChanges: mockGetRecentChanges,
  }
}

export const createMockPermissionUtils = () => {
  const mockHasPermission = vi.fn().mockReturnValue(true)
  const mockHasAgentPermission = vi.fn().mockReturnValue(true)
  const mockMergePermissions = vi.fn().mockReturnValue(DEFAULT_AGENT_PERMISSIONS)
  const mockValidatePermissionMatrix = vi.fn().mockReturnValue(true)

  return {
    hasPermission: mockHasPermission,
    hasAgentPermission: mockHasAgentPermission,
    mergePermissions: mockMergePermissions,
    validatePermissionMatrix: mockValidatePermissionMatrix,
  }
}

// Combined Permission API Mock
export const createMockPermissionAPI = () => {
  return {
    User: createMockUserPermissionAPI(),
    Template: createMockPermissionTemplateAPI(),
    Audit: createMockPermissionAuditAPI(),
    Utils: createMockPermissionUtils(),
  }
}

// User API Mocks (for forms and other components)
export const createMockUserAPI = () => {
  return {
    getUsers: vi.fn().mockResolvedValue([
      { user_id: 'user-1', email: 'user1@example.com', full_name: 'User One' },
      { user_id: 'user-2', email: 'user2@example.com', full_name: 'User Two' },
      { user_id: 'user-3', email: 'user3@example.com', full_name: 'User Three' },
    ]),
    getUser: vi.fn().mockResolvedValue({
      user_id: 'test-user-id',
      email: 'test@example.com',
      full_name: 'Test User',
    }),
    createUser: vi.fn().mockResolvedValue({
      user_id: 'new-user-id',
      email: 'new@example.com',
      full_name: 'New User',
    }),
    updateUser: vi.fn().mockResolvedValue({
      user_id: 'test-user-id',
      email: 'updated@example.com',
      full_name: 'Updated User',
    }),
    deleteUser: vi.fn().mockResolvedValue(undefined),
  }
}

// Client API Mocks
export const createMockClientAPI = () => {
  return {
    getClients: vi.fn().mockResolvedValue([
      { client_id: 'client-1', name: 'Client One', ssn: '123-45-6789' },
      { client_id: 'client-2', name: 'Client Two', ssn: '987-65-4321' },
    ]),
    getClient: vi.fn().mockResolvedValue({
      client_id: 'test-client-id',
      name: 'Test Client',
      ssn: '123-45-6789',
    }),
    createClient: vi.fn().mockResolvedValue({
      client_id: 'new-client-id',
      name: 'New Client',
      ssn: '111-22-3333',
    }),
    updateClient: vi.fn().mockResolvedValue({
      client_id: 'test-client-id',
      name: 'Updated Client',
      ssn: '123-45-6789',
    }),
    deleteClient: vi.fn().mockResolvedValue(undefined),
  }
}

// Auth Store Mock
export const createMockAuthStore = () => {
  const store = {
    user: {
      user_id: 'test-user-id',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'admin',
    },
    token: 'mock-jwt-token',
    isAuthenticated: true,
    login: vi.fn(),
    logout: vi.fn(),
    refreshToken: vi.fn(),
    // Add getState method for zustand compatibility
    getState: vi.fn(() => store),
    setState: vi.fn(),
    subscribe: vi.fn(() => vi.fn()), // Return unsubscribe function
  }
  return store
}

// WebSocket Mock
export const createMockWebSocket = () => {
  return {
    send: vi.fn(),
    close: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    onopen: null as ((event: Event) => void) | null,
    onmessage: null as ((event: MessageEvent) => void) | null,
    onclose: null as ((event: CloseEvent) => void) | null,
    onerror: null as ((event: Event) => void) | null,
    readyState: WebSocket.OPEN,
  }
}

// Global mock setup function
export const setupGlobalMocks = () => {
  // Mock fetch
  global.fetch = vi.fn().mockRejectedValue(new Error('fetch should not be called in tests'))
  
  // Mock WebSocket
  global.WebSocket = vi.fn(() => createMockWebSocket()) as unknown as typeof WebSocket
  
  // Mock console methods to reduce noise in tests
  global.console.error = vi.fn()
  global.console.warn = vi.fn()
}

// Reset all mocks
export const resetAllMocks = () => {
  vi.clearAllMocks()
}