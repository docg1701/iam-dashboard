'use client'

import React, { Component, ReactNode, ErrorInfo } from 'react'

import { Button } from '../ui/button'
import { Card } from '../ui/card'

interface AuthError extends Error {
  code?: string
  statusCode?: number
  retryable?: boolean
}

interface AuthErrorBoundaryState {
  hasError: boolean
  error: AuthError | null
  errorId: string
}

interface AuthErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: AuthError, errorInfo: ErrorInfo) => void
  enableRetry?: boolean
}

/**
 * Error boundary specifically for authentication-related errors.
 * Catches errors in authentication flows and provides user-friendly recovery options.
 *
 * Features:
 * - Categorizes authentication errors by type
 * - Provides appropriate user messages in Portuguese
 * - Offers retry mechanisms for retryable errors
 * - Logs detailed error information for debugging
 * - Graceful fallback UI components
 *
 * @example
 * <AuthErrorBoundary>
 *   <LoginForm />
 * </AuthErrorBoundary>
 *
 * @example
 * <AuthErrorBoundary
 *   onError={(error) => logToMonitoring(error)}
 *   enableRetry={true}
 * >
 *   <AuthProvider>
 *     <App />
 *   </AuthProvider>
 * </AuthErrorBoundary>
 */
export class AuthErrorBoundary extends Component<
  AuthErrorBoundaryProps,
  AuthErrorBoundaryState
