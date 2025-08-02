"use client"

import { createContext, useContext, useEffect, ReactNode } from "react"
import useAuthStore from "@/store/authStore"
import type { User } from "@/types/auth"

interface AuthContextValue {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  hasRole: (role: 'sysadmin' | 'admin' | 'user') => boolean
  hasAnyRole: (roles: ('sysadmin' | 'admin' | 'user')[]) => boolean
  isAdmin: boolean
  isSysAdmin: boolean
  canAccess: (resource: string, action?: string) => boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const { 
    user, 
    isAuthenticated, 
    isLoading, 
    hasPermission,
    isTokenExpired,
    refreshToken,
    logout
  } = useAuthStore()

  // Auto-refresh token on mount and when it's about to expire
  useEffect(() => {
    if (!isAuthenticated || !user) return

    const checkAndRefreshToken = async () => {
      try {
        // Check if token is expired or will expire in the next 5 minutes
        if (isTokenExpired()) {
          await refreshToken()
        }
      } catch (error) {
        console.error('Token refresh failed:', error)
        logout()
      }
    }

    // Check immediately
    checkAndRefreshToken()

    // Set up interval to check every 5 minutes
    const interval = setInterval(checkAndRefreshToken, 5 * 60 * 1000)

    return () => clearInterval(interval)
  }, [isAuthenticated, user, isTokenExpired, refreshToken, logout])

  const hasRole = (role: 'sysadmin' | 'admin' | 'user'): boolean => {
    return hasPermission(role)
  }

  const hasAnyRole = (roles: ('sysadmin' | 'admin' | 'user')[]): boolean => {
    return roles.some(role => hasPermission(role))
  }

  const canAccess = (resource: string, action: string = 'read'): boolean => {
    if (!isAuthenticated || !user) return false

    // Basic resource-based access control
    const resourcePermissions: Record<string, Record<string, ('sysadmin' | 'admin' | 'user')[]>> = {
      users: {
        read: ['sysadmin', 'admin'],
        create: ['sysadmin', 'admin'],
        update: ['sysadmin', 'admin'],
        delete: ['sysadmin'],
      },
      clients: {
        read: ['sysadmin', 'admin', 'user'],
        create: ['sysadmin', 'admin', 'user'],
        update: ['sysadmin', 'admin', 'user'],
        delete: ['sysadmin', 'admin'],
      },
      reports: {
        read: ['sysadmin', 'admin', 'user'],
        create: ['sysadmin', 'admin'],
        update: ['sysadmin', 'admin'],
        delete: ['sysadmin', 'admin'],
      },
      settings: {
        read: ['sysadmin', 'admin'],
        create: ['sysadmin'],
        update: ['sysadmin'],
        delete: ['sysadmin'],
      },
      audit: {
        read: ['sysadmin'],
        create: [],
        update: [],
        delete: [],
      },
    }

    const allowedRoles = resourcePermissions[resource]?.[action]
    if (!allowedRoles) return false

    return allowedRoles.some(role => hasPermission(role))
  }

  const contextValue: AuthContextValue = {
    user,
    isAuthenticated,
    isLoading,
    hasRole,
    hasAnyRole,
    isAdmin: hasPermission('admin'),
    isSysAdmin: hasPermission('sysadmin'),
    canAccess,
  }

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuthContext(): AuthContextValue {
  const context = useContext(AuthContext)
  
  if (!context) {
    throw new Error('useAuthContext must be used within an AuthProvider')
  }
  
  return context
}

// Component for conditional rendering based on roles
interface RoleGuardProps {
  roles: ('sysadmin' | 'admin' | 'user')[]
  children: ReactNode
  fallback?: ReactNode
  requireAll?: boolean
}

export function RoleGuard({ 
  roles, 
  children, 
  fallback = null,
  requireAll = false 
}: RoleGuardProps) {
  const { hasRole, hasAnyRole } = useAuthContext()

  const hasAccess = requireAll 
    ? roles.every(role => hasRole(role))
    : hasAnyRole(roles)

  return hasAccess ? <>{children}</> : <>{fallback}</>
}

// Component for conditional rendering based on resource access
interface ResourceGuardProps {
  resource: string
  action?: string
  children: ReactNode
  fallback?: ReactNode
}

export function ResourceGuard({ 
  resource, 
  action = 'read', 
  children, 
  fallback = null 
}: ResourceGuardProps) {
  const { canAccess } = useAuthContext()

  return canAccess(resource, action) ? <>{children}</> : <>{fallback}</>
}