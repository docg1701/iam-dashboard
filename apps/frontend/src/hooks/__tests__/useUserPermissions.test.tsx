/**
 * useUserPermissions Hook Tests
 *
 * Comprehensive tests for the useUserPermissions hook covering all role scenarios
 * Following CLAUDE.md rules: no internal mocking, only external API mocking
 */

import React from "react";
import { renderHook, waitFor } from "@testing-library/react";
import {
  describe,
  it,
  expect,
  beforeEach,
  vi,
  afterEach,
  useTestSetup,
  TestWrapper,
  mockSuccessfulFetch,
  mockFailedFetch,
  mockNetworkError,
} from "@/test/test-template";

import { useUserPermissions } from "../useUserPermissions";
import useAuthStore from "@/store/authStore";
import type { User } from "@/types/auth";
import { AgentName } from "@/types/permissions";

// Use standardized test setup
useTestSetup();

// Mock data for API responses
const mockSysadminUser: User = {
  user_id: "sysadmin-123",
  email: "sysadmin@test.com",
  role: "sysadmin",
  is_active: true,
  totp_enabled: false,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
  full_name: "System Admin",
};

const mockAdminUser: User = {
  user_id: "admin-123",
  email: "admin@test.com",
  role: "admin",
  is_active: true,
  totp_enabled: false,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
  full_name: "Admin User",
};

const mockRegularUser: User = {
  user_id: "user-123",
  email: "user@test.com",
  role: "user",
  is_active: true,
  totp_enabled: false,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
  full_name: "Regular User",
};

const mockUserPermissions = {
  [AgentName.CLIENT_MANAGEMENT]: {
    create: true,
    read: true,
    update: true,
    delete: false,
  },
  [AgentName.PDF_PROCESSING]: {
    create: false,
    read: true,
    update: false,
    delete: false,
  },
  [AgentName.REPORTS_ANALYSIS]: {
    create: false,
    read: true,
    update: false,
    delete: false,
  },
  [AgentName.AUDIO_RECORDING]: {
    create: false,
    read: false,
    update: false,
    delete: false,
  },
};

// API response structure expected by the API client
const createMockApiResponse = (userId: string) => ({
  user_id: userId,
  permissions: [
    {
      agent_name: AgentName.CLIENT_MANAGEMENT,
      permissions: mockUserPermissions[AgentName.CLIENT_MANAGEMENT],
    },
    {
      agent_name: AgentName.PDF_PROCESSING,
      permissions: mockUserPermissions[AgentName.PDF_PROCESSING],
    },
    {
      agent_name: AgentName.REPORTS_ANALYSIS,
      permissions: mockUserPermissions[AgentName.REPORTS_ANALYSIS],
    },
    {
      agent_name: AgentName.AUDIO_RECORDING,
      permissions: mockUserPermissions[AgentName.AUDIO_RECORDING],
    },
  ],
  last_updated: "2024-01-01T00:00:00Z",
});

// Helper function to simulate user authentication via API response
const simulateUserLogin = (user: User) => {
  // Set up user in auth store directly - this simulates successful login
  const authStore = useAuthStore.getState();
  authStore.setUser(user);
  authStore.setToken(`mock-token-${user.user_id}`);
};