> {
  private retryTimeouts: Set<NodeJS.Timeout> = new Set()

  constructor(props: AuthErrorBoundaryProps) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorId: '',
    }
  }

  static getDerivedStateFromError(
    error: Error
  ): Partial<AuthErrorBoundaryState> {
    // Generate unique error ID for tracking
    const errorId = `auth_error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

    return {
      hasError: true,
      error: error as AuthError,
      errorId,
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const authError = error as AuthError

    // TODO: Integrate with proper error tracking service

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(authError, errorInfo)
    }

    // Report to monitoring service in production
    if (process.env.NODE_ENV === 'production') {
      this.reportErrorToMonitoring(authError, errorInfo)
    }
  }

  componentWillUnmount() {
    // Clear any pending retry timeouts
    this.retryTimeouts.forEach(timeout => clearTimeout(timeout))
    this.retryTimeouts.clear()
  }

  private reportErrorToMonitoring = (
    error: AuthError,
    errorInfo: ErrorInfo
  ) => {
    // In a real application, this would send to Sentry, DataDog, etc.
    // For now, we'll create a detailed error report
    const errorReport = {
      id: this.state.errorId,
      message: error.message,
      stack: error.stack,
      code: error.code,
      statusCode: error.statusCode,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: window.navigator.userAgent,
      url: window.location.href,
    }

    // TODO: Send error report to actual monitoring service
  }

  private categorizeError = (
    error: AuthError
  ): {
    category: string
    message: string
    isRetryable: boolean
    severity: 'low' | 'medium' | 'high' | 'critical'
  } => {
    const message = error.message.toLowerCase()
    const code = error.code
    const statusCode = error.statusCode

    // Network-related errors
    if (
      message.includes('network') ||
      message.includes('fetch') ||
      statusCode === 0
    ) {
      return {
        category: 'network',
        message:
          'Problema de conexão com o servidor. Verifique sua internet e tente novamente.',
        isRetryable: true,
        severity: 'medium',
      }
    }

    // Server errors
    if (statusCode && statusCode >= 500) {
      return {
        category: 'server',
        message:
          'Erro interno do servidor. Nossa equipe foi notificada. Tente novamente em alguns minutos.',
        isRetryable: true,
        severity: 'high',
      }
    }

    // Authentication/Authorization errors
    if (
      statusCode === 401 ||
      message.includes('unauthorized') ||
      message.includes('invalid credentials')
    ) {
      return {
        category: 'auth',
        message:
          'Credenciais inválidas ou sessão expirada. Faça login novamente.',
        isRetryable: false,
        severity: 'medium',
      }
    }

    if (
      statusCode === 403 ||
      message.includes('forbidden') ||
      message.includes('access denied')
    ) {
      return {
        category: 'permission',
        message: 'Você não tem permissão para acessar este recurso.',
        isRetryable: false,
        severity: 'medium',
      }
    }

    // Token/Session errors
    if (
      message.includes('token') ||
      message.includes('session') ||
      code === 'TOKEN_EXPIRED'
    ) {
      return {
        category: 'session',
        message:
          'Sua sessão expirou. Você será redirecionado para fazer login novamente.',
        isRetryable: false,
        severity: 'low',
      }
    }

    // 2FA related errors
    if (
      message.includes('2fa') ||
      message.includes('totp') ||
      code === 'INVALID_2FA'
    ) {
      return {
        category: '2fa',
        message:
          'Código de autenticação de dois fatores inválido. Verifique o código e tente novamente.',
        isRetryable: true,
        severity: 'medium',
      }
    }

    // Client-side validation errors
    if (statusCode === 400 || message.includes('validation')) {
      return {
        category: 'validation',
        message:
          'Dados fornecidos são inválidos. Verifique as informações e tente novamente.',
        isRetryable: true,
        severity: 'low',
      }
    }

    // Generic/Unknown errors
    return {
      category: 'unknown',
      message:
        'Ocorreu um erro inesperado. Tente novamente ou contate o suporte se o problema persistir.',
      isRetryable: true,
      severity: 'medium',
    }
  }

  private handleRetry = () => {
    if (this.props.enableRetry !== false) {
      // Clear error state to retry rendering
      this.setState({
        hasError: false,
        error: null,
        errorId: '',
      })
    }
  }

  private handleReload = () => {
    window.location.reload()
  }

  private handleGoHome = () => {
    window.location.href = '/'
  }

  private handleLoginRedirect = () => {
    // Clear any stored auth tokens
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
    window.location.href = '/login'
  }

  render() {
    if (!this.state.hasError) {
      return this.props.children
    }

    if (this.props.fallback) {
      return this.props.fallback
    }

    const { error } = this.state
    if (!error) {
      return null
    }

    const errorDetails = this.categorizeError(error)

    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
        <Card className="w-full max-w-md space-y-6 p-6">
          <div className="text-center">
            {/* Error icon based on category */}
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
              {errorDetails.category === 'network' && (
                <svg
                  className="h-8 w-8 text-red-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              )}
              {errorDetails.category === 'auth' && (
                <svg
                  className="h-8 w-8 text-red-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                  />
                </svg>
              )}
              {(errorDetails.category === 'server' ||
                errorDetails.category === 'unknown') && (
                <svg
                  className="h-8 w-8 text-red-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.082 16.5c-.77.833.192 2.5 1.732 2.5z"
                  />
                </svg>
              )}
              {errorDetails.category === '2fa' && (
                <svg
                  className="h-8 w-8 text-red-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              )}
            </div>

            <h1 className="mb-2 text-xl font-semibold text-gray-900">
              Erro de Autenticação
            </h1>

            <p className="mb-6 text-gray-600">{errorDetails.message}</p>

            {/* Error details for development */}
            {process.env.NODE_ENV === 'development' && (
              <details className="mb-4 rounded bg-gray-100 p-3 text-left text-sm">
                <summary className="mb-2 cursor-pointer font-medium text-gray-700">
                  Detalhes Técnicos (Desenvolvimento)
                </summary>
                <div className="space-y-1 text-xs text-gray-600">
                  <div>
                    <strong>ID:</strong> {this.state.errorId}
                  </div>
                  <div>
                    <strong>Categoria:</strong> {errorDetails.category}
                  </div>
                  <div>
                    <strong>Severidade:</strong> {errorDetails.severity}
                  </div>
                  <div>
                    <strong>Código:</strong> {error.code || 'N/A'}
                  </div>
                  <div>
                    <strong>Status HTTP:</strong> {error.statusCode || 'N/A'}
                  </div>
                  <div>
                    <strong>Mensagem Original:</strong> {error.message}
                  </div>
                </div>
              </details>
            )}
          </div>

          <div className="space-y-3">
            {/* Primary action based on error category */}
            {errorDetails.category === 'auth' && (
              <Button
                onClick={this.handleLoginRedirect}
                className="w-full"
                variant="default"
              >
                Fazer Login Novamente
              </Button>
            )}

            {errorDetails.category === 'session' && (
              <Button
                onClick={this.handleLoginRedirect}
                className="w-full"
                variant="default"
              >
                Ir para Login
              </Button>
            )}

            {errorDetails.isRetryable &&
              errorDetails.category !== 'auth' &&
              errorDetails.category !== 'session' && (
                <Button
                  onClick={this.handleRetry}
                  className="w-full"
                  variant="default"
                >
                  Tentar Novamente
                </Button>
              )}

            {/* Secondary actions */}
            <div className="flex gap-2">
              <Button
                onClick={this.handleReload}
                className="flex-1"
                variant="outline"
              >
                Recarregar Página
              </Button>

              <Button
                onClick={this.handleGoHome}
                className="flex-1"
                variant="outline"
              >
                Ir para Início
              </Button>
            </div>
          </div>

          {/* Support information */}
          <div className="border-t pt-4 text-center text-xs text-gray-500">
            Se o problema persistir, contate o suporte técnico informando o
            código:
            <br />
            <code className="rounded bg-gray-100 px-2 py-1">
              {this.state.errorId}
            </code>
          </div>
        </Card>
      </div>
    )
  }
}

/**
 * Higher-order component to wrap components with authentication error boundary
 */
export const withAuthErrorBoundary = <P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<AuthErrorBoundaryProps, 'children'>
) => {
  const WrappedComponent = (props: P) => (
    <AuthErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </AuthErrorBoundary>
  )

  WrappedComponent.displayName = `withAuthErrorBoundary(${Component.displayName || Component.name})`
  return WrappedComponent
}

export default AuthErrorBoundary
