// Authentication types for the IAM Dashboard

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token?: string
  token_type?: string
  expires_in?: number
  requires_2fa: boolean
  temp_token?: string
  user?: User
}

export interface TwoFactorRequest {
  temp_token: string
  totp_code: string
}

export interface TwoFactorResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface User {
  user_id: string
  email: string
  role: 'sysadmin' | 'admin' | 'user'
  is_active: boolean
  totp_enabled: boolean
  created_at: string
  updated_at: string
  last_login?: string
}

export interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  requires2FA: boolean
  tempToken: string | null
}

export interface TwoFactorSetupResponse {
  secret: string
  qr_code: string
  backup_codes: string[]
}

export interface PasswordStrengthResult {
  score: number // 0-4
  feedback: string[]
  isValid: boolean
}

export interface LoginFormData {
  email: string
  password: string
}

export interface TwoFactorFormData {
  totp_code: string
}