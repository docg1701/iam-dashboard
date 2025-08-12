'use client';

import React, { Component, ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertTriangle, RefreshCw, Bug, Home } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
  errorId?: string;
}

/**
 * Global error boundary for catching and handling all application errors.
 * Provides comprehensive error reporting, recovery options, and user-friendly feedback.
 */
export class GlobalErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Generate unique error ID for tracking
    const errorId = `ERR_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    
    return {
      hasError: true,
      error,
      errorId,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Enhanced error logging with context
    const errorContext = {
      errorId: this.state.errorId,
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      url: window.location.href,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
      userId: this.getCurrentUserId(),
      sessionId: this.getSessionId(),
      buildVersion: process.env.NEXT_PUBLIC_BUILD_VERSION || 'unknown',
      environment: process.env.NODE_ENV,
    };

    console.error('GlobalErrorBoundary caught an error:', errorContext);

    // Store error info
    this.setState({
      error,
      errorInfo,
    });

    // Report to monitoring service
    this.reportError(errorContext);

    // Store error in localStorage for debugging
    try {
      const storedErrors = JSON.parse(localStorage.getItem('app-errors') || '[]');
      storedErrors.push(errorContext);
      // Keep only last 10 errors
      const recentErrors = storedErrors.slice(-10);
      localStorage.setItem('app-errors', JSON.stringify(recentErrors));
    } catch {
      // Silently fail if unable to store errors
    }
  }

  private reportError = async (errorContext: any) => {
    // In production, this would integrate with monitoring services
    if (process.env.NODE_ENV === 'production') {
      try {
        // Example: Send to monitoring service
        await fetch('/api/errors', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(errorContext),
        });
      } catch {
        // Silently fail if error reporting fails
        console.warn('Failed to report error to monitoring service');
      }
    }
  };

  private getCurrentUserId = (): string | null => {
    try {
      const authData = localStorage.getItem('auth-storage');
      if (authData) {
        const parsed = JSON.parse(authData);
        return parsed.state?.user?.id || null;
      }
    } catch {
      // Silently fail
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
      errorId: undefined,
    });
    
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  private handleRefresh = () => {
    window.location.reload();
  };

  private handleGoHome = () => {
    window.location.href = '/';
  };

  private handleReportBug = () => {
    const errorDetails = {
      errorId: this.state.errorId,
      message: this.state.error?.message,
      url: window.location.href,
      timestamp: new Date().toISOString(),
    };

    const mailto = `mailto:support@iam-dashboard.com?subject=Bug Report - ${this.state.errorId}&body=${encodeURIComponent(
      `Error ID: ${errorDetails.errorId}\n` +
      `Message: ${errorDetails.message}\n` +
      `URL: ${errorDetails.url}\n` +
      `Timestamp: ${errorDetails.timestamp}\n\n` +
      'Please describe what you were doing when this error occurred:\n\n'
    )}`;

    window.open(mailto);
  };

  private getErrorCategory = (): string => {
    if (!this.state.error) return 'unknown';

    const message = this.state.error.message.toLowerCase();
    
    if (message.includes('chunk') || message.includes('loading')) {
      return 'network';
    }
    if (message.includes('auth') || message.includes('token')) {
      return 'authentication';
    }
    if (message.includes('permission') || message.includes('access')) {
      return 'authorization';
    }
    if (message.includes('network') || message.includes('fetch')) {
      return 'network';
    }
    
    return 'application';
  };

  private getErrorMessage = (): string => {
    const category = this.getErrorCategory();
    
    switch (category) {
      case 'network':
        return 'Problema de conexão detectado. Verifique sua internet e tente novamente.';
      case 'authentication':
        return 'Erro de autenticação. Você pode precisar fazer login novamente.';
      case 'authorization':
        return 'Você não tem permissão para acessar este recurso.';
      default:
        return 'Ocorreu um erro inesperado na aplicação. Nossa equipe foi notificada.';
    }
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const errorCategory = this.getErrorCategory();
      const errorMessage = this.getErrorMessage();

      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-gray-50">
          <div className="max-w-lg w-full space-y-6">
            <div className="text-center">
              <AlertTriangle className="h-16 w-16 text-red-500 mx-auto mb-4" />
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                Oops! Algo deu errado
              </h1>
              <p className="text-gray-600">
                {errorMessage}
              </p>
            </div>

            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Erro Identificado</AlertTitle>
              <AlertDescription>
                ID do erro: <code className="font-mono text-xs">{this.state.errorId}</code>
                <br />
                Categoria: <span className="capitalize">{errorCategory}</span>
              </AlertDescription>
            </Alert>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Button onClick={this.handleReset} className="w-full">
                <RefreshCw className="h-4 w-4 mr-2" />
                Tentar Novamente
              </Button>
              
              <Button variant="outline" onClick={this.handleRefresh} className="w-full">
                <RefreshCw className="h-4 w-4 mr-2" />
                Recarregar Página
              </Button>
              
              <Button variant="outline" onClick={this.handleGoHome} className="w-full">
                <Home className="h-4 w-4 mr-2" />
                Ir para Início
              </Button>
              
              <Button variant="outline" onClick={this.handleReportBug} className="w-full">
                <Bug className="h-4 w-4 mr-2" />
                Reportar Bug
              </Button>
            </div>

            {/* Development mode error details */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mt-6 p-4 bg-gray-100 rounded text-xs">
                <summary className="cursor-pointer font-medium mb-2">
                  Detalhes do Erro (Desenvolvimento)
                </summary>
                <div className="space-y-2">
                  <div>
                    <strong>Message:</strong>
                    <pre className="mt-1 whitespace-pre-wrap break-words">
                      {this.state.error.message}
                    </pre>
                  </div>
                  
                  {this.state.error.stack && (
                    <div>
                      <strong>Stack Trace:</strong>
                      <pre className="mt-1 whitespace-pre-wrap break-words text-xs">
                        {this.state.error.stack}
                      </pre>
                    </div>
                  )}
                  
                  {this.state.errorInfo?.componentStack && (
                    <div>
                      <strong>Component Stack:</strong>
                      <pre className="mt-1 whitespace-pre-wrap break-words text-xs">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    </div>
                  )}
                </div>
              </details>
            )}

            <div className="text-center text-sm text-gray-500">
              <p>
                Se o problema persistir, entre em contato com nosso suporte técnico.
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default GlobalErrorBoundary;