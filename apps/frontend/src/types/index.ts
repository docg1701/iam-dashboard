// Basic type definitions for the IAM Dashboard

// Re-export user types from shared package to maintain consistency
export type {
  User,
  UserRole,
  UserStatus,
  UserCreateSchema
} from '@iam-dashboard/shared'

import type { User } from '@iam-dashboard/shared'

export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
}

export interface ApiResponse<T = unknown> {
  data?: T
  message?: string
  error?: string
  status: number
}

export interface PaginatedResponse<T = unknown> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

// Re-export client types from shared package
export type {
  Client,
  ClientCreate,
  ClientUpdate,
  ClientResponse,
  ClientListItem,
  ClientStatus,
  ClientErrorResponse,
  ClientFormData
} from '@iam-dashboard/shared'

export * from './auth'

// Theme and branding types
export interface ThemeConfig {
  primary: string
  secondary: string
  accent: string
  background: string
  foreground: string
  card: string
  cardForeground: string
  popover: string
  popoverForeground: string
  muted: string
  mutedForeground: string
  border: string
  input: string
  ring: string
  radius: string
}

export interface BrandingConfig {
  logo?: string
  favicon?: string
  companyName: string
  theme: ThemeConfig
}