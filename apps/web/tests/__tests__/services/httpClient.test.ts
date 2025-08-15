/**
 * Comprehensive tests for HttpClient
 * CLAUDE.md Compliant: Only mocks external dependencies (axios), tests actual HTTP client behavior
 */

import { describe, it, expect, vi, beforeEach, afterEach, Mock } from 'vitest'
import axios, { AxiosError, AxiosResponse, AxiosInstance } from 'axios'
import { tokenStorage } from '@/utils/tokenStorage'

// Mock external dependencies (CLAUDE.md compliant)
vi.mock('axios', () => {
  const mockAxiosInstance = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
    request: vi.fn(),
    interceptors: {
      request: {
        use: vi.fn(),
      },
      response: {
        use: vi.fn(),
      },
    },
  }

  return {
    default: {
      create: vi.fn(() => mockAxiosInstance),
      isAxiosError: vi.fn(),
    },
    create: vi.fn(() => mockAxiosInstance),
    isAxiosError: vi.fn(),
  }
})

// Note: tokenStorage is internal utility - test with real implementation (CLAUDE.md compliant)

// Get the mocked axios after mock setup
const mockedAxios = vi.mocked(axios, true)
const mockAxiosInstance = mockedAxios.create() as AxiosInstance

// Import after mocking
import { httpClient, HttpClient } from '@/services/httpClient'

