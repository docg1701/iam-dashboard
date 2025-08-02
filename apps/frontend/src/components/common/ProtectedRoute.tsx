"use client"

import { useEffect, ReactNode } from "react"
import { useRouter } from "next/navigation"
import useAuthStore from "@/store/authStore"
import { Loader2 } from "lucide-react"

interface ProtectedRouteProps {
  children: ReactNode
  requiredRole?: 'sysadmin' | 'admin' | 'user'
  fallback?: ReactNode
  redirectTo?: string
}

export function ProtectedRoute({ 
  children, 
  requiredRole = 'user',
  fallback,
  redirectTo = '/login'
}: ProtectedRouteProps) {
  const router = useRouter()
  const { 
    isAuthenticated, 
    isLoading, 
    user, 
    hasPermission,
    isTokenExpired,
    refreshToken,
    logout 
  } = useAuthStore()

  useEffect(() => {
    // Skip auth check during hydration
    if (typeof window === 'undefined') return

    const checkAuth = async () => {
      // If not authenticated, redirect to login
      if (!isAuthenticated || !user) {
        router.push(redirectTo)
        return
      }

      // Check if token is expired
      if (isTokenExpired()) {
        try {
          await refreshToken()
        } catch (error) {
          console.error('Token refresh failed:', error)
          logout()
          router.push(redirectTo)
          return
        }
      }

      // Check role-based permissions
      if (!hasPermission(requiredRole)) {
        router.push('/unauthorized')
        return
      }
    }

    checkAuth()
  }, [
    isAuthenticated, 
    user, 
    requiredRole, 
    router, 
    redirectTo, 
    hasPermission, 
    isTokenExpired, 
    refreshToken, 
    logout
  ])

  // Show loading during auth check
  if (isLoading) {
    return (
      fallback || (
        <div className="min-h-screen flex items-center justify-center">
          <div className="flex items-center gap-2">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>Verificando autenticação...</span>
          </div>
        </div>
      )
    )
  }

  // Don't render children until auth is verified
  if (!isAuthenticated || !user || !hasPermission(requiredRole)) {
    return (
      fallback || (
        <div className="min-h-screen flex items-center justify-center">
          <div className="flex items-center gap-2">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>Redirecionando...</span>
          </div>
        </div>
      )
    )
  }

  return <>{children}</>
}

// Higher-order component for protecting pages
export function withAuth<T extends object>(
  Component: React.ComponentType<T>,
  options?: Omit<ProtectedRouteProps, 'children'>
) {
  return function AuthenticatedComponent(props: T) {
    return (
      <ProtectedRoute {...options}>
        <Component {...props} />
      </ProtectedRoute>
    )
  }
}

// Hook for checking authentication status
export function useAuth() {
  const store = useAuthStore()
  
  return {
    ...store,
    isAdmin: store.hasPermission('admin'),
    isSysAdmin: store.hasPermission('sysadmin'),
  }
}