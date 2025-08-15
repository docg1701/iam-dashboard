/**
 * Client management hooks using TanStack Query
 * Provides query and mutation hooks for client CRUD operations
 * Based on Story 1.4 requirements and following established patterns
 */

import {
  useQuery,
  useMutation,
  useQueryClient,
  UseQueryResult,
  UseMutationResult,
} from '@tanstack/react-query'

import { clientsService } from '@/services/clients.service'
import {
  ClientCreateRequest,
  ClientResponse,
  ClientUpdateRequest,
  ClientListResponse,
  ClientListParams,
} from '@/types/client'

// Query keys for consistent caching
export const clientsQueryKeys = {
  all: ['clients'] as const,
  lists: () => [...clientsQueryKeys.all, 'list'] as const,
  list: (params?: ClientListParams) =>
    [...clientsQueryKeys.lists(), params] as const,
  details: () => [...clientsQueryKeys.all, 'detail'] as const,
  detail: (id: string) => [...clientsQueryKeys.details(), id] as const,
}

/**
 * Hook for creating a new client
 * Includes optimistic updates and cache invalidation
 */
export function useCreateClient(): UseMutationResult<
  ClientResponse,
  Error,
  ClientCreateRequest,
  unknown
> {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ClientCreateRequest) =>
      clientsService.createClient(data),
    onSuccess: (newClient: ClientResponse) => {
      // Invalidate and refetch client lists
      queryClient.invalidateQueries({
        queryKey: clientsQueryKeys.lists(),
      })

      // Add the new client to the query cache
      queryClient.setQueryData(clientsQueryKeys.detail(newClient.id), newClient)

      // Show success message in Portuguese
      // eslint-disable-next-line no-console
      console.log(`Cliente "${newClient.name}" criado com sucesso`)
    },
    onError: (error: Error) => {
      // Error message already handled by service layer in Portuguese
      // eslint-disable-next-line no-console
      console.error('Erro ao criar cliente:', error.message)
    },
  })
}

/**
 * Hook for getting a specific client by ID
 * Includes stale-while-revalidate pattern
 */
export function useGetClient(
  id: string,
  options?: {
    enabled?: boolean
    refetchOnWindowFocus?: boolean
  }
): UseQueryResult<ClientResponse, Error> {
  return useQuery({
    queryKey: clientsQueryKeys.detail(id),
    queryFn: () => clientsService.getClient(id),
    enabled: !!id && (options?.enabled ?? true),
    refetchOnWindowFocus: options?.refetchOnWindowFocus ?? false,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}

/**
 * Hook for listing clients with pagination and filtering
 * Supports server-side pagination and search
 */
export function useListClients(
  params: ClientListParams = {},
  options?: {
    enabled?: boolean
    keepPreviousData?: boolean
  }
): UseQueryResult<ClientListResponse, Error> {
  return useQuery({
    queryKey: clientsQueryKeys.list(params),
    queryFn: () => clientsService.listClients(params),
    enabled: options?.enabled ?? true,
    placeholderData: options?.keepPreviousData
      ? previousData => previousData
      : undefined,
    staleTime: 2 * 60 * 1000, // 2 minutes (shorter for lists)
    gcTime: 5 * 60 * 1000, // 5 minutes
  })
}

/**
 * Hook for updating an existing client
 * Includes optimistic updates for better UX
 */
export function useUpdateClient(): UseMutationResult<
  ClientResponse,
  Error,
  { id: string; data: ClientUpdateRequest },
  { previousClient?: ClientResponse; previousLists?: unknown[] }
> {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ClientUpdateRequest }) =>
      clientsService.updateClient(id, data),
    onMutate: async ({ id, data }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({
        queryKey: clientsQueryKeys.detail(id),
      })

      // Snapshot the previous value
      const previousClient = queryClient.getQueryData<ClientResponse>(
        clientsQueryKeys.detail(id)
      )

      // Optimistically update the client
      if (previousClient) {
        const optimisticClient: ClientResponse = {
          ...previousClient,
          ...data,
          updated_at: new Date().toISOString(),
        }

        queryClient.setQueryData(clientsQueryKeys.detail(id), optimisticClient)

        // Update client in any list queries
        queryClient.setQueriesData(
          { queryKey: clientsQueryKeys.lists() },
          (oldData: ClientListResponse | undefined) => {
            if (!oldData) {
              return oldData
            }

            return {
              ...oldData,
              clients: oldData.clients.map(client =>
                client.id === id ? optimisticClient : client
              ),
            }
          }
        )
      }

      // Return context for rollback
      return { previousClient }
    },
    onError: (error, variables, context) => {
      // Rollback on error
      if (context?.previousClient) {
        queryClient.setQueryData(
          clientsQueryKeys.detail(variables.id),
          context.previousClient
        )
      }

      // Invalidate queries to refetch accurate data
      queryClient.invalidateQueries({
        queryKey: clientsQueryKeys.all,
      })

      // eslint-disable-next-line no-console
      console.error('Erro ao atualizar cliente:', error.message)
    },
    onSuccess: (updatedClient: ClientResponse, { id }) => {
      // Update the client cache with server response
      queryClient.setQueryData(clientsQueryKeys.detail(id), updatedClient)

      // Update client in list queries
      queryClient.setQueriesData(
        { queryKey: clientsQueryKeys.lists() },
        (oldData: ClientListResponse | undefined) => {
          if (!oldData) {
            return oldData
          }

          return {
            ...oldData,
            clients: oldData.clients.map(client =>
              client.id === id ? updatedClient : client
            ),
          }
        }
      )

      // eslint-disable-next-line no-console
      console.log(`Cliente "${updatedClient.name}" atualizado com sucesso`)
    },
    onSettled: (data, error, { id }) => {
      // Always refetch after mutation settles
      queryClient.invalidateQueries({
        queryKey: clientsQueryKeys.detail(id),
      })
    },
  })
}

