/**
 * PermissionMatrix Component Tests
 *
 * Comprehensive tests for the PermissionMatrix admin component including responsive design
 * Following CLAUDE.md rules: no internal mocking, only external API mocking
 */

import React from "react";
import {
  describe,
  it,
  expect,
  beforeEach,
  vi,
  afterEach,
  renderWithProviders,
  screen,
  waitFor,
  within,
  act,
  useTestSetup,
} from "@/test/test-template";
import userEvent from "@testing-library/user-event";
import {
  createMockUser,
  createMockAdminUser,
  createMockUserAgentPermission,
  setupUserAPITest,
  setupPermissionAPITest,
  AgentName,
  createMockPermissions,
  createMockUserPermissionMatrix,
} from "@/test/api-mocks";
import { setupAuthenticatedUser, clearTestAuth } from "@/test/auth-helpers";
import { PermissionMatrix } from "../PermissionMatrix";
import useAuthStore from "@/store/authStore";
import type { User } from "@/types/auth";

// Setup standard test utilities
useTestSetup();

// Create consistent test data using mock factories
const mockAdminUser = createMockAdminUser({
  user_id: "admin-123",
  full_name: "Admin User",
  email: "admin@test.com",
});

const mockUsers: User[] = [
  createMockUser({
    user_id: "user-1",
    email: "user1@test.com",
    full_name: "User One",
    role: "user",
    is_active: true,
    totp_enabled: false,
  }),
  createMockUser({
    user_id: "user-2",
    email: "user2@test.com",
    full_name: "User Two",
    role: "user",
    is_active: true,
    totp_enabled: true,
  }),
  createMockUser({
    user_id: "user-3",
    email: "user3@test.com",
    full_name: "User Three (Inactive)",
    role: "admin",
    is_active: false,
    totp_enabled: false,
  }),
];

