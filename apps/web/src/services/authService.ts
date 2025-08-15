/**
 * Authentication service for API calls
 * Handles login, logout, 2FA, and user management
 * Based on Story 1.3 requirements and API specification
 */

import {
  LoginCredentials,
  LoginResponse,
  RefreshTokenResponse,
  TwoFactorSetupResponse,
  User,
  UserPermission,
  SessionInfo,
  HttpError,
} from '@/types/auth'

import { httpClient } from './httpClient'

class AuthService {
  private readonly apiPath = '/api/v1/auth'

  /**
   * Login with email and password (and optional TOTP code)
   */
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      const response = await httpClient.post<LoginResponse>(
        `${this.apiPath}/login`,
        {
          email: credentials.email,
          password: credentials.password,
          totp_code: credentials.totp_code,
        }
      )

      return response
    } catch (error: unknown) {
      const httpError = error as HttpError
      const message = httpError.response?.data?.detail || 'Login failed'
      throw new Error(message)
    }
  }

  /**
   * Logout current user and invalidate tokens
   */
  async logout(): Promise<void> {
    try {
      await httpClient.post(`${this.apiPath}/logout`)
    } catch (error) {
      // Even if logout fails on server, we should clear local tokens
      // TODO: Log logout failures to monitoring service
    }
  }

  /**
   * Refresh authentication tokens
   */
  async refreshToken(refreshToken: string): Promise<RefreshTokenResponse> {
    try {
      const response = await httpClient.post<RefreshTokenResponse>(
        `${this.apiPath}/refresh`,
        {
          refresh_token: refreshToken,
        }
      )

      return response
    } catch (error: unknown) {
      const httpError = error as HttpError
      const message = httpError.response?.data?.detail || 'Token refresh failed'
      throw new Error(message)
    }
  }

  /**
   * Get current user profile and permissions
   */
  async getCurrentUser(): Promise<{
    user: User
    permissions: UserPermission[]
  }> {
    try {
      const response = await httpClient.get<{
        user: User
        permissions: UserPermission[]
      }>(`${this.apiPath}/me`)

      return response
    } catch (error: unknown) {
      const httpError = error as HttpError
      const message =
        httpError.response?.data?.detail || 'Failed to get user profile'
      throw new Error(message)
    }
  }

  /**
   * Setup two-factor authentication for current user
   */
  async setup2FA(): Promise<TwoFactorSetupResponse> {
    try {
      const response = await httpClient.post<TwoFactorSetupResponse>(
        `${this.apiPath}/setup-2fa`
      )

      return response
    } catch (error: unknown) {
      const httpError = error as HttpError
      const message = httpError.response?.data?.detail || 'Failed to setup 2FA'
      throw new Error(message)
    }
  }

  /**
   * Verify and enable two-factor authentication
   */
  async enable2FA(
    totpCode: string
  ): Promise<{ success: boolean; backup_codes: string[] }> {
    try {
      const response = await httpClient.post<{
        success: boolean
        backup_codes: string[]
      }>(`${this.apiPath}/enable-2fa`, {
        totp_code: totpCode,
      })

      return response
    } catch (error: unknown) {
      const httpError = error as HttpError
      const message = httpError.response?.data?.detail || 'Failed to enable 2FA'
      throw new Error(message)
    }
  }

  /**
   * Disable two-factor authentication
   */
  async disable2FA(totpCode: string): Promise<{ success: boolean }> {
    try {
      const response = await httpClient.post<{ success: boolean }>(
        `${this.apiPath}/disable-2fa`,
        {
          totp_code: totpCode,
        }
      )

      return response
    } catch (error: unknown) {
      const httpError = error as HttpError
      const message =
        httpError.response?.data?.detail || 'Failed to disable 2FA'
      throw new Error(message)
    }
  }

  /**
   * Generate new backup codes for 2FA
   */
  async generateBackupCodes(): Promise<{ backup_codes: string[] }> {
    try {
      const response = await httpClient.post<{ backup_codes: string[] }>(
        `${this.apiPath}/generate-backup-codes`
      )

      return response
    } catch (error: unknown) {
      const httpError = error as HttpError
      const message =
        httpError.response?.data?.detail || 'Failed to generate backup codes'
      throw new Error(message)
    }
  }

  /**
   * Change user password
   */
  async changePassword(
    currentPassword: string,
    newPassword: string
  ): Promise<{ success: boolean }> {
    try {
      const response = await httpClient.post<{ success: boolean }>(
        `${this.apiPath}/change-password`,
        {
          current_password: currentPassword,
          new_password: newPassword,
        }
      )

      return response
    } catch (error: unknown) {
      const httpError = error as HttpError
      const message =
        httpError.response?.data?.detail || 'Failed to change password'
      throw new Error(message)
    }
  }

  /**
   * Request password reset (send email)
   */
  async requestPasswordReset(email: string): Promise<{ success: boolean }> {
    try {
      const response = await httpClient.post<{ success: boolean }>(
        `${this.apiPath}/request-password-reset`,
        {
          email,
        }
      )

      return response
    } catch (error: unknown) {
      const httpError = error as HttpError
      const message =
        httpError.response?.data?.detail || 'Failed to request password reset'
      throw new Error(message)
    }
  }

  /**
   * Reset password with token from email
   */
  async resetPassword(
    token: string,
    newPassword: string
  ): Promise<{ success: boolean }> {
    try {
      const response = await httpClient.post<{ success: boolean }>(
        `${this.apiPath}/reset-password`,
        {
          token,
          new_password: newPassword,
        }
      )

      return response
    } catch (error: unknown) {
      const httpError = error as HttpError
      const message =
        httpError.response?.data?.detail || 'Failed to reset password'
      throw new Error(message)
    }
  }

  /**
   * Verify email address with token
   */
  async verifyEmail(token: string): Promise<{ success: boolean }> {
    try {
      const response = await httpClient.post<{ success: boolean }>(
        `${this.apiPath}/verify-email`,
        {
          token,
        }
      )

      return response
    } catch (error: unknown) {
      const httpError = error as HttpError
      const message =
        httpError.response?.data?.detail || 'Failed to verify email'
      throw new Error(message)
    }
  }

  /**
   * Get user sessions and device information
   */
  async getUserSessions(): Promise<{ sessions: SessionInfo[] }> {
    try {
      const response = await httpClient.get<{ sessions: SessionInfo[] }>(
        `${this.apiPath}/sessions`
      )

      return response
    } catch (error: unknown) {
      const httpError = error as HttpError
      const message =
        httpError.response?.data?.detail || 'Failed to get user sessions'
      throw new Error(message)
    }
  }

  /**
   * Revoke a specific session
   */
  async revokeSession(sessionId: string): Promise<{ success: boolean }> {
    try {
      const response = await httpClient.delete<{ success: boolean }>(
        `${this.apiPath}/sessions/${sessionId}`
      )

      return response
    } catch (error: unknown) {
      const httpError = error as HttpError
      const message =
        httpError.response?.data?.detail || 'Failed to revoke session'
      throw new Error(message)
    }
  }

  /**
   * Revoke all sessions except current
   */
  async revokeAllOtherSessions(): Promise<{
    success: boolean
    revoked_count: number
  }> {
    try {
      const response = await httpClient.delete<{
        success: boolean
        revoked_count: number
      }>(`${this.apiPath}/sessions/others`)

      return response
    } catch (error: unknown) {
      const httpError = error as HttpError
      const message =
        httpError.response?.data?.detail || 'Failed to revoke sessions'
      throw new Error(message)
    }
  }
}

// Create singleton instance
export const authService = new AuthService()

// Export for testing
export { AuthService }
