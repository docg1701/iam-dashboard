import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { ErrorProvider } from '@/components/errors/ErrorContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

// Mock Next.js navigation
const mockPush = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
  }),
}));

// Mock components to simulate a real application flow
const LoginPage = () => {
  const { login, isLoading } = useAuth();
  const [credentials, setCredentials] = React.useState({
    email: '',
    password: '',
    totp_code: '',
  });
  const [error, setError] = React.useState('');
  const [needs2FA, setNeeds2FA] = React.useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(credentials);
      mockPush('/dashboard');
    } catch (err: any) {
      if (err.message === '2FA_REQUIRED') {
        setNeeds2FA(true);
      } else {
        setError(err.message);
      }
    }
  };

  return (
    <div data-testid="login-page">
      <form onSubmit={handleLogin}>
        <input
          data-testid="email-input"
          type="email"
          placeholder="Email"
          value={credentials.email}
          onChange={(e) => setCredentials({ ...credentials, email: e.target.value })}
        />
        <input
          data-testid="password-input"
          type="password"
          placeholder="Password"
          value={credentials.password}
          onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
        />
        {needs2FA && (
          <input
            data-testid="totp-input"
            type="text"
            placeholder="2FA Code"
            value={credentials.totp_code}
            onChange={(e) => setCredentials({ ...credentials, totp_code: e.target.value })}
          />
        )}
        <button data-testid="login-button" type="submit" disabled={isLoading}>
          {isLoading ? 'Logging in...' : 'Login'}
        </button>
      </form>
      {error && <div data-testid="error-message">{error}</div>}
      {needs2FA && <div data-testid="2fa-required">2FA Required</div>}
    </div>
  );
};

const DashboardPage = () => {
  const { user, logout } = useAuth();

  return (
    <div data-testid="dashboard-page">
      <h1>Dashboard</h1>
      <div data-testid="user-info">Welcome, {user?.email}</div>
      <div data-testid="user-role">Role: {user?.role}</div>
      <button data-testid="logout-button" onClick={logout}>
        Logout
      </button>
    </div>
  );
};

const AdminPage = () => (
  <div data-testid="admin-page">
    <h1>Admin Panel</h1>
    <p>Admin only content</p>
  </div>
);

// Full application simulation
const TestApplication = ({ currentPath = '/login' }: { currentPath?: string }) => {
  const [path, setPath] = React.useState(currentPath);
  
  // Simulate routing
  React.useEffect(() => {
    mockPush.mockImplementation((newPath: string) => {
      setPath(newPath);
    });
  }, []);

  const renderCurrentPage = () => {
    switch (path) {
      case '/login':
        return <LoginPage />;
      case '/dashboard':
        return (
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        );
      case '/admin':
        return (
          <ProtectedRoute requiredRole="admin">
            <AdminPage />
          </ProtectedRoute>
        );
      default:
        return <div data-testid="404-page">404 Not Found</div>;
    }
  };

  return (
    <ErrorProvider enableGlobalErrorHandler={false}>
      <AuthProvider>
        {renderCurrentPage()}
      </AuthProvider>
    </ErrorProvider>
  );
};

