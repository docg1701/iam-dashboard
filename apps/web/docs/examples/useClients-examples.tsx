/**
 * Examples of how to use the client hooks in components
 * This file serves as documentation and usage examples
 */

import React from 'react'
import {
  useCreateClient,
  useGetClient,
  useListClients,
  useUpdateClient,
  useDeleteClient,
  usePrefetchClient,
  useInvalidateClients,
} from '@/hooks/useClients'
import type { ClientCreateRequest, ClientUpdateRequest } from '@/types/client'

// Example 1: Simple client list component
export function ClientList() {
  const {
    data: clientsData,
    isLoading,
    error,
  } = useListClients({
    page: 1,
    per_page: 10,
    is_active: true,
  })

  if (isLoading) {
    return <div>Carregando clientes...</div>
  }

  if (error) {
    return <div>Erro ao carregar clientes: {error.message}</div>
  }

  return (
    <div>
      <h2>Clientes ({clientsData?.total || 0})</h2>
      <ul>
        {clientsData?.clients.map(client => (
          <li key={client.id}>
            {client.name} - {client.cpf}
          </li>
        ))}
      </ul>
    </div>
  )
}

// Example 2: Client details with prefetching
export function ClientDetails({ clientId }: { clientId: string }) {
  const { data: client, isLoading, error } = useGetClient(clientId)
  const { prefetchClient } = usePrefetchClient()

  // Prefetch related clients on hover
  const handleMouseEnter = (id: string) => {
    prefetchClient(id)
  }

  if (isLoading) {
    return <div>Carregando cliente...</div>
  }

  if (error) {
    return <div>Erro ao carregar cliente: {error.message}</div>
  }

  if (!client) {
    return <div>Cliente não encontrado</div>
  }

  return (
    <div>
      <h2>{client.name}</h2>
      <p>CPF: {client.cpf}</p>
      <p>Data de Nascimento: {client.birth_date}</p>
      <p>Status: {client.is_active ? 'Ativo' : 'Inativo'}</p>
      <p>Criado em: {new Date(client.created_at).toLocaleDateString()}</p>
    </div>
  )
}

// Example 3: Create client form
export function CreateClientForm() {
  const createClientMutation = useCreateClient()

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)

    const clientData: ClientCreateRequest = {
      name: formData.get('name') as string,
      cpf: formData.get('cpf') as string,
      birth_date: formData.get('birth_date') as string,
    }

    createClientMutation.mutate(clientData)
  }

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="name">Nome:</label>
        <input type="text" id="name" name="name" required />
      </div>
      <div>
        <label htmlFor="cpf">CPF:</label>
        <input type="text" id="cpf" name="cpf" required />
      </div>
      <div>
        <label htmlFor="birth_date">Data de Nascimento:</label>
        <input type="date" id="birth_date" name="birth_date" required />
      </div>
      <button type="submit" disabled={createClientMutation.isPending}>
        {createClientMutation.isPending ? 'Criando...' : 'Criar Cliente'}
      </button>
      {createClientMutation.error && (
        <div style={{ color: 'red' }}>
          Erro: {createClientMutation.error.message}
        </div>
      )}
    </form>
  )
}

// Example 4: Update client with optimistic updates
export function UpdateClientForm({ clientId }: { clientId: string }) {
  const { data: client } = useGetClient(clientId)
  const updateClientMutation = useUpdateClient()

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)

    const updateData: ClientUpdateRequest = {
      name: formData.get('name') as string,
      cpf: formData.get('cpf') as string,
      birth_date: formData.get('birth_date') as string,
    }

    updateClientMutation.mutate({ id: clientId, data: updateData })
  }

  if (!client) {
    return <div>Cliente não encontrado</div>
  }

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="name">Nome:</label>
        <input
          type="text"
          id="name"
          name="name"
          defaultValue={client.name}
          required
        />
      </div>
      <div>
        <label htmlFor="cpf">CPF:</label>
        <input
          type="text"
          id="cpf"
          name="cpf"
          defaultValue={client.cpf}
          required
        />
      </div>
      <div>
        <label htmlFor="birth_date">Data de Nascimento:</label>
        <input
          type="date"
          id="birth_date"
          name="birth_date"
          defaultValue={client.birth_date}
          required
        />
      </div>
      <button type="submit" disabled={updateClientMutation.isPending}>
        {updateClientMutation.isPending
          ? 'Atualizando...'
          : 'Atualizar Cliente'}
      </button>
      {updateClientMutation.error && (
        <div style={{ color: 'red' }}>
          Erro: {updateClientMutation.error.message}
        </div>
      )}
    </form>
  )
}

