# Client Management Hooks

This directory contains TanStack Query hooks for managing client operations in the IAM Dashboard.

## Overview

The `useClients.ts` file provides a complete set of hooks for client CRUD operations with proper caching, error handling, and optimistic updates.

## Available Hooks

### Query Hooks

- **`useGetClient(id, options?)`** - Fetch a specific client by ID
- **`useListClients(params?, options?)`** - Fetch paginated list of clients with filtering

### Mutation Hooks

- **`useCreateClient()`** - Create a new client
- **`useUpdateClient()`** - Update an existing client with optimistic updates
- **`useDeleteClient()`** - Soft delete a client with optimistic updates

### Utility Hooks

- **`usePrefetchClient()`** - Prefetch client data for performance
- **`useInvalidateClients()`** - Manual cache invalidation

## Key Features

### 1. Consistent Query Keys
```typescript
export const clientsQueryKeys = {
  all: ['clients'] as const,
  lists: () => [...clientsQueryKeys.all, 'list'] as const,
  list: (params?: ClientListParams) => [...clientsQueryKeys.lists(), params] as const,
  details: () => [...clientsQueryKeys.all, 'detail'] as const,
  detail: (id: string) => [...clientsQueryKeys.details(), id] as const,
}
```

### 2. Optimistic Updates
Mutations include optimistic updates for better user experience:
- Update operations show changes immediately
- Rollback on error
- Proper cache synchronization

### 3. Error Handling
- Portuguese error messages from service layer
- Proper error propagation
- Automatic retry logic from TanStack Query configuration

### 4. Cache Management
- Automatic cache invalidation after mutations
- Stale-while-revalidate pattern
- Configurable cache times (5-10 minutes)

## Usage Examples

### Basic Usage
```typescript
// Fetch client list
const { data, isLoading, error } = useListClients({ page: 1, per_page: 10 })

// Create client
const createMutation = useCreateClient()
createMutation.mutate({ name: 'João', cpf: '12345678901', birth_date: '1990-01-01' })

// Update client
const updateMutation = useUpdateClient()
updateMutation.mutate({ id: '1', data: { name: 'João Santos' } })
```

### Advanced Features
```typescript
// Prefetch for performance
const { prefetchClient } = usePrefetchClient()
prefetchClient('123') // Prefetch client data

// Manual cache refresh
const { invalidateAllClients } = useInvalidateClients()
invalidateAllClients() // Force refetch all client data

// Paginated list with keepPreviousData
const { data } = useListClients(
  { page, per_page: 10 }, 
  { keepPreviousData: true }
)
```

## Integration with Existing Architecture

### Service Layer Integration
Hooks use the existing `clientsService` from `/services/clients.service.ts`:
- Maintains existing error handling patterns
- Portuguese error messages
- Consistent API communication

### TypeScript Support
Full TypeScript support with proper type inference:
- Import types from `/types/client.ts`
- Type-safe parameters and return values
- IntelliSense support

### Testing
Comprehensive test coverage in `__tests__/useClients.test.tsx`:
- All hooks tested with success and error scenarios
- Mock service integration
- Proper TanStack Query test setup

## Best Practices

### 1. Query Key Management
Always use the provided `clientsQueryKeys` for consistent caching:
```typescript
// ✅ Good
queryClient.invalidateQueries({ queryKey: clientsQueryKeys.lists() })

// ❌ Bad
queryClient.invalidateQueries({ queryKey: ['clients', 'list'] })
```

### 2. Error Handling
Let the hooks handle errors with Portuguese messages:
```typescript
const { data, error } = useListClients()
if (error) {
  // error.message already contains user-friendly Portuguese message
  return <div>Erro: {error.message}</div>
}
```

### 3. Loading States
Use the provided loading states for better UX:
```typescript
const { data, isLoading, isFetching } = useListClients()
// isLoading: initial load
// isFetching: background refetch
```

### 4. Optimistic Updates
Trust the optimistic updates for mutations:
```typescript
const updateMutation = useUpdateClient()
// UI updates immediately, rolls back on error
updateMutation.mutate({ id: '1', data: { name: 'New Name' } })
```

## TanStack Query Configuration

Hooks inherit configuration from the global QueryClient in `/app/providers.tsx`:
- 1-minute stale time for queries
- 10-minute garbage collection time
- Smart retry logic (no retry on 4xx errors except 408, 429)
- Exponential backoff retry delay

Individual hooks may override these defaults based on usage patterns:
- Lists: 2-minute stale time (more frequent updates)
- Details: 5-minute stale time (less frequent updates)

## Dependencies

- `@tanstack/react-query` ^5.84.0
- Existing service layer (`/services/clients.service.ts`)
- TypeScript types (`/types/client.ts`)

## File Structure

```
src/hooks/
├── useClients.ts              # Main hooks file
├── __tests__/
│   └── useClients.test.tsx    # Comprehensive tests
└── README.md                  # This file

docs/examples/
└── useClients-examples.tsx    # Usage examples
```

For complete usage examples, see `/docs/examples/useClients-examples.tsx`.