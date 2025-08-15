/**
 * Client management service for API calls
 * Handles client CRUD operations with proper error handling and validation
 * Based on Story 1.4 requirements and API specification
 *
 * Features:
 * - Input validation using Zod schemas
 * - Response validation for type safety
 * - Portuguese error messages for better UX
 * - Consistent data transformation between frontend and backend
 */

import {
  validateClientCreate,
  validateClientUpdate,
  validateClientListParams,
  validateClientResponse,
  validateClientListResponse,
  type ClientCreateFormData,
  type ClientUpdateFormData,
  type ClientListParams as ValidatedClientListParams,
} from '@/lib/validations/client'
import {
  ClientCreateRequest,
  ClientResponse,
  ClientUpdateRequest,
  ClientListResponse,
  ClientListParams,
  HttpError,
} from '@/types/client'

import { httpClient } from './httpClient'

class ClientsService {
  private readonly apiPath = '/api/v1/clients'

  /**
   * Create a new client with validation
   */
  async createClient(
    data: ClientCreateFormData | ClientCreateRequest
  ): Promise<ClientResponse> {
    try {
      // Validate input data
      const validatedData = validateClientCreate(data)

      const response = await httpClient.post<ClientResponse>(this.apiPath, {
        name: validatedData.name,
        cpf: validatedData.cpf,
        birth_date: validatedData.birthDate,
      })

      // Validate response data
      return validateClientResponse(response)
    } catch (error: unknown) {
      const httpError = error as HttpError
      const message = this.getErrorMessage(httpError, 'Falha ao criar cliente')
      throw new Error(message)
    }
  }

  /**
   * Get a specific client by ID with response validation
   */
  async getClient(id: string): Promise<ClientResponse> {
    try {
      const response = await httpClient.get<ClientResponse>(
        `${this.apiPath}/${id}`
      )

      // Validate response data
      return validateClientResponse(response)
    } catch (error: unknown) {
      const httpError = error as HttpError
      const message = this.getErrorMessage(httpError, 'Falha ao buscar cliente')
      throw new Error(message)
    }
  }

  /**
   * List clients with pagination and optional filtering
   */
  async listClients(
    params: ValidatedClientListParams | ClientListParams = {}
  ): Promise<ClientListResponse> {
    try {
      // Validate and normalize parameters
      const validatedParams = validateClientListParams(params)

      const searchParams = new URLSearchParams()

      if (validatedParams.page !== undefined) {
        searchParams.append('page', validatedParams.page.toString())
      }
      if (validatedParams.per_page !== undefined) {
        searchParams.append('per_page', validatedParams.per_page.toString())
      }
      if (
        validatedParams.search !== undefined &&
        validatedParams.search.trim() !== ''
      ) {
        searchParams.append('search', validatedParams.search.trim())
      }
      if (validatedParams.is_active !== undefined) {
        searchParams.append('is_active', validatedParams.is_active.toString())
      }

      const queryString = searchParams.toString()
      const url = queryString ? `${this.apiPath}?${queryString}` : this.apiPath

      const response = await httpClient.get<ClientListResponse>(url)

      // Validate response data
      return validateClientListResponse(response)
    } catch (error: unknown) {
      const httpError = error as HttpError
      const message = this.getErrorMessage(
        httpError,
        'Falha ao listar clientes'
      )
      throw new Error(message)
    }
  }

  /**
   * Update an existing client with validation
   */
  async updateClient(
    id: string,
    data: ClientUpdateFormData | ClientUpdateRequest
  ): Promise<ClientResponse> {
    try {
      // Validate input data
      const validatedData = validateClientUpdate(data)

      const updateData: Partial<ClientUpdateRequest> = {}

      // Only include fields that are provided and map form field names to API field names
      if (validatedData.name !== undefined) {
        updateData.name = validatedData.name
      }
      if (validatedData.cpf !== undefined) {
        updateData.cpf = validatedData.cpf
      }
      if (validatedData.birthDate !== undefined) {
        updateData.birth_date = validatedData.birthDate
      }
      if (validatedData.is_active !== undefined) {
        updateData.is_active = validatedData.is_active
      }

      const response = await httpClient.put<ClientResponse>(
        `${this.apiPath}/${id}`,
        updateData
      )

      // Validate response data
      return validateClientResponse(response)
    } catch (error: unknown) {
      const httpError = error as HttpError
      const message = this.getErrorMessage(
        httpError,
        'Falha ao atualizar cliente'
      )
      throw new Error(message)
    }
  }

  /**
   * Delete a client (soft delete)
   */
  async deleteClient(id: string): Promise<void> {
    try {
      await httpClient.delete(`${this.apiPath}/${id}`)
    } catch (error: unknown) {
      const httpError = error as HttpError
      const message = this.getErrorMessage(
        httpError,
        'Falha ao excluir cliente'
      )
      throw new Error(message)
    }
  }

  /**
   * Extract user-friendly error message from HTTP error
   * Uses Portuguese messages for better user experience
   */
  private getErrorMessage(error: HttpError, defaultMessage: string): string {
    // Try to get the error message from the response
    const responseDetail = error.response?.data?.detail
    const responseMessage = error.response?.data?.message
    const status = error.response?.status

    // Handle specific HTTP status codes with Portuguese messages
    if (status) {
      switch (status) {
        case 400:
          return (
            responseDetail || responseMessage || 'Dados inválidos fornecidos'
          )
        case 401:
          return 'Sessão expirada. Faça login novamente'
        case 403:
          return 'Você não tem permissão para realizar esta ação'
        case 404:
          return 'Cliente não encontrado'
        case 409:
          if (responseDetail?.includes('CPF')) {
            return 'CPF já cadastrado no sistema'
          }
          return responseDetail || responseMessage || 'Conflito de dados'
        case 422:
          // Handle validation errors
          if (error.response?.data?.errors) {
            const validationErrors = error.response.data.errors
            if (validationErrors.length > 0) {
              return validationErrors.map(err => err.message).join(', ')
            }
          }
          return (
            responseDetail || responseMessage || 'Dados de entrada inválidos'
          )
        case 500:
          return 'Erro interno do servidor. Tente novamente mais tarde'
        default:
          return responseDetail || responseMessage || defaultMessage
      }
    }

    // If no specific status, try to use the detail or message from response
    if (responseDetail) {
      return responseDetail
    }

    if (responseMessage) {
      return responseMessage
    }

    // Use the provided default message as fallback
    return defaultMessage
  }
}

// Create singleton instance
export const clientsService = new ClientsService()

// Export for testing
export { ClientsService }
