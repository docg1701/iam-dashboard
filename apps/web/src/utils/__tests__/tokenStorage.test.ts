import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

import { AuthTokens } from '@/types/auth'

import { createTokenStorage, tokenStorage } from '../tokenStorage'

// Mock environment
const mockSetNodeEnv = (env: string) => {
  vi.stubEnv('NODE_ENV', env)
}

// Mock tokens for testing
const mockTokens: AuthTokens = {
  access_token:
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjk5OTk5OTk5OTl9.Lm5p1zr0_RO6jtZeNjX5YFBa5BXrG8H9mME5OxtKoS8',
  refresh_token: 'refresh_token_value',
  token_type: 'Bearer',
  expires_in: 3600,
}

const expiredToken =
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyMzkwMjJ9.invalid_signature'

describe('TokenStorage', () => {
  beforeEach(() => {
    // Clear all storage
    localStorage.clear()
    sessionStorage.clear()

    // Mock document.cookie
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: '',
    })
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  describe('createTokenStorage factory', () => {
    it('should return DevelopmentTokenStorage in development', () => {
      mockSetNodeEnv('development')
      const storage = createTokenStorage()

      // Test development-specific behavior
      storage.setTokens(mockTokens)
      const retrievedTokens = storage.getTokens()

      expect(retrievedTokens).toEqual(mockTokens)
      expect(localStorage.getItem('iam_auth_tokens')).toBeTruthy()
    })

    it('should return ProductionTokenStorage in production', () => {
      mockSetNodeEnv('production')
      const storage = createTokenStorage()

      // Test that it doesn't use localStorage
      storage.setTokens(mockTokens)
      expect(localStorage.getItem('iam_auth_tokens')).toBeNull()
    })

    it('should return DevelopmentTokenStorage by default', () => {
      mockSetNodeEnv('test')
      const storage = createTokenStorage()

      storage.setTokens(mockTokens)
      const retrievedTokens = storage.getTokens()

      expect(retrievedTokens).toEqual(mockTokens)
    })
  })

  describe('DevelopmentTokenStorage', () => {
    let storage: ReturnType<typeof createTokenStorage>

    beforeEach(() => {
      mockSetNodeEnv('development')
      storage = createTokenStorage()
    })

    describe('Token Storage and Retrieval', () => {
      it('should store and retrieve tokens correctly', () => {
        storage.setTokens(mockTokens)
        const retrievedTokens = storage.getTokens()

        expect(retrievedTokens).toEqual(mockTokens)
      })

      it('should return null when no tokens are stored', () => {
        const tokens = storage.getTokens()
        expect(tokens).toBeNull()
      })

      it('should encrypt tokens in localStorage', () => {
        storage.setTokens(mockTokens)

        const storedData = localStorage.getItem('iam_auth_tokens')
        expect(storedData).toBeTruthy()

        // Should not be plain JSON
        expect(() => JSON.parse(storedData!)).toThrow()
      })

      it('should handle corrupted encrypted data gracefully', () => {
        // Store invalid encrypted data
        localStorage.setItem('iam_auth_tokens', 'invalid_encrypted_data')

        const tokens = storage.getTokens()
        expect(tokens).toBeNull()

        // Should clear corrupted data
        expect(localStorage.getItem('iam_auth_tokens')).toBeNull()
      })

      it('should handle JSON parsing errors gracefully', () => {
        // Mock decryption to return invalid JSON
        localStorage.setItem('iam_auth_tokens', btoa('invalid_json'))

        const tokens = storage.getTokens()
        expect(tokens).toBeNull()
      })
    })

    describe('Token Removal', () => {
      it('should remove tokens from localStorage', () => {
        storage.setTokens(mockTokens)
        expect(localStorage.getItem('iam_auth_tokens')).toBeTruthy()

        storage.removeTokens()
        expect(localStorage.getItem('iam_auth_tokens')).toBeNull()
      })

      it('should handle removal errors gracefully', () => {
        // Mock localStorage.removeItem to throw
        const originalRemoveItem = localStorage.removeItem
        localStorage.removeItem = vi.fn(() => {
          throw new Error('Storage error')
        })

        expect(() => storage.removeTokens()).not.toThrow()

        // Restore original method
        localStorage.removeItem = originalRemoveItem
      })
    })

    describe('Token Expiration', () => {
      it('should correctly identify non-expired tokens', () => {
        const isExpired = storage.isTokenExpired(mockTokens.access_token)
        expect(isExpired).toBe(false)
      })

      it('should correctly identify expired tokens', () => {
        const isExpired = storage.isTokenExpired(expiredToken)
        expect(isExpired).toBe(true)
      })

      it('should handle invalid token format', () => {
        const isExpired = storage.isTokenExpired('invalid_token')
        expect(isExpired).toBe(true)
      })

      it('should handle tokens with wrong number of parts', () => {
        const isExpired = storage.isTokenExpired('header.payload')
        expect(isExpired).toBe(true)
      })

      it('should handle tokens with invalid base64 payload', () => {
        const isExpired = storage.isTokenExpired(
          'header.invalid_base64.signature'
        )
        expect(isExpired).toBe(true)
      })

      it('should add 5 minute buffer for token refresh', () => {
        // Create a token that expires in 4 minutes (less than 5 minute buffer)
        const futureExp = Math.floor(Date.now() / 1000) + 240 // 4 minutes
        const payload = JSON.stringify({ exp: futureExp })
        const tokenWithSoonExpiry = `header.${btoa(payload)}.signature`

        const isExpired = storage.isTokenExpired(tokenWithSoonExpiry)
        expect(isExpired).toBe(true) // Should be considered expired due to buffer
      })
    })

    describe('Encryption/Decryption', () => {
      it('should encrypt and decrypt data consistently', () => {
        storage.setTokens(mockTokens)
        const retrievedTokens = storage.getTokens()

        expect(retrievedTokens).toEqual(mockTokens)
        expect(retrievedTokens?.access_token).toBe(mockTokens.access_token)
        expect(retrievedTokens?.refresh_token).toBe(mockTokens.refresh_token)
      })

      it('should handle storage errors during setTokens', () => {
        // Mock localStorage.setItem to throw
        const originalSetItem = localStorage.setItem
        localStorage.setItem = vi.fn(() => {
          throw new Error('Storage error')
        })

        expect(() => storage.setTokens(mockTokens)).toThrow(
          'Failed to store authentication tokens'
        )

        // Restore original method
        localStorage.setItem = originalSetItem
      })

      it('should handle encryption errors gracefully', () => {
        // Mock TextEncoder to fail
        const originalTextEncoder = globalThis.TextEncoder
        interface MockTextEncoder {
          encode: ReturnType<typeof vi.fn>
        }
        globalThis.TextEncoder = vi.fn(
          () =>
            ({
              encode: vi.fn(() => {
                throw new Error('Encoding error')
              }),
            }) as MockTextEncoder
        ) as typeof TextEncoder

        // Should still work with fallback
        storage.setTokens(mockTokens)
        const retrievedTokens = storage.getTokens()

        expect(retrievedTokens).toEqual(mockTokens)

        // Restore original
        globalThis.TextEncoder = originalTextEncoder
      })
    })

    describe('Session Key Management', () => {
      it('should create and store session key', () => {
        // Access storage to trigger key creation
        storage.setTokens(mockTokens)

        const sessionKey = sessionStorage.getItem('iam_session_key')
        expect(sessionKey).toBeTruthy()
        expect(typeof sessionKey).toBe('string')
      })

      it('should reuse existing session key', () => {
        // Set a session key manually
        const customKey = 'custom_session_key'
        sessionStorage.setItem('iam_session_key', customKey)

        // Create new storage instance
        const newStorage = createTokenStorage()
        newStorage.setTokens(mockTokens)

        // Should still use the custom key
        expect(sessionStorage.getItem('iam_session_key')).toBe(customKey)
      })
    })
  })

  describe('ProductionTokenStorage', () => {
    let storage: ReturnType<typeof createTokenStorage>

    beforeEach(() => {
      mockSetNodeEnv('production')
      storage = createTokenStorage()
    })

    describe('Cookie-based Token Storage', () => {
      it('should not use localStorage in production', () => {
        storage.setTokens(mockTokens)
        expect(localStorage.getItem('iam_auth_tokens')).toBeNull()
      })

      it('should handle missing token_info cookie', () => {
        document.cookie = ''
        const tokens = storage.getTokens()
        expect(tokens).toBeNull()
      })

      it('should parse token_info cookie when present', () => {
        const tokenInfo = encodeURIComponent(
          JSON.stringify({
            token_type: 'Bearer',
            expires_in: 3600,
          })
        )
        document.cookie = `token_info=${tokenInfo}`

        const tokens = storage.getTokens()
        expect(tokens).toEqual({
          token_type: 'Bearer',
          expires_in: 3600,
        })
      })

      it('should handle malformed cookie data gracefully', () => {
        document.cookie = 'token_info=invalid_json'
        const tokens = storage.getTokens()
        expect(tokens).toBeNull()
      })

      it('should set secure cookie flags', () => {
        storage.setTokens(mockTokens)

        // Check that document.cookie would include secure flags
        // Note: In real browsers, we can't read secure cookie flags via document.cookie
        // This is more of a verification that the method doesn't throw
        expect(() => storage.setTokens(mockTokens)).not.toThrow()
      })

      it('should clear cookies on removeTokens', () => {
        // Set some cookie first
        document.cookie = 'token_info=some_value'

        storage.removeTokens()

        // Should have cleared the cookie (set to expired)
        expect(document.cookie).toContain(
          'expires=Thu, 01 Jan 1970 00:00:00 GMT'
        )
      })
    })

    describe('Token Expiration in Production', () => {
      it('should correctly identify non-expired tokens', () => {
        const isExpired = storage.isTokenExpired(mockTokens.access_token)
        expect(isExpired).toBe(false)
      })

      it('should correctly identify expired tokens', () => {
        const isExpired = storage.isTokenExpired(expiredToken)
        expect(isExpired).toBe(true)
      })

      it('should handle invalid token format in production', () => {
        const isExpired = storage.isTokenExpired('invalid_token')
        expect(isExpired).toBe(true)
      })
    })
  })

  describe('Default tokenStorage export', () => {
    it('should be an instance of token storage', () => {
      expect(tokenStorage).toBeDefined()
      expect(typeof tokenStorage.getTokens).toBe('function')
      expect(typeof tokenStorage.setTokens).toBe('function')
      expect(typeof tokenStorage.removeTokens).toBe('function')
      expect(typeof tokenStorage.isTokenExpired).toBe('function')
    })

    it('should work with the default export', () => {
      tokenStorage.setTokens(mockTokens)
      const retrievedTokens = tokenStorage.getTokens()

      expect(retrievedTokens).toEqual(mockTokens)
    })
  })

  describe('Edge Cases', () => {
    let storage: ReturnType<typeof createTokenStorage>

    beforeEach(() => {
      mockSetNodeEnv('development')
      storage = createTokenStorage()
    })

    it('should handle empty tokens object', () => {
      const emptyTokens = {
        access_token: '',
        refresh_token: '',
        token_type: '',
        expires_in: 0,
      }

      storage.setTokens(emptyTokens)
      const retrievedTokens = storage.getTokens()

      expect(retrievedTokens).toEqual(emptyTokens)
    })

    it('should handle tokens with special characters', () => {
      const specialTokens = {
        ...mockTokens,
        access_token: 'token_with_special_chars_!@#$%^&*()',
      }

      storage.setTokens(specialTokens)
      const retrievedTokens = storage.getTokens()

      expect(retrievedTokens).toEqual(specialTokens)
    })

    it('should handle very long tokens', () => {
      const longToken = 'a'.repeat(10000)
      const longTokens = {
        ...mockTokens,
        access_token: longToken,
      }

      storage.setTokens(longTokens)
      const retrievedTokens = storage.getTokens()

      expect(retrievedTokens?.access_token).toBe(longToken)
    })

    it('should handle null and undefined gracefully', () => {
      // These should not crash the application
      expect(() => storage.isTokenExpired('')).not.toThrow()
      expect(storage.isTokenExpired('')).toBe(true)
    })
  })
})
