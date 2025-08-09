/**
 * Simple Hooks Integration Tests
 *
 * Basic integration tests for custom hooks without complex permission dependencies
 * Following CLAUDE.md rules: no internal mocking, only external API mocking
 */

import React from "react";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";

// Import store and types
import useAuthStore from "@/store/authStore";
import type { User } from "@/types/auth";

// Test utilities
const createTestQueryClient = () => {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
      mutations: { retry: false },
    },
  });
};

const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

// Mock data
const mockUser: User = {
  user_id: "user-123",
  email: "test@example.com",
  role: "admin",
  is_active: true,
  totp_enabled: false,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
  full_name: "Test User",
};

const mockFetch = vi.fn();

beforeEach(() => {
  global.fetch = mockFetch;

  // Reset auth store
  useAuthStore.setState({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: false,
    requires2FA: false,
    tempToken: null,
  });
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("Auth Store Integration Tests", () => {
  it("initializes with empty state", () => {
    const store = useAuthStore.getState();

    expect(store.user).toBeNull();
    expect(store.token).toBeNull();
    expect(store.isAuthenticated).toBe(false);
    expect(store.isLoading).toBe(false);
  });

  it("updates state when user logs in", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          access_token: "test-token",
          token_type: "bearer",
          expires_in: 3600,
          requires_2fa: false,
          user: {
            user_id: "user-123",
            email: "test@example.com",
            role: "admin",
            full_name: "Test User",
          },
        }),
    } as Response);

    const { login } = useAuthStore.getState();

    await act(async () => {
      await login({ email: "test@example.com", password: "password123" });
    });

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.token).toBe("test-token");
    expect(state.user?.email).toBe("test@example.com");
  });

  it("handles login errors correctly", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Invalid credentials"));

    const { login } = useAuthStore.getState();

    await expect(
      login({ email: "wrong@example.com", password: "wrong" }),
    ).rejects.toThrow("Invalid credentials");

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.token).toBeNull();
  });

  it("handles 2FA login flow", async () => {
    // First request requires 2FA
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          requires_2fa: true,
          temp_token: "temp-token-123",
        }),
    } as Response);

    const { login } = useAuthStore.getState();

    const result = await login({
      email: "test@example.com",
      password: "password123",
    });

    expect(result.requires_2fa).toBe(true);
    expect(result.temp_token).toBe("temp-token-123");

    const state = useAuthStore.getState();
    expect(state.requires2FA).toBe(true);
    expect(state.tempToken).toBe("temp-token-123");
    expect(state.isAuthenticated).toBe(false); // Not authenticated yet
  });

  it("completes 2FA verification", async () => {
    // Set up 2FA state
    useAuthStore.setState({
      requires2FA: true,
      tempToken: "temp-token-123",
      isLoading: false,
    });

    // Mock 2FA verification response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          access_token: "final-token",
          token_type: "bearer",
          expires_in: 3600,
          user: {
            user_id: "user-123",
            email: "test@example.com",
            role: "admin",
            full_name: "Test User",
          },
        }),
    } as Response);

    const { verify2FA } = useAuthStore.getState();

    await act(async () => {
      await verify2FA({ totp_code: "123456" }, "temp-token-123");
    });

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.token).toBe("final-token");
    expect(state.requires2FA).toBe(false);
    expect(state.tempToken).toBeNull();
  });

  it("clears authentication on logout", async () => {
    // Mock logout API call
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ success: true }),
    } as Response);

    // Set authenticated state
    useAuthStore.setState({
      user: mockUser,
      token: "test-token",
      isAuthenticated: true,
      isLoading: false,
    });

    const { logout } = useAuthStore.getState();
    await logout();

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it("checks role permissions correctly", () => {
    // Test admin user
    useAuthStore.setState({
      user: { ...mockUser, role: "admin" },
      isAuthenticated: true,
    });

    const { hasPermission } = useAuthStore.getState();

    expect(hasPermission("user")).toBe(true); // Admin can access user-level
    expect(hasPermission("admin")).toBe(true); // Admin can access admin-level
    expect(hasPermission("sysadmin")).toBe(false); // Admin cannot access sysadmin-level

    // Test regular user
    useAuthStore.setState({
      user: { ...mockUser, role: "user" },
      isAuthenticated: true,
    });

    expect(hasPermission("user")).toBe(true); // User can access user-level
    expect(hasPermission("admin")).toBe(false); // User cannot access admin-level
    expect(hasPermission("sysadmin")).toBe(false); // User cannot access sysadmin-level
  });

  it("denies permissions when not authenticated", () => {
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
    });

    const { hasPermission } = useAuthStore.getState();

    expect(hasPermission("user")).toBe(false);
    expect(hasPermission("admin")).toBe(false);
    expect(hasPermission("sysadmin")).toBe(false);
  });
});

describe("Token Management", () => {
  it("detects expired tokens correctly", () => {
    const { isTokenExpired } = useAuthStore.getState();

    // No token - should be expired
    expect(isTokenExpired()).toBe(true);

    // Valid token (JWT structure with future expiry)
    const futureTime = Math.floor(Date.now() / 1000) + 3600; // 1 hour from now
    const validToken = `header.${btoa(JSON.stringify({ exp: futureTime }))}.signature`;

    useAuthStore.setState({ token: validToken });
    expect(isTokenExpired()).toBe(false);

    // Expired token
    const pastTime = Math.floor(Date.now() / 1000) - 3600; // 1 hour ago
    const expiredToken = `header.${btoa(JSON.stringify({ exp: pastTime }))}.signature`;

    useAuthStore.setState({ token: expiredToken });
    expect(isTokenExpired()).toBe(true);
  });

  it("handles token refresh", async () => {
    useAuthStore.setState({
      user: mockUser,
      token: "old-token",
      isAuthenticated: true,
    });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          access_token: "new-token",
          token_type: "bearer",
          expires_in: 3600,
        }),
    } as Response);

    const { refreshToken } = useAuthStore.getState();

    await act(async () => {
      await refreshToken();
    });

    const state = useAuthStore.getState();
    expect(state.token).toBe("new-token");
    expect(state.isAuthenticated).toBe(true);
  });
});