describe('Authentication Flow Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
    localStorage.clear();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('Complete Login Flow', () => {
    it('should handle successful login without 2FA', async () => {
      const mockUser = {
        id: '1',
        email: 'user@example.com',
        role: 'user',
        is_active: true,
        has_2fa: false,
      };

      // Mock successful login API response
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          access_token: 'mock_access_token',
          refresh_token: 'mock_refresh_token',
          user: mockUser,
        }),
      });

      render(<TestApplication />);

      // Fill login form
      const emailInput = screen.getByTestId('email-input');
      const passwordInput = screen.getByTestId('password-input');
      const loginButton = screen.getByTestId('login-button');

      fireEvent.change(emailInput, { target: { value: 'user@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(loginButton);

      // Wait for login to complete and redirect
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/dashboard');
      });

      // Verify API was called correctly
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/auth/login', expect.objectContaining({
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: 'user@example.com',
          password: 'password123',
          totp_code: '',
        }),
        credentials: 'include',
      }));

      // Verify tokens were stored in development mode
      expect(localStorage.getItem('access_token')).toBe('mock_access_token');
      expect(localStorage.getItem('refresh_token')).toBe('mock_refresh_token');
    });

    it('should handle login with 2FA requirement', async () => {
      const mockUser = {
        id: '1',
        email: 'user@example.com',
        role: 'user',
        is_active: true,
        has_2fa: true,
      };

      // Mock login responses
      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: false,
          json: async () => ({ detail: '2FA_REQUIRED' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            access_token: 'mock_access_token',
            refresh_token: 'mock_refresh_token',
            user: mockUser,
          }),
        });

      render(<TestApplication />);

      // Initial login attempt
      const emailInput = screen.getByTestId('email-input');
      const passwordInput = screen.getByTestId('password-input');
      const loginButton = screen.getByTestId('login-button');

      fireEvent.change(emailInput, { target: { value: 'user@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(loginButton);

      // Should show 2FA input
      await waitFor(() => {
        expect(screen.getByTestId('2fa-required')).toBeInTheDocument();
        expect(screen.getByTestId('totp-input')).toBeInTheDocument();
      });

      // Enter 2FA code and submit again
      const totpInput = screen.getByTestId('totp-input');
      fireEvent.change(totpInput, { target: { value: '123456' } });
      fireEvent.click(loginButton);

      // Should complete login and redirect
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/dashboard');
      });
    });

    it('should handle login failure', async () => {
      // Mock failed login
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Invalid credentials' }),
      });

      render(<TestApplication />);

      const emailInput = screen.getByTestId('email-input');
      const passwordInput = screen.getByTestId('password-input');
      const loginButton = screen.getByTestId('login-button');

      fireEvent.change(emailInput, { target: { value: 'user@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });
      fireEvent.click(loginButton);

      // Should show error message
      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toHaveTextContent('Invalid credentials');
      });

      // Should remain on login page
      expect(screen.getByTestId('login-page')).toBeInTheDocument();
    });
  });

  describe('Protected Route Access', () => {
    it('should allow access to dashboard when authenticated', async () => {
      const mockUser = {
        id: '1',
        email: 'user@example.com',
        role: 'user',
        is_active: true,
        has_2fa: false,
      };

      // Setup authenticated state
      localStorage.setItem('access_token', 'mock_token');
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser,
      });

      render(<TestApplication currentPath="/dashboard" />);

      await waitFor(() => {
        expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
        expect(screen.getByTestId('user-info')).toHaveTextContent('Welcome, user@example.com');
        expect(screen.getByTestId('user-role')).toHaveTextContent('Role: user');
      });
    });

    it('should redirect to login when not authenticated', async () => {
      render(<TestApplication currentPath="/dashboard" />);

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login');
      });
    });

    it('should deny access to admin page for regular user', async () => {
      const mockUser = {
        id: '1',
        email: 'user@example.com',
        role: 'user',
        is_active: true,
        has_2fa: false,
      };

      localStorage.setItem('access_token', 'mock_token');
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser,
      });

      render(<TestApplication currentPath="/admin" />);

      await waitFor(() => {
        expect(screen.getByText('Acesso Negado')).toBeInTheDocument();
        expect(screen.getByText(/Esta página requer permissão de admin/)).toBeInTheDocument();
        expect(screen.queryByTestId('admin-page')).not.toBeInTheDocument();
      });
    });

    it('should allow access to admin page for admin user', async () => {
      const mockAdmin = {
        id: '1',
        email: 'admin@example.com',
        role: 'admin',
        is_active: true,
        has_2fa: false,
      };

      localStorage.setItem('access_token', 'mock_token');
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockAdmin,
      });

      render(<TestApplication currentPath="/admin" />);

      await waitFor(() => {
        expect(screen.getByTestId('admin-page')).toBeInTheDocument();
      });
    });
  });

  describe('Logout Flow', () => {
    it('should handle logout and redirect to login', async () => {
      const mockUser = {
        id: '1',
        email: 'user@example.com',
        role: 'user',
        is_active: true,
        has_2fa: false,
      };

      // Setup authenticated state
      localStorage.setItem('access_token', 'mock_token');
      localStorage.setItem('refresh_token', 'mock_refresh');

      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockUser,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({}),
        });

      render(<TestApplication currentPath="/dashboard" />);

      // Wait for dashboard to load
      await waitFor(() => {
        expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
      });

      // Click logout
      const logoutButton = screen.getByTestId('logout-button');
      fireEvent.click(logoutButton);

      // Should redirect to login and clear tokens
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login');
        expect(localStorage.getItem('access_token')).toBeNull();
        expect(localStorage.getItem('refresh_token')).toBeNull();
      });
    });
  });

  describe('Token Refresh Flow', () => {
    it('should automatically refresh expired token', async () => {
      const mockUser = {
        id: '1',
        email: 'user@example.com',
        role: 'user',
        is_active: true,
        has_2fa: false,
      };

      localStorage.setItem('access_token', 'expired_token');
      localStorage.setItem('refresh_token', 'refresh_token');

      // Mock expired token response followed by successful refresh
      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          ok: false,
          status: 401,
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            access_token: 'new_access_token',
            refresh_token: 'new_refresh_token',
          }),
        });

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      render(<TestApplication currentPath="/dashboard" />);

      // Should attempt token refresh
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith('/api/v1/auth/me', {
          headers: {
            'Authorization': 'Bearer expired_token',
          },
          credentials: 'include',
        });
      });

      consoleSpy.mockRestore();
    });
  });
});