'use client'

import { useRouter } from 'next/navigation'
import React, { ReactNode, useEffect } from 'react'

import { useAuth, usePermissions } from '../../contexts/AuthContext'

interface ProtectedRouteProps {
  children: ReactNode
  requiredRole?: 'sysadmin' | 'admin' | 'user'
  requiredPermission?: {
    agent: string
    action: 'create' | 'read' | 'update' | 'delete'
  }
  fallback?: ReactNode
  redirectTo?: string
}

// Componente de carregamento
const LoadingSpinner = () => (
  <div className="flex min-h-screen items-center justify-center">
    <div className="h-32 w-32 animate-spin rounded-full border-b-2 border-blue-600"></div>
    <span className="ml-4 text-gray-600">Carregando...</span>
  </div>
)

// Componente de acesso negado
const AccessDenied = ({ message }: { message: string }) => (
  <div className="flex min-h-screen items-center justify-center">
    <div className="p-8 text-center">
      <div className="mb-4 text-6xl text-red-500">🚫</div>
      <h1 className="mb-2 text-2xl font-bold text-gray-800">Acesso Negado</h1>
      <p className="text-gray-600">{message}</p>
    </div>
  </div>
)

/**
 * Componente para proteger rotas que requerem autenticação
 *
 * @example
 * // Rota que requer apenas autenticação
 * <ProtectedRoute>
 *   <DashboardPage />
 * </ProtectedRoute>
 *
 * @example
 * // Rota que requer papel específico
 * <ProtectedRoute requiredRole="admin">
 *   <AdminPanel />
 * </ProtectedRoute>
 *
 * @example
 * // Rota que requer permissão específica
 * <ProtectedRoute requiredPermission={{ agent: "client_management", action: "read" }}>
 *   <ClientsList />
 * </ProtectedRoute>
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRole,
  requiredPermission,
  fallback,
  redirectTo = '/login',
}) => {
  const { user, isAuthenticated, isLoading } = useAuth()
  const { hasRole } = usePermissions()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push(redirectTo)
    }
  }, [isAuthenticated, isLoading, router, redirectTo])

  // Exibir loading enquanto verifica autenticação
  if (isLoading) {
    return fallback || <LoadingSpinner />
  }

  // Redirecionar se não estiver autenticado
  if (!isAuthenticated || !user) {
    return null // O useEffect já vai redirecionar
  }

  // Verificar papel se necessário
  if (requiredRole && !hasRole(requiredRole)) {
    const message = `Esta página requer permissão de ${requiredRole}. Você tem permissão de ${user.role}.`
    return fallback || <AccessDenied message={message} />
  }

  // Verificar permissão específica se necessário
  if (requiredPermission) {
    // TODO: Implementar verificação de permissão específica quando o sistema de permissões estiver pronto
    // Por enquanto, assumir que usuários autenticados têm acesso básico
  }

  // Renderizar conteúdo protegido
  return <>{children}</>
}

interface PermissionGuardProps {
  children: ReactNode
  requiredRole?: 'sysadmin' | 'admin' | 'user'
  requiredPermission?: {
    agent: string
    action: 'create' | 'read' | 'update' | 'delete'
  }
  fallback?: ReactNode
}

/**
 * Componente para renderizar condicionalmente baseado em permissões
 * Usado dentro de páginas para mostrar/ocultar elementos específicos
 *
 * @example
 * <PermissionGuard requiredRole="admin">
 *   <DeleteButton />
 * </PermissionGuard>
 */
export const PermissionGuard: React.FC<PermissionGuardProps> = ({
  children,
  requiredRole,
  requiredPermission,
  fallback,
}) => {
  const { user, isAuthenticated } = useAuth()
  const { hasRole } = usePermissions()

  if (!isAuthenticated || !user) {
    return fallback || null
  }

  if (requiredRole && !hasRole(requiredRole)) {
    return fallback || null
  }

  if (requiredPermission) {
    // TODO: Implementar verificação de permissão específica
  }

  return <>{children}</>
}

interface RoleGuardProps {
  children: ReactNode
  roles: ('sysadmin' | 'admin' | 'user')[]
  fallback?: ReactNode
}

/**
 * Componente para renderizar baseado em uma lista de papéis permitidos
 *
 * @example
 * <RoleGuard roles={['admin', 'sysadmin']}>
 *   <AdminFeature />
 * </RoleGuard>
 */
export const RoleGuard: React.FC<RoleGuardProps> = ({
  children,
  roles,
  fallback,
}) => {
  const { user, isAuthenticated } = useAuth()

  if (!isAuthenticated || !user) {
    return fallback || null
  }

  if (!roles.includes(user.role)) {
    return fallback || null
  }

  return <>{children}</>
}

// Hook para verificar se uma rota específica está acessível
export const useRouteAccess = (
  requiredRole?: 'sysadmin' | 'admin' | 'user',
  requiredPermission?: {
    agent: string
    action: 'create' | 'read' | 'update' | 'delete'
  }
) => {
  const { user, isAuthenticated } = useAuth()
  const { hasRole } = usePermissions()

  if (!isAuthenticated || !user) {
    return { canAccess: false, reason: 'Não autenticado' }
  }

  if (requiredRole && !hasRole(requiredRole)) {
    return {
      canAccess: false,
      reason: `Requer permissão de ${requiredRole}, mas você tem ${user.role}`,
    }
  }

  if (requiredPermission) {
    // TODO: Implementar verificação de permissão específica
    return { canAccess: true, reason: 'Permissão específica não verificada' }
  }

  return { canAccess: true, reason: 'Acesso permitido' }
}

export default ProtectedRoute
