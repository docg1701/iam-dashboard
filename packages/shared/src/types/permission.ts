/**
 * Permission-related TypeScript type definitions
 */

export interface PermissionCreateRequest {
  name: string
  description: string
  resource: string
  action: PermissionAction
}

export interface PermissionUpdateRequest {
  name?: string
  description?: string
  resource?: string
  action?: PermissionAction
}

export interface PermissionResponse {
  id: string
  name: string
  description: string
  resource: string
  action: PermissionAction
  created_at: string
  updated_at: string
}

export type PermissionAction = 'create' | 'read' | 'update' | 'delete' | 'manage'

export interface UserPermission {
  user_id: string
  permission_id: string
  granted_by: string
  granted_at: string
}

export interface RolePermission {
  role: string
  permission_id: string
  granted_by: string
  granted_at: string
}

export interface PermissionListFilter {
  resource?: string
  action?: PermissionAction
  search?: string
  page?: number
  limit?: number
}