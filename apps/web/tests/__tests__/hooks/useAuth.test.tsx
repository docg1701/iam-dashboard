import React from 'react';
import { renderHook, act, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { ErrorProvider } from '@/components/errors/ErrorContext';

// Mock Next.js router
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

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <ErrorProvider enableGlobalErrorHandler={false}>
    <AuthProvider>{children}</AuthProvider>
  </ErrorProvider>
);

describe('useAuth hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
    localStorage.clear();
    // Set NODE_ENV to development for proper token handling
    process.env.NODE_ENV = 'development';
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('should provide initial unauthenticated state', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('should handle successful login', async () => {
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      role: 'user' as const,
      is_active: true,
      has_2fa: false,
    };

    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        access_token: 'mock_token',
        refresh_token: 'mock_refresh',
        user: mockUser,
      }),
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login({ 
        email: 'test@example.com', 
        password: 'password' 
      });
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
    expect(localStorage.getItem('access_token')).toBe('mock_token');
  });

  it('should handle login failure', async () => {
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: 'Invalid credentials' }),
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await expect(async () => {
      await act(async () => {
        await result.current.login({ 
          email: 'test@example.com', 
          password: 'wrong' 
        });
      });
    }).rejects.toThrow('Invalid credentials');

    expect(result.current.isAuthenticated).toBe(false);
  });

  it('should handle logout', async () => {
    // Setup initial authenticated state
    localStorage.setItem('access_token', 'mock_token');
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(mockPush).toHaveBeenCalledWith('/login');
  });

  it('should handle token refresh', async () => {
    localStorage.setItem('refresh_token', 'mock_refresh');

    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        access_token: 'new_token',
        refresh_token: 'new_refresh',
      }),
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.refreshToken();
    });

    expect(localStorage.getItem('access_token')).toBe('new_token');
  });

  it('should handle 2FA setup', async () => {
    localStorage.setItem('access_token', 'mock_token');

    const mock2FAData = {
      secret: 'MOCK_SECRET',
      qr_code_url: 'data:image/png;base64,mock',
      backup_codes: ['123456', '789012'],
    };

    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => mock2FAData,
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    let setupResult;
    await act(async () => {
      setupResult = await result.current.setup2FA();
    });

    expect(setupResult).toEqual(mock2FAData);
  });

  it('should handle 2FA enable', async () => {
    localStorage.setItem('access_token', 'mock_token');
    
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      role: 'user' as const,
      is_active: true,
      has_2fa: false,
    };

    // Mock sequence: first get user, then enable 2FA
    global.fetch = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

    const { result } = renderHook(() => useAuth(), { wrapper });

    // Wait for initial auth check
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.enable2FA('123456');
    });

    expect(result.current.user?.has_2fa).toBe(true);
  });
});