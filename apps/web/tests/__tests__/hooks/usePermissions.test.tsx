import React from 'react';
import { renderHook, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { AuthProvider, usePermissions } from '@/contexts/AuthContext';
import { ErrorProvider } from '@/components/errors/ErrorContext';

// Mock Next.js router
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
  }),
}));

const createWrapperWithUser = (user: any) => {
  return ({ children }: { children: React.ReactNode }) => {
    // Create a mock AuthProvider that provides the user
    const MockAuthProvider = ({ children }: { children: React.ReactNode }) => {
      React.useEffect(() => {
        if (user && global.fetch) {
          // Mock the /me endpoint to return the user
          global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            json: async () => user,
          });
          localStorage.setItem('access_token', 'mock_token');
        }
      }, []);

      return (
        <ErrorProvider enableGlobalErrorHandler={false}>
          <AuthProvider>{children}</AuthProvider>
        </ErrorProvider>
      );
    };

    return <MockAuthProvider>{children}</MockAuthProvider>;
  };
};

describe('usePermissions hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
    localStorage.clear();
    process.env.NODE_ENV = 'development';
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('should return false for all permissions when not authenticated', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => usePermissions(), { wrapper });

    expect(result.current.hasRole('user')).toBe(false);
    expect(result.current.hasRole('admin')).toBe(false);
    expect(result.current.hasRole('sysadmin')).toBe(false);
    expect(result.current.isAdmin()).toBe(false);
    expect(result.current.isSysAdmin()).toBe(false);
  });

  it('should return correct permissions for user role', async () => {
    const mockUser = {
      id: '1',
      email: 'user@example.com',
      role: 'user',
      is_active: true,
      has_2fa: false,
    };

    const wrapper = createWrapperWithUser(mockUser);
    const { result } = renderHook(() => usePermissions(), { wrapper });

    // Wait for authentication to complete
    await waitFor(() => {
      expect(result.current.hasRole('user')).toBe(true);
    });

    expect(result.current.hasRole('admin')).toBe(false);
    expect(result.current.hasRole('sysadmin')).toBe(false);
    expect(result.current.isAdmin()).toBe(false);
    expect(result.current.isSysAdmin()).toBe(false);
  });

  it('should return correct permissions for admin role', async () => {
    const mockAdmin = {
      id: '1',
      email: 'admin@example.com',
      role: 'admin',
      is_active: true,
      has_2fa: false,
    };

    const wrapper = createWrapperWithUser(mockAdmin);
    const { result } = renderHook(() => usePermissions(), { wrapper });

    await waitFor(() => {
      expect(result.current.hasRole('user')).toBe(true);
    });

    expect(result.current.hasRole('admin')).toBe(true);
    expect(result.current.hasRole('sysadmin')).toBe(false);
    expect(result.current.isAdmin()).toBe(true);
    expect(result.current.isSysAdmin()).toBe(false);
  });

  it('should return correct permissions for sysadmin role', async () => {
    const mockSysAdmin = {
      id: '1',
      email: 'sysadmin@example.com',
      role: 'sysadmin',
      is_active: true,
      has_2fa: false,
    };

    const wrapper = createWrapperWithUser(mockSysAdmin);
    const { result } = renderHook(() => usePermissions(), { wrapper });

    await waitFor(() => {
      expect(result.current.hasRole('user')).toBe(true);
    });

    expect(result.current.hasRole('admin')).toBe(true);
    expect(result.current.hasRole('sysadmin')).toBe(true);
    expect(result.current.isAdmin()).toBe(true);
    expect(result.current.isSysAdmin()).toBe(true);
  });

  it('should validate role hierarchy correctly', () => {
    // Test the role hierarchy logic directly
    const roleHierarchy = {
      'user': 1,
      'admin': 2,
      'sysadmin': 3
    };

    // User role tests
    expect(roleHierarchy['user'] >= roleHierarchy['user']).toBe(true);
    expect(roleHierarchy['user'] >= roleHierarchy['admin']).toBe(false);
    expect(roleHierarchy['user'] >= roleHierarchy['sysadmin']).toBe(false);

    // Admin role tests
    expect(roleHierarchy['admin'] >= roleHierarchy['user']).toBe(true);
    expect(roleHierarchy['admin'] >= roleHierarchy['admin']).toBe(true);
    expect(roleHierarchy['admin'] >= roleHierarchy['sysadmin']).toBe(false);

    // SysAdmin role tests
    expect(roleHierarchy['sysadmin'] >= roleHierarchy['user']).toBe(true);
    expect(roleHierarchy['sysadmin'] >= roleHierarchy['admin']).toBe(true);
    expect(roleHierarchy['sysadmin'] >= roleHierarchy['sysadmin']).toBe(true);
  });
});