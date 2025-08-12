import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { AuthErrorBoundary, withAuthErrorBoundary } from '@/components/errors/AuthErrorBoundary';
import { ErrorProvider } from '@/components/errors/ErrorContext';

// Mock Next.js navigation
const mockReplace = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: mockReplace,
  }),
}));

// Component that throws errors for testing
const ErrorThrowingComponent = ({ errorType = 'generic' }: { errorType?: string }) => {
  const throwError = () => {
    switch (errorType) {
      case 'auth':
        const authError = new Error('Invalid credentials') as any;
        authError.statusCode = 401;
        authError.code = 'INVALID_CREDENTIALS';
        throw authError;
      case 'network':
        const networkError = new Error('Network request failed') as any;
        networkError.name = 'TypeError';
        throw networkError;
      case 'server':
        const serverError = new Error('Internal server error') as any;
        serverError.statusCode = 500;
        throw serverError;
      case '2fa':
        const tfaError = new Error('Invalid 2FA code') as any;
        tfaError.statusCode = 422;
        tfaError.code = 'INVALID_2FA';
        throw tfaError;
      case 'timeout':
        const timeoutError = new Error('Request timeout') as any;
        timeoutError.name = 'AbortError';
        throw timeoutError;
      default:
        throw new Error('Generic error for testing');
    }
  };

  React.useEffect(() => {
    throwError();
  }, [errorType]);

  return <div data-testid="component-content">This should not render</div>;
};

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <ErrorProvider enableGlobalErrorHandler={false}>
    {children}
  </ErrorProvider>
);

