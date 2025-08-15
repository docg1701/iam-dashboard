/**
 * Client-related TypeScript type definitions
 */

export interface ClientCreateRequest {
  name: string
  email: string
  cpf_cnpj: string
  phone?: string
  metadata?: Record<string, unknown>
}

export interface ClientUpdateRequest {
  name?: string
  email?: string
  phone?: string
  status?: ClientStatus
  metadata?: Record<string, unknown>
}

export interface ClientResponse {
  id: string
  name: string
  email: string
  cpf_cnpj: string
  phone?: string
  status: ClientStatus
  created_at: string
  updated_at: string
  metadata: Record<string, unknown>
}

export type ClientStatus = 'active' | 'inactive' | 'pending' | 'suspended'

export interface ClientListFilter {
  status?: ClientStatus
  search?: string
  page?: number
  limit?: number
}