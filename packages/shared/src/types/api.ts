/**
 * API-related TypeScript type definitions
 */

export interface ApiResponse<T = unknown> {
  data: T
  message?: string
  success: boolean
  timestamp?: string
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

export interface ApiError {
  message: string
  code?: string
  field?: string
  details?: Record<string, unknown>
  timestamp?: string
}

export interface ApiErrorResponse {
  error: ApiError
  success: false
  timestamp: string
}

export interface ValidationError {
  field: string
  message: string
  code?: string
}

export interface ValidationErrorResponse extends ApiErrorResponse {
  error: ApiError & {
    validation_errors: ValidationError[]
  }
}

export interface HealthCheckResponse {
  status: 'healthy' | 'unhealthy'
  timestamp: string
  version: string
  services: {
    database: 'connected' | 'disconnected'
    redis: 'connected' | 'disconnected'
  }
}

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

export interface RequestOptions {
  method?: HttpMethod
  headers?: Record<string, string>
  body?: unknown
  timeout?: number
}