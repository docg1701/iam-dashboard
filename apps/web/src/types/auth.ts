/**
 * Authentication system types for IAM Dashboard
 * Aligned with Story 1.3 requirements and backend API specification
 */

export type UserRole = 'sysadmin' | 'admin' | 'user'

export interface User {
  id: string
  email: string
  role: UserRole
  is_active: boolean
  is_2fa_enabled: boolean
  created_at: string
  updated_at: string
}

export interface UserPermission {
  id: string
  user_id: string
  agent_name: string
  can_create: boolean
  can_read: boolean
  can_update: boolean
  can_delete: boolean
}

export interface LoginCredentials {
  email: string
  password: string
  totp_code?: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
  permissions: UserPermission[]
}

export interface RefreshTokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface AuthState {
  user: User | null
  permissions: UserPermission[]
  tokens: AuthTokens | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

export interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => Promise<void>
  refreshToken: () => Promise<void>
  clearError: () => void
}

export interface TwoFactorSetupResponse {
  secret: string
  qr_code_url: string
  backup_codes: string[]
}

export interface AuthError {
  message: string
  code: string
  details?: Record<string, unknown>
}

export interface TokenStorage {
  getTokens(): AuthTokens | null
  setTokens(tokens: AuthTokens): void
  removeTokens(): void
  isTokenExpired(token: string): boolean
}

export type AuthAction = 
  | { type: 'AUTH_START' }
  | { type: 'AUTH_SUCCESS'; payload: { user: User; permissions: UserPermission[]; tokens: AuthTokens } }
  | { type: 'AUTH_FAILURE'; payload: { error: string } }
  | { type: 'AUTH_LOGOUT' }
  | { type: 'REFRESH_SUCCESS'; payload: { tokens: AuthTokens } }
  | { type: 'CLEAR_ERROR' }