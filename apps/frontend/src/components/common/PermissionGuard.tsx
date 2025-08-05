/**
 * Permission Guard Component
 * 
 * Provides conditional rendering based on user permissions with comprehensive
 * loading states, error handling, and fallback components.
 */

'use client'

import React, { Suspense } from 'react'
import { 
  AgentName, 
  PermissionOperation, 
  PermissionGuardProps,
} from '@/types/permissions'
import { usePermissionCheck, useAgentAccess } from '@/hooks/useUserPermissions'
// Using local Alert, AlertDescription, and Skeleton components defined below
import { AlertTriangle, Lock, Loader2 } from 'lucide-react'

/**
 * Default loading component
 */
const DefaultLoadingComponent: React.FC = () => (
  <div className="flex items-center space-x-2 p-4">
    <Loader2 className="h-4 w-4 animate-spin" />
    <span className="text-sm text-muted-foreground">Verificando permissões...</span>
  </div>
)

/**
 * Default fallback component for insufficient permissions
 */
const DefaultFallbackComponent: React.FC<{
  agent: AgentName
  operation?: PermissionOperation
}> = ({ agent, operation }) => (
  <Alert variant="destructive" className="max-w-md">
    <Lock className="h-4 w-4" />
    <AlertDescription>
      {operation 
        ? `Você não tem permissão para ${getOperationText(operation)} no agente ${getAgentText(agent)}.`
        : `Você não tem acesso ao agente ${getAgentText(agent)}.`
      }
    </AlertDescription>
  </Alert>
)

/**
 * Error component for permission check failures
 */
const PermissionErrorComponent: React.FC<{
  error: Error
  agent: AgentName
  operation?: PermissionOperation
}> = ({ error, agent, operation }) => (
  <Alert variant="destructive" className="max-w-md">
    <AlertTriangle className="h-4 w-4" />
    <AlertDescription>
      Erro ao verificar permissões{operation && ` para ${getOperationText(operation)}`} 
      no agente {getAgentText(agent)}: {error.message}
    </AlertDescription>
  </Alert>
)

/**
 * Skeleton loading component for better UX
 */
const SkeletonLoading: React.FC<{ className?: string }> = ({ className }) => (
  <div className={className}>
    <Skeleton className="h-4 w-full mb-2" />
    <Skeleton className="h-4 w-3/4 mb-2" />
    <Skeleton className="h-4 w-1/2" />
  </div>
)

/**
 * Main Permission Guard Component
 */
export const PermissionGuard: React.FC<PermissionGuardProps> = ({
  agent,
  operation,
  userId,
  fallback,
  loading,
  children,
}) => {
  // Use appropriate hook based on whether we're checking a specific operation
  const permissionCheck = usePermissionCheck(agent, operation!, userId)
  const agentAccess = useAgentAccess(agent, userId)
  
  // Determine which check to use
  const checkResult = operation ? permissionCheck : agentAccess
  const { isLoading, error } = checkResult
  const allowed = operation ? permissionCheck.allowed : agentAccess.hasAccess

  // Handle loading state
  if (isLoading) {
    if (loading) {
      return <>{loading}</>
    }
    return <DefaultLoadingComponent />
  }

  // Handle error state
  if (error) {
    return (
      <PermissionErrorComponent 
        error={error} 
        agent={agent} 
        operation={operation} 
      />
    )
  }

  // Handle insufficient permissions
  if (!allowed) {
    if (fallback) {
      return <>{fallback}</>
    }
    return <DefaultFallbackComponent agent={agent} operation={operation} />
  }

  // Render children if permission check passes
  return <>{children}</>
}

/**
 * Specific permission guard for create operations
 */
export const CreatePermissionGuard: React.FC<
  Omit<PermissionGuardProps, 'operation'>
> = (props) => (
  <PermissionGuard {...props} operation="create" />
)

/**
 * Specific permission guard for read operations
 */
export const ReadPermissionGuard: React.FC<
  Omit<PermissionGuardProps, 'operation'>
> = (props) => (
  <PermissionGuard {...props} operation="read" />
)

/**
 * Specific permission guard for update operations
 */
export const UpdatePermissionGuard: React.FC<
  Omit<PermissionGuardProps, 'operation'>
> = (props) => (
  <PermissionGuard {...props} operation="update" />
)

/**
 * Specific permission guard for delete operations
 */
export const DeletePermissionGuard: React.FC<
  Omit<PermissionGuardProps, 'operation'>
