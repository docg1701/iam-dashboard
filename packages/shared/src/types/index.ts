/**
 * Shared TypeScript type definitions
 */

// Basic common types
export interface BaseEntity {
  id: string
  created_at: string
  updated_at: string
}

// User types
export interface User extends BaseEntity {
  email: string
  full_name: string
  is_active: boolean
  role: UserRole
}

export type UserRole = 'admin' | 'manager' | 'user' | 'viewer'

// Client types
export interface Client extends BaseEntity {
  name: string
  email: string
  cpf_cnpj: string
  phone?: string
  status: ClientStatus
  metadata: Record<string, unknown>
}

export type ClientStatus = 'active' | 'inactive' | 'pending' | 'suspended'

// Permission types
export interface Permission extends BaseEntity {
  name: string
  description: string
  resource: string
  action: PermissionAction
}

export type PermissionAction = 'create' | 'read' | 'update' | 'delete' | 'manage'

// API response types
export interface ApiResponse<T = unknown> {
  data: T
  message?: string
  success: boolean
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number
    limit: number
    total: number
    totalPages: number
    hasNext: boolean
    hasPrev: boolean
  }
}

// Error types
export interface ApiError {
  message: string
  code?: string
  field?: string
  details?: Record<string, unknown>
}

// Form types
export interface FormValidationError {
  field: string
  message: string
}

// Export all types from subdirectories
export * from './client'
export * from './user'
export * from './permission'
export * from './api'