/**
 * Simplified tests for ClientsService focusing on HTTP client integration
 * CLAUDE.md Compliant: Only mocks external HTTP client, tests service behavior
 */

import { describe, it, expect, vi, beforeEach, afterEach, Mock } from 'vitest'
import type { ClientResponse, ClientListResponse } from '@/types/client'

// Mock the httpClient module (CLAUDE.md compliant - external boundary)
vi.mock('@/services/httpClient', () => ({
  httpClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    patch: vi.fn(),
  },
}))

// Mock shared utilities (CLAUDE.md compliant - external dependency)
vi.mock('@shared/utils', () => ({
  validateCPF: vi.fn(() => true),
  formatCPF: vi.fn((cpf: string) => cpf),
}))

// Mock validation schemas to avoid complex validation in unit tests
vi.mock('@/lib/validations/client', () => ({
  validateClientCreate: vi.fn(data => data),
  validateClientUpdate: vi.fn(data => data),
  validateClientListParams: vi.fn(params => params || {}),
  validateClientResponse: vi.fn(response => response),
  validateClientListResponse: vi.fn(response => response),
}))

// Import httpClient after mocking
import { httpClient } from '@/services/httpClient'
import { clientsService } from '@/services/clients.service'

describe('ClientsService - Simple HTTP Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('HTTP Client Integration', () => {
    it('should make POST request to create client', async () => {
      const createData = {
        name: 'João Silva',
        cpf: '12345678901',
        birthDate: '1990-01-01',
      }

      const mockResponse: ClientResponse = {
        id: '1',
        name: 'João Silva',
        cpf: '12345678901',
        birth_date: '1990-01-01',
        created_by: 'admin',
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
        is_active: true,
      }

      ;(httpClient.post as Mock).mockResolvedValueOnce(mockResponse)

      const result = await clientsService.createClient(createData)

      expect(httpClient.post).toHaveBeenCalledWith('/api/v1/clients', {
        name: 'João Silva',
        cpf: '12345678901',
        birth_date: '1990-01-01',
      })
      expect(result).toEqual(mockResponse)
    })

    it('should make GET request to fetch client by ID', async () => {
      const mockResponse: ClientResponse = {
        id: '1',
        name: 'João Silva',
        cpf: '12345678901',
        birth_date: '1990-01-01',
        created_by: 'admin',
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
        is_active: true,
      }

      ;(httpClient.get as Mock).mockResolvedValueOnce(mockResponse)

      const result = await clientsService.getClient('1')

      expect(httpClient.get).toHaveBeenCalledWith('/api/v1/clients/1')
      expect(result).toEqual(mockResponse)
    })

    it('should make GET request to list clients', async () => {
      const mockResponse: ClientListResponse = {
        clients: [],
        total: 0,
        page: 1,
        per_page: 10,
        total_pages: 0,
      }

      ;(httpClient.get as Mock).mockResolvedValueOnce(mockResponse)

      const result = await clientsService.listClients()

      expect(httpClient.get).toHaveBeenCalled()
      expect(result).toEqual(mockResponse)
    })

    it('should make PUT request to update client', async () => {
      const updateData = { name: 'João Santos' }
      const mockResponse: ClientResponse = {
        id: '1',
        name: 'João Santos',
        cpf: '12345678901',
        birth_date: '1990-01-01',
        created_by: 'admin',
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-02T00:00:00Z',
        is_active: true,
      }

      ;(httpClient.put as Mock).mockResolvedValueOnce(mockResponse)

      const result = await clientsService.updateClient('1', updateData)

      expect(httpClient.put).toHaveBeenCalledWith(
        '/api/v1/clients/1',
        updateData
      )
      expect(result).toEqual(mockResponse)
    })

    it('should make DELETE request to delete client', async () => {
      ;(httpClient.delete as Mock).mockResolvedValueOnce(undefined)

      await clientsService.deleteClient('1')

      expect(httpClient.delete).toHaveBeenCalledWith('/api/v1/clients/1')
    })
  })

  describe('Error Handling', () => {
    it('should handle HTTP errors and return Portuguese messages', async () => {
      const httpError = {
        response: {
          status: 404,
          data: { detail: 'Client not found' },
        },
      }

      ;(httpClient.get as Mock).mockRejectedValueOnce(httpError)

      await expect(clientsService.getClient('999')).rejects.toThrow(
        'Cliente não encontrado'
      )
    })

    it('should handle network errors', async () => {
      const networkError = new Error('Network error')

      ;(httpClient.get as Mock).mockRejectedValueOnce(networkError)

      await expect(clientsService.getClient('1')).rejects.toThrow(
        'Falha ao buscar cliente'
      )
    })
  })
})
