"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { useError } from '@/components/errors/ErrorContext';
// Enhanced error handling for authentication

// Tipos para o contexto de autenticação
interface User {
  id: string;
  email: string;
  role: 'sysadmin' | 'admin' | 'user';
  is_active: boolean;
  has_2fa: boolean;
}

interface LoginCredentials {
  email: string;
  password: string;
  totp_code?: string;
}

interface AuthError extends Error {
  code?: string;
  statusCode?: number;
  retryable?: boolean;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: AuthError | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  setup2FA: () => Promise<{ secret: string; qr_code_url: string; backup_codes: string[] }>;
  enable2FA: (code: string) => Promise<void>;
  disable2FA: () => Promise<void>;
  clearError: () => void;
  retry: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Hook personalizado para usar o contexto de auth
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider');
  }
  return context;
};

// Hook para verificar permissões
export const usePermissions = () => {
  const { user } = useAuth();
  
  const hasRole = useCallback((requiredRole: 'sysadmin' | 'admin' | 'user') => {
    if (!user) return false;
    
    const roleHierarchy = {
      'user': 1,
      'admin': 2,
      'sysadmin': 3
    };
    
    return roleHierarchy[user.role] >= roleHierarchy[requiredRole];
  }, [user]);

  const isAdmin = useCallback(() => hasRole('admin'), [hasRole]);
  const isSysAdmin = useCallback(() => hasRole('sysadmin'), [hasRole]);

  return {
    hasRole,
    isAdmin,
    isSysAdmin,
  };
};

