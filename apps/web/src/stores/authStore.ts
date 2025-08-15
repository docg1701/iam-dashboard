import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: string
  email: string
  role: 'sysadmin' | 'admin' | 'user'
  is_active: boolean
  has_2fa: boolean
}

interface Permissions {
  [agentName: string]: {
    create: boolean
    read: boolean
    update: boolean
    delete: boolean
  }
}

interface AuthState {
  // Estado
  user: User | null
  permissions: Permissions
  isAuthenticated: boolean
  isLoading: boolean

  // Tokens (apenas para desenvolvimento)
  accessToken: string | null
  refreshToken: string | null

  // Ações
  setUser: (user: User | null) => void
  setPermissions: (permissions: Permissions) => void
  setTokens: (accessToken: string | null, refreshToken: string | null) => void
  setLoading: (loading: boolean) => void
  clearAuth: () => void

  // Utilitários de permissão
  hasPermission: (
    agentName: string,
    action: 'create' | 'read' | 'update' | 'delete'
  ) => boolean
  hasRole: (requiredRole: 'sysadmin' | 'admin' | 'user') => boolean
  isAdmin: () => boolean
  isSysAdmin: () => boolean
}

const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Estado inicial
      user: null,
      permissions: {},
      isAuthenticated: false,
      isLoading: false,
      accessToken: null,
      refreshToken: null,

      // Ações
      setUser: user =>
        set({
          user,
          isAuthenticated: !!user,
        }),

      setPermissions: permissions => set({ permissions }),

      setTokens: (accessToken, refreshToken) =>
        set({
          accessToken,
          refreshToken,
        }),

      setLoading: isLoading => set({ isLoading }),

      clearAuth: () =>
        set({
          user: null,
          permissions: {},
          isAuthenticated: false,
          accessToken: null,
          refreshToken: null,
          isLoading: false,
        }),

      // Utilitários de permissão
      hasPermission: (agentName, action) => {
        const { permissions } = get()
        const agentPermissions = permissions[agentName]
        return agentPermissions ? agentPermissions[action] : false
      },

      hasRole: requiredRole => {
        const { user } = get()
        if (!user) {
          return false
        }

        const roleHierarchy = {
          user: 1,
          admin: 2,
          sysadmin: 3,
        }

        return roleHierarchy[user.role] >= roleHierarchy[requiredRole]
      },

      isAdmin: () => {
        const { hasRole } = get()
        return hasRole('admin')
      },

      isSysAdmin: () => {
        const { hasRole } = get()
        return hasRole('sysadmin')
      },
    }),
    {
      name: 'auth-storage',
      // Apenas persistir dados não sensíveis
      partialize: state => ({
        user: state.user,
        permissions: state.permissions,
        isAuthenticated: state.isAuthenticated,
        // Tokens são persistidos apenas em desenvolvimento
        ...(process.env.NODE_ENV === 'development' && {
          accessToken: state.accessToken,
          refreshToken: state.refreshToken,
        }),
      }),
    }
  )
)

export default useAuthStore
