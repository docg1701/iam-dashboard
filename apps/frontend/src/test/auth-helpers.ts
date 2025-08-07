import useAuthStore from '@/store/authStore'
import type { User } from '@/types/auth'

/**
 * Auth Store Test Utilities
 * 
 * Provides standardized mock users and auth state management for tests.
 * Follows CLAUDE.md testing directives - NEVER mocks internal code,
 * only provides test data and state management utilities.
 */

// ============================================================================
// Mock User Factories
// ============================================================================

/**
 * Create a mock regular user with customizable properties
 */
export const createMockUser = (overrides: Partial<User> = {}): User => ({
  user_id: 'test-user-123',
  email: 'test@example.com',
  full_name: 'Test User',
  role: 'user',
  is_active: true,
  totp_enabled: false,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
  last_login: '2025-01-01T12:00:00Z',
  ...overrides
})

/**
 * Create a mock admin user with admin privileges
 */
export const createMockAdmin = (overrides: Partial<User> = {}): User => 
  createMockUser({ 
    user_id: 'admin-user-456',
    role: 'admin', 
    email: 'admin@example.com', 
    full_name: 'Admin User',
    totp_enabled: true,
    last_login: '2025-01-01T08:00:00Z',
    ...overrides 
  })

/**
 * Create a mock system administrator with full privileges
 */
export const createMockSysAdmin = (overrides: Partial<User> = {}): User =>
  createMockUser({ 
    user_id: 'sysadmin-user-789',
    role: 'sysadmin', 
    email: 'sysadmin@example.com', 
    full_name: 'System Administrator',
    totp_enabled: true,
    last_login: '2025-01-01T06:00:00Z',
    ...overrides 
  })

/**
 * Create an inactive user for testing access control
 */
export const createMockInactiveUser = (overrides: Partial<User> = {}): User =>
  createMockUser({
    user_id: 'inactive-user-000',
    email: 'inactive@example.com',
    full_name: 'Inactive User',
    is_active: false,
    last_login: '2024-12-01T00:00:00Z',
    ...overrides
  })

/**
 * Create a user with 2FA enabled for testing TOTP flows
 */
export const createMock2FAUser = (overrides: Partial<User> = {}): User =>
  createMockUser({
    user_id: '2fa-user-321',
    email: '2fa@example.com',
    full_name: '2FA User',
    totp_enabled: true,
    role: 'admin',
    last_login: '2025-01-01T10:00:00Z',
    ...overrides
  })

// ============================================================================
// Auth State Management Utilities
// ============================================================================

/**
 * Setup authenticated state in auth store
 * 
 * @param user - User object or null for unauthenticated state
 * @param token - JWT token string or null
 */
export const setupTestAuth = (user: User | null = null, token: string | null = null) => {
  useAuthStore.setState({
    user,
    token,
    isAuthenticated: !!user && !!token,
    isLoading: false,
    requires2FA: false,
    tempToken: null,
  })
}

/**
 * Clear all authentication state
 */
export const clearTestAuth = () => {
  useAuthStore.setState({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: false,
    requires2FA: false,
    tempToken: null,
  })
}

/**
 * Setup authenticated user with specified role
 */
export const setupAuthenticatedUser = (role: 'user' | 'admin' | 'sysadmin' = 'user') => {
  const user = role === 'admin' ? createMockAdmin() : 
                role === 'sysadmin' ? createMockSysAdmin() : 
                createMockUser({ role })
                
  const token = `mock-jwt-token-${role}-${user.user_id}`
  setupTestAuth(user, token)
  return { user, token }
}

/**
 * Setup unauthenticated state (explicit for clarity)
 */
export const setupUnauthenticatedUser = () => {
  clearTestAuth()
}

/**
 * Setup 2FA required state for testing TOTP flows
 */
export const setup2FARequiredState = (tempToken: string = 'temp-token-123') => {
  useAuthStore.setState({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: false,
    requires2FA: true,
    tempToken,
  })
  return tempToken
}

/**
 * Setup loading state for testing async auth operations
 */
export const setupAuthLoading = (isLoading: boolean = true) => {
  useAuthStore.setState({
    isLoading,
  })
}

// ============================================================================
// Permission Test Utilities
// ============================================================================

/**
 * Test role hierarchy validation
 * 
 * Validates that the role hierarchy is working correctly:
 * sysadmin > admin > user
 */
