/**
 * Client management types for IAM Dashboard
 * Aligned with backend API specification and client schemas
 */

export interface Client {
  id: string
  name: string
  cpf: string
  birth_date: string
  created_by: string
  created_at: string
  updated_at: string
  is_active: boolean
}

export interface ClientCreateRequest {
  name: string
  cpf: string
  birth_date: string
}

export interface ClientUpdateRequest {
  name?: string
  cpf?: string
  birth_date?: string
  is_active?: boolean
}

export interface ClientResponse {
  id: string
  name: string
  cpf: string
  birth_date: string
  created_by: string
  created_at: string
  updated_at: string
  is_active: boolean
}

export interface ClientListResponse {
  clients: ClientResponse[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

export interface ClientListParams {
  page?: number
  per_page?: number
  search?: string
  is_active?: boolean
}

export interface HttpError {
  message: string
  response?: {
    status: number
    statusText: string
    data?: {
      detail?: string
      message?: string
      errors?: Array<{
        field: string
        message: string
      }>
    }
  }
  name?: string
  code?: string
}
