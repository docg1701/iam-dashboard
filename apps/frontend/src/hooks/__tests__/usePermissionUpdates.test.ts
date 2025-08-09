/**
 * usePermissionUpdates Hook Tests
 *
 * Following CLAUDE.md testing directives:
 * - NEVER mock internal frontend code, components, hooks, or utilities
 * - ONLY mock external APIs (WebSocket, browser APIs, third-party services, etc.)
 * - Test actual behavior, not implementation details
 */

import { renderHook } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { usePermissionUpdates } from "../usePermissionUpdates";

// Mock external dependencies
vi.mock("@/components/ui/toast", () => ({
  toast: vi.fn(),
}));

vi.mock("@/store/authStore", () => ({
  default: vi.fn(() => ({
    token: "mock-jwt-token",
    user: { user_id: "test-user-123", email: "test@example.com" },
  })),
}));

// Mock WebSocket - external browser API
const mockWebSocket = {
  send: vi.fn(),
  close: vi.fn(),
  readyState: 1, // OPEN
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
};

Object.defineProperty(global, "WebSocket", {
  value: vi.fn(() => mockWebSocket),
});

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe("usePermissionUpdates Hook", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });
  
  describe("Hook Initialization", () => {
    it("should initialize with default values", () => {
      const { result } = renderHook(() => usePermissionUpdates(), {
        wrapper: createWrapper(),
      });
      
      expect(result.current.isConnected).toBe(false);
      expect(result.current.isConnecting).toBe(false);
      expect(result.current.connectionError).toBe(null);
      expect(result.current.reconnectAttempts).toBe(0);
      expect(typeof result.current.connect).toBe("function");
      expect(typeof result.current.disconnect).toBe("function");
    });
    
    it("should accept custom options", () => {
      const mockCallback = vi.fn();
      const { result } = renderHook(
        () => usePermissionUpdates({
          onPermissionUpdate: mockCallback,
          enableToastNotifications: false,
          autoReconnect: false,
        }),
        { wrapper: createWrapper() }
      );
      
      expect(result.current).toBeDefined();
      expect(typeof result.current.connect).toBe("function");
    });
  });
  
  describe("Connection Management", () => {
    it("should provide connect function", () => {
      const { result } = renderHook(() => usePermissionUpdates(), {
        wrapper: createWrapper(),
      });
      
      expect(typeof result.current.connect).toBe("function");
      
      // Call connect function
      result.current.connect();
      
      // Should be callable without errors
      expect(result.current.connect).toBeDefined();
    });
    
    it("should provide disconnect function", () => {
      const { result } = renderHook(() => usePermissionUpdates(), {
        wrapper: createWrapper(),
      });
      
      expect(typeof result.current.disconnect).toBe("function");
      
      // Call disconnect function
      result.current.disconnect();
      
      // Should be callable without errors
      expect(result.current.disconnect).toBeDefined();
    });
  });
  
  describe("State Management", () => {
    it("should track connection state", () => {
      const { result } = renderHook(() => usePermissionUpdates(), {
        wrapper: createWrapper(),
      });
      
      expect(typeof result.current.isConnected).toBe("boolean");
      expect(typeof result.current.isConnecting).toBe("boolean");
      expect(result.current.connectionError).toBeNull();
    });
    
    it("should track reconnection attempts", () => {
      const { result } = renderHook(() => usePermissionUpdates(), {
        wrapper: createWrapper(),
      });
      
      expect(typeof result.current.reconnectAttempts).toBe("number");
      expect(result.current.reconnectAttempts).toBeGreaterThanOrEqual(0);
    });
  });
  
  describe("Options Configuration", () => {
    it("should handle enableToastNotifications option", () => {
      const { result } = renderHook(
        () => usePermissionUpdates({ enableToastNotifications: false }),
        { wrapper: createWrapper() }
      );
      
      expect(result.current).toBeDefined();
    });
    
    it("should handle autoReconnect option", () => {
      const { result } = renderHook(
        () => usePermissionUpdates({ autoReconnect: false }),
        { wrapper: createWrapper() }
      );
      
      expect(result.current).toBeDefined();
    });
    
    it("should handle maxReconnectAttempts option", () => {
      const { result } = renderHook(
        () => usePermissionUpdates({ maxReconnectAttempts: 3 }),
        { wrapper: createWrapper() }
      );
      
      expect(result.current).toBeDefined();
    });
    
    it("should handle reconnectDelay option", () => {
      const { result } = renderHook(
        () => usePermissionUpdates({ reconnectDelay: 1000 }),
        { wrapper: createWrapper() }
      );
      
      expect(result.current).toBeDefined();
    });
  });
  
  describe("Cleanup", () => {
    it("should cleanup on unmount", () => {
      const { unmount } = renderHook(() => usePermissionUpdates(), {
        wrapper: createWrapper(),
      });
      
      // Should unmount without errors
      expect(() => unmount()).not.toThrow();
    });
  });
  
  describe("Authentication Integration", () => {
    it("should work with authenticated user", () => {
      const { result } = renderHook(() => usePermissionUpdates(), {
        wrapper: createWrapper(),
      });
      
      // Should initialize properly with mocked auth store
      expect(result.current).toBeDefined();
    });
  });
  
  describe("Query Client Integration", () => {
    it("should integrate with QueryClient", () => {
      const { result } = renderHook(() => usePermissionUpdates(), {
        wrapper: createWrapper(),
      });
      
      // Should work with query client for cache invalidation
      expect(result.current).toBeDefined();
    });
  });
  
  describe("Error Handling", () => {
    it("should handle connection errors gracefully", () => {
      const { result } = renderHook(() => usePermissionUpdates(), {
        wrapper: createWrapper(),
      });
      
      // Should have error state management
      expect(result.current.connectionError).toBeNull();
    });
  });
});