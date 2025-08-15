import { renderHook, act, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import React from 'react'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'
import { ErrorProvider } from '@/components/errors/ErrorContext'

// Mock Next.js navigation
const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: vi.fn(),
  }),
}))

// Test wrapper with both AuthProvider and ErrorProvider
const createWrapper = () => {
  return ({ children }: { children: React.ReactNode }) => (
    <ErrorProvider enableGlobalErrorHandler={false}>
      <AuthProvider>{children}</AuthProvider>
    </ErrorProvider>
  )
}

describe('Enhanced AuthContext with Error Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn()
    localStorage.clear()

    // Mock console methods to reduce test noise
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.spyOn(console, 'warn').mockImplementation(() => {})
    vi.spyOn(console, 'group').mockImplementation(() => {})
    vi.spyOn(console, 'groupEnd').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Enhanced Login with Error Handling', () => {
    it('should handle successful login with proper error clearing', async () => {
      const mockUser = {
        id: '1',
        email: 'user@example.com',
        role: 'user',
        is_active: true,
        has_2fa: false,
      }

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          access_token: 'token',
          refresh_token: 'refresh',
          user: mockUser,
        }),
      })

      const wrapper = createWrapper()
      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        await result.current.login({
          email: 'user@example.com',
          password: 'password',
        })
      })

      expect(result.current.user).toEqual(mockUser)
      expect(result.current.isAuthenticated).toBe(true)
      expect(result.current.error).toBeNull()
      expect(result.current.isLoading).toBe(false)
    })

    it('should handle network errors with proper categorization', async () => {
      // Mock fetch to throw network error
      global.fetch = vi
        .fn()
        .mockRejectedValueOnce(new TypeError('fetch failed'))

      const wrapper = createWrapper()
      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        try {
          await result.current.login({
            email: 'user@example.com',
            password: 'password',
          })
        } catch (error) {
          // Expected to throw
        }
      })

      expect(result.current.error).toBeTruthy()
      expect(result.current.error?.code).toBe('NETWORK_ERROR')
      expect(result.current.error?.retryable).toBe(true)
      expect(result.current.isAuthenticated).toBe(false)
      expect(result.current.isLoading).toBe(false)
    })

    it('should handle authentication errors with proper categorization', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Invalid credentials' }),
      })

      const wrapper = createWrapper()
      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        try {
          await result.current.login({
            email: 'user@example.com',
            password: 'wrongpassword',
          })
        } catch (error) {
          // Expected to throw
        }
      })

      expect(result.current.error).toBeTruthy()
      expect(result.current.error?.code).toBe('INVALID_CREDENTIALS')
      expect(result.current.error?.statusCode).toBe(401)
      expect(result.current.error?.retryable).toBe(false)
      expect(result.current.isAuthenticated).toBe(false)
    })

    it('should handle 2FA required errors properly', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 422,
        json: async () => ({ detail: '2FA code required' }),
      })

      const wrapper = createWrapper()
      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        try {
          await result.current.login({
            email: 'user@example.com',
            password: 'password',
          })
        } catch (error) {
          // Expected to throw
        }
      })

      expect(result.current.error).toBeTruthy()
      expect(result.current.error?.code).toBe('MISSING_2FA')
      expect(result.current.error?.statusCode).toBe(422)
    })

    it('should handle server errors with retry capability', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Internal server error' }),
      })

      const wrapper = createWrapper()
      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        try {
          await result.current.login({
            email: 'user@example.com',
            password: 'password',
          })
        } catch (error) {
          // Expected to throw
        }
      })

      expect(result.current.error).toBeTruthy()
      expect(result.current.error?.statusCode).toBe(500)
      expect(result.current.error?.retryable).toBe(true)
    })

    it('should handle timeout errors with proper classification', async () => {
      // Mock AbortController timeout - simulate the actual AbortError that would be thrown
      const abortError = new DOMException(
        'The operation was aborted',
        'AbortError'
      )
      global.fetch = vi.fn().mockRejectedValueOnce(abortError)

      const wrapper = createWrapper()
      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        try {
          await result.current.login({
            email: 'user@example.com',
            password: 'password',
          })
        } catch (error) {
          // Expected to throw
        }
      })

      await waitFor(() => {
        expect(result.current.error).toBeTruthy()
        expect(result.current.error?.code).toBe('TIMEOUT')
        expect(result.current.error?.retryable).toBe(true)
      })
    })

    it('should validate response structure and handle malformed responses', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          // Missing user.id - this should trigger INVALID_RESPONSE
          access_token: 'token',
          refresh_token: 'refresh',
          user: {
            email: 'user@example.com',
            // Missing required 'id' field
          },
        }),
      })

      const wrapper = createWrapper()
      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        try {
          await result.current.login({
            email: 'user@example.com',
            password: 'password',
          })
        } catch (error) {
          // Expected to throw
        }
      })

      await waitFor(() => {
        expect(result.current.error).toBeTruthy()
        expect(result.current.error?.code).toBe('INVALID_RESPONSE')
        expect(result.current.isAuthenticated).toBe(false)
      })
    })
  })

  describe('Error Management Functions', () => {
    it('should clear errors when clearError is called', async () => {
      global.fetch = vi.fn().mockRejectedValueOnce(new Error('Test error'))

      const wrapper = createWrapper()
      const { result } = renderHook(() => useAuth(), { wrapper })

      // Trigger error
      await act(async () => {
        try {
          await result.current.login({
            email: 'user@example.com',
            password: 'password',
          })
        } catch (error) {
          // Expected
        }
      })

      expect(result.current.error).toBeTruthy()

      // Clear error
      act(() => {
        result.current.clearError()
      })

      expect(result.current.error).toBeNull()
    })

    it('should retry failed actions when retry is called', async () => {
      let callCount = 0
      global.fetch = vi.fn().mockImplementation(() => {
        callCount++
        if (callCount === 1) {
          return Promise.reject(new Error('Network error'))
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({
            access_token: 'token',
            refresh_token: 'refresh',
            user: {
              id: '1',
              email: 'user@example.com',
              role: 'user',
              is_active: true,
              has_2fa: false,
            },
          }),
        })
      })

      const wrapper = createWrapper()
      const { result } = renderHook(() => useAuth(), { wrapper })

      // First attempt - should fail
      await act(async () => {
        try {
          await result.current.login({
            email: 'user@example.com',
            password: 'password',
          })
        } catch (error) {
          // Expected
        }
      })

      expect(result.current.error).toBeTruthy()
      expect(result.current.isAuthenticated).toBe(false)

      // Retry - should succeed
      await act(async () => {
        await result.current.retry()
      })

      expect(result.current.error).toBeNull()
      expect(result.current.isAuthenticated).toBe(true)
      expect(callCount).toBe(2)
    })
  })

  describe('Enhanced 2FA Operations with Error Handling', () => {
    it('should handle 2FA setup errors properly', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Server error during 2FA setup' }),
      })

      const wrapper = createWrapper()
      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        try {
          await result.current.setup2FA()
        } catch (error) {
          expect((error as Error).message).toContain('Falha ao configurar 2FA')
        }
      })
    })

    it('should handle 2FA enable errors with proper error context', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Invalid TOTP code' }),
      })

      const wrapper = createWrapper()
      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        try {
          await result.current.enable2FA('123456')
        } catch (error) {
          expect((error as Error).message).toBe('Invalid TOTP code')
        }
      })
    })
  })

  describe('Error Context Integration', () => {
    it('should integrate with global error context for error reporting', async () => {
      global.fetch = vi.fn().mockRejectedValueOnce(new Error('Network failure'))

      const wrapper = createWrapper()
      const { result } = renderHook(() => useAuth(), { wrapper })

      await act(async () => {
        try {
          await result.current.login({
            email: 'user@example.com',
            password: 'password',
          })
        } catch (error) {
          // Expected
        }
      })

      // Error should be captured both locally and in global context
      expect(result.current.error).toBeTruthy()
    })
  })

  describe('Loading States and Error States', () => {
    it('should manage loading states correctly during error scenarios', async () => {
      let resolvePromise: (value: Response | PromiseLike<Response>) => void
      const delayedPromise = new Promise(resolve => {
        resolvePromise = resolve
      })

      global.fetch = vi.fn().mockReturnValueOnce(delayedPromise)

      const wrapper = createWrapper()
      const { result } = renderHook(() => useAuth(), { wrapper })

      // Start login - should be loading
      act(() => {
        // Start login but don't await it - let it run in background
        result.current.login({
          email: 'user@example.com',
          password: 'password',
        })
      })

      // Wait for loading state to be set
      await waitFor(() => {
        expect(result.current.isLoading).toBe(true)
      })

      expect(result.current.error).toBeNull()

      // Resolve with error
      await act(async () => {
        resolvePromise!(
          new Response(JSON.stringify({ detail: 'Invalid credentials' }), {
            status: 401,
            statusText: 'Unauthorized',
          })
        )
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
        expect(result.current.error).toBeTruthy()
      })
    })
  })
})
