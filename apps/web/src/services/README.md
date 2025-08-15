# Services Documentation

This directory contains service modules that handle API communications for the IAM Dashboard.

## Available Services

### AuthService (`authService.ts`)
Handles authentication-related API calls including login, logout, 2FA operations, and user management.

### ClientsService (`clients.service.ts`)
Handles client management operations including CRUD operations with proper error handling.

## Usage Examples

### Using ClientsService

```typescript
import { clientsService } from '@/services/clients.service'

// Create a new client
try {
  const newClient = await clientsService.createClient({
    name: 'João Silva Santos',
    cpf: '12345678901',
    birth_date: '1990-05-15'
  })
  console.log('Client created:', newClient)
} catch (error) {
  console.error('Error creating client:', error.message)
}

// Get a specific client
try {
  const client = await clientsService.getClient('client-uuid-here')
  console.log('Client found:', client)
} catch (error) {
  console.error('Error fetching client:', error.message)
}

// List clients with pagination
try {
  const clientsList = await clientsService.listClients({
    page: 1,
    per_page: 10,
    search: 'João',
    is_active: true
  })
  console.log('Clients list:', clientsList)
} catch (error) {
  console.error('Error listing clients:', error.message)
}

// Update a client
try {
  const updatedClient = await clientsService.updateClient('client-uuid-here', {
    name: 'João Silva Santos Jr.',
    is_active: true
  })
  console.log('Client updated:', updatedClient)
} catch (error) {
  console.error('Error updating client:', error.message)
}

// Delete a client (soft delete)
try {
  await clientsService.deleteClient('client-uuid-here')
  console.log('Client deleted successfully')
} catch (error) {
  console.error('Error deleting client:', error.message)
}
```

## Error Handling

All services implement consistent error handling with user-friendly Portuguese messages for better UX. Errors are automatically extracted from HTTP responses and include:

- 400: Dados inválidos fornecidos
- 401: Sessão expirada. Faça login novamente
- 403: Você não tem permissão para realizar esta ação
- 404: Cliente não encontrado (or appropriate resource)
- 409: Conflito de dados (e.g., CPF já cadastrado)
- 422: Dados de entrada inválidos
- 500: Erro interno do servidor

## HTTP Client

All services use the shared `httpClient` which provides:

- Automatic JWT token management
- Token refresh on 401 errors
- Request/response interceptors
- Consistent timeout handling
- Authentication header management