// Example 5: Delete client with confirmation
export function DeleteClientButton({ clientId }: { clientId: string }) {
  const deleteClientMutation = useDeleteClient()

  const handleDelete = () => {
    if (window.confirm('Tem certeza que deseja excluir este cliente?')) {
      deleteClientMutation.mutate(clientId)
    }
  }

  return (
    <button
      onClick={handleDelete}
      disabled={deleteClientMutation.isPending}
      style={{
        backgroundColor: 'red',
        color: 'white',
        opacity: deleteClientMutation.isPending ? 0.6 : 1,
      }}
    >
      {deleteClientMutation.isPending ? 'Excluindo...' : 'Excluir Cliente'}
    </button>
  )
}

// Example 6: Paginated client list with search
export function PaginatedClientList() {
  const [page, setPage] = React.useState(1)
  const [search, setSearch] = React.useState('')
  const perPage = 10

  const {
    data: clientsData,
    isLoading,
    error,
    isFetching,
  } = useListClients(
    {
      page,
      per_page: perPage,
      search: search.trim() || undefined,
      is_active: true,
    },
    {
      keepPreviousData: true, // Keep previous data while fetching new page
    }
  )

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(event.target.value)
    setPage(1) // Reset to first page when searching
  }

  return (
    <div>
      <div>
        <input
          type="text"
          placeholder="Buscar clientes..."
          value={search}
          onChange={handleSearchChange}
        />
        {isFetching && <span> Carregando...</span>}
      </div>

      {isLoading && page === 1 ? (
        <div>Carregando clientes...</div>
      ) : error ? (
        <div>Erro ao carregar clientes: {error.message}</div>
      ) : (
        <>
          <ul>
            {clientsData?.clients.map(client => (
              <li key={client.id}>
                {client.name} - {client.cpf}
              </li>
            ))}
          </ul>

          {/* Pagination controls */}
          <div>
            <button
              onClick={() => setPage(page - 1)}
              disabled={page === 1 || isFetching}
            >
              Anterior
            </button>
            <span>
              Página {page} de {clientsData?.total_pages || 1}
            </span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={
                !clientsData || page >= clientsData.total_pages || isFetching
              }
            >
              Próxima
            </button>
          </div>

          <div>Total: {clientsData?.total || 0} clientes</div>
        </>
      )}
    </div>
  )
}

// Example 7: Manual cache invalidation
export function RefreshDataButton() {
  const { invalidateAllClients, invalidateClientLists } = useInvalidateClients()

  return (
    <div>
      <button onClick={invalidateAllClients}>Atualizar Todos os Dados</button>
      <button onClick={invalidateClientLists}>Atualizar Listas</button>
    </div>
  )
}

// Example 8: Error handling with retry
export function ClientListWithRetry() {
  const {
    data: clientsData,
    isLoading,
    error,
    refetch,
    isRefetching,
  } = useListClients()

  if (isLoading) {
    return <div>Carregando clientes...</div>
  }

  if (error) {
    return (
      <div>
        <p>Erro ao carregar clientes: {error.message}</p>
        <button onClick={() => refetch()} disabled={isRefetching}>
          {isRefetching ? 'Tentando novamente...' : 'Tentar Novamente'}
        </button>
      </div>
    )
  }

  return (
    <div>
      <h2>Clientes ({clientsData?.total || 0})</h2>
      <button onClick={() => refetch()} disabled={isRefetching}>
        {isRefetching ? 'Atualizando...' : 'Atualizar'}
      </button>
      <ul>
        {clientsData?.clients.map(client => (
          <li key={client.id}>
            {client.name} - {client.cpf}
          </li>
        ))}
      </ul>
    </div>
  )
}
