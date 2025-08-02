// Basic type definitions for the IAM Dashboard

export interface User {
  id: string
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
  created_at: string
  updated_at: string
}

export enum UserRole {
  SYSADMIN = 'sysadmin',
  ADMIN = 'admin',
  USER = 'user',
}

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

export interface Client {
  client_id: string
  full_name: string
  ssn: string
  birth_date: string
  status: ClientStatus
  created_at: string
  updated_at: string
  created_by: string
}

export enum ClientStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended',
}

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