// Provedor do contexto de autenticação
interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<AuthError | null>(null);
  const [lastFailedAction, setLastFailedAction] = useState<(() => Promise<void>) | null>(null);
  const router = useRouter();
  const { addAuthError } = useError();
  // Enhanced error handling for authentication flows

  const isAuthenticated = !!user;

  // Helper function to create AuthError with proper categorization
  const createAuthError = (error: any, context?: Record<string, any>): AuthError => {
    const authError = error as AuthError;
    
    // Enhance error with additional context
    if (error instanceof Error) {
      authError.name = error.name;
      authError.stack = error.stack;
    }
    
    // Set status code from response if available
    if (context?.response?.status) {
      authError.statusCode = context.response.status;
    }
    
    // Determine if error is retryable
    if (authError.statusCode) {
      // Network errors and server errors are retryable
      authError.retryable = authError.statusCode >= 500 || authError.statusCode === 0;
      
      // Rate limiting is retryable
      if (authError.statusCode === 429) authError.retryable = true;
      
      // Client errors are generally not retryable
      if (authError.statusCode >= 400 && authError.statusCode < 500) {
        authError.retryable = false;
      }
    } else {
      // Network/fetch errors are retryable
      authError.retryable = error.message?.includes('fetch') || error.message?.includes('network');
    }
    
    return authError;
  };

  // Função para fazer login
  const login = async (credentials: LoginCredentials): Promise<void> => {
    const action = async () => {
      try {
        setError(null); // Clear previous errors
        setIsLoading(true);
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout
        
        const response = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(credentials),
          credentials: 'include', // Para cookies httpOnly
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          let errorData;
          try {
            errorData = await response.json();
          } catch {
            errorData = { detail: `HTTP ${response.status}: ${response.statusText}` };
          }

          const authError = createAuthError(new Error(errorData.detail || 'Falha no login'), {
            response,
            credentials: { email: credentials.email }, // Don't log password
          });
          
          authError.statusCode = response.status;
          
          // Set specific error codes
          if (response.status === 401) {
            authError.code = 'INVALID_CREDENTIALS';
          } else if (response.status === 422 && errorData.detail?.includes('2FA')) {
            authError.code = 'MISSING_2FA';
          } else if (response.status === 429) {
            authError.code = 'RATE_LIMITED';
          }

          setError(authError);
          
          // Add to global error context
          addAuthError(authError.message, {
            code: authError.code,
            statusCode: authError.statusCode,
            email: credentials.email,
          });
          
          throw authError;
        }

        const data = await response.json();
        
        // Validate response structure
        if (!data.user || !data.user.id) {
          const validationError = createAuthError(new Error('Invalid response from server'));
          validationError.code = 'INVALID_RESPONSE';
          setError(validationError);
          addAuthError('Invalid response from authentication server');
          throw validationError;
        }
        
        // Armazenar tokens se necessário (desenvolvimento)
        if (process.env.NODE_ENV === 'development') {
          if (data.access_token) localStorage.setItem('access_token', data.access_token);
          if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token);
        }
        
        setUser(data.user);
        setError(null); // Clear any previous errors on success
        
      } catch (error) {
        if (error.name === 'AbortError') {
          const timeoutError = createAuthError(new Error('Timeout na conexão com o servidor'));
          timeoutError.code = 'TIMEOUT';
          timeoutError.retryable = true;
          setError(timeoutError);
          console.error('Timeout na autenticação:', timeoutError);
          throw timeoutError;
        }
        
        // Network/fetch errors
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
          const networkError = createAuthError(error);
          networkError.code = 'NETWORK_ERROR';
          networkError.retryable = true;
          setError(networkError);
          console.error('Erro de conexão durante o login:', networkError);
          throw networkError;
        }
        
        // Re-throw AuthErrors (already handled above)
        if (error instanceof Error && 'statusCode' in error) {
          throw error;
        }
        
        // Handle unexpected errors
        const unexpectedError = createAuthError(error);
        unexpectedError.code = 'UNEXPECTED_ERROR';
        setError(unexpectedError);
        console.error('Erro inesperado durante login:', unexpectedError);
        throw unexpectedError;
      } finally {
        setIsLoading(false);
      }
    };

    setLastFailedAction(() => action);
    return action();
  };

  // Função para fazer logout
  const logout = async (): Promise<void> => {
    try {
      setIsLoading(true);
      
      // Tentar fazer logout no backend
      try {
        const token = localStorage.getItem('access_token');
        if (token) {
          await fetch('/api/v1/auth/logout', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
            },
            credentials: 'include',
          });
        }
      } catch (error) {
        console.warn('Erro ao fazer logout no backend:', error);
      }

      // Limpar estado local
      setUser(null);
      
      // Limpar tokens do localStorage (desenvolvimento)
      if (process.env.NODE_ENV === 'development') {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      }
      
      // Redirecionar para login
      router.push('/login');
    } catch (error) {
      console.error('Erro no logout:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Função para renovar token
  const refreshToken = async (): Promise<void> => {
    try {
      const refresh_token = localStorage.getItem('refresh_token');
      if (!refresh_token) {
        throw new Error('Token de refresh não encontrado');
      }

      const response = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token }),
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Falha ao renovar token');
      }

      const data = await response.json();
      
      // Atualizar tokens
      if (process.env.NODE_ENV === 'development') {
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
      }
    } catch (error) {
      console.error('Erro ao renovar token:', error);
      await logout();
    }
  };

  // Função para configurar 2FA
  const setup2FA = async (): Promise<{ secret: string; qr_code_url: string; backup_codes: string[] }> => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/auth/setup-2fa', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Falha ao configurar 2FA');
      }

      return await response.json();
    } catch (error) {
      console.error('Erro ao configurar 2FA:', error);
      throw error;
    }
  };

  // Função para habilitar 2FA
  const enable2FA = async (code: string): Promise<void> => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/auth/enable-2fa', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ totp_code: code }),
        credentials: 'include',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Falha ao habilitar 2FA');
      }

      // Atualizar user para mostrar que 2FA está habilitado
      if (user) {
        setUser({ ...user, has_2fa: true });
      }
    } catch (error) {
      console.error('Erro ao habilitar 2FA:', error);
      throw error;
    }
  };

  // Função para desabilitar 2FA
  const disable2FA = async (): Promise<void> => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/auth/disable-2fa', {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Falha ao desabilitar 2FA');
      }

      // Atualizar user para mostrar que 2FA está desabilitado
      if (user) {
        setUser({ ...user, has_2fa: false });
      }
    } catch (error) {
      console.error('Erro ao desabilitar 2FA:', error);
      throw error;
    }
  };

  // Verificar se o usuário está autenticado ao carregar a aplicação
  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Em produção, os tokens estarão em cookies httpOnly
        // Em desenvolvimento, verificamos localStorage
        if (process.env.NODE_ENV === 'development') {
          const token = localStorage.getItem('access_token');
          if (!token) {
            setIsLoading(false);
            return;
          }

          // Verificar se o token ainda é válido usando /auth/me endpoint
          try {
            const response = await fetch('/api/v1/auth/me', {
              method: 'GET',
              headers: {
                'Authorization': `Bearer ${token}`,
              },
              credentials: 'include',
            });

            if (response.ok) {
              const data = await response.json();
              setUser(data.user);
            } else if (response.status === 401) {
              // Token invalid/expired, try refresh
              const refreshTokenValue = localStorage.getItem('refresh_token');
              if (refreshTokenValue) {
                await refreshToken();
              } else {
                await logout();
              }
            } else {
              console.error('Auth check failed:', response.status);
              await logout();
            }
          } catch (error) {
            console.error('Erro ao verificar autenticação:', error);
            await logout();
          }
        }
      } catch (error) {
        console.error('Erro ao verificar autenticação:', error);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  // Configurar renovação automática de token
  useEffect(() => {
    if (!isAuthenticated) return;

    // Renovar token a cada 45 minutos (15 min antes da expiração de 1h)
    const interval = setInterval(() => {
      refreshToken();
    }, 45 * 60 * 1000);

    return () => clearInterval(interval);
  }, [isAuthenticated]);

  // Clear error function
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Retry function
  const retry = useCallback(async (): Promise<void> => {
    if (lastFailedAction) {
      return lastFailedAction();
    }
  }, [lastFailedAction]);

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    refreshToken,
    setup2FA,
    enable2FA,
    disable2FA,
    clearError,
    retry,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};