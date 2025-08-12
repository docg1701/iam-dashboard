/**
 * HTTP client service with automatic token refresh
 * Handles authentication headers and token rotation
 * Based on Story 1.3 requirements
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { AuthTokens, RefreshTokenResponse } from '@/types/auth'
import { tokenStorage } from '@/utils/tokenStorage'

class HttpClient {
  private client: AxiosInstance
  private isRefreshing = false
  private refreshPromise: Promise<AuthTokens> | null = null
  private readonly baseURL: string

  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true, // Important for httpOnly cookies in production
    })

    this.setupInterceptors()
  }

  private setupInterceptors(): void {
    // Request interceptor to add auth headers
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const tokens = tokenStorage.getTokens()
        
        if (tokens?.access_token) {
          config.headers.Authorization = `Bearer ${tokens.access_token}`
        }

        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor to handle token refresh
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      async (error) => {
        const originalRequest = error.config

        // Check if error is 401 and we haven't already tried to refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            const newTokens = await this.handleTokenRefresh()
            
            // Update the original request with new token
            originalRequest.headers.Authorization = `Bearer ${newTokens.access_token}`
            
            // Retry the original request
            return this.client(originalRequest)
          } catch (refreshError) {
            // Refresh failed, redirect to login
            this.handleAuthFailure()
            return Promise.reject(refreshError)
          }
        }

        return Promise.reject(error)
      }
    )
  }

  private async handleTokenRefresh(): Promise<AuthTokens> {
    // If already refreshing, return the existing promise
    if (this.isRefreshing && this.refreshPromise) {
      return this.refreshPromise
    }

    this.isRefreshing = true

    this.refreshPromise = this.refreshTokens()
      .finally(() => {
        this.isRefreshing = false
        this.refreshPromise = null
      })

    return this.refreshPromise
  }

  private async refreshTokens(): Promise<AuthTokens> {
    const currentTokens = tokenStorage.getTokens()

    if (!currentTokens?.refresh_token) {
      throw new Error('No refresh token available')
    }

    try {
      const response = await axios.post<RefreshTokenResponse>(
        `${this.baseURL}/api/v1/auth/refresh`,
        {
          refresh_token: currentTokens.refresh_token,
        },
        {
          headers: {
            'Content-Type': 'application/json',
          },
          withCredentials: true,
        }
      )

      const newTokens: AuthTokens = {
        access_token: response.data.access_token,
        refresh_token: response.data.refresh_token,
        token_type: response.data.token_type,
        expires_in: response.data.expires_in,
      }

      tokenStorage.setTokens(newTokens)
      return newTokens
    } catch (error) {
      console.error('Token refresh failed:', error)
      tokenStorage.removeTokens()
      throw new Error('Failed to refresh authentication tokens')
    }
  }

  private handleAuthFailure(): void {
    tokenStorage.removeTokens()
    
    // Emit custom event for auth failure
    window.dispatchEvent(new CustomEvent('auth:failure', {
      detail: { reason: 'token_refresh_failed' }
    }))

    // In a real app, you might want to redirect to login
    // But we'll let the auth context handle this
    console.warn('Authentication failed, tokens cleared')
  }

  // Public methods for making HTTP requests
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config)
    return response.data
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config)
    return response.data
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(url, data, config)
    return response.data
  }

  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.patch<T>(url, data, config)
    return response.data
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config)
    return response.data
  }

  // Method to manually refresh tokens (for background refresh)
  async refreshTokensManually(): Promise<void> {
    await this.handleTokenRefresh()
  }

  // Method to check if tokens need refresh
  shouldRefreshTokens(): boolean {
    const tokens = tokenStorage.getTokens()
    
    if (!tokens?.access_token) {
      return false
    }

    return tokenStorage.isTokenExpired(tokens.access_token)
  }

  // Get current auth status
  isAuthenticated(): boolean {
    const tokens = tokenStorage.getTokens()
    return !!(tokens?.access_token && !tokenStorage.isTokenExpired(tokens.access_token))
  }
}

// Create singleton instance
export const httpClient = new HttpClient()

// Export for testing or advanced usage
export { HttpClient }