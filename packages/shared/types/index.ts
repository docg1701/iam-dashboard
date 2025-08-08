/**
 * Shared type definitions for Multi-Agent IAM Dashboard
 * 
 * This module exports common types used across frontend and backend.
 * All types follow TypeScript best practices and include JSDoc documentation.
 */

import { z } from 'zod'

// User and Authentication Types
export const UserRoleSchema = z.enum(['sysadmin', 'admin', 'user'])
export type UserRole = z.infer<typeof UserRoleSchema>

export const UserStatusSchema = z.enum(['active', 'inactive', 'suspended'])
export type UserStatus = z.infer<typeof UserStatusSchema>

export interface User {
  user_id: string
  email: string
  full_name: string
  role: UserRole
  status: UserStatus
  created_at: string
  updated_at: string
  last_login_at?: string
  is_verified: boolean
}

// Client Management Types
export const ClientStatusSchema = z.enum(['active', 'inactive', 'archived'])
export type ClientStatus = z.infer<typeof ClientStatusSchema>

export interface Client {
  client_id: string
  full_name: string
  cpf: string // Format: XXX.XXX.XXX-XX
  birth_date: string // ISO 8601 date format
  status: ClientStatus
  notes?: string | null
  created_by: string // User ID reference
  updated_by: string // User ID reference
  created_at: string // ISO 8601 timestamp
  updated_at: string // ISO 8601 timestamp
}

export interface ClientCreate {
  full_name: string
  cpf: string
  birth_date: string
  notes?: string | null
}

export interface ClientUpdate {
  full_name?: string
  cpf?: string
  birth_date?: string
  notes?: string | null
  status?: ClientStatus
}

export interface ClientResponse {
  client_id: string
  full_name: string
  cpf: string // Will be masked for security (e.g., XXX.XXX.XXX-XX)
  birth_date: string
  status: ClientStatus
  notes?: string | null
  created_by: string
  updated_by: string
  created_at: string
  updated_at: string
}

export interface ClientListItem {
  client_id: string
  full_name: string
  cpf: string // Masked
  status: ClientStatus
  created_at: string
}

export interface ClientErrorResponse {
  detail: string
  field_errors?: Record<string, string[]>
}

export interface ClientFormData {
  full_name: string
  cpf: string
  birth_date: string
  notes?: string | null
}

// API Response Types
export interface ApiResponse<T = unknown> {
  success: boolean
  data?: T
  message?: string
  error_code?: string
  details?: Record<string, unknown>
}

export interface PaginatedResponse<T = unknown> {
  success: boolean
  data: T[]
  pagination: {
    page: number
    per_page: number
    total: number
    total_pages: number
  }
}

// Error Types
export interface ApiError {
  message: string
  error_code?: string
  details?: Record<string, unknown>
  timestamp: string
}

// Agent Types
export const AgentTypeSchema = z.enum([
  'client_management',
  'pdf_processing', 
  'reports_analysis',
  'audio_recording'
])
export type AgentType = z.infer<typeof AgentTypeSchema>

export interface AgentStatus {
  agent_id: string
  type: AgentType
  name: string
  status: 'online' | 'offline' | 'error'
  last_activity: string
  version: string
}

// Configuration Types
export interface BrandingConfig {
  primary_color: string
  secondary_color: string
  logo_url?: string
  favicon_url?: string
  company_name: string
  font_family: string
  border_radius: string
}

// Validation Schemas
export const ClientCreateSchema = z.object({
  full_name: z.string().min(2).max(255),
  cpf: z.string().regex(/^\d{3}\.\d{3}\.\d{3}-\d{2}$/, 'CPF must be in format XXX.XXX.XXX-XX'),
  birth_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format'),
  notes: z.string().optional()
})

export const ClientUpdateSchema = z.object({
  full_name: z.string().min(2).max(255).optional(),
  cpf: z.string().regex(/^\d{3}\.\d{3}\.\d{3}-\d{2}$/, 'CPF must be in format XXX.XXX.XXX-XX').optional(),
  birth_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format').optional(),
  notes: z.string().optional(),
  status: ClientStatusSchema.optional()
})

export const ClientFormDataSchema = z.object({
  full_name: z.string().min(2).max(255),
  cpf: z.string().regex(/^\d{3}\.\d{3}\.\d{3}-\d{2}$/, 'CPF must be in format XXX.XXX.XXX-XX'),
  birth_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format'),
  notes: z.string().optional()
})

export const UserCreateSchema = z.object({
  email: z.string().email('Invalid email format'),
  full_name: z.string().min(2).max(255),
  role: UserRoleSchema,
  password: z.string().min(8).max(128)
})

// Schemas are already exported above inline with their definitions