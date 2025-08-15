'use client'

import { useRouter } from 'next/navigation'
import { useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useListClients } from '@/hooks/useClients'
import {
  formatCPFForDisplay,
  formatBirthDateForDisplay,
} from '@/lib/validations/client'

export default function ClientsPage() {
  const router = useRouter()
  const [searchTerm, setSearchTerm] = useState('')
  const [page, setPage] = useState(1)
  const perPage = 10

  const {
    data: clientsData,
    isLoading,
    isError,
    error,
    refetch,
  } = useListClients({
    page,
    per_page: perPage,
    search: searchTerm || undefined,
    is_active: true,
  })

  const handleCreateNew = () => {
    router.push('/clients/new')
  }

  const handleSearch = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setPage(1) // Reset to first page when searching
    refetch()
  }

  const handlePageChange = (newPage: number) => {
    setPage(newPage)
  }

  const handleClientClick = (clientId: string) => {
    // TODO: Navigate to client details page when implemented
    // eslint-disable-next-line no-console
    console.log('Navigate to client:', clientId)
  }

  if (isError) {
    const errorMessage =
      error instanceof Error
        ? error.message
        : 'Erro ao carregar lista de clientes'

    return (
      <div className="container mx-auto px-4 py-8">
        <div className="mx-auto max-w-4xl">
          <Card className="border-red-200 bg-red-50">
            <CardHeader>
              <CardTitle className="text-red-800">
                ❌ Erro ao carregar clientes
              </CardTitle>
              <CardDescription className="text-red-600">
                {errorMessage}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                onClick={() => refetch()}
                variant="outline"
                className="border-red-300 text-red-700 hover:bg-red-100"
              >
                Tentar novamente
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Gerenciamento de Clientes
              </h1>
              <p className="mt-2 text-gray-600">
                Visualize e gerencie todos os clientes cadastrados no sistema
              </p>
            </div>
            <Button onClick={handleCreateNew} className="ml-4">
              ➕ Novo Cliente
            </Button>
          </div>
        </div>

        {/* Search Bar */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <form onSubmit={handleSearch} className="flex gap-4">
              <Input
                type="text"
                placeholder="Buscar por nome ou CPF..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="flex-1"
              />
              <Button type="submit" variant="outline">
                🔍 Buscar
              </Button>
              {searchTerm && (
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => {
                    setSearchTerm('')
                    setPage(1)
                    refetch()
                  }}
                >
                  ✕ Limpar
                </Button>
              )}
            </form>
          </CardContent>
        </Card>

        {/* Loading State */}
        {isLoading && (
          <Card>
            <CardContent className="py-12 text-center">
              <div className="flex items-center justify-center space-x-2">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
                <span className="text-gray-600">Carregando clientes...</span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Clients List */}
        {!isLoading && clientsData && (
          <>
            {/* Stats */}
            <div className="mb-6 grid gap-4 md:grid-cols-3">
              <Card>
                <CardContent className="p-4">
                  <div className="text-2xl font-bold text-blue-600">
                    {clientsData.total}
                  </div>
                  <div className="text-sm text-gray-600">Total de Clientes</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-2xl font-bold text-green-600">
                    {clientsData.clients.length}
                  </div>
                  <div className="text-sm text-gray-600">Nesta Página</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-2xl font-bold text-purple-600">
                    {clientsData.total_pages}
                  </div>
                  <div className="text-sm text-gray-600">Páginas Total</div>
                </CardContent>
              </Card>
            </div>

            {/* Clients Table */}
            {clientsData.clients.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <div className="text-gray-500">
                    {searchTerm
                      ? `Nenhum cliente encontrado para "${searchTerm}"`
                      : 'Nenhum cliente cadastrado ainda'}
                  </div>
                  {!searchTerm && (
                    <Button
                      onClick={handleCreateNew}
                      className="mt-4"
                      variant="outline"
                    >
                      ➕ Cadastrar Primeiro Cliente
                    </Button>
                  )}
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle>
                    Lista de Clientes
                    {searchTerm && (
                      <span className="text-sm font-normal text-gray-600">
                        {' '}
                        (resultados para &quot;{searchTerm}&quot;)
                      </span>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {clientsData.clients.map(client => (
                      <div
                        key={client.id}
                        className="flex cursor-pointer items-center justify-between rounded-lg border p-4 transition-colors hover:bg-gray-50"
                        onClick={() => handleClientClick(client.id)}
                      >
                        <div className="flex-1">
                          <div className="flex items-center space-x-4">
                            <div>
                              <h3 className="font-semibold text-gray-900">
                                {client.name}
                              </h3>
                              <p className="text-sm text-gray-600">
                                CPF: {formatCPFForDisplay(client.cpf)}
                              </p>
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-gray-600">
                            Nascimento:{' '}
                            {formatBirthDateForDisplay(client.birth_date)}
                          </div>
                          <div className="text-xs text-gray-500">
                            Criado:{' '}
                            {new Date(client.created_at).toLocaleDateString(
                              'pt-BR'
                            )}
                          </div>
                        </div>
                        <div className="ml-4">
                          {client.is_active ? (
                            <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                              Ativo
                            </span>
                          ) : (
                            <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800">
                              Inativo
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Pagination */}
            {clientsData.total_pages > 1 && (
              <Card className="mt-6">
                <CardContent className="py-4">
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-gray-600">
                      Página {clientsData.page} de {clientsData.total_pages} (
                      {clientsData.total} clientes total)
                    </div>
                    <div className="flex space-x-2">
                      <Button
                        onClick={() => handlePageChange(page - 1)}
                        disabled={page <= 1}
                        variant="outline"
                        size="sm"
                      >
                        ← Anterior
                      </Button>
                      <Button
                        onClick={() => handlePageChange(page + 1)}
                        disabled={page >= clientsData.total_pages}
                        variant="outline"
                        size="sm"
                      >
                        Próxima →
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </>
        )}

        {/* Development Debug Info */}
        {process.env.NODE_ENV === 'development' && (
          <Card className="mt-8 border-blue-200 bg-blue-50">
            <CardHeader>
              <CardTitle className="text-sm text-blue-800">
                🔧 Informações de Debug (Development)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-1 text-xs text-blue-700">
                <p>• Busca atual: &quot;{searchTerm || 'sem filtro'}&quot;</p>
                <p>• Página atual: {page}</p>
                <p>• Itens por página: {perPage}</p>
                <p>
                  • Estado de carregamento:{' '}
                  {isLoading ? 'carregando' : 'carregado'}
                </p>
                <p>• Total de clientes: {clientsData?.total || 0}</p>
                <p>• Hook: useListClients com TanStack Query</p>
                <p>• Validação: Zod schemas para type safety</p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