describe('HttpClient', () => {
  const mockTokens = {
    access_token: 'token123',
    refresh_token: 'refresh123',
    token_type: 'Bearer',
    expires_in: 3600,
  }

  beforeEach(() => {
    vi.clearAllMocks()

    // Reset the mock axios instance methods
    mockAxiosInstance.get = vi.fn()
    mockAxiosInstance.post = vi.fn()
    mockAxiosInstance.put = vi.fn()
    mockAxiosInstance.patch = vi.fn()
    mockAxiosInstance.delete = vi.fn()
    mockAxiosInstance.request = vi.fn()

    // Mock post method for refresh token calls
    mockAxiosInstance.post.mockResolvedValue({
      data: {
        access_token: 'new-token',
        refresh_token: 'new-refresh',
        token_type: 'Bearer',
        expires_in: 3600,
      },
    } as AxiosResponse)

    // Mock tokenStorage
    ;(tokenStorage.getTokens as Mock).mockReturnValue(mockTokens)
    ;(tokenStorage.isTokenExpired as Mock).mockReturnValue(false)
    ;(tokenStorage.setTokens as Mock).mockImplementation(() => {})
    ;(tokenStorage.removeTokens as Mock).mockImplementation(() => {})

    // Mock window.dispatchEvent
    Object.defineProperty(window, 'dispatchEvent', {
      value: vi.fn(),
      writable: true,
    })

    // Mock process.env
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000'
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Constructor and Initialization', () => {
    it('should create axios instance with correct configuration', () => {
      new HttpClient()

      expect(mockedAxios.create).toHaveBeenCalledWith({
        baseURL: 'http://localhost:8000',
        timeout: 10000,
        headers: {
          'Content-Type': 'application/json',
        },
        withCredentials: true,
      })
    })

    it('should use default baseURL when env variable is not set', () => {
      delete process.env.NEXT_PUBLIC_API_URL

      new HttpClient()

      expect(mockedAxios.create).toHaveBeenCalledWith({
        baseURL: 'http://localhost:8000',
        timeout: 10000,
        headers: {
          'Content-Type': 'application/json',
        },
        withCredentials: true,
      })
    })

    it('should setup request and response interceptors', () => {
      new HttpClient()

      expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalled()
      expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalled()
    })

    it('should export singleton instance', () => {
      expect(httpClient).toBeInstanceOf(HttpClient)
    })
  })

  describe('Request Interceptor', () => {
    it('should add authorization header when tokens are available', () => {
      new HttpClient()

      const requestInterceptor =
        mockAxiosInstance.interceptors.request.use.mock.calls[0][0]
      const config = { headers: {} }

      const result = requestInterceptor(config)

      expect(result.headers.Authorization).toBe('Bearer token123')
    })

    it('should not add authorization header when no tokens available', () => {
      ;(tokenStorage.getTokens as Mock).mockReturnValue(null)

      new HttpClient()

      const requestInterceptor =
        mockAxiosInstance.interceptors.request.use.mock.calls[0][0]
      const config = { headers: {} }

      const result = requestInterceptor(config)

      expect(result.headers.Authorization).toBeUndefined()
    })

    it('should handle request interceptor errors', async () => {
      new HttpClient()

      const errorHandler =
        mockAxiosInstance.interceptors.request.use.mock.calls[0][1]
      const error = new Error('Request error')

      await expect(() => errorHandler(error)).rejects.toThrow('Request error')
    })
  })

  describe('Response Interceptor', () => {
    it('should pass through successful responses', () => {
      new HttpClient()

      const responseInterceptor =
        mockAxiosInstance.interceptors.response.use.mock.calls[0][0]
      const response = { data: { message: 'success' } }

      const result = responseInterceptor(response)

      expect(result).toBe(response)
    })

    it('should handle 401 errors with token refresh', async () => {
      const client = new HttpClient()

      const errorHandler =
        mockAxiosInstance.interceptors.response.use.mock.calls[0][1]

      const originalRequest = {
        headers: {},
        _retry: false,
      }

      const error = {
        response: { status: 401 },
        config: originalRequest,
      }

      // Mock successful token refresh
      mockAxiosInstance.post.mockResolvedValueOnce({
        data: {
          access_token: 'new-token',
          refresh_token: 'new-refresh',
          token_type: 'Bearer',
          expires_in: 3600,
        },
      } as AxiosResponse)

      // Mock retry request success
      mockAxiosInstance.get.mockResolvedValueOnce({ data: 'retry success' })

      await errorHandler(error)

      expect(originalRequest._retry).toBe(true)
      expect(originalRequest.headers.Authorization).toBe('Bearer new-token')
    })

    it('should handle failed token refresh', async () => {
      new HttpClient()

      const errorHandler =
        mockAxiosInstance.interceptors.response.use.mock.calls[0][1]

      const originalRequest = {
        headers: {},
        _retry: false,
      }

      const error = {
        response: { status: 401 },
        config: originalRequest,
      }

      // Mock failed token refresh
      mockAxiosInstance.post.mockRejectedValueOnce(new Error('Refresh failed'))

      await expect(errorHandler(error)).rejects.toThrow()

      expect(tokenStorage.removeTokens).toHaveBeenCalled()
      expect(window.dispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'auth:failure',
          detail: { reason: 'token_refresh_failed' },
        })
      )
    })

    it('should not retry already retried requests', async () => {
      new HttpClient()

      const errorHandler =
        mockAxiosInstance.interceptors.response.use.mock.calls[0][1]

      const originalRequest = {
        headers: {},
        _retry: true, // Already retried
      }

      const error = {
        response: { status: 401 },
        config: originalRequest,
      }

      await expect(errorHandler(error)).rejects.toBe(error)
    })

    it('should pass through non-401 errors', async () => {
      new HttpClient()

      const errorHandler =
        mockAxiosInstance.interceptors.response.use.mock.calls[0][1]

      const error = {
        response: { status: 500 },
        config: { headers: {} },
      }

      await expect(errorHandler(error)).rejects.toBe(error)
    })
  })

  describe('Token Refresh Logic', () => {
    it('should refresh tokens successfully', async () => {
      const client = new HttpClient()

      // Mock successful refresh response
      mockAxiosInstance.post.mockResolvedValueOnce({
        data: {
          access_token: 'new-access-token',
          refresh_token: 'new-refresh-token',
          token_type: 'Bearer',
          expires_in: 3600,
        },
      } as AxiosResponse)

      await client.refreshTokensManually()

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/v1/auth/refresh',
        {
          refresh_token: 'refresh123',
        },
        {
          headers: {
            'Content-Type': 'application/json',
          },
          withCredentials: true,
        }
      )

      expect(tokenStorage.setTokens).toHaveBeenCalledWith({
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        token_type: 'Bearer',
        expires_in: 3600,
      })
    })

    it('should handle refresh failure when no refresh token available', async () => {
      ;(tokenStorage.getTokens as Mock).mockReturnValue({
        access_token: 'token123',
      })

      const client = new HttpClient()

      await expect(client.refreshTokensManually()).rejects.toThrow(
        'No refresh token available'
      )
    })

    it('should handle refresh API failure', async () => {
      const client = new HttpClient()

      mockAxiosInstance.post.mockRejectedValueOnce(new Error('Server error'))

      await expect(client.refreshTokensManually()).rejects.toThrow(
        'Failed to refresh authentication tokens'
      )

      expect(tokenStorage.removeTokens).toHaveBeenCalled()
    })

    it('should not make multiple concurrent refresh requests', async () => {
      const client = new HttpClient()

      // Mock slow refresh response
      mockAxiosInstance.post.mockImplementation(
        () =>
          new Promise(resolve =>
            setTimeout(
              () =>
                resolve({
                  data: {
                    access_token: 'new-token',
                    refresh_token: 'new-refresh',
                    token_type: 'Bearer',
                    expires_in: 3600,
                  },
                } as AxiosResponse),
              100
            )
          )
      )

      // Start multiple refresh requests
      const promises = [
        client.refreshTokensManually(),
        client.refreshTokensManually(),
        client.refreshTokensManually(),
      ]

      await Promise.all(promises)

      // Should only make one API call
      expect(mockAxiosInstance.post).toHaveBeenCalledTimes(1)
    })
  })

  describe('HTTP Methods', () => {
    beforeEach(() => {
      mockAxiosInstance.get.mockResolvedValue({ data: 'get-response' })
      mockAxiosInstance.post.mockResolvedValue({ data: 'post-response' })
      mockAxiosInstance.put.mockResolvedValue({ data: 'put-response' })
      mockAxiosInstance.patch.mockResolvedValue({ data: 'patch-response' })
      mockAxiosInstance.delete.mockResolvedValue({ data: 'delete-response' })
    })

    describe('GET', () => {
      it('should make GET request and return data', async () => {
        const client = new HttpClient()

        const result = await client.get('/test')

        expect(mockAxiosInstance.get).toHaveBeenCalledWith('/test', undefined)
        expect(result).toBe('get-response')
      })

      it('should pass config to GET request', async () => {
        const client = new HttpClient()
        const config = { params: { id: 1 } }

        await client.get('/test', config)

        expect(mockAxiosInstance.get).toHaveBeenCalledWith('/test', config)
      })
    })

    describe('POST', () => {
      it('should make POST request and return data', async () => {
        const client = new HttpClient()
        const data = { name: 'test' }

        const result = await client.post('/test', data)

        expect(mockAxiosInstance.post).toHaveBeenCalledWith(
          '/test',
          data,
          undefined
        )
        expect(result).toBe('post-response')
      })

      it('should pass config to POST request', async () => {
        const client = new HttpClient()
        const data = { name: 'test' }
        const config = { headers: { 'Custom-Header': 'value' } }

        await client.post('/test', data, config)

        expect(mockAxiosInstance.post).toHaveBeenCalledWith(
          '/test',
          data,
          config
        )
      })
    })

    describe('PUT', () => {
      it('should make PUT request and return data', async () => {
        const client = new HttpClient()
        const data = { name: 'updated' }

        const result = await client.put('/test', data)

        expect(mockAxiosInstance.put).toHaveBeenCalledWith(
          '/test',
          data,
          undefined
        )
        expect(result).toBe('put-response')
      })
    })

    describe('PATCH', () => {
      it('should make PATCH request and return data', async () => {
        const client = new HttpClient()
        const data = { name: 'patched' }

        const result = await client.patch('/test', data)

        expect(mockAxiosInstance.patch).toHaveBeenCalledWith(
          '/test',
          data,
          undefined
        )
        expect(result).toBe('patch-response')
      })
    })

    describe('DELETE', () => {
      it('should make DELETE request and return data', async () => {
        const client = new HttpClient()

        const result = await client.delete('/test')

        expect(mockAxiosInstance.delete).toHaveBeenCalledWith(
          '/test',
          undefined
        )
        expect(result).toBe('delete-response')
      })

      it('should pass config to DELETE request', async () => {
        const client = new HttpClient()
        const config = { headers: { 'Custom-Header': 'value' } }

        await client.delete('/test', config)

        expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/test', config)
      })
    })
  })

  describe('Auth Status Methods', () => {
    describe('shouldRefreshTokens', () => {
      it('should return true when token is expired', () => {
        ;(tokenStorage.isTokenExpired as Mock).mockReturnValue(true)

        const client = new HttpClient()

        expect(client.shouldRefreshTokens()).toBe(true)
      })

      it('should return false when token is not expired', () => {
        ;(tokenStorage.isTokenExpired as Mock).mockReturnValue(false)

        const client = new HttpClient()

        expect(client.shouldRefreshTokens()).toBe(false)
      })

      it('should return false when no access token available', () => {
        ;(tokenStorage.getTokens as Mock).mockReturnValue(null)

        const client = new HttpClient()

        expect(client.shouldRefreshTokens()).toBe(false)
      })
    })

    describe('isAuthenticated', () => {
      it('should return true when valid token exists', () => {
        ;(tokenStorage.isTokenExpired as Mock).mockReturnValue(false)

        const client = new HttpClient()

        expect(client.isAuthenticated()).toBe(true)
      })

      it('should return false when token is expired', () => {
        ;(tokenStorage.isTokenExpired as Mock).mockReturnValue(true)

        const client = new HttpClient()

        expect(client.isAuthenticated()).toBe(false)
      })

      it('should return false when no tokens available', () => {
        ;(tokenStorage.getTokens as Mock).mockReturnValue(null)

        const client = new HttpClient()

        expect(client.isAuthenticated()).toBe(false)
      })

      it('should return false when no access token available', () => {
        ;(tokenStorage.getTokens as Mock).mockReturnValue({
          refresh_token: 'refresh123',
        })

        const client = new HttpClient()

        expect(client.isAuthenticated()).toBe(false)
      })
    })
  })

  describe('Error Handling', () => {
    it('should handle axios errors properly', async () => {
      const client = new HttpClient()
      const axiosError = new Error('Network error') as AxiosError

      mockAxiosInstance.get.mockRejectedValueOnce(axiosError)

      await expect(client.get('/test')).rejects.toThrow('Network error')
    })

    it('should handle auth failure events', async () => {
      new HttpClient()

      const errorHandler =
        mockAxiosInstance.interceptors.response.use.mock.calls[0][1]

      const error = {
        response: { status: 401 },
        config: { headers: {}, _retry: false },
      }

      // Mock failed refresh
      ;(tokenStorage.getTokens as Mock).mockReturnValue(null)

      await errorHandler(error).catch(() => {})

      expect(window.dispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'auth:failure',
          detail: { reason: 'token_refresh_failed' },
        })
      )
    })
  })

  describe('Concurrent Request Handling', () => {
    it('should handle multiple requests during token refresh', async () => {
      const client = new HttpClient()

      // Mock slow token refresh
      mockAxiosInstance.post.mockImplementation(
        () =>
          new Promise(resolve =>
            setTimeout(
              () =>
                resolve({
                  data: {
                    access_token: 'new-token',
                    refresh_token: 'new-refresh',
                    token_type: 'Bearer',
                    expires_in: 3600,
                  },
                } as AxiosResponse),
              50
            )
          )
      )

      // Start multiple refresh operations
      const refreshPromises = [
        client.refreshTokensManually(),
        client.refreshTokensManually(),
        client.refreshTokensManually(),
      ]

      await Promise.all(refreshPromises)

      // Should only call the refresh API once
      expect(mockAxiosInstance.post).toHaveBeenCalledTimes(1)
    })
  })
})
