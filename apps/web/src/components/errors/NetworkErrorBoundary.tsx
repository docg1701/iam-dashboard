"use client";

import React, { Component, ReactNode, ErrorInfo } from 'react';
import { Button } from '../ui/button';
import { Card } from '../ui/card';

interface NetworkError extends Error {
  code?: string;
  statusCode?: number;
  url?: string;
  retryable?: boolean;
}

interface NetworkErrorBoundaryState {
  hasError: boolean;
  error: NetworkError | null;
  retryCount: number;
  errorId: string;
}

interface NetworkErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  maxRetries?: number;
  retryDelay?: number;
  onError?: (error: NetworkError, errorInfo: ErrorInfo) => void;
  onRetry?: (retryCount: number) => void;
}

/**
 * Error boundary for network and API-related errors.
 * Provides automatic retry mechanisms and user-friendly error messages.
 * 
 * Features:
 * - Automatic retry for retryable errors
 * - Exponential backoff for retry attempts
 * - Network status monitoring
 * - Offline/online state handling
 * - User-friendly error messages in Portuguese
 * 
 * @example
 * <NetworkErrorBoundary maxRetries={3} retryDelay={1000}>
 *   <APIDataComponent />
 * </NetworkErrorBoundary>
 * 
 * @example
 * <NetworkErrorBoundary 
 *   onError={(error) => logToMonitoring(error)}
 *   onRetry={(count) => analytics.track('retry_attempt', { count })}
 * >
 *   <DataFetchingComponent />
 * </NetworkErrorBoundary>
 */
export class NetworkErrorBoundary extends Component<NetworkErrorBoundaryProps, NetworkErrorBoundaryState> {
  private retryTimeout: NodeJS.Timeout | null = null;
  private isOnline: boolean = true;