export const testRoleHierarchy = () => {
  const { hasPermission } = useAuthStore.getState()
  
  // Test sysadmin permissions
  setupAuthenticatedUser('sysadmin')
  const sysadminCanAdmin = hasPermission('admin')
  const sysadminCanUser = hasPermission('user')
  
  // Test admin permissions
  setupAuthenticatedUser('admin')
  const adminCanUser = hasPermission('user')
  const adminCannotSysAdmin = !hasPermission('sysadmin')
  
  // Test user permissions
  setupAuthenticatedUser('user')
  const userCannotAdmin = !hasPermission('admin')
  const userCannotSysAdmin = !hasPermission('sysadmin')
  
  return {
    sysadminCanAdmin,
    sysadminCanUser,
    adminCanUser,
    adminCannotSysAdmin,
    userCannotAdmin,
    userCannotSysAdmin
  }
}

// ============================================================================
// Auth Flow Test Scenarios
// ============================================================================

/**
 * Common auth test scenarios for different component test needs
 */
export const AuthScenarios = {
  // Successful login without 2FA
  simpleLogin: {
    user: createMockUser(),
    token: 'mock-jwt-simple-login',
    setup: () => setupAuthenticatedUser('user')
  },
  
  // Admin user with full permissions
  adminLogin: {
    user: createMockAdmin(),
    token: 'mock-jwt-admin-login',
    setup: () => setupAuthenticatedUser('admin')
  },
  
  // System admin with all permissions
  sysadminLogin: {
    user: createMockSysAdmin(),
    token: 'mock-jwt-sysadmin-login',
    setup: () => setupAuthenticatedUser('sysadmin')
  },
  
  // 2FA required flow
  twoFactorLogin: {
    tempToken: 'temp-token-2fa-123',
    setup: () => setup2FARequiredState('temp-token-2fa-123')
  },
  
  // Unauthenticated state
  noAuth: {
    setup: () => setupUnauthenticatedUser()
  },
  
  // Inactive user
  inactiveUser: {
    user: createMockInactiveUser(),
    setup: () => {
      const user = createMockInactiveUser()
      setupTestAuth(user, null) // Inactive users get no token
      return user
    }
  },
  
  // Loading state
  authLoading: {
    setup: () => setupAuthLoading(true)
  }
} as const

// ============================================================================
// Mock JWT Token Utilities
// ============================================================================

/**
 * Create a mock JWT token structure for testing token parsing
 */
export const createMockJWTToken = (payload: any = {}, expiresIn: number = 3600) => {
  const header = { alg: 'HS256', typ: 'JWT' }
  const defaultPayload = {
    user_id: 'test-user-123',
    email: 'test@example.com',
    role: 'user',
    exp: Math.floor(Date.now() / 1000) + expiresIn, // expires in 1 hour by default
    iat: Math.floor(Date.now() / 1000)
  }
  
  const finalPayload = { ...defaultPayload, ...payload }
  
  // Create a fake JWT structure (header.payload.signature)
  const encodedHeader = btoa(JSON.stringify(header))
  const encodedPayload = btoa(JSON.stringify(finalPayload))
  const signature = 'mock-signature'
  
  return `${encodedHeader}.${encodedPayload}.${signature}`
}

/**
 * Create an expired JWT token for testing token refresh flows
 */
export const createExpiredJWTToken = (payload: any = {}) => {
  return createMockJWTToken(payload, -3600) // expired 1 hour ago
}

// ============================================================================
// Test Assertions Helpers
// ============================================================================

/**
 * Assert that auth state matches expected values
 */
export const expectAuthState = (expected: {
  isAuthenticated?: boolean
  isLoading?: boolean
  requires2FA?: boolean
  user?: User | null
  token?: string | null
}) => {
  const state = useAuthStore.getState()
  
  if (expected.isAuthenticated !== undefined) {
    expect(state.isAuthenticated).toBe(expected.isAuthenticated)
  }
  if (expected.isLoading !== undefined) {
    expect(state.isLoading).toBe(expected.isLoading)
  }
  if (expected.requires2FA !== undefined) {
    expect(state.requires2FA).toBe(expected.requires2FA)
  }
  if (expected.user !== undefined) {
    expect(state.user).toEqual(expected.user)
  }
  if (expected.token !== undefined) {
    expect(state.token).toBe(expected.token)
  }
}

export default {
  // Mock user factories
  createMockUser,
  createMockAdmin,
  createMockSysAdmin,
  createMockInactiveUser,
  createMock2FAUser,
  
  // State management utilities
  setupTestAuth,
  clearTestAuth,
  setupAuthenticatedUser,
  setupUnauthenticatedUser,
  setup2FARequiredState,
  setupAuthLoading,
  
  // Permission utilities
  testRoleHierarchy,
  
  // Test scenarios
  AuthScenarios,
  
  // JWT utilities
  createMockJWTToken,
  createExpiredJWTToken,
  
  // Test assertions
  expectAuthState,
}