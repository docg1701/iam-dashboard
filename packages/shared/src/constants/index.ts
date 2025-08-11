/**
 * Shared constants for IAM Dashboard
 */

// API Configuration
export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
} as const

// Status constants
export const CLIENT_STATUS = {
  ACTIVE: 'active',
  INACTIVE: 'inactive', 
  PENDING: 'pending',
  SUSPENDED: 'suspended',
} as const

export const USER_ROLES = {
  ADMIN: 'admin',
  MANAGER: 'manager', 
  USER: 'user',
  VIEWER: 'viewer',
} as const

export const PERMISSION_ACTIONS = {
  CREATE: 'create',
  READ: 'read',
  UPDATE: 'update', 
  DELETE: 'delete',
  MANAGE: 'manage',
} as const

// Validation constants
export const VALIDATION = {
  EMAIL_REGEX: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
  PHONE_REGEX: /^\+?[\d\s\-\(\)]+$/,
  CPF_LENGTH: 11,
  CNPJ_LENGTH: 14,
  MIN_PASSWORD_LENGTH: 8,
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
} as const

// UI Constants
export const UI_CONFIG = {
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
  DEBOUNCE_DELAY: 300,
  TOAST_DURATION: 5000,
} as const

// Cache keys
export const CACHE_KEYS = {
  USER_PROFILE: 'user-profile',
  CLIENT_LIST: 'client-list',
  PERMISSIONS: 'permissions',
  USER_PERMISSIONS: 'user-permissions',
} as const

// Local storage keys
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'auth-token',
  REFRESH_TOKEN: 'refresh-token',
  USER_PREFERENCES: 'user-preferences',
  THEME: 'theme',
} as const

// Error messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Erro de conexão. Verifique sua internet.',
  UNAUTHORIZED: 'Acesso não autorizado. Faça login novamente.',
  FORBIDDEN: 'Você não tem permissão para esta ação.',
  NOT_FOUND: 'Recurso não encontrado.',
  VALIDATION_ERROR: 'Dados inválidos. Verifique os campos.',
  SERVER_ERROR: 'Erro interno do servidor. Tente novamente.',
} as const

// Success messages
export const SUCCESS_MESSAGES = {
  CREATED: 'Criado com sucesso!',
  UPDATED: 'Atualizado com sucesso!',
  DELETED: 'Excluído com sucesso!',
  SAVED: 'Salvo com sucesso!',
} as const