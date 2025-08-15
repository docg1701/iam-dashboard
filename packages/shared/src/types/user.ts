/**
 * User-related TypeScript type definitions
 */

export interface UserCreateRequest {
  email: string
  full_name: string
  password: string
  role: UserRole
}

export interface UserUpdateRequest {
  email?: string
  full_name?: string
  role?: UserRole
  is_active?: boolean
}

export interface UserResponse {
  id: string
  email: string
  full_name: string
  is_active: boolean
  role: UserRole
  created_at: string
  updated_at: string
  last_login?: string
}

export type UserRole = 'admin' | 'manager' | 'user' | 'viewer'

export interface UserLoginRequest {
  email: string
  password: string
}

export interface UserLoginResponse {
  access_token: string
  refresh_token: string
  user: UserResponse
  expires_in: number
}

export interface UserListFilter {
  role?: UserRole
  is_active?: boolean
  search?: string
  page?: number
  limit?: number
}