describe("useUserPermissions Hook", () => {
  describe("Sysadmin User Behavior", () => {
    beforeEach(() => {
      simulateUserLogin(mockSysadminUser);
    });

    it("should return permissions based on API response for sysadmin", async () => {
      // Mock the permissions API response for sysadmin
      const sysadminApiResponse = createMockApiResponse(
        mockSysadminUser.user_id,
      );
      mockSuccessfulFetch("/api/v1/permissions/users/", sysadminApiResponse);

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Test the actual hook interface - hasPermission takes agent and operation
      expect(
        result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, "create"),
      ).toBe(true);
      expect(
        result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, "read"),
      ).toBe(true);
      expect(
        result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, "update"),
      ).toBe(true);
      expect(
        result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, "delete"),
      ).toBe(false); // Based on mock data

      expect(
        result.current.hasPermission(AgentName.PDF_PROCESSING, "create"),
      ).toBe(false); // Based on mock data
      expect(
        result.current.hasPermission(AgentName.PDF_PROCESSING, "read"),
      ).toBe(true);

      // Test hasAgentPermission for overall agent access
      expect(
        result.current.hasAgentPermission(AgentName.CLIENT_MANAGEMENT),
      ).toBe(true);
      expect(result.current.hasAgentPermission(AgentName.PDF_PROCESSING)).toBe(
        true,
      ); // Has read permission
      expect(result.current.hasAgentPermission(AgentName.AUDIO_RECORDING)).toBe(
        false,
      ); // No permissions
    });

    it("should not be loading for sysadmin permissions after data is fetched", async () => {
      const sysadminApiResponse = createMockApiResponse(
        mockSysadminUser.user_id,
      );
      mockSuccessfulFetch("/api/v1/permissions/users/", sysadminApiResponse);

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });

    it("should have null error for sysadmin on successful API response", async () => {
      const sysadminApiResponse = createMockApiResponse(
        mockSysadminUser.user_id,
      );
      mockSuccessfulFetch("/api/v1/permissions/users/", sysadminApiResponse);

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper,
      });

      await waitFor(() => {
        expect(result.current.error).toBe(null);
      });
    });
  });

  describe("Admin User Behavior", () => {
    beforeEach(() => {
      simulateUserLogin(mockAdminUser);
    });

    it("should return permissions based on API response", async () => {
      const adminApiResponse = createMockApiResponse(mockAdminUser.user_id);
      mockSuccessfulFetch("/api/v1/permissions/users/", adminApiResponse);

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Test permissions based on what the API returns
      expect(
        result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, "create"),
      ).toBe(true);
      expect(
        result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, "read"),
      ).toBe(true);
      expect(
        result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, "update"),
      ).toBe(true);
      expect(
        result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, "delete"),
      ).toBe(false);
    });

    it("should return reports_analysis permissions based on API response", async () => {
      const adminApiResponse = createMockApiResponse(mockAdminUser.user_id);
      mockSuccessfulFetch("/api/v1/permissions/users/", adminApiResponse);

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Test permissions based on API response
      expect(
        result.current.hasPermission(AgentName.REPORTS_ANALYSIS, "create"),
      ).toBe(false);
      expect(
        result.current.hasPermission(AgentName.REPORTS_ANALYSIS, "read"),
      ).toBe(true);
      expect(
        result.current.hasPermission(AgentName.REPORTS_ANALYSIS, "update"),
      ).toBe(false);
      expect(
        result.current.hasPermission(AgentName.REPORTS_ANALYSIS, "delete"),
      ).toBe(false);
    });

    it("should return false for agents without explicit permissions", async () => {
      const emptyPermissions = {
        [AgentName.CLIENT_MANAGEMENT]: {
          create: false,
          read: false,
          update: false,
          delete: false,
        },
        [AgentName.PDF_PROCESSING]: {
          create: false,
          read: false,
          update: false,
          delete: false,
        },
        [AgentName.REPORTS_ANALYSIS]: {
          create: false,
          read: false,
          update: false,
          delete: false,
        },
        [AgentName.AUDIO_RECORDING]: {
          create: false,
          read: false,
          update: false,
          delete: false,
        },
      };

      const emptyApiResponse = {
        user_id: mockAdminUser.user_id,
        permissions: [
          {
            agent_name: AgentName.CLIENT_MANAGEMENT,
            permissions: emptyPermissions[AgentName.CLIENT_MANAGEMENT],
          },
          {
            agent_name: AgentName.PDF_PROCESSING,
            permissions: emptyPermissions[AgentName.PDF_PROCESSING],
          },
          {
            agent_name: AgentName.REPORTS_ANALYSIS,
            permissions: emptyPermissions[AgentName.REPORTS_ANALYSIS],
          },
          {
            agent_name: AgentName.AUDIO_RECORDING,
            permissions: emptyPermissions[AgentName.AUDIO_RECORDING],
          },
        ],
        last_updated: "2024-01-01T00:00:00Z",
      };
      mockSuccessfulFetch("/api/v1/permissions/users/", emptyApiResponse);

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Should return false for agents without permissions
      expect(
        result.current.hasPermission(AgentName.AUDIO_RECORDING, "create"),
      ).toBe(false);
      expect(
        result.current.hasPermission(AgentName.AUDIO_RECORDING, "read"),
      ).toBe(false);
      expect(result.current.hasAgentPermission(AgentName.AUDIO_RECORDING)).toBe(
        false,
      );
    });
  });

  describe("Regular User Behavior", () => {
    beforeEach(() => {
      simulateUserLogin(mockRegularUser);
    });

    it("should fetch and return explicit permissions only", async () => {
      const regularUserApiResponse = createMockApiResponse(
        mockRegularUser.user_id,
      );
      mockSuccessfulFetch("/api/v1/permissions/users/", regularUserApiResponse);

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Should have the permissions from API
      expect(
        result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, "create"),
      ).toBe(true);
      expect(
        result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, "read"),
      ).toBe(true);
      expect(
        result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, "update"),
      ).toBe(true);
      expect(
        result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, "delete"),
      ).toBe(false);

      expect(
        result.current.hasPermission(AgentName.PDF_PROCESSING, "create"),
      ).toBe(false);
      expect(
        result.current.hasPermission(AgentName.PDF_PROCESSING, "read"),
      ).toBe(true);

      expect(
        result.current.hasPermission(AgentName.AUDIO_RECORDING, "create"),
      ).toBe(false);
      expect(
        result.current.hasPermission(AgentName.AUDIO_RECORDING, "read"),
      ).toBe(false);
    });

    it("should be loading while fetching permissions", async () => {
      // Mock delayed response using test template utility
      const regularUserApiResponse = createMockApiResponse(
        mockRegularUser.user_id,
      );

      // Create a delayed promise manually
      vi.mocked(global.fetch).mockImplementationOnce(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  ok: true,
                  status: 200,
                  json: () => Promise.resolve(regularUserApiResponse),
                } as Response),
              100,
            ),
          ),
      );

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper,
      });

      // Should be loading initially
      expect(result.current.isLoading).toBe(true);

      // Wait for loading to finish
      await waitFor(
        () => {
          expect(result.current.isLoading).toBe(false);
        },
        { timeout: 500 },
      );
    });
  });

  describe("Not Authenticated Behavior", () => {
    beforeEach(() => {
      // Clear auth state naturally
      const authStore = useAuthStore.getState();
      authStore.clearAuth();
    });

    it("should return false for all permissions when not authenticated", () => {
      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper,
      });

      // Hook should return default permissions when not authenticated
      expect(
        result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, "read"),
      ).toBe(false);
      expect(
        result.current.hasPermission(AgentName.PDF_PROCESSING, "read"),
      ).toBe(false);
      expect(
        result.current.hasPermission(AgentName.REPORTS_ANALYSIS, "read"),
      ).toBe(false);
      expect(
        result.current.hasPermission(AgentName.AUDIO_RECORDING, "read"),
      ).toBe(false);
    });

    it("should not be loading when not authenticated", () => {
      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper,
      });

      expect(result.current.isLoading).toBe(false);
    });

    it("should not make API calls when not authenticated", () => {
      renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper,
      });

      expect(vi.mocked(global.fetch)).not.toHaveBeenCalled();
    });
  });

  describe("Error Handling", () => {
    beforeEach(() => {
      simulateUserLogin(mockRegularUser);
    });

    it("should handle API errors gracefully", async () => {
      mockNetworkError("/api/v1/permissions/users/", "API Error");

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.error).toBeTruthy();
      expect(
        result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, "read"),
      ).toBe(false);
    });

    it("should handle HTTP error responses", async () => {
      mockFailedFetch("/api/v1/permissions/users/", "Forbidden", 403);

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.error).toBeTruthy();
      expect(
        result.current.hasPermission(AgentName.CLIENT_MANAGEMENT, "read"),
      ).toBe(false);
    });
  });

  describe("Permission Matrix Utilities", () => {
    beforeEach(() => {
      simulateUserLogin(mockRegularUser);
    });

    it("should provide permission matrix for all agents", async () => {
      const regularUserApiResponse = createMockApiResponse(
        mockRegularUser.user_id,
      );
      mockSuccessfulFetch("/api/v1/permissions/users/", regularUserApiResponse);

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const matrix = result.current.getUserMatrix();

      expect(matrix).toBeTruthy();
      expect(matrix?.permissions).toHaveProperty(AgentName.CLIENT_MANAGEMENT);
      expect(matrix?.permissions).toHaveProperty(AgentName.PDF_PROCESSING);
      expect(matrix?.permissions).toHaveProperty(AgentName.REPORTS_ANALYSIS);
      expect(matrix?.permissions).toHaveProperty(AgentName.AUDIO_RECORDING);

      expect(matrix?.permissions[AgentName.CLIENT_MANAGEMENT]).toEqual({
        create: true,
        read: true,
        update: true,
        delete: false,
      });
      expect(matrix?.permissions[AgentName.PDF_PROCESSING]).toEqual({
        create: false,
        read: true,
        update: false,
        delete: false,
      });
    });

    it("should check if user has agent access", async () => {
      const regularUserApiResponse = createMockApiResponse(
        mockRegularUser.user_id,
      );
      mockSuccessfulFetch("/api/v1/permissions/users/", regularUserApiResponse);

      const { result } = renderHook(() => useUserPermissions(), {
        wrapper: TestWrapper,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(
        result.current.hasAgentPermission(AgentName.CLIENT_MANAGEMENT),
      ).toBe(true);
      expect(result.current.hasAgentPermission(AgentName.PDF_PROCESSING)).toBe(
        true,
      );
      expect(result.current.hasAgentPermission(AgentName.AUDIO_RECORDING)).toBe(
        false,
      );
    });
  });
});