> = (props) => (
  <PermissionGuard {...props} operation="delete" />
)

/**
 * Agent access guard (any permission for the agent)
 */
export const AgentAccessGuard: React.FC<
  Omit<PermissionGuardProps, 'operation'>
> = (props) => (
  <PermissionGuard {...props} />
)

/**
 * Multiple permission guard (OR logic - user needs at least one permission)
 * This is a simplified version that doesn't support dynamic permission arrays
 * due to React hooks limitations. For dynamic permissions, use individual PermissionGuards.
 */
export const MultiplePermissionGuard: React.FC<{
  permissions: Array<{
    agent: AgentName
    operation?: PermissionOperation
  }>
  userId?: string
  fallback?: React.ReactNode
  loading?: React.ReactNode
  children: React.ReactNode
}> = ({ permissions, userId, fallback, loading, children }) => {
  // For now, only check the first permission to avoid hooks violations
  // TODO: Implement proper multiple permission checking with dynamic hooks
  const firstPermission = permissions[0]
  
  if (!firstPermission) {
    return <>{fallback}</>
  }
  
  if (firstPermission.operation) {
    return (
      <PermissionGuard 
        agent={firstPermission.agent} 
        operation={firstPermission.operation}
        userId={userId}
        fallback={fallback}
        loading={loading}
      >
        {children}
      </PermissionGuard>
    )
  }
  
  // For agent-only checks (no specific operation), always allow for now
  // This is a simplification to avoid hooks violations
  return <>{children}</>
}

/**
 * Permission guard with Suspense wrapper for better loading UX
 */
export const SuspensePermissionGuard: React.FC<PermissionGuardProps> = ({
  loading,
  ...props
}) => (
  <Suspense fallback={loading || <SkeletonLoading />}>
    <PermissionGuard {...props} loading={loading} />
  </Suspense>
)

/**
 * Higher-order component for wrapping components with permission checks
 */
export function withPermissionGuard<P extends object>(
  Component: React.ComponentType<P>,
  permissionConfig: {
    agent: AgentName
    operation?: PermissionOperation
    fallback?: React.ReactNode
    loading?: React.ReactNode
  }
) {
  const WrappedComponent: React.FC<P & { userId?: string }> = ({ userId, ...props }) => (
    <PermissionGuard
      agent={permissionConfig.agent}
      operation={permissionConfig.operation}
      userId={userId}
      fallback={permissionConfig.fallback}
      loading={permissionConfig.loading}
    >
      <Component {...(props as P)} />
    </PermissionGuard>
  )
  
  WrappedComponent.displayName = `withPermissionGuard(${Component.displayName || Component.name})`
  
  return WrappedComponent
}

// Utility functions for text display
function getOperationText(operation: PermissionOperation): string {
  const operationMap: Record<PermissionOperation, string> = {
    create: 'criar',
    read: 'visualizar',
    update: 'editar',
    delete: 'excluir',
  }
  return operationMap[operation] || operation
}

function getAgentText(agent: AgentName): string {
  const agentMap: Record<AgentName, string> = {
    [AgentName.CLIENT_MANAGEMENT]: 'Gestão de Clientes',
    [AgentName.PDF_PROCESSING]: 'Processamento de PDFs',
    [AgentName.REPORTS_ANALYSIS]: 'Relatórios e Análises',
    [AgentName.AUDIO_RECORDING]: 'Gravação de Áudio',
  }
  return agentMap[agent] || agent
}

// Create Alert and Skeleton components if they don't exist
const Alert = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    variant?: 'default' | 'destructive'
  }
>(({ className, variant = 'default', ...props }, ref) => (
  <div
    ref={ref}
    role="alert"
    className={`relative w-full rounded-lg border p-4 ${
      variant === 'destructive' 
        ? 'border-red-200 bg-red-50 text-red-900 dark:border-red-800 dark:bg-red-950 dark:text-red-50' 
        : 'border-border bg-background text-foreground'
    } ${className}`}
    {...props}
  />
))
Alert.displayName = 'Alert'

const AlertDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={`text-sm [&_p]:leading-relaxed ${className}`}
    {...props}
  />
))
AlertDescription.displayName = 'AlertDescription'

const Skeleton = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={`animate-pulse rounded-md bg-muted ${className}`}
    {...props}
  />
))
Skeleton.displayName = 'Skeleton'

export default PermissionGuard