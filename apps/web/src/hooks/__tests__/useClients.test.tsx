/**
 * Tests for client management hooks
 * Tests TanStack Query integration and proper error handling
 */

/* eslint-disable import/order */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

import { clientsService } from '@/services/clients.service'
import type { ClientResponse, ClientListResponse } from '@/types/client'

import {
  useCreateClient,
  useGetClient,
  useListClients,
  useUpdateClient,
  useDeleteClient,
  clientsQueryKeys,
} from '../useClients'

// Mock the clients service
vi.mock('@/services/clients.service', () => ({
  clientsService: {
    createClient: vi.fn(),
    getClient: vi.fn(),
    listClients: vi.fn(),
    updateClient: vi.fn(),
    deleteClient: vi.fn(),
  },
}))

// Mock console methods to avoid noise in tests
vi.spyOn(console, 'log').mockImplementation(() => {})
vi.spyOn(console, 'error').mockImplementation(() => {})

describe('useClients hooks', () => {
  let queryClient: QueryClient

  // Test wrapper component
  const createWrapper = (queryClient: QueryClient) => {
    const Wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )
    Wrapper.displayName = 'TestQueryClientWrapper'
    return Wrapper
  }

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: Infinity },
        mutations: { retry: false },
      },
    })
    vi.clearAllMocks()
  })

  afterEach(() => {
    queryClient.clear()
  })

  describe('clientsQueryKeys', () => {
    it('should generate correct query keys', () => {
      expect(clientsQueryKeys.all).toEqual(['clients'])
      expect(clientsQueryKeys.lists()).toEqual(['clients', 'list'])
      expect(clientsQueryKeys.list({ page: 1 })).toEqual([
        'clients',
        'list',
        { page: 1 },
      ])
      expect(clientsQueryKeys.details()).toEqual(['clients', 'detail'])
      expect(clientsQueryKeys.detail('123')).toEqual([
        'clients',
        'detail',
        '123',
      ])
    })
  })

  describe('useCreateClient', () => {
    it('should create a client successfully', async () => {
      const mockClient: ClientResponse = {
        id: '1',
        name: 'João Silva',
        cpf: '12345678901',
        birth_date: '1990-01-01',
        created_by: 'admin',
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
        is_active: true,
      }

      vi.mocked(clientsService.createClient).mockResolvedValue(mockClient)

      const { result } = renderHook(() => useCreateClient(), {
        wrapper: createWrapper(queryClient),
      })

      const createData = {
        name: 'João Silva',
        cpf: '12345678901',
        birth_date: '1990-01-01',
      }

      result.current.mutate(createData)

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(clientsService.createClient).toHaveBeenCalledWith(createData)
      expect(result.current.data).toEqual(mockClient)
    })

    it('should handle create client error', async () => {
      const error = new Error('CPF já cadastrado no sistema')
      vi.mocked(clientsService.createClient).mockRejectedValue(error)

      const { result } = renderHook(() => useCreateClient(), {
        wrapper: createWrapper(queryClient),
      })

      const createData = {
        name: 'João Silva',
        cpf: '12345678901',
        birth_date: '1990-01-01',
      }

      result.current.mutate(createData)

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toEqual(error)
    })
  })

  describe('useGetClient', () => {
    it('should fetch a client successfully', async () => {
      const mockClient: ClientResponse = {
        id: '1',
        name: 'João Silva',
        cpf: '12345678901',
        birth_date: '1990-01-01',
        created_by: 'admin',
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
        is_active: true,
      }

      vi.mocked(clientsService.getClient).mockResolvedValue(mockClient)

      const { result } = renderHook(() => useGetClient('1'), {
        wrapper: createWrapper(queryClient),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(clientsService.getClient).toHaveBeenCalledWith('1')
      expect(result.current.data).toEqual(mockClient)
    })

    it('should not fetch when disabled', () => {
      const { result } = renderHook(
        () => useGetClient('1', { enabled: false }),
        {
          wrapper: createWrapper(queryClient),
        }
      )

      expect(result.current.isFetching).toBe(false)
      expect(clientsService.getClient).not.toHaveBeenCalled()
    })

    it('should handle fetch client error', async () => {
      const error = new Error('Cliente não encontrado')
      vi.mocked(clientsService.getClient).mockRejectedValue(error)

      const { result } = renderHook(() => useGetClient('999'), {
        wrapper: createWrapper(queryClient),
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toEqual(error)
    })
  })

  describe('useListClients', () => {
    it('should fetch clients list successfully', async () => {
      const mockResponse: ClientListResponse = {
        clients: [
          {
            id: '1',
            name: 'João Silva',
            cpf: '12345678901',
            birth_date: '1990-01-01',
            created_by: 'admin',
            created_at: '2023-01-01T00:00:00Z',
            updated_at: '2023-01-01T00:00:00Z',
            is_active: true,
          },
        ],
        total: 1,
        page: 1,
        per_page: 10,
        total_pages: 1,
      }

      vi.mocked(clientsService.listClients).mockResolvedValue(mockResponse)

      const { result } = renderHook(() => useListClients({ page: 1 }), {
        wrapper: createWrapper(queryClient),
      })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(clientsService.listClients).toHaveBeenCalledWith({ page: 1 })
      expect(result.current.data).toEqual(mockResponse)
    })

    it('should handle list clients error', async () => {
      const error = new Error('Falha ao listar clientes')
      vi.mocked(clientsService.listClients).mockRejectedValue(error)

      const { result } = renderHook(() => useListClients(), {
        wrapper: createWrapper(queryClient),
      })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toEqual(error)
    })
  })

  describe('useUpdateClient', () => {
    it('should update a client successfully', async () => {
      const mockUpdatedClient: ClientResponse = {
        id: '1',
        name: 'João Santos',
        cpf: '12345678901',
        birth_date: '1990-01-01',
        created_by: 'admin',
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-02T00:00:00Z',
        is_active: true,
      }

      vi.mocked(clientsService.updateClient).mockResolvedValue(
        mockUpdatedClient
      )

      const { result } = renderHook(() => useUpdateClient(), {
        wrapper: createWrapper(queryClient),
      })

      const updateData = { name: 'João Santos' }
      result.current.mutate({ id: '1', data: updateData })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(clientsService.updateClient).toHaveBeenCalledWith('1', updateData)
      expect(result.current.data).toEqual(mockUpdatedClient)
    })

    it('should handle update client error', async () => {
      const error = new Error('Dados inválidos fornecidos')
      vi.mocked(clientsService.updateClient).mockRejectedValue(error)

      const { result } = renderHook(() => useUpdateClient(), {
        wrapper: createWrapper(queryClient),
      })

      const updateData = { name: '' }
      result.current.mutate({ id: '1', data: updateData })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toEqual(error)
    })
  })

  describe('useDeleteClient', () => {
    it('should delete a client successfully', async () => {
      vi.mocked(clientsService.deleteClient).mockResolvedValue(undefined)

      const { result } = renderHook(() => useDeleteClient(), {
        wrapper: createWrapper(queryClient),
      })

      result.current.mutate('1')

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(clientsService.deleteClient).toHaveBeenCalledWith('1')
    })

    it('should handle delete client error', async () => {
      const error = new Error('Cliente não encontrado')
      vi.mocked(clientsService.deleteClient).mockRejectedValue(error)

      const { result } = renderHook(() => useDeleteClient(), {
        wrapper: createWrapper(queryClient),
      })

      result.current.mutate('999')

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toEqual(error)
    })
  })
})
