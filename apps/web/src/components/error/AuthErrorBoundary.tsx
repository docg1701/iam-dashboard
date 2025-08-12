'use client';

import React, { Component, ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertTriangle, RefreshCw, LogIn } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
  isAuthError: boolean;
}

/**
 * Enhanced error boundary for authentication-related errors.
 * Provides specific handling for authentication failures, token expiration, 
 * and permission errors with appropriate recovery actions.
 */
export class AuthErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      isAuthError: false,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    // Detect authentication-related errors
    const isAuthError = 
      error.message.includes('401') ||
      error.message.includes('403') ||
      error.message.includes('Unauthorized') ||
      error.message.includes('Token') ||
      error.message.includes('Authentication') ||
      error.message.includes('Permission denied');

    return {
      hasError: true,
      error,
      isAuthError,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log authentication errors for monitoring
    console.error('AuthErrorBoundary caught an error:', {
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      isAuthError: this.state.isAuthError,
      timestamp: new Date().toISOString(),
    });

    // Store error info for debugging
    this.setState({
      error,
      errorInfo,
    });

    // Report to monitoring service in production
    if (process.env.NODE_ENV === 'production') {
      // TODO: Integrate with monitoring service (Sentry, LogRocket, etc.)
      this.reportError(error, errorInfo);
    }
  }

  private reportError = (error: Error, errorInfo: React.ErrorInfo) => {
    // Integration point for error reporting services
    // This would typically send to Sentry, LogRocket, or similar
    const errorReport = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      url: window.location.href,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
      userId: this.getCurrentUserId(),
      sessionId: this.getSessionId(),
    };

    // Mock error reporting (replace with actual service)
    console.log('Error reported to monitoring service:', errorReport);
  };

  private getCurrentUserId = (): string | null => {
    try {
      // Safely get user ID from auth context or localStorage
      const authData = localStorage.getItem('auth-storage');
      if (authData) {
        const parsed = JSON.parse(authData);
        return parsed.state?.user?.id || null;
      }
    } catch {
      // Silently fail if unable to get user ID
    }
    return null;
  };

  private getSessionId = (): string => {
    try {
      let sessionId = sessionStorage.getItem('session-id');
      if (!sessionId) {
        sessionId = Math.random().toString(36).substring(7);
        sessionStorage.setItem('session-id', sessionId);
      }
      return sessionId;
    } catch {
      return 'unknown';
    }
  };

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: undefined,
      errorInfo: undefined,
      isAuthError: false,
    });
    
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  private handleRelogin = () => {
    // Clear authentication state and redirect to login
    try {
      localStorage.removeItem('auth-storage');
      sessionStorage.clear();
    } catch {
      // Silently fail if unable to clear storage
    }
    
    // Redirect to login page
    window.location.href = '/login';
  };

  private handleRefresh = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Authentication-specific error UI
      if (this.state.isAuthError) {
        return (
          <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
            <div className="max-w-md w-full space-y-4">
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>Erro de Autenticação</AlertTitle>
                <AlertDescription>
                  Sua sessão expirou ou você não tem permissão para acessar este recurso.
                  Por favor, faça login novamente.
                </AlertDescription>
              </Alert>

              <div className="flex flex-col gap-2">
                <Button onClick={this.handleRelogin} className="w-full">
                  <LogIn className="h-4 w-4 mr-2" />
                  Fazer Login Novamente
                </Button>
                
                <Button variant="outline" onClick={this.handleReset} className="w-full">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Tentar Novamente
                </Button>
              </div>

              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="mt-4 p-3 bg-gray-100 rounded text-xs">
                  <summary className="cursor-pointer font-medium">
                    Detalhes do Erro (Desenvolvimento)
                  </summary>
                  <pre className="mt-2 whitespace-pre-wrap">
                    {this.state.error.message}
                    {this.state.error.stack && `\n\nStack:\n${this.state.error.stack}`}
                  </pre>
                </details>
              )}
            </div>
          </div>
        );
      }

      // General error UI
      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
          <div className="max-w-md w-full space-y-4">
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Algo deu errado</AlertTitle>
              <AlertDescription>
                Ocorreu um erro inesperado. Você pode tentar recarregar a página ou 
                entrar em contato com o suporte se o problema persistir.
              </AlertDescription>
            </Alert>

            <div className="flex flex-col gap-2">
              <Button onClick={this.handleRefresh} className="w-full">
                <RefreshCw className="h-4 w-4 mr-2" />
                Recarregar Página
              </Button>
              
              <Button variant="outline" onClick={this.handleReset} className="w-full">
                Tentar Novamente
              </Button>
            </div>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mt-4 p-3 bg-gray-100 rounded text-xs">
                <summary className="cursor-pointer font-medium">
                  Detalhes do Erro (Desenvolvimento)
                </summary>
                <pre className="mt-2 whitespace-pre-wrap">
                  {this.state.error.message}
                  {this.state.error.stack && `\n\nStack:\n${this.state.error.stack}`}
                  {this.state.errorInfo?.componentStack && 
                    `\n\nComponent Stack:\n${this.state.errorInfo.componentStack}`}
                </pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default AuthErrorBoundary;