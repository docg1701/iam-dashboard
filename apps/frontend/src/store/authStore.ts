"use client"

import { create } from "zustand"
import { persist, createJSONStorage } from "zustand/middleware"
import type { AuthState, User, LoginFormData, TwoFactorFormData } from "@/types/auth"

interface AuthActions {
  // Auth actions
  login: (credentials: LoginFormData) => Promise<{ requires_2fa: boolean; temp_token?: string }>
  verify2FA: (data: TwoFactorFormData, tempToken: string) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
  
  // State setters
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  setLoading: (isLoading: boolean) => void
  setRequires2FA: (requires2FA: boolean) => void
  setTempToken: (tempToken: string | null) => void
  
  // Utilities
  clearAuth: () => void
  isTokenExpired: () => boolean
  hasPermission: (requiredRole: 'sysadmin' | 'admin' | 'user') => boolean
}

type AuthStore = AuthState & AuthActions

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Role hierarchy for permission checking
const ROLE_HIERARCHY = {
  sysadmin: 3,
  admin: 2,
  user: 1,
} as const

const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      requires2FA: false,
      tempToken: null,

      // Auth actions
      login: async (credentials: LoginFormData) => {
        set({ isLoading: true })
        
        try {
          const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(credentials),
          })

          if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Login failed')
          }

          const data = await response.json()

          if (data.requires_2fa) {
            set({ 
              requires2FA: true, 
              tempToken: data.session_id,
              isLoading: false 
            })
            return { requires_2fa: true, temp_token: data.session_id }
          } else {
            // Direct login without 2FA
            set({
              user: data.user,
              token: data.access_token,
              isAuthenticated: true,
              isLoading: false,
              requires2FA: false,
              tempToken: null,
            })
            return { requires_2fa: false }
          }
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      verify2FA: async (data: TwoFactorFormData, tempToken: string) => {
        set({ isLoading: true })
        
        try {
          const response = await fetch(`${API_BASE_URL}/api/v1/auth/2fa/verify`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              session_id: tempToken,
              totp_code: data.totp_code,
            }),
          })

          if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || '2FA verification failed')
          }

          const result = await response.json()

          set({
            user: result.user,
            token: result.access_token,
            isAuthenticated: true,
            isLoading: false,
            requires2FA: false,
            tempToken: null,
          })
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      logout: async () => {
        const { token } = get()
        
        if (token) {
          try {
            await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
              },
            })
          } catch (error) {
            console.error('Logout API call failed:', error)
            // Continue with local logout even if API call fails
          }
        }

        // Clear all auth state
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
          requires2FA: false,
          tempToken: null,
        })
      },

      refreshToken: async () => {
        const { token } = get()
        
        if (!token) {
          throw new Error('No token available for refresh')
        }

        try {
          const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          })

          if (!response.ok) {
            throw new Error('Token refresh failed')
          }

          const data = await response.json()

          set({
            token: data.access_token,
            user: data.user,
            isAuthenticated: true,
          })
        } catch (error) {
          // If refresh fails, logout the user
          get().logout()
          throw error
        }
      },

      // State setters
      setUser: (user: User | null) => set({ user, isAuthenticated: !!user }),
      setToken: (token: string | null) => set({ token }),
      setLoading: (isLoading: boolean) => set({ isLoading }),
      setRequires2FA: (requires2FA: boolean) => set({ requires2FA }),
      setTempToken: (tempToken: string | null) => set({ tempToken }),

      // Utilities
      clearAuth: () => set({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        requires2FA: false,
        tempToken: null,
      }),

      isTokenExpired: () => {
        const { token } = get()
        if (!token) return true

        try {
          const payload = JSON.parse(atob(token.split('.')[1]))
          const currentTime = Date.now() / 1000
          return payload.exp < currentTime
        } catch {
          return true
        }
      },

      hasPermission: (requiredRole: 'sysadmin' | 'admin' | 'user') => {
        const { user, isAuthenticated } = get()
        
        if (!isAuthenticated || !user) {
          return false
        }

        const userRoleLevel = ROLE_HIERARCHY[user.role]
        const requiredRoleLevel = ROLE_HIERARCHY[requiredRole]

        return userRoleLevel >= requiredRoleLevel
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

export default useAuthStore