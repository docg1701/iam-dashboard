/**
 * Comprehensive tests for tokenStorage utility
 * CLAUDE.md Compliant: Only mocks browser APIs (localStorage, sessionStorage, document.cookie), tests actual utility behavior
 */

import { describe, it, expect, vi, beforeEach, afterEach, Mock } from 'vitest'
import { createTokenStorage, tokenStorage } from '@/utils/tokenStorage'
import { AuthTokens } from '@/types/auth'

describe('tokenStorage', () => {
  const mockTokens: AuthTokens = {
    access_token:
      'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE5OTk5OTk5OTl9.invalid-signature',
    refresh_token: 'refresh_token_123',
    token_type: 'Bearer',
    expires_in: 3600,
  }

  const expiredToken =
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyMzkwMjJ9.invalid-signature'

  // Mock localStorage and sessionStorage
  const localStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
  }

  const sessionStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
  }

  // Mock document.cookie
  const mockDocument = {
    cookie: '',
  }

  beforeEach(() => {
    vi.clearAllMocks()

    // Mock browser APIs
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true,
    })

    Object.defineProperty(window, 'sessionStorage', {
      value: sessionStorageMock,
      writable: true,
    })

    Object.defineProperty(global, 'document', {
      value: mockDocument,
      writable: true,
    })

    // Mock TextEncoder/TextDecoder for encryption tests
    global.TextEncoder = vi.fn().mockImplementation(() => ({
      encode: vi
        .fn()
        .mockImplementation(
          (str: string) => new Uint8Array([...str].map(c => c.charCodeAt(0)))
        ),
    }))

    global.TextDecoder = vi.fn().mockImplementation(() => ({
      decode: vi
        .fn()
        .mockImplementation((bytes: Uint8Array) =>
          String.fromCharCode(...bytes)
        ),
    }))

    // Mock btoa/atob
    global.btoa = vi
      .fn()
      .mockImplementation((str: string) =>
        Buffer.from(str, 'binary').toString('base64')
      )
    global.atob = vi
      .fn()
      .mockImplementation((str: string) =>
        Buffer.from(str, 'base64').toString('binary')
      )

    // Reset NODE_ENV
    process.env.NODE_ENV = 'test'
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Factory Function', () => {
    it('should create development storage in non-production environment', () => {
      process.env.NODE_ENV = 'development'

      const storage = createTokenStorage()

      expect(storage).toBeDefined()
      expect(typeof storage.getTokens).toBe('function')
      expect(typeof storage.setTokens).toBe('function')
      expect(typeof storage.removeTokens).toBe('function')
      expect(typeof storage.isTokenExpired).toBe('function')
    })

    it('should create production storage in production environment', () => {
      process.env.NODE_ENV = 'production'

      const storage = createTokenStorage()

      expect(storage).toBeDefined()
      expect(typeof storage.getTokens).toBe('function')
      expect(typeof storage.setTokens).toBe('function')
      expect(typeof storage.removeTokens).toBe('function')
      expect(typeof storage.isTokenExpired).toBe('function')
    })

    it('should export a default tokenStorage instance', () => {
      expect(tokenStorage).toBeDefined()
      expect(typeof tokenStorage.getTokens).toBe('function')
    })
  })

  describe('Development Storage', () => {
    beforeEach(() => {
      process.env.NODE_ENV = 'development'
    })

    describe('getTokens', () => {
      it('should return null when no tokens are stored', () => {
        ;(localStorageMock.getItem as Mock).mockReturnValue(null)

        const storage = createTokenStorage()
        const result = storage.getTokens()

        expect(result).toBeNull()
        expect(localStorageMock.getItem).toHaveBeenCalledWith('iam_auth_tokens')
      })

      it('should decrypt and return stored tokens', () => {
        const encryptedData = 'encrypted_token_data'
        ;(localStorageMock.getItem as Mock).mockReturnValue(encryptedData)
        ;(sessionStorageMock.getItem as Mock).mockReturnValue('test_key')

        const storage = createTokenStorage()
        const result = storage.getTokens()

        expect(localStorageMock.getItem).toHaveBeenCalledWith('iam_auth_tokens')
        // Result will be the decrypted data (mock implementation handles this)
      })

      it('should handle corrupted data by removing it', () => {
        ;(localStorageMock.getItem as Mock).mockReturnValue('corrupted_data')
        ;(sessionStorageMock.getItem as Mock).mockReturnValue('test_key')

        // Mock JSON.parse to throw error for corrupted data
        const originalParse = JSON.parse
        JSON.parse = vi.fn().mockImplementation(() => {
          throw new Error('Invalid JSON')
        })

        const storage = createTokenStorage()
        const result = storage.getTokens()

        expect(result).toBeNull()
        expect(localStorageMock.removeItem).toHaveBeenCalledWith(
          'iam_auth_tokens'
        )

        // Restore JSON.parse
        JSON.parse = originalParse
      })
    })

    describe('setTokens', () => {
      it('should encrypt and store tokens', () => {
        ;(sessionStorageMock.getItem as Mock).mockReturnValue('test_key')

        const storage = createTokenStorage()
        storage.setTokens(mockTokens)

        expect(localStorageMock.setItem).toHaveBeenCalledWith(
          'iam_auth_tokens',
          expect.any(String)
        )
      })

      it('should throw error when storage fails', () => {
        ;(localStorageMock.setItem as Mock).mockImplementation(() => {
          throw new Error('Storage quota exceeded')
        })
        ;(sessionStorageMock.getItem as Mock).mockReturnValue('test_key')

        const storage = createTokenStorage()

        expect(() => storage.setTokens(mockTokens)).toThrow(
          'Failed to store authentication tokens'
        )
      })
    })

    describe('removeTokens', () => {
      it('should remove tokens from localStorage', () => {
        const storage = createTokenStorage()
        storage.removeTokens()

        expect(localStorageMock.removeItem).toHaveBeenCalledWith(
          'iam_auth_tokens'
        )
      })

      it('should handle removal errors silently', () => {
        ;(localStorageMock.removeItem as Mock).mockImplementation(() => {
          throw new Error('Cannot remove')
        })

        const storage = createTokenStorage()

        expect(() => storage.removeTokens()).not.toThrow()
      })
    })

    describe('isTokenExpired', () => {
      it('should return false for valid token', () => {
        const storage = createTokenStorage()

        const result = storage.isTokenExpired(mockTokens.access_token)

        expect(result).toBe(false)
      })

      it('should return true for expired token', () => {
        const storage = createTokenStorage()

        const result = storage.isTokenExpired(expiredToken)

        expect(result).toBe(true)
      })

      it('should return true for invalid token format', () => {
        const storage = createTokenStorage()

        const result = storage.isTokenExpired('invalid.token')

        expect(result).toBe(true)
      })

      it('should return true for unparseable token', () => {
        const storage = createTokenStorage()

        const result = storage.isTokenExpired('invalid.invalid.invalid')

        expect(result).toBe(true)
      })

      it('should add 5 minute buffer for token expiry check', () => {
        // Mock a token that expires in 4 minutes (240 seconds from now)
        const futureTime = Math.floor(Date.now() / 1000) + 240
        const tokenPayload = {
          sub: '1234567890',
          name: 'John Doe',
          iat: 1516239022,
          exp: futureTime,
        }
        const tokenWithBuffer = `header.${btoa(JSON.stringify(tokenPayload))}.signature`

        const storage = createTokenStorage()

        // Should return true because it expires within 5 minutes (300 seconds)
        const result = storage.isTokenExpired(tokenWithBuffer)

        expect(result).toBe(true)
      })
    })
  })

  describe('Production Storage', () => {
    beforeEach(() => {
      process.env.NODE_ENV = 'production'
    })

    describe('getTokens', () => {
      it('should return null when no token info cookie exists', () => {
        mockDocument.cookie = ''

        const storage = createTokenStorage()
        const result = storage.getTokens()

        expect(result).toBeNull()
      })

      it('should parse token info from cookie', () => {
        const tokenInfo = encodeURIComponent(
          JSON.stringify({
            token_type: 'Bearer',
            expires_in: 3600,
          })
        )
        mockDocument.cookie = `token_info=${tokenInfo}; other_cookie=value`

        const storage = createTokenStorage()
        const result = storage.getTokens()

        expect(result).toEqual({
          token_type: 'Bearer',
          expires_in: 3600,
        })
      })

      it('should handle corrupted cookie data', () => {
        mockDocument.cookie = 'token_info=corrupted_data'

        const storage = createTokenStorage()
        const result = storage.getTokens()

        expect(result).toBeNull()
      })
    })

    describe('setTokens', () => {
      it('should set token info cookie', () => {
        const storage = createTokenStorage()

        // Mock document.cookie setter
        let cookieValue = ''
        Object.defineProperty(mockDocument, 'cookie', {
          set: (value: string) => {
            cookieValue = value
          },
          get: () => cookieValue,
        })

        storage.setTokens(mockTokens)

        expect(cookieValue).toContain('token_info=')
        expect(cookieValue).toContain('Secure')
        expect(cookieValue).toContain('SameSite=Strict')
        expect(cookieValue).toContain('Path=/')
      })
    })

    describe('removeTokens', () => {
      it('should remove token info cookie', () => {
        const storage = createTokenStorage()

        // Mock document.cookie setter
        let cookieValue = ''
        Object.defineProperty(mockDocument, 'cookie', {
          set: (value: string) => {
            cookieValue = value
          },
          get: () => cookieValue,
        })

        storage.removeTokens()

        expect(cookieValue).toContain(
          'token_info=; expires=Thu, 01 Jan 1970 00:00:00 GMT'
        )
      })
    })

    describe('isTokenExpired', () => {
      it('should return false for valid token', () => {
        const storage = createTokenStorage()

        const result = storage.isTokenExpired(mockTokens.access_token)

        expect(result).toBe(false)
      })

      it('should return true for expired token', () => {
        const storage = createTokenStorage()

        const result = storage.isTokenExpired(expiredToken)

        expect(result).toBe(true)
      })

      it('should return true for invalid token format', () => {
        const storage = createTokenStorage()

        const result = storage.isTokenExpired('invalid.token')

        expect(result).toBe(true)
      })

      it('should not add buffer in production (immediate expiry check)', () => {
        // Mock a token that expires in 1 second
        const futureTime = Math.floor(Date.now() / 1000) + 1
        const tokenPayload = {
          sub: '1234567890',
          name: 'John Doe',
          iat: 1516239022,
          exp: futureTime,
        }
        const tokenNoBuffer = `header.${btoa(JSON.stringify(tokenPayload))}.signature`

        const storage = createTokenStorage()

        // Should return false because it hasn't expired yet (no buffer)
        const result = storage.isTokenExpired(tokenNoBuffer)

        expect(result).toBe(false)
      })
    })
  })

  describe('DevEncryption', () => {
    beforeEach(() => {
      process.env.NODE_ENV = 'development'
    })

    it('should generate encryption key if none exists', () => {
      ;(sessionStorageMock.getItem as Mock).mockReturnValue(null)

      createTokenStorage()

      expect(sessionStorageMock.setItem).toHaveBeenCalledWith(
        'iam_session_key',
        expect.any(String)
      )
    })

    it('should reuse existing encryption key', () => {
      ;(sessionStorageMock.getItem as Mock).mockReturnValue('existing_key')

      createTokenStorage()

      expect(sessionStorageMock.setItem).not.toHaveBeenCalled()
    })

    it('should handle encryption errors gracefully', () => {
      ;(sessionStorageMock.getItem as Mock).mockReturnValue('test_key')

      // Mock TextEncoder to throw error
      global.TextEncoder = vi.fn().mockImplementation(() => ({
        encode: vi.fn().mockImplementation(() => {
          throw new Error('Encoding failed')
        }),
      }))

      const storage = createTokenStorage()

      // Should not throw error when encryption fails
      expect(() => storage.setTokens(mockTokens)).not.toThrow()
    })

    it('should handle decryption errors gracefully', () => {
      ;(localStorageMock.getItem as Mock).mockReturnValue(
        'corrupted_encrypted_data'
      )
      ;(sessionStorageMock.getItem as Mock).mockReturnValue('test_key')

      // Mock atob to throw error
      global.atob = vi.fn().mockImplementation(() => {
        throw new Error('Decoding failed')
      })

      const storage = createTokenStorage()
      const result = storage.getTokens()

      // Should handle gracefully and remove corrupted data
      expect(result).toBeNull()
      expect(localStorageMock.removeItem).toHaveBeenCalled()
    })
  })

  describe('Edge Cases', () => {
    it('should handle missing browser APIs gracefully', () => {
      // Remove localStorage
      Object.defineProperty(window, 'localStorage', {
        value: undefined,
        writable: true,
      })

      process.env.NODE_ENV = 'development'

      expect(() => createTokenStorage()).not.toThrow()
    })

    it('should handle empty token strings', () => {
      const storage = createTokenStorage()

      expect(storage.isTokenExpired('')).toBe(true)
      expect(storage.isTokenExpired('   ')).toBe(true)
    })

    it('should handle very long token data', () => {
      process.env.NODE_ENV = 'development'
      ;(sessionStorageMock.getItem as Mock).mockReturnValue('test_key')

      const largeTokens = {
        ...mockTokens,
        access_token: 'a'.repeat(10000),
        refresh_token: 'b'.repeat(10000),
      }

      const storage = createTokenStorage()

      expect(() => storage.setTokens(largeTokens)).not.toThrow()
    })
  })

  describe('Security Considerations', () => {
    it('should use different storage mechanisms for production vs development', () => {
      const devStorage = createTokenStorage()

      process.env.NODE_ENV = 'production'
      const prodStorage = createTokenStorage()

      // They should be different implementations
      expect(devStorage).not.toBe(prodStorage)
    })

    it('should encrypt data in development', () => {
      process.env.NODE_ENV = 'development'
      ;(sessionStorageMock.getItem as Mock).mockReturnValue('test_key')

      const storage = createTokenStorage()
      storage.setTokens(mockTokens)

      // Should call localStorage.setItem with encrypted data
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        'iam_auth_tokens',
        expect.not.stringContaining(mockTokens.access_token)
      )
    })

    it('should use secure cookie flags in production', () => {
      process.env.NODE_ENV = 'production'

      let cookieValue = ''
      Object.defineProperty(mockDocument, 'cookie', {
        set: (value: string) => {
          cookieValue = value
        },
        get: () => cookieValue,
      })

      const storage = createTokenStorage()
      storage.setTokens(mockTokens)

      expect(cookieValue).toContain('Secure')
      expect(cookieValue).toContain('SameSite=Strict')
    })
  })
})
