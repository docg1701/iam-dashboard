/**
 * Tests for API client.
 * 
 * This module tests the API client functionality including
 * HTTP methods, authentication, and error handling.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { ApiClient } from '@/lib/api'

// Mock fetch globally  
global.fetch = vi.fn() as unknown as typeof fetch

describe('ApiClient', () => {
  let apiClient: ApiClient

  beforeEach(() => {
    apiClient = new ApiClient()
    vi.clearAllMocks()
  })

  describe('GET requests', () => {
    it('should make GET request with correct parameters', async () => {
      const mockResponse = { data: 'test' }
      
      ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })

      const result = await apiClient.get('/test')

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should handle GET request errors', async () => {
      ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
      })

      await expect(apiClient.get('/nonexistent')).rejects.toThrow(
        'API Error: 404 Not Found'
      )
    })
  })

  describe('POST requests', () => {
    it('should make POST request with body', async () => {
      const requestData = { name: 'test' }
      const mockResponse = { id: 1, ...requestData }
      
      ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })

      const result = await apiClient.post('/test', requestData)

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify(requestData),
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should make POST request without body', async () => {
      const mockResponse = { success: true }
      
      ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })

      const result = await apiClient.post('/test')

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          method: 'POST',
          body: undefined,
        })
      )
      expect(result).toEqual(mockResponse)
    })
  })

  describe('Authentication', () => {
    it('should set authorization header', () => {
      const token = 'test-token'
      apiClient.setAuthToken(token)

      // Access private property for testing
      const headers = (apiClient as unknown as { defaultHeaders: Record<string, string> }).defaultHeaders
      expect(headers['Authorization']).toBe(`Bearer ${token}`)
    })

    it('should remove authorization header', () => {
      apiClient.setAuthToken('test-token')
      apiClient.removeAuthToken()

      const headers = (apiClient as unknown as { defaultHeaders: Record<string, string> }).defaultHeaders
      expect(headers['Authorization']).toBeUndefined()
    })

    it('should include auth token in requests', async () => {
      const token = 'test-token'
      apiClient.setAuthToken(token)

      ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      })

      await apiClient.get('/protected')

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/protected',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': `Bearer ${token}`,
          }),
        })
      )
    })
  })

  describe('PUT and DELETE requests', () => {
    it('should make PUT request', async () => {
      const requestData = { name: 'updated' }
      const mockResponse = { success: true }
      
      ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })

      const result = await apiClient.put('/test/1', requestData)

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test/1',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(requestData),
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should make DELETE request', async () => {
      const mockResponse = { deleted: true }
      
      ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })

      const result = await apiClient.delete('/test/1')

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/test/1',
        expect.objectContaining({
          method: 'DELETE',
        })
      )
      expect(result).toEqual(mockResponse)
    })
  })
})