  constructor(props: NetworkErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      retryCount: 0,
      errorId: '',
    };
  }

  static getDerivedStateFromError(error: Error): Partial<NetworkErrorBoundaryState> {
    const errorId = `network_error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    return {
      hasError: true,
      error: error as NetworkError,
      errorId,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const networkError = error as NetworkError;
    
    // Enhanced error logging
    console.group(`🌐 Network Error [${this.state.errorId}]`);
    console.error('Error:', networkError);
    console.error('URL:', networkError.url || 'Unknown');
    console.error('Status Code:', networkError.statusCode || 'Unknown');
    console.error('Component Stack:', errorInfo.componentStack);
    console.groupEnd();

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(networkError, errorInfo);
    }

    // Auto-retry for retryable errors
    if (this.isRetryableError(networkError) && this.state.retryCount < (this.props.maxRetries || 3)) {
      this.scheduleRetry();
    }
  }

  componentDidMount() {
    // Monitor online/offline status
    window.addEventListener('online', this.handleOnline);
    window.addEventListener('offline', this.handleOffline);
    this.isOnline = navigator.onLine;
  }

  componentWillUnmount() {
    window.removeEventListener('online', this.handleOnline);
    window.removeEventListener('offline', this.handleOffline);
    if (this.retryTimeout) {
      clearTimeout(this.retryTimeout);
    }
  }

  private handleOnline = () => {
    this.isOnline = true;
    // If we have a network error and we're back online, try to recover
    if (this.state.hasError && this.state.error && this.isNetworkError(this.state.error)) {
      this.handleRetry();
    }
  };

  private handleOffline = () => {
    this.isOnline = false;
  };

  private isNetworkError = (error: NetworkError): boolean => {
    const message = error.message.toLowerCase();
    return (
      message.includes('network') ||
      message.includes('fetch') ||
      message.includes('connection') ||
      error.code === 'NETWORK_ERROR' ||
      error.statusCode === 0 ||
      !this.isOnline
    );
  };

  private isRetryableError = (error: NetworkError): boolean => {
    // Network errors are generally retryable
    if (this.isNetworkError(error)) return true;
    
    // Server errors (5xx) are retryable
    if (error.statusCode && error.statusCode >= 500) return true;
    
    // Rate limiting (429) is retryable
    if (error.statusCode === 429) return true;
    
    // Timeout errors are retryable
    if (error.message.toLowerCase().includes('timeout')) return true;
    
    // Client errors (4xx) are generally not retryable
    if (error.statusCode && error.statusCode >= 400 && error.statusCode < 500) return false;
    
    return error.retryable !== false;
  };

  private getRetryDelay = (retryCount: number): number => {
    const baseDelay = this.props.retryDelay || 1000;
    // Exponential backoff with jitter
    const delay = baseDelay * Math.pow(2, retryCount);
    const jitter = Math.random() * 0.1 * delay;
    return delay + jitter;
  };

  private scheduleRetry = () => {
    const delay = this.getRetryDelay(this.state.retryCount);
    
    this.retryTimeout = setTimeout(() => {
      this.handleRetry();
    }, delay);
  };

  private handleRetry = () => {
    const newRetryCount = this.state.retryCount + 1;
    
    if (this.props.onRetry) {
      this.props.onRetry(newRetryCount);
    }

    console.info(`🔄 Network Error Recovery - Attempt ${newRetryCount}/${this.props.maxRetries || 3}`);

    this.setState({
      hasError: false,
      error: null,
      retryCount: newRetryCount,
    });
  };

  private handleManualRetry = () => {
    if (this.retryTimeout) {
      clearTimeout(this.retryTimeout);
    }
    this.handleRetry();
  };

  private handleReload = () => {
    window.location.reload();
  };

  private categorizeNetworkError = (error: NetworkError) => {
    if (!this.isOnline) {
      return {
        title: 'Sem Conexão com a Internet',
        message: 'Verifique sua conexão com a internet e tente novamente.',
        icon: '📡',
        severity: 'high' as const,
      };
    }

    if (error.statusCode === 0 || this.isNetworkError(error)) {
      return {
        title: 'Problema de Conexão',
        message: 'Não foi possível conectar ao servidor. Verifique sua conexão.',
        icon: '🌐',
        severity: 'medium' as const,
      };
    }

    if (error.statusCode && error.statusCode >= 500) {
      return {
        title: 'Erro do Servidor',
        message: 'O servidor está temporariamente indisponível. Tente novamente em alguns minutos.',
        icon: '🔧',
        severity: 'high' as const,
      };
    }

    if (error.statusCode === 429) {
      return {
        title: 'Muitas Tentativas',
        message: 'Você fez muitas solicitações rapidamente. Aguarde um momento antes de tentar novamente.',
        icon: '⏱️',
        severity: 'medium' as const,
      };
    }

    if (error.statusCode && error.statusCode >= 400) {
      return {
        title: 'Erro na Solicitação',
        message: 'Houve um problema com sua solicitação. Tente novamente.',
        icon: '⚠️',
        severity: 'low' as const,
      };
    }

    return {
      title: 'Erro de Conexão',
      message: 'Ocorreu um problema de rede inesperado.',
      icon: '🚫',
      severity: 'medium' as const,
    };
  };

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    if (this.props.fallback) {
      return this.props.fallback;
    }

    const { error } = this.state;
    if (!error) return null;

    const errorDetails = this.categorizeNetworkError(error);
    const maxRetries = this.props.maxRetries || 3;
    const canRetry = this.isRetryableError(error) && this.state.retryCount < maxRetries;
    const isRetrying = this.retryTimeout !== null;

    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full p-6 space-y-6">
          <div className="text-center">
            <div className="text-4xl mb-4">{errorDetails.icon}</div>
            
            <h1 className="text-xl font-semibold text-gray-900 mb-2">
              {errorDetails.title}
            </h1>
            
            <p className="text-gray-600 mb-4">
              {errorDetails.message}
            </p>

            {/* Network status indicator */}
            <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium mb-4 ${
              this.isOnline 
                ? 'bg-green-100 text-green-800' 
                : 'bg-red-100 text-red-800'
            }`}>
              <div className={`w-2 h-2 rounded-full mr-2 ${
                this.isOnline ? 'bg-green-400' : 'bg-red-400'
              }`} />
              {this.isOnline ? 'Online' : 'Offline'}
            </div>

            {/* Retry information */}
            {this.state.retryCount > 0 && (
              <p className="text-sm text-gray-500 mb-4">
                Tentativa {this.state.retryCount} de {maxRetries}
              </p>
            )}

            {/* Loading state for automatic retry */}
            {isRetrying && (
              <div className="flex items-center justify-center text-sm text-blue-600 mb-4">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                Tentando novamente...
              </div>
            )}

            {/* Development details */}
            {process.env.NODE_ENV === 'development' && (
              <details className="text-left mb-4 p-3 bg-gray-100 rounded text-sm">
                <summary className="cursor-pointer font-medium text-gray-700 mb-2">
                  Detalhes Técnicos (Desenvolvimento)
                </summary>
                <div className="text-xs text-gray-600 space-y-1">
                  <div><strong>ID:</strong> {this.state.errorId}</div>
                  <div><strong>URL:</strong> {error.url || 'N/A'}</div>
                  <div><strong>Status:</strong> {error.statusCode || 'N/A'}</div>
                  <div><strong>Código:</strong> {error.code || 'N/A'}</div>
                  <div><strong>Tentativas:</strong> {this.state.retryCount}/{maxRetries}</div>
                  <div><strong>Online:</strong> {this.isOnline ? 'Sim' : 'Não'}</div>
                  <div><strong>Mensagem:</strong> {error.message}</div>
                </div>
              </details>
            )}
          </div>

          <div className="space-y-3">
            {/* Retry button */}
            {canRetry && !isRetrying && (
              <Button 
                onClick={this.handleManualRetry}
                className="w-full"
                variant="default"
              >
                Tentar Novamente
              </Button>
            )}

            {/* Action buttons */}
            <div className="flex gap-2">
              <Button 
                onClick={this.handleReload}
                className="flex-1"
                variant="outline"
              >
                Recarregar Página
              </Button>
              
              <Button 
                onClick={() => window.history.back()}
                className="flex-1"
                variant="outline"
              >
                Voltar
              </Button>
            </div>

            {/* Network troubleshooting */}
            {!this.isOnline && (
              <div className="text-xs text-gray-600 bg-yellow-50 p-3 rounded border-l-4 border-yellow-400">
                <strong>Dicas para resolver:</strong>
                <ul className="mt-1 ml-4 list-disc">
                  <li>Verifique se o Wi-Fi ou dados móveis estão ativados</li>
                  <li>Tente acessar outros sites para confirmar a conexão</li>
                  <li>Reinicie seu roteador se necessário</li>
                </ul>
              </div>
            )}
          </div>

          {/* Support information */}
          <div className="text-center text-xs text-gray-500 border-t pt-4">
            Se o problema persistir, contate o suporte informando:<br />
            <code className="bg-gray-100 px-2 py-1 rounded">
              {this.state.errorId}
            </code>
          </div>
        </Card>
      </div>
    );
  }
}

/**
 * Higher-order component to wrap components with network error boundary
 */
export const withNetworkErrorBoundary = <P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<NetworkErrorBoundaryProps, 'children'>
) => {
  const WrappedComponent = (props: P) => (
    <NetworkErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </NetworkErrorBoundary>
  );

  WrappedComponent.displayName = `withNetworkErrorBoundary(${Component.displayName || Component.name})`;
  return WrappedComponent;
};

export default NetworkErrorBoundary;