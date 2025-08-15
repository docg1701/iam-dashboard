/**
 * Simplified tests for ClientsService
 * Tests HTTP client integration with basic functionality
 * Follows CLAUDE.md guidelines: Only mocks external boundaries (HTTP calls)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

import type {
  ClientResponse,
  ClientListResponse,
  ClientCreateFormData,
  ClientUpdateFormData,
} from '@/types/client'

import { ClientsService, clientsService } from '../clients.service'
import { httpClient } from '../httpClient'

// Mock external HTTP client (following CLAUDE.md guidelines)
vi.mock('../httpClient', () => ({
  httpClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockHttpClient = vi.mocked(httpClient)

describe('ClientsService', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    // Ensure mocks are properly reset
    mockHttpClient.get.mockClear()
    mockHttpClient.post.mockClear()
    mockHttpClient.put.mockClear()
    mockHttpClient.delete.mockClear()
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  // Sample valid Brazilian CPF for testing
  const validCPF = '11144477735'

  const mockClientResponse: ClientResponse = {
    id: '123e4567-e89b-12d3-a456-426614174000',
    name: 'João Silva Santos',
    cpf: validCPF,
    birth_date: '1985-03-15',
    created_by: '456e7890-e89b-12d3-a456-426614174001',
    created_at: '2025-08-15T10:30:00Z',
    updated_at: '2025-08-15T10:30:00Z',
    is_active: true,
  }

  const mockClientListResponse: ClientListResponse = {
    clients: [mockClientResponse],
    total: 1,
    page: 1,
    per_page: 10,
    total_pages: 1,
  }

  describe('createClient', () => {
    const validCreateData: ClientCreateFormData = {
      name: 'João Silva Santos',
      cpf: validCPF,
      birthDate: '1985-03-15',
    }

    it('should create client successfully with valid data', async () => {
      // Setup mock before the call
      mockHttpClient.post.mockResolvedValueOnce(mockClientResponse)

      // Call the service
      const result = await clientsService.createClient(validCreateData)

      // Verify the HTTP call was made with correct parameters
      expect(mockHttpClient.post).toHaveBeenCalledTimes(1)
      expect(mockHttpClient.post).toHaveBeenCalledWith('/api/v1/clients', {
        name: 'João Silva Santos',
        cpf: validCPF,
        birth_date: '1985-03-15',
      })
      expect(result).toEqual(mockClientResponse)
    })

    it('should handle 400 Bad Request with Portuguese message', async () => {
      const error = {
        response: {
          status: 400,
          data: { detail: 'Dados inválidos fornecidos' },
        },
      }
      mockHttpClient.post.mockRejectedValueOnce(error)

      await expect(
        clientsService.createClient(validCreateData)
      ).rejects.toThrow('Dados inválidos fornecidos')
    })

    it('should handle 401 Unauthorized with Portuguese message', async () => {
      const error = {
        response: {
          status: 401,
          data: {},
        },
      }
      mockHttpClient.post.mockRejectedValueOnce(error)

      await expect(
        clientsService.createClient(validCreateData)
      ).rejects.toThrow('Sessão expirada. Faça login novamente')
    })

    it('should handle 403 Forbidden with Portuguese message', async () => {
      const error = {
        response: {
          status: 403,
          data: {},
        },
      }
      mockHttpClient.post.mockRejectedValueOnce(error)

      await expect(
        clientsService.createClient(validCreateData)
      ).rejects.toThrow('Você não tem permissão para realizar esta ação')
    })

    it('should handle 409 Conflict for duplicate CPF', async () => {
      const error = {
        response: {
          status: 409,
          data: { detail: 'CPF já cadastrado no sistema' },
        },
      }
      mockHttpClient.post.mockRejectedValueOnce(error)

      await expect(
        clientsService.createClient(validCreateData)
      ).rejects.toThrow('CPF já cadastrado no sistema')
    })

    it('should handle 422 Validation errors with multiple messages', async () => {
      const error = {
        response: {
          status: 422,
          data: {
            detail: 'Validation failed',
            errors: [
              { field: 'cpf', message: 'CPF inválido' },
              { field: 'name', message: 'Nome muito curto' },
            ],
          },
        },
      }
      mockHttpClient.post.mockRejectedValueOnce(error)

      await expect(
        clientsService.createClient(validCreateData)
      ).rejects.toThrow('CPF inválido, Nome muito curto')
    })

    it('should handle 500 Internal Server Error', async () => {
      const error = {
        response: {
          status: 500,
          data: {},
        },
      }
      mockHttpClient.post.mockRejectedValueOnce(error)

      await expect(
        clientsService.createClient(validCreateData)
      ).rejects.toThrow('Erro interno do servidor. Tente novamente mais tarde')
    })

    it('should handle network errors with fallback message', async () => {
      const error = new Error('Network Error')
      mockHttpClient.post.mockRejectedValueOnce(error)

      await expect(
        clientsService.createClient(validCreateData)
      ).rejects.toThrow('Falha ao criar cliente')
    })

    it('should validate input data using Zod schemas', async () => {
      const invalidData = {
        name: '', // Too short
        cpf: '123', // Invalid CPF
        birthDate: 'invalid-date',
      }

      await expect(clientsService.createClient(invalidData)).rejects.toThrow() // Should throw validation error
    })
  })

  describe('getClient', () => {
    const clientId = '123e4567-e89b-12d3-a456-426614174000'

    it('should get client successfully', async () => {
      mockHttpClient.get.mockResolvedValueOnce(mockClientResponse)

      const result = await clientsService.getClient(clientId)

      expect(mockHttpClient.get).toHaveBeenCalledWith(
        `/api/v1/clients/${clientId}`
      )
      expect(result).toEqual(mockClientResponse)
    })

    it('should handle 404 Not Found with Portuguese message', async () => {
      const error = {
        response: {
          status: 404,
          data: {},
        },
      }
      mockHttpClient.get.mockRejectedValueOnce(error)

      await expect(clientsService.getClient(clientId)).rejects.toThrow(
        'Cliente não encontrado'
      )
    })

    it('should handle errors with fallback message', async () => {
      const error = new Error('Network Error')
      mockHttpClient.get.mockRejectedValueOnce(error)

      await expect(clientsService.getClient(clientId)).rejects.toThrow(
        'Falha ao buscar cliente'
      )
    })
  })

  describe('listClients', () => {
    it('should list clients with default parameters', async () => {
      mockHttpClient.get.mockResolvedValueOnce(mockClientListResponse)

      const result = await clientsService.listClients()

      expect(mockHttpClient.get).toHaveBeenCalledWith(
        '/api/v1/clients?page=1&per_page=10'
      )
      expect(result).toEqual(mockClientListResponse)
    })

    it('should build query string correctly with all parameters', async () => {
      mockHttpClient.get.mockResolvedValueOnce(mockClientListResponse)

      const params = {
        page: 2,
        per_page: 20,
        search: 'João Silva',
        is_active: true,
      }

      await clientsService.listClients(params)

      expect(mockHttpClient.get).toHaveBeenCalledWith(
        '/api/v1/clients?page=2&per_page=20&search=Jo%C3%A3o+Silva&is_active=true'
      )
    })

    it('should handle empty search parameter', async () => {
      mockHttpClient.get.mockResolvedValueOnce(mockClientListResponse)

      const params = {
        page: 1,
        search: '   ', // Whitespace only
      }

      await clientsService.listClients(params)

      expect(mockHttpClient.get).toHaveBeenCalledWith(
        '/api/v1/clients?page=1&per_page=10'
      )
    })

    it('should validate parameters using Zod schemas', async () => {
      const invalidParams = {
        page: -1, // Invalid page number
        per_page: 150, // Too large
      }

      await expect(clientsService.listClients(invalidParams)).rejects.toThrow() // Should throw validation error
    })

    it('should handle errors with fallback message', async () => {
      const error = new Error('Network Error')
      mockHttpClient.get.mockRejectedValueOnce(error)

      await expect(clientsService.listClients()).rejects.toThrow(
        'Falha ao listar clientes'
      )
    })
  })

  describe('updateClient', () => {
    const clientId = '123e4567-e89b-12d3-a456-426614174000'
    const validUpdateData: ClientUpdateFormData = {
      name: 'João Silva Santos Updated',
      is_active: false,
    }

    it('should update client successfully with partial data', async () => {
      mockHttpClient.put.mockResolvedValueOnce(mockClientResponse)

      const result = await clientsService.updateClient(
        clientId,
        validUpdateData
      )

      expect(mockHttpClient.put).toHaveBeenCalledWith(
        `/api/v1/clients/${clientId}`,
        {
          name: 'João Silva Santos Updated',
          is_active: false,
        }
      )
      expect(result).toEqual(mockClientResponse)
    })

    it('should handle field name mapping correctly', async () => {
      mockHttpClient.put.mockResolvedValueOnce(mockClientResponse)

      const updateData: ClientUpdateFormData = {
        name: 'New Name',
        cpf: validCPF,
        birthDate: '1990-01-01', // Form field name
        is_active: true,
      }

      await clientsService.updateClient(clientId, updateData)

      expect(mockHttpClient.put).toHaveBeenCalledWith(
        `/api/v1/clients/${clientId}`,
        {
          name: 'New Name',
          cpf: validCPF,
          birth_date: '1990-01-01', // API field name
          is_active: true,
        }
      )
    })

    it('should only include defined fields in update request', async () => {
      mockHttpClient.put.mockResolvedValueOnce(mockClientResponse)

      const partialData: ClientUpdateFormData = {
        name: 'Only Name Updated',
        // Other fields undefined
      }

      await clientsService.updateClient(clientId, partialData)

      expect(mockHttpClient.put).toHaveBeenCalledWith(
        `/api/v1/clients/${clientId}`,
        {
          name: 'Only Name Updated',
          // Should not include undefined fields
        }
      )
    })

    it('should handle errors with fallback message', async () => {
      const error = new Error('Network Error')
      mockHttpClient.put.mockRejectedValueOnce(error)

      await expect(
        clientsService.updateClient(clientId, validUpdateData)
      ).rejects.toThrow('Falha ao atualizar cliente')
    })
  })

  describe('deleteClient', () => {
    const clientId = '123e4567-e89b-12d3-a456-426614174000'

    it('should delete client successfully', async () => {
      mockHttpClient.delete.mockResolvedValueOnce(undefined)

      await clientsService.deleteClient(clientId)

      expect(mockHttpClient.delete).toHaveBeenCalledWith(
        `/api/v1/clients/${clientId}`
      )
    })

    it('should handle errors with fallback message', async () => {
      const error = new Error('Network Error')
      mockHttpClient.delete.mockRejectedValueOnce(error)

      await expect(clientsService.deleteClient(clientId)).rejects.toThrow(
        'Falha ao excluir cliente'
      )
    })
  })

  describe('error message extraction', () => {
    it('should prefer response detail over default message', async () => {
      const error = {
        response: {
          status: 400,
          data: { detail: 'Specific error message' },
        },
      }
      mockHttpClient.post.mockRejectedValueOnce(error)

      await expect(
        clientsService.createClient({
          name: 'Test',
          cpf: validCPF,
          birthDate: '1990-01-01',
        })
      ).rejects.toThrow('Specific error message')
    })

    it('should use message field if detail not available', async () => {
      const error = {
        response: {
          status: 400,
          data: { message: 'Alternative error message' },
        },
      }
      mockHttpClient.post.mockRejectedValueOnce(error)

      await expect(
        clientsService.createClient({
          name: 'Test',
          cpf: validCPF,
          birthDate: '1990-01-01',
        })
      ).rejects.toThrow('Alternative error message')
    })

    it('should fall back to default message when no response data', async () => {
      const error = { response: undefined }
      mockHttpClient.post.mockRejectedValueOnce(error)

      await expect(
        clientsService.createClient({
          name: 'Test',
          cpf: validCPF,
          birthDate: '1990-01-01',
        })
      ).rejects.toThrow('Falha ao criar cliente')
    })
  })

  describe('response validation', () => {
    it('should validate successful response data', async () => {
      const invalidResponse = {
        id: 'invalid-uuid', // Invalid UUID format
        name: 'Test',
        // Missing required fields
      }
      mockHttpClient.get.mockResolvedValueOnce(invalidResponse)

      await expect(clientsService.getClient('test-id')).rejects.toThrow() // Should throw validation error
    })

    it('should validate list response data', async () => {
      const invalidListResponse = {
        clients: 'not-an-array', // Should be array
        total: 'invalid', // Should be number
      }
      mockHttpClient.get.mockResolvedValueOnce(invalidListResponse)

      await expect(clientsService.listClients()).rejects.toThrow() // Should throw validation error
    })
  })

  describe('service instance', () => {
    it('should export singleton instance', () => {
      expect(clientsService).toBeInstanceOf(ClientsService)
    })

    it('should export class for testing', () => {
      expect(ClientsService).toBeDefined()
      const newInstance = new ClientsService()
      expect(newInstance).toBeInstanceOf(ClientsService)
    })
  })
})