/**
 * Hook for deleting a client (soft delete)
 * Includes optimistic updates and proper cache management
 */
export function useDeleteClient(): UseMutationResult<
  void,
  Error,
  string,
  { previousClient?: ClientResponse }
> {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => clientsService.deleteClient(id),
    onMutate: async (id: string) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({
        queryKey: clientsQueryKeys.detail(id),
      })

      // Snapshot the previous value
      const previousClient = queryClient.getQueryData<ClientResponse>(
        clientsQueryKeys.detail(id)
      )

      // Optimistically update by setting is_active to false
      if (previousClient) {
        const optimisticClient: ClientResponse = {
          ...previousClient,
          is_active: false,
          updated_at: new Date().toISOString(),
        }

        queryClient.setQueryData(clientsQueryKeys.detail(id), optimisticClient)

        // Update client in list queries
        queryClient.setQueriesData(
          { queryKey: clientsQueryKeys.lists() },
          (oldData: ClientListResponse | undefined) => {
            if (!oldData) {
              return oldData
            }

            return {
              ...oldData,
              clients: oldData.clients.map(client =>
                client.id === id ? optimisticClient : client
              ),
            }
          }
        )
      }

      return { previousClient }
    },
    onError: (error, id, context) => {
      // Rollback on error
      if (context?.previousClient) {
        queryClient.setQueryData(
          clientsQueryKeys.detail(id),
          context.previousClient
        )
      }

      // Invalidate queries to refetch accurate data
      queryClient.invalidateQueries({
        queryKey: clientsQueryKeys.all,
      })

      // eslint-disable-next-line no-console
      console.error('Erro ao excluir cliente:', error.message)
    },
    onSuccess: (data, id) => {
      // Remove the client from detail cache
      queryClient.removeQueries({
        queryKey: clientsQueryKeys.detail(id),
      })

      // Invalidate list queries to refetch updated data
      queryClient.invalidateQueries({
        queryKey: clientsQueryKeys.lists(),
      })

      // eslint-disable-next-line no-console
      console.log('Cliente excluído com sucesso')
    },
  })
}

/**
 * Hook for prefetching a client
 * Useful for hover states or anticipated navigation
 */
export function usePrefetchClient() {
  const queryClient = useQueryClient()

  const prefetchClient = (id: string) => {
    queryClient.prefetchQuery({
      queryKey: clientsQueryKeys.detail(id),
      queryFn: () => clientsService.getClient(id),
      staleTime: 5 * 60 * 1000, // 5 minutes
    })
  }

  return { prefetchClient }
}

/**
 * Hook for invalidating client queries
 * Useful for manual cache refresh
 */
export function useInvalidateClients() {
  const queryClient = useQueryClient()

  const invalidateAllClients = () => {
    queryClient.invalidateQueries({
      queryKey: clientsQueryKeys.all,
    })
  }

  const invalidateClientLists = () => {
    queryClient.invalidateQueries({
      queryKey: clientsQueryKeys.lists(),
    })
  }

  const invalidateClient = (id: string) => {
    queryClient.invalidateQueries({
      queryKey: clientsQueryKeys.detail(id),
    })
  }

  return {
    invalidateAllClients,
    invalidateClientLists,
    invalidateClient,
  }
}

/**
 * Type exports for consumers
 */
export type {
  ClientCreateRequest,
  ClientResponse,
  ClientUpdateRequest,
  ClientListResponse,
  ClientListParams,
}