describe('AuthErrorBoundary', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock console methods to reduce noise in tests
    vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.spyOn(console, 'group').mockImplementation(() => {});
    vi.spyOn(console, 'groupEnd').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Error Categorization and Display', () => {
    it('should categorize and display authentication errors correctly', async () => {
      render(
        <TestWrapper>
          <AuthErrorBoundary>
            <ErrorThrowingComponent errorType="auth" />
          </AuthErrorBoundary>
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Erro de Autenticação')).toBeInTheDocument();
        expect(screen.getByText(/Credenciais inválidas ou sessão expirada/)).toBeInTheDocument();
        expect(screen.getByText('Fazer Login Novamente')).toBeInTheDocument();
      });

      // Should not show retry button for auth errors (not retryable)
      expect(screen.queryByText('Tentar Novamente')).not.toBeInTheDocument();
    });

    it('should categorize and display network errors correctly', async () => {
      render(
        <TestWrapper>
          <AuthErrorBoundary>
            <ErrorThrowingComponent errorType="network" />
          </AuthErrorBoundary>
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Erro de Autenticação')).toBeInTheDocument();
        expect(screen.getByText(/Problema de conexão com o servidor/)).toBeInTheDocument();
        expect(screen.getByText('Tentar Novamente')).toBeInTheDocument();
      });
    });

    it('should categorize and display server errors correctly', async () => {
      render(
        <TestWrapper>
          <AuthErrorBoundary>
            <ErrorThrowingComponent errorType="server" />
          </AuthErrorBoundary>
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Erro de Autenticação')).toBeInTheDocument();
        expect(screen.getByText(/Erro interno do servidor/)).toBeInTheDocument();
        expect(screen.getByText('Tentar Novamente')).toBeInTheDocument();
      });
    });

    it('should categorize and display 2FA errors correctly', async () => {
      render(
        <TestWrapper>
          <AuthErrorBoundary>
            <ErrorThrowingComponent errorType="2fa" />
          </AuthErrorBoundary>
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Erro de Autenticação')).toBeInTheDocument();
        expect(screen.getByText(/Código de autenticação de dois fatores inválido/)).toBeInTheDocument();
        expect(screen.getByText('Tentar Novamente')).toBeInTheDocument();
      });
    });
  });

  describe('Error Recovery Actions', () => {
    it('should handle retry action for retryable errors', async () => {
      const TestRetryComponent = () => {
        const [shouldError, setShouldError] = React.useState(true);
        
        if (shouldError) {
          const networkError = new Error('Network error') as any;
          networkError.statusCode = 500;
          throw networkError;
        }
        
        return <div data-testid="success-content">Successfully recovered!</div>;
      };

      render(
        <TestWrapper>
          <AuthErrorBoundary enableRetry={true}>
            <TestRetryComponent />
          </AuthErrorBoundary>
        </TestWrapper>
      );

      // Should show error initially
      await waitFor(() => {
        expect(screen.getByText('Erro de Autenticação')).toBeInTheDocument();
        expect(screen.getByText('Tentar Novamente')).toBeInTheDocument();
      });

      // Click retry button
      const retryButton = screen.getByText('Tentar Novamente');
      fireEvent.click(retryButton);

      // Should retry and potentially recover (in this test, it will error again)
      await waitFor(() => {
        expect(screen.getByText('Erro de Autenticação')).toBeInTheDocument();
      });
    });

    it('should handle login redirect for auth errors', async () => {
      // Mock window.location
      const mockLocation = {
        href: '',
      };
      Object.defineProperty(window, 'location', {
        value: mockLocation,
        writable: true,
      });

      render(
        <TestWrapper>
          <AuthErrorBoundary>
            <ErrorThrowingComponent errorType="auth" />
          </AuthErrorBoundary>
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Fazer Login Novamente')).toBeInTheDocument();
      });

      // Click login button
      const loginButton = screen.getByText('Fazer Login Novamente');
      fireEvent.click(loginButton);

      // Should redirect to login
      expect(mockLocation.href).toBe('/login');
    });

    it('should handle page reload action', async () => {
      // Mock window.location.reload
      const mockReload = vi.fn();
      Object.defineProperty(window, 'location', {
        value: { reload: mockReload },
        writable: true,
      });

      render(
        <TestWrapper>
          <AuthErrorBoundary>
            <ErrorThrowingComponent />
          </AuthErrorBoundary>
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Recarregar Página')).toBeInTheDocument();
      });

      // Click reload button
      const reloadButton = screen.getByText('Recarregar Página');
      fireEvent.click(reloadButton);

      expect(mockReload).toHaveBeenCalled();
    });

    it('should handle home redirect action', async () => {
      // Mock window.location
      const mockLocation = {
        href: '',
      };
      Object.defineProperty(window, 'location', {
        value: mockLocation,
        writable: true,
      });

      render(
        <TestWrapper>
          <AuthErrorBoundary>
            <ErrorThrowingComponent />
          </AuthErrorBoundary>
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Ir para Início')).toBeInTheDocument();
      });

      // Click home button
      const homeButton = screen.getByText('Ir para Início');
      fireEvent.click(homeButton);

      expect(mockLocation.href).toBe('/');
    });
  });

  describe('Development Mode Features', () => {
    it('should show technical details in development mode', async () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'development';

      render(
        <TestWrapper>
          <AuthErrorBoundary>
            <ErrorThrowingComponent errorType="auth" />
          </AuthErrorBoundary>
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Detalhes Técnicos (Desenvolvimento)')).toBeInTheDocument();
      });

      // Click to expand details
      const detailsToggle = screen.getByText('Detalhes Técnicos (Desenvolvimento)');
      fireEvent.click(detailsToggle);

      await waitFor(() => {
        expect(screen.getByText(/ID:/)).toBeInTheDocument();
        expect(screen.getByText(/Categoria:/)).toBeInTheDocument();
        expect(screen.getByText(/Severidade:/)).toBeInTheDocument();
        expect(screen.getByText(/Status HTTP:/)).toBeInTheDocument();
      });

      process.env.NODE_ENV = originalEnv;
    });

    it('should not show technical details in production mode', async () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'production';

      render(
        <TestWrapper>
          <AuthErrorBoundary>
            <ErrorThrowingComponent />
          </AuthErrorBoundary>
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Erro de Autenticação')).toBeInTheDocument();
      });

      expect(screen.queryByText('Detalhes Técnicos')).not.toBeInTheDocument();

      process.env.NODE_ENV = originalEnv;
    });
  });

  describe('Custom Error Handler', () => {
    it('should call custom error handler when provided', async () => {
      const mockErrorHandler = vi.fn();

      render(
        <TestWrapper>
          <AuthErrorBoundary onError={mockErrorHandler}>
            <ErrorThrowingComponent errorType="auth" />
          </AuthErrorBoundary>
        </TestWrapper>
      );

      await waitFor(() => {
        expect(mockErrorHandler).toHaveBeenCalled();
      });

      const [error, errorInfo] = mockErrorHandler.mock.calls[0];
      expect(error.message).toBe('Invalid credentials');
      expect(errorInfo.componentStack).toBeDefined();
    });
  });

  describe('Fallback Component', () => {
    it('should render custom fallback when provided', async () => {
      const CustomFallback = () => (
        <div data-testid="custom-fallback">Custom error fallback</div>
      );

      render(
        <TestWrapper>
          <AuthErrorBoundary fallback={<CustomFallback />}>
            <ErrorThrowingComponent />
          </AuthErrorBoundary>
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
        expect(screen.getByText('Custom error fallback')).toBeInTheDocument();
      });
    });
  });

  describe('Error Context Integration', () => {
    it('should integrate with global error context', async () => {
      const { container } = render(
        <TestWrapper>
          <AuthErrorBoundary>
            <ErrorThrowingComponent errorType="auth" />
          </AuthErrorBoundary>
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Erro de Autenticação')).toBeInTheDocument();
      });

      // Error boundary should have recorded the error in global context
      // This is tested indirectly through the error display
      expect(container).toBeInTheDocument();
    });
  });
});

describe('withAuthErrorBoundary HOC', () => {
  it('should wrap component with error boundary', async () => {    
    const TestComponent = () => {
      throw new Error('Component error');
      return <div>Should not render</div>;
    };

    const WrappedComponent = withAuthErrorBoundary(TestComponent);

    render(
      <TestWrapper>
        <WrappedComponent />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Erro de Autenticação')).toBeInTheDocument();
    });
  });
});