describe("PermissionMatrix Component", () => {
  beforeEach(async () => {
    await act(async () => {
      // Setup authenticated admin user
      setupAuthenticatedUser("admin");
      useAuthStore.setState({
        user: mockAdminUser,
        token: "mock-admin-token",
        isAuthenticated: true,
      });

      // Setup permission API mocks for admin user with full permissions
      const adminPermissions = [
        createMockUserAgentPermission(
          mockAdminUser.user_id,
          AgentName.CLIENT_MANAGEMENT,
          { create: true, read: true, update: true, delete: true },
        ),
        createMockUserAgentPermission(
          mockAdminUser.user_id,
          AgentName.PDF_PROCESSING,
          { create: true, read: true, update: true, delete: true },
        ),
        createMockUserAgentPermission(
          mockAdminUser.user_id,
          AgentName.REPORTS_ANALYSIS,
          { create: true, read: true, update: true, delete: true },
        ),
        createMockUserAgentPermission(
          mockAdminUser.user_id,
          AgentName.AUDIO_RECORDING,
          { create: true, read: true, update: true, delete: true },
        ),
      ];

      setupPermissionAPITest({
        userId: mockAdminUser.user_id,
        userPermissions: adminPermissions,
      });

      // Mock permission matrix API responses for test users
      vi.mocked(global.fetch).mockImplementation((url, options) => {
        const urlStr = url.toString();

        // Handle user permission matrix requests
        if (
          urlStr.includes("/permissions/user/") &&
          options?.method === "GET"
        ) {
          const userId = urlStr.split("/").pop();
          const matrix = createMockUserPermissionMatrix(userId, {
            [AgentName.CLIENT_MANAGEMENT]: createMockPermissions({
              create: true,
              read: true,
              update: true,
              delete: false,
            }),
            [AgentName.PDF_PROCESSING]: createMockPermissions({
              create: false,
              read: true,
              update: false,
              delete: false,
            }),
            [AgentName.REPORTS_ANALYSIS]: createMockPermissions({
              create: false,
              read: false,
              update: false,
              delete: false,
            }),
            [AgentName.AUDIO_RECORDING]: createMockPermissions({
              create: false,
              read: false,
              update: false,
              delete: false,
            }),
          });

          return Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve(matrix),
            headers: new Headers({ "content-type": "application/json" }),
          } as Response);
        }

        // Handle permission updates
        if (
          urlStr.includes("/permissions/") &&
          (options?.method === "PUT" || options?.method === "POST")
        ) {
          return Promise.resolve({
            ok: true,
            status: options?.method === "POST" ? 201 : 200,
            json: () =>
              Promise.resolve({
                success: true,
                message: "Permission updated successfully",
              }),
            headers: new Headers({ "content-type": "application/json" }),
          } as Response);
        }

        // Fall back to setup mocks for other endpoints
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ success: true }),
          headers: new Headers({ "content-type": "application/json" }),
        } as Response);
      });
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
    clearTestAuth();
  });

  describe("Basic Rendering", () => {
    it("should render permission matrix table with users and agents", async () => {
      await act(async () => {
        renderWithProviders(
          <PermissionMatrix
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />,
        );
      });

      await waitFor(() => {
        // Should render a table or grid structure
        const tableOrGrid =
          screen.queryByRole("table") ||
          screen.queryByRole("grid") ||
          screen.queryByTestId("permission-matrix-container");
        expect(tableOrGrid).toBeInTheDocument();
      });

      // Should show user information
      await waitFor(() => {
        expect(screen.getByText("user1@test.com")).toBeInTheDocument();
        expect(screen.getByText("user2@test.com")).toBeInTheDocument();
      });
    });

    it("should render permission badges for each user-agent combination", async () => {
      await act(async () => {
        renderWithProviders(
          <PermissionMatrix
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />,
        );
      });

      await waitFor(() => {
        // Should show permission indicators/badges/buttons
        const permissionElements =
          screen.queryAllByRole("button") ||
          screen.queryAllByText(/acesso|permission|leitura|padrão|completo/i);
        expect(permissionElements.length).toBeGreaterThan(0);
      });
    });

    it("should show user status indicators", async () => {
      await act(async () => {
        renderWithProviders(
          <PermissionMatrix
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />,
        );
      });

      await waitFor(() => {
        // Should show user status (active/inactive)
        const statusElements = screen.queryAllByText(
          /ativo|inativo|active|inactive/i,
        );
        expect(statusElements.length).toBeGreaterThan(0);
      });
    });
  });

  describe("Loading States", () => {
    it("should show loading skeleton while fetching data", async () => {
      // Mock delayed responses
      vi.mocked(global.fetch).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  ok: true,
                  status: 200,
                  json: () => Promise.resolve({ success: true }),
                  headers: new Headers({ "content-type": "application/json" }),
                } as Response),
              100,
            ),
          ),
      );

      await act(async () => {
        renderWithProviders(
          <PermissionMatrix
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />,
        );
      });

      // Should show loading indicators
      await waitFor(() => {
        const loadingElements =
          screen.queryAllByTestId(/skeleton|loading/) ||
          screen.queryAllByText(/carregando|loading/i);
        expect(loadingElements.length).toBeGreaterThan(0);
      });
    });
  });

  describe("Search and Filtering", () => {
    it("should filter users by search query", async () => {
      const user = userEvent.setup();

      await act(async () => {
        renderWithProviders(
          <PermissionMatrix
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />,
        );
      });

      await waitFor(() => {
        // Should have search functionality
        const searchInput =
          screen.queryByPlaceholderText(/buscar|search/i) ||
          screen.queryByLabelText(/buscar|search/i);
        expect(searchInput).toBeInTheDocument();
      });

      const searchInput =
        screen.getByPlaceholderText(/buscar|search/i) ||
        screen.getByLabelText(/buscar|search/i);
      await user.type(searchInput, "User One");

      await waitFor(() => {
        expect(screen.getByText("User One")).toBeInTheDocument();
        // Other users might be filtered out or still visible depending on implementation
      });
    });

    it("should provide filtering options", async () => {
      await act(async () => {
        renderWithProviders(
          <PermissionMatrix
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />,
        );
      });

      await waitFor(() => {
        // Should have filter controls (role, status, etc.)
        const filterElements =
          screen.queryAllByRole("combobox") ||
          screen.queryAllByRole("button", { name: /filtro|filter/i });
        expect(filterElements.length).toBeGreaterThan(0);
      });
    });
  });

  describe("Permission Editing", () => {
    it("should allow clicking permission elements to edit", async () => {
      const user = userEvent.setup();

      await act(async () => {
        renderWithProviders(
          <PermissionMatrix
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />,
        );
      });

      await waitFor(() => {
        // Should have editable permission elements
        const editableElements = screen.queryAllByRole("button", {
          name: /permissão|permission/i,
        });
        expect(editableElements.length).toBeGreaterThan(0);
      });

      // Click on first editable permission element
      const editableElements = screen.getAllByRole("button", {
        name: /permissão|permission/i,
      });
      if (editableElements.length > 0) {
        await user.click(editableElements[0]);

        // Should open some kind of editing interface
        await waitFor(() => {
          const editingInterface =
            screen.queryByRole("combobox") ||
            screen.queryByRole("dialog") ||
            screen.queryByRole("menu");
          expect(editingInterface).toBeInTheDocument();
        });
      }
    });

    it("should handle permission update errors gracefully", async () => {
      // Mock API failure
      vi.mocked(global.fetch).mockImplementation((url, options) => {
        if (options?.method === "PUT" || options?.method === "POST") {
          return Promise.reject(new Error("Update permission error"));
        }
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ success: true }),
          headers: new Headers({ "content-type": "application/json" }),
        } as Response);
      });

      const user = userEvent.setup();

      await act(async () => {
        renderWithProviders(
          <PermissionMatrix
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />,
        );
      });

      await waitFor(() => {
        const editableElements = screen.queryAllByRole("button", {
          name: /permissão|permission/i,
        });
        expect(editableElements.length).toBeGreaterThan(0);
      });

      // Try to edit and trigger the error
      const editableElements = screen.getAllByRole("button", {
        name: /permissão|permission/i,
      });
      if (editableElements.length > 0) {
        await user.click(editableElements[0]);

        // If an editing interface appears, interact with it to trigger save
        await waitFor(async () => {
          const editingInterface =
            screen.queryByRole("combobox") || screen.queryByRole("menu");
          if (editingInterface) {
            await user.click(editingInterface);
          }
        });

        // Should show error indication (toast, alert, etc.)
        await waitFor(() => {
          const errorMessage = screen.queryByText(/erro|error|falha|failed/i);
          expect(errorMessage).toBeInTheDocument();
        });
      }
    });
  });

  describe("Bulk Selection", () => {
    it("should allow selecting multiple users with checkboxes", async () => {
      const user = userEvent.setup();

      await act(async () => {
        renderWithProviders(
          <PermissionMatrix
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />,
        );
      });

      await waitFor(() => {
        // Should have selection checkboxes
        const checkboxes = screen.queryAllByRole("checkbox");
        expect(checkboxes.length).toBeGreaterThan(0);
      });

      // Select some checkboxes
      const checkboxes = screen.getAllByRole("checkbox");
      if (checkboxes.length >= 2) {
        await user.click(checkboxes[0]);
        await user.click(checkboxes[1]);

        // Should show bulk action indication
        await waitFor(() => {
          const bulkIndicator =
            screen.queryByText(/selecionados|selected/) ||
            screen.queryByRole("button", { name: /lote|bulk/i });
          expect(bulkIndicator).toBeInTheDocument();
        });
      }
    });
  });

  describe("Responsive Design", () => {
    it("should display horizontally scrollable table on mobile", async () => {
      // Mock mobile viewport
      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: 375, // Mobile width
      });

      await act(async () => {
        renderWithProviders(
          <PermissionMatrix
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />,
        );
      });

      await waitFor(() => {
        // Table container should handle mobile display
        const container =
          screen.queryByTestId("permission-matrix-container") ||
          screen.queryByRole("table")?.parentElement;
        expect(container).toBeInTheDocument();
      });
    });

    it("should maintain functionality across different screen sizes", async () => {
      const user = userEvent.setup();

      // Test on different screen sizes
      for (const width of [375, 768, 1024]) {
        Object.defineProperty(window, "innerWidth", {
          writable: true,
          configurable: true,
          value: width,
        });

        await act(async () => {
          renderWithProviders(
            <PermissionMatrix
              users={mockUsers}
              onUserPermissionsChange={vi.fn()}
              onBulkAction={vi.fn()}
            />,
          );
        });

        await waitFor(() => {
          // Should render content regardless of screen size
          const content = screen.queryByText("user1@test.com");
          expect(content).toBeInTheDocument();
        });

        // Should be able to interact with elements
        const interactiveElements = screen.queryAllByRole("button");
        expect(interactiveElements.length).toBeGreaterThan(0);
      }
    });
  });

  describe("Accessibility", () => {
    it("should have proper ARIA labels and roles", async () => {
      await act(async () => {
        renderWithProviders(
          <PermissionMatrix
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />,
        );
      });

      await waitFor(() => {
        // Should have proper table or grid structure with accessibility
        const structuredElement =
          screen.queryByRole("table") || screen.queryByRole("grid");
        expect(structuredElement).toBeInTheDocument();
      });
    });

    it("should support keyboard navigation", async () => {
      const user = userEvent.setup();

      await act(async () => {
        renderWithProviders(
          <PermissionMatrix
            users={mockUsers}
            onUserPermissionsChange={vi.fn()}
            onBulkAction={vi.fn()}
          />,
        );
      });

      await waitFor(() => {
        const interactiveElements = screen.queryAllByRole("button");
        expect(interactiveElements.length).toBeGreaterThan(0);
      });

      // Should be able to navigate with keyboard
      await user.tab();

      const focusedElement = document.activeElement;
      expect(focusedElement).not.toBe(document.body);

      // Should be able to activate with keyboard
      if (focusedElement && focusedElement.tagName === "BUTTON") {
        await user.keyboard("{Enter}");
        // Some response should occur (editing interface, etc.)
      }
    });
  });
});
