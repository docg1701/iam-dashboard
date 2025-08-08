"use client"

import { create } from "zustand"
import { persist, createJSONStorage } from "zustand/middleware"
import type { AuthState, User, LoginFormData, TwoFactorFormData } from "@/types/auth"
import * as authAPI from "@/lib/api/auth"

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
          const data = await authAPI.login(credentials)

          if (data.requires_2fa) {
            set({ 
              requires2FA: true, 
              tempToken: data.temp_token,
              isLoading: false 
            })
            return { requires_2fa: true, temp_token: data.temp_token }
          } else {
            // Direct login without 2FA - transform API response to match User interface
            const user: User | null = data.user ? {
              user_id: data.user.user_id,
              email: data.user.email,
              role: data.user.role,
              is_active: true, // Default to active if login succeeds
              totp_enabled: false, // Since we didn't require 2FA
              created_at: new Date().toISOString(), // Default values
              updated_at: new Date().toISOString(),
              full_name: data.user.full_name, // Add missing full_name
            } : null
            
            set({
              user,
              token: data.access_token,
              isAuthenticated: !!user && !!data.access_token,
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
          const result = await authAPI.verify2FA({
            temp_token: tempToken,
            totp_code: data.totp_code,
          })

          // Transform API response to match User interface
          const user: User = {
            user_id: result.user.user_id,
            email: result.user.email,
            role: result.user.role,
            is_active: true, // Default to active if 2FA succeeds
            totp_enabled: true, // User has 2FA enabled since they just verified
            created_at: new Date().toISOString(), // Default values
            updated_at: new Date().toISOString(),
            full_name: result.user.full_name,
          }

          set({
            user,
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
            await authAPI.logout()
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
          const data = await authAPI.refreshToken(token)

          set({
            token: data.access_token,
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