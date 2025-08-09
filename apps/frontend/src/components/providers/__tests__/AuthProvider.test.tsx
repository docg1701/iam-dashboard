/**
 * AuthProvider Component Tests
 * Tests authentication context provider, role-based access, and integration with Zustand store
 * Following CLAUDE.md rules: no internal mocking, only external API mocking
 */
import {
  AuthProvider,
  useAuthContext,
  RoleGuard,
  ResourceGuard,
} from "../AuthProvider";
import useAuthStore from "@/store/authStore";
import type { User } from "@/types/auth";
import {
  describe,
  it,
  expect,
  vi,
  beforeEach,
  afterEach,
  renderWithProviders,
  screen,
  waitFor,
  act,
  userEvent,
  useTestSetup,
  mockSuccessfulFetch,
  mockFailedFetch,
} from "@/test/test-template";
import {
  createMockUser,
  createMockAdmin,
  createMockSysAdmin,
  setupTestAuth,
  clearTestAuth,
  setupAuthenticatedUser,
  createMockJWTToken,
  createExpiredJWTToken,
} from "@/test/auth-helpers";

// Use standardized test setup
useTestSetup();

describe("AuthProvider", () => {
  describe("Context Provider Setup", () => {
    it("should render children and provide auth context", () => {
      const TestChild = () => {
        const context = useAuthContext();
        return (
          <div>
            <div data-testid="authenticated">
              {context.isAuthenticated.toString()}
            </div>
            <div data-testid="loading">{context.isLoading.toString()}</div>
          </div>
        );
      };

      renderWithProviders(
        <AuthProvider>
          <TestChild />
        </AuthProvider>,
      );

      expect(screen.getByTestId("authenticated")).toHaveTextContent("false");
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });

    it("should throw error when useAuthContext is used outside provider", () => {
      const TestChild = () => {
        useAuthContext();
        return <div>Should not render</div>;
      };

      // Suppress console.error for this test
      const consoleSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});

      expect(() => {
        renderWithProviders(<TestChild />);
      }).toThrow("useAuthContext must be used within an AuthProvider");

      consoleSpy.mockRestore();
    });

    it("should provide all required context values", () => {
      const TestChild = () => {
        const context = useAuthContext();
        return (
          <div>
            <div data-testid="user">{context.user ? "exists" : "null"}</div>
            <div data-testid="authenticated">
              {context.isAuthenticated.toString()}
            </div>
            <div data-testid="loading">{context.isLoading.toString()}</div>
            <div data-testid="is-admin">{context.isAdmin.toString()}</div>
            <div data-testid="is-sysadmin">{context.isSysAdmin.toString()}</div>
            <div data-testid="has-role-function">
              {typeof context.hasRole === "function"
                ? "function"
                : "not-function"}
            </div>
            <div data-testid="has-any-role-function">
              {typeof context.hasAnyRole === "function"
                ? "function"
                : "not-function"}
            </div>
            <div data-testid="can-access-function">
              {typeof context.canAccess === "function"
                ? "function"
                : "not-function"}
            </div>
          </div>
        );
      };

      renderWithProviders(
        <AuthProvider>
          <TestChild />
        </AuthProvider>,
      );

      expect(screen.getByTestId("user")).toHaveTextContent("null");
      expect(screen.getByTestId("authenticated")).toHaveTextContent("false");
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
      expect(screen.getByTestId("is-admin")).toHaveTextContent("false");
      expect(screen.getByTestId("is-sysadmin")).toHaveTextContent("false");
      expect(screen.getByTestId("has-role-function")).toHaveTextContent(
        "function",
      );
      expect(screen.getByTestId("has-any-role-function")).toHaveTextContent(
        "function",
      );
      expect(screen.getByTestId("can-access-function")).toHaveTextContent(
        "function",
      );
    });
  });

  describe("Auth State Propagation", () => {
    it("should propagate authenticated user state to children", () => {
      const mockUser = createMockAdmin();
      const validToken = createMockJWTToken({
        role: "admin",
        user_id: mockUser.user_id,
      });

      const TestChild = () => {
        const context = useAuthContext();
        return (
          <div>
            <div data-testid="authenticated">
              {context.isAuthenticated.toString()}
            </div>
            <div data-testid="user-email">
              {context.user?.email || "no-email"}
            </div>
            <div data-testid="user-role">{context.user?.role || "no-role"}</div>
            <div data-testid="is-admin">{context.isAdmin.toString()}</div>
          </div>
        );
      };

      act(() => {
        setupTestAuth(mockUser, validToken);
      });

      renderWithProviders(
        <AuthProvider>
          <TestChild />
        </AuthProvider>,
      );

      expect(screen.getByTestId("authenticated")).toHaveTextContent("true");
      expect(screen.getByTestId("user-email")).toHaveTextContent(
        "admin@example.com",
      );
      expect(screen.getByTestId("user-role")).toHaveTextContent("admin");
      expect(screen.getByTestId("is-admin")).toHaveTextContent("true");
    });

    it("should propagate loading state to children", () => {
      const TestChild = () => {
        const context = useAuthContext();
        return <div data-testid="loading">{context.isLoading.toString()}</div>;
      };

      act(() => {
        useAuthStore.setState({ isLoading: true });
      });

      renderWithProviders(
        <AuthProvider>
          <TestChild />
        </AuthProvider>,
      );

      expect(screen.getByTestId("loading")).toHaveTextContent("true");
    });

    it("should update context when auth state changes", () => {
      const mockUser = createMockUser();
      const validToken = createMockJWTToken({
        role: "user",
        user_id: mockUser.user_id,
      });

      const TestChild = () => {
        const context = useAuthContext();
        return (
          <div>
            <div data-testid="authenticated">
              {context.isAuthenticated.toString()}
            </div>
            <div data-testid="user-role">{context.user?.role || "no-role"}</div>
          </div>
        );
      };

      const { rerender } = renderWithProviders(
        <AuthProvider>
          <TestChild />
        </AuthProvider>,
      );

      expect(screen.getByTestId("authenticated")).toHaveTextContent("false");
      expect(screen.getByTestId("user-role")).toHaveTextContent("no-role");

      // Login user
      act(() => {
        setupTestAuth(mockUser, validToken);
      });

      rerender(
        <AuthProvider>
          <TestChild />
        </AuthProvider>,
      );

      expect(screen.getByTestId("authenticated")).toHaveTextContent("true");
      expect(screen.getByTestId("user-role")).toHaveTextContent("user");

      // Logout user
      act(() => {
        clearTestAuth();
      });

      rerender(
        <AuthProvider>
          <TestChild />
        </AuthProvider>,
      );

      expect(screen.getByTestId("authenticated")).toHaveTextContent("false");
      expect(screen.getByTestId("user-role")).toHaveTextContent("no-role");
    });
  });

  describe("Role-based Access Functions", () => {
    it("should provide hasRole function that works correctly", () => {
      const mockUser = createMockAdmin();
      const validToken = createMockJWTToken({
        role: "admin",
        user_id: mockUser.user_id,
      });

      const TestChild = () => {
        const context = useAuthContext();
        return (
          <div>
            <div data-testid="has-admin">
              {context.hasRole("admin").toString()}
            </div>
            <div data-testid="has-user">
              {context.hasRole("user").toString()}
            </div>
            <div data-testid="has-sysadmin">
              {context.hasRole("sysadmin").toString()}
            </div>
          </div>
        );
      };

      act(() => {
        setupTestAuth(mockUser, validToken);
      });

      renderWithProviders(
        <AuthProvider>
          <TestChild />
        </AuthProvider>,
      );

      expect(screen.getByTestId("has-admin")).toHaveTextContent("true");
      expect(screen.getByTestId("has-user")).toHaveTextContent("true"); // Admin can access user resources
      expect(screen.getByTestId("has-sysadmin")).toHaveTextContent("false");
    });

    it("should provide hasAnyRole function that works correctly", () => {
      const mockUser = createMockUser();
      const validToken = createMockJWTToken({
        role: "user",
        user_id: mockUser.user_id,
      });

      const TestChild = () => {
        const context = useAuthContext();
        return (
          <div>
            <div data-testid="has-admin-or-user">
              {context.hasAnyRole(["admin", "user"]).toString()}
            </div>
            <div data-testid="has-sysadmin-or-admin">
              {context.hasAnyRole(["sysadmin", "admin"]).toString()}
            </div>
            <div data-testid="has-user-only">
              {context.hasAnyRole(["user"]).toString()}
            </div>
          </div>
        );
      };

      act(() => {
        setupTestAuth(mockUser, validToken);
      });

      renderWithProviders(
        <AuthProvider>
          <TestChild />
        </AuthProvider>,
      );

      expect(screen.getByTestId("has-admin-or-user")).toHaveTextContent("true");
      expect(screen.getByTestId("has-sysadmin-or-admin")).toHaveTextContent(
        "false",
      );
      expect(screen.getByTestId("has-user-only")).toHaveTextContent("true");
    });

    it("should provide isAdmin and isSysAdmin computed properties", () => {
      const sysadminUser = createMockSysAdmin();
      const adminUser = createMockAdmin();
      const regularUser = createMockUser();
      const validToken = createMockJWTToken();

      const TestChild = () => {
        const context = useAuthContext();
        return (
          <div>
            <div data-testid="is-admin">{context.isAdmin.toString()}</div>
            <div data-testid="is-sysadmin">{context.isSysAdmin.toString()}</div>
          </div>
        );
      };

      // Test sysadmin
      act(() => {
        useAuthStore.getState().setUser(sysadminUser);
        useAuthStore.getState().setToken(validToken);
      });

      const { rerender } = renderWithProviders(
        <AuthProvider>
          <TestChild />
        </AuthProvider>,
      );

      expect(screen.getByTestId("is-admin")).toHaveTextContent("true"); // Sysadmin has admin permissions
      expect(screen.getByTestId("is-sysadmin")).toHaveTextContent("true");

      // Test admin
      act(() => {
        setupTestAuth(adminUser, validToken);
      });

      rerender(
        <AuthProvider>
          <TestChild />
        </AuthProvider>,
      );

      expect(screen.getByTestId("is-admin")).toHaveTextContent("true");
      expect(screen.getByTestId("is-sysadmin")).toHaveTextContent("false");

      // Test regular user
      act(() => {
        setupTestAuth(regularUser, validToken);
      });

      rerender(
        <AuthProvider>
          <TestChild />
        </AuthProvider>,
      );

      expect(screen.getByTestId("is-admin")).toHaveTextContent("false");
      expect(screen.getByTestId("is-sysadmin")).toHaveTextContent("false");
    });
  });

  describe("Resource-based Access Control", () => {
    it("should provide canAccess function for resource-based permissions", () => {
      const adminUser = createMockAdmin();
      const validToken = createMockJWTToken({
        role: "admin",
        user_id: adminUser.user_id,
      });

      const TestChild = () => {
        const context = useAuthContext();
        return (
          <div>
            <div data-testid="can-read-users">
              {context.canAccess("users", "read").toString()}
            </div>
            <div data-testid="can-create-users">
              {context.canAccess("users", "create").toString()}
            </div>
            <div data-testid="can-delete-users">
              {context.canAccess("users", "delete").toString()}
            </div>
            <div data-testid="can-read-clients">
              {context.canAccess("clients", "read").toString()}
            </div>
            <div data-testid="can-read-settings">
              {context.canAccess("settings", "read").toString()}
            </div>
            <div data-testid="can-update-settings">
              {context.canAccess("settings", "update").toString()}
            </div>
            <div data-testid="can-read-audit">
              {context.canAccess("audit", "read").toString()}
            </div>
          </div>
        );
      };

      act(() => {
        useAuthStore.getState().setUser(adminUser);
        useAuthStore.getState().setToken(validToken);
      });

      renderWithProviders(
        <AuthProvider>
          <TestChild />
        </AuthProvider>,
      );

      // Admin permissions
      expect(screen.getByTestId("can-read-users")).toHaveTextContent("true");
      expect(screen.getByTestId("can-create-users")).toHaveTextContent("true");
      expect(screen.getByTestId("can-delete-users")).toHaveTextContent("false"); // Only sysadmin
      expect(screen.getByTestId("can-read-clients")).toHaveTextContent("true");
      expect(screen.getByTestId("can-read-settings")).toHaveTextContent("true");
      expect(screen.getByTestId("can-update-settings")).toHaveTextContent(
        "false",
      ); // Only sysadmin
      expect(screen.getByTestId("can-read-audit")).toHaveTextContent("false"); // Only sysadmin
    });

    it("should handle canAccess with default read action", () => {
      const userRole = createMockUser();
      const validToken = createMockJWTToken({
        role: "user",
        user_id: userRole.user_id,
      });

      const TestChild = () => {
        const context = useAuthContext();
        return (
          <div>
            <div data-testid="can-access-clients">
              {context.canAccess("clients").toString()}
            </div>
            <div data-testid="can-access-users">
              {context.canAccess("users").toString()}
            </div>
            <div data-testid="can-access-reports">
              {context.canAccess("reports").toString()}
            </div>
          </div>
        );
      };

      act(() => {
        useAuthStore.getState().setUser(userRole);
        useAuthStore.getState().setToken(validToken);
      });

      renderWithProviders(
        <AuthProvider>
          <TestChild />
        </AuthProvider>,
      );

      expect(screen.getByTestId("can-access-clients")).toHaveTextContent(
        "true",
      );
      expect(screen.getByTestId("can-access-users")).toHaveTextContent("false");
      expect(screen.getByTestId("can-access-reports")).toHaveTextContent(
        "true",
      );
    });

    it("should return false for canAccess when user is not authenticated", () => {
      const TestChild = () => {
        const context = useAuthContext();
        return (
          <div>
            <div data-testid="can-access-anything">
              {context.canAccess("clients", "read").toString()}
            </div>
          </div>
        );
      };

      renderWithProviders(
        <AuthProvider>
          <TestChild />
        </AuthProvider>,
      );

      expect(screen.getByTestId("can-access-anything")).toHaveTextContent(
        "false",
      );
    });

    it("should return false for canAccess with unknown resource", () => {
      const adminUser = createMockAdmin();
      const validToken = createMockJWTToken({
        role: "admin",
        user_id: adminUser.user_id,
      });

      const TestChild = () => {
        const context = useAuthContext();
        return (
          <div>
            <div data-testid="can-access-unknown">
              {context.canAccess("unknown-resource", "read").toString()}
            </div>
          </div>
        );
      };

      act(() => {
        useAuthStore.getState().setUser(adminUser);
        useAuthStore.getState().setToken(validToken);
      });

      renderWithProviders(
        <AuthProvider>
          <TestChild />
        </AuthProvider>,
      );

      expect(screen.getByTestId("can-access-unknown")).toHaveTextContent(
        "false",
      );
    });
  });

  describe("Token Refresh Functionality", () => {
    it("should auto-refresh expired token on mount", async () => {
      const mockUser = createMockAdmin();
      const expiredToken = createExpiredJWTToken({
        role: "admin",
        user_id: mockUser.user_id,
      });
      const newToken = createMockJWTToken({
        role: "admin",
        user_id: mockUser.user_id,
      });

      act(() => {
        setupTestAuth(mockUser, expiredToken);
      });

      // Mock successful token refresh
      mockSuccessfulFetch("/auth/refresh", {
        access_token: newToken,
        token_type: "bearer",
        expires_in: 3600,
      });

      const TestChild = () => {
        const context = useAuthContext();
        return (
          <div data-testid="authenticated">
            {context.isAuthenticated.toString()}
          </div>
        );
      };

      renderWithProviders(
        <AuthProvider>
          <TestChild />
        </AuthProvider>,
      );

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining("/auth/refresh"),
          expect.objectContaining({
            method: "POST",
            headers: expect.objectContaining({
              Authorization: `Bearer ${expiredToken}`,
            }),
          }),
        );
      });

      // Should remain authenticated after refresh
      expect(screen.getByTestId("authenticated")).toHaveTextContent("true");
    });

    it("should logout when token refresh fails", async () => {
      const mockUser = createMockAdmin();
      const expiredToken = createExpiredJWTToken({
        role: "admin",
        user_id: mockUser.user_id,
      });

      act(() => {
        setupTestAuth(mockUser, expiredToken);
      });

      // Mock failed token refresh
      mockFailedFetch("/auth/refresh", "Token refresh failed", 401);

      const TestChild = () => {
        const context = useAuthContext();
        return (
          <div>
            <div data-testid="authenticated">
              {context.isAuthenticated.toString()}
            </div>
            <div data-testid="user">{context.user ? "exists" : "null"}</div>
          </div>
        );
      };

      renderWithProviders(
        <AuthProvider>
          <TestChild />
        </AuthProvider>,
      );

      await waitFor(() => {
        expect(screen.getByTestId("authenticated")).toHaveTextContent("false");
        expect(screen.getByTestId("user")).toHaveTextContent("null");
      });
    });

    it("should handle interval-based token refresh", async () => {
      vi.useFakeTimers();

      const mockUser = createMockAdmin();
      const expiredToken = createExpiredJWTToken({
        role: "admin",
        user_id: mockUser.user_id,
      });
      const newToken = createMockJWTToken({
        role: "admin",
        user_id: mockUser.user_id,
      });

      act(() => {
        setupTestAuth(mockUser, expiredToken);
      });

      // Mock successful token refresh
      mockSuccessfulFetch("/auth/refresh", {
        access_token: newToken,
        token_type: "bearer",
        expires_in: 3600,
      });

      const TestChild = () => {
        const context = useAuthContext();
        return (
          <div data-testid="authenticated">
            {context.isAuthenticated.toString()}
          </div>
        );
      };

      renderWithProviders(
        <AuthProvider>
          <TestChild />
        </AuthProvider>,
      );

      // Fast forward 5 minutes to trigger interval
      await act(async () => {
        vi.advanceTimersByTime(5 * 60 * 1000);
        await vi.runOnlyPendingTimersAsync();
      });

      // Should call refresh due to interval
      expect(global.fetch).toHaveBeenCalled();

      vi.useRealTimers();
    });

    it("should cleanup interval on unmount", async () => {
      vi.useFakeTimers();

      const mockUser = createMockAdmin();
      const validToken = createMockJWTToken({
        role: "admin",
        user_id: mockUser.user_id,
      });

      act(() => {
        setupTestAuth(mockUser, validToken);
      });

      const TestChild = () => {
        const context = useAuthContext();
        return (
          <div data-testid="authenticated">
            {context.isAuthenticated.toString()}
          </div>
        );
      };

      const { unmount } = renderWithProviders(
        <AuthProvider>
          <TestChild />
        </AuthProvider>,
      );

      unmount();

      // Fast forward time after unmount
      await act(async () => {
        vi.advanceTimersByTime(10 * 60 * 1000);
        await vi.runAllTimersAsync();
      });

      // Should not call refresh after unmount
      expect(global.fetch).not.toHaveBeenCalled();

      vi.useRealTimers();
    });
  });
});

describe("RoleGuard Component", () => {
  it("should render children when user has required role", () => {
    const adminUser = createMockAdmin();
    const validToken = createMockJWTToken({
      role: "admin",
      user_id: adminUser.user_id,
    });

    act(() => {
      setupTestAuth(adminUser, validToken);
    });

    renderWithProviders(
      <AuthProvider>
        <RoleGuard roles={["admin"]}>
          <div data-testid="protected-content">Conteúdo de Admin</div>
        </RoleGuard>
      </AuthProvider>,
    );

    expect(screen.getByTestId("protected-content")).toBeInTheDocument();
    expect(screen.getByText("Conteúdo de Admin")).toBeInTheDocument();
  });

  it("should render fallback when user lacks required role", () => {
    const userRole = createMockUser();
    const validToken = createMockJWTToken({
      role: "user",
      user_id: userRole.user_id,
    });

    act(() => {
      setupTestAuth(userRole, validToken);
    });

    renderWithProviders(
      <AuthProvider>
        <RoleGuard
          roles={["admin"]}
          fallback={<div data-testid="access-denied">Acesso Negado</div>}
        >
          <div data-testid="protected-content">Conteúdo de Admin</div>
        </RoleGuard>
      </AuthProvider>,
    );

    expect(screen.queryByTestId("protected-content")).not.toBeInTheDocument();
    expect(screen.getByTestId("access-denied")).toBeInTheDocument();
    expect(screen.getByText("Acesso Negado")).toBeInTheDocument();
  });

  it("should render null fallback by default when access denied", () => {
    const userRole = createMockUser();
    const validToken = createMockJWTToken({
      role: "user",
      user_id: userRole.user_id,
    });

    act(() => {
      setupTestAuth(userRole, validToken);
    });

    renderWithProviders(
      <AuthProvider>
        <RoleGuard roles={["admin"]}>
          <div data-testid="protected-content">Conteúdo de Admin</div>
        </RoleGuard>
      </AuthProvider>,
    );

    expect(screen.queryByTestId("protected-content")).not.toBeInTheDocument();
  });

  it("should handle multiple roles with requireAll=false (default)", () => {
    const userRole = createMockUser();
    const validToken = createMockJWTToken({
      role: "user",
      user_id: userRole.user_id,
    });

    act(() => {
      setupTestAuth(userRole, validToken);
    });

    renderWithProviders(
      <AuthProvider>
        <RoleGuard roles={["admin", "user"]}>
          <div data-testid="protected-content">Conteúdo Multi-Role</div>
        </RoleGuard>
      </AuthProvider>,
    );

    // Should render because user has one of the required roles
    expect(screen.getByTestId("protected-content")).toBeInTheDocument();
  });

  it("should handle multiple roles with requireAll=true", () => {
    const adminUser = createMockAdmin();
    const validToken = createMockJWTToken({
      role: "admin",
      user_id: adminUser.user_id,
    });

    act(() => {
      setupTestAuth(adminUser, validToken);
    });

    renderWithProviders(
      <AuthProvider>
        <RoleGuard roles={["admin", "sysadmin"]} requireAll={true}>
          <div data-testid="protected-content">Conteúdo Restrito</div>
        </RoleGuard>
      </AuthProvider>,
    );

    // Should not render because admin doesn't have sysadmin role
    expect(screen.queryByTestId("protected-content")).not.toBeInTheDocument();
  });

  it("should work with sysadmin having all permissions", () => {
    const sysadminUser = createMockSysAdmin();
    const validToken = createMockJWTToken({
      role: "sysadmin",
      user_id: sysadminUser.user_id,
    });

    act(() => {
      setupTestAuth(sysadminUser, validToken);
    });

    renderWithProviders(
      <AuthProvider>
        <RoleGuard roles={["admin", "sysadmin"]} requireAll={true}>
          <div data-testid="protected-content">Conteúdo Super Restrito</div>
        </RoleGuard>
      </AuthProvider>,
    );

    // Should render because sysadmin has both admin and sysadmin permissions
    expect(screen.getByTestId("protected-content")).toBeInTheDocument();
  });
});

describe("ResourceGuard Component", () => {
  it("should render children when user has resource access", () => {
    const adminUser = createMockAdmin();
    const validToken = createMockJWTToken({
      role: "admin",
      user_id: adminUser.user_id,
    });

    act(() => {
      setupTestAuth(adminUser, validToken);
    });

    renderWithProviders(
      <AuthProvider>
        <ResourceGuard resource="users" action="read">
          <div data-testid="user-list">Lista de Usuários</div>
        </ResourceGuard>
      </AuthProvider>,
    );

    expect(screen.getByTestId("user-list")).toBeInTheDocument();
    expect(screen.getByText("Lista de Usuários")).toBeInTheDocument();
  });

  it("should render fallback when user lacks resource access", () => {
    const userRole = createMockUser();
    const validToken = createMockJWTToken({
      role: "user",
      user_id: userRole.user_id,
    });

    act(() => {
      setupTestAuth(userRole, validToken);
    });

    renderWithProviders(
      <AuthProvider>
        <ResourceGuard
          resource="users"
          action="read"
          fallback={<div data-testid="no-access">Sem Acesso aos Usuários</div>}
        >
          <div data-testid="user-list">Lista de Usuários</div>
        </ResourceGuard>
      </AuthProvider>,
    );

    expect(screen.queryByTestId("user-list")).not.toBeInTheDocument();
    expect(screen.getByTestId("no-access")).toBeInTheDocument();
    expect(screen.getByText("Sem Acesso aos Usuários")).toBeInTheDocument();
  });

  it("should use default read action when action not specified", () => {
    const userRole = createMockUser();
    const validToken = createMockJWTToken({
      role: "user",
      user_id: userRole.user_id,
    });

    act(() => {
      setupTestAuth(userRole, validToken);
    });

    renderWithProviders(
      <AuthProvider>
        <ResourceGuard resource="clients">
          <div data-testid="client-list">Lista de Clientes</div>
        </ResourceGuard>
      </AuthProvider>,
    );

    // User can read clients by default
    expect(screen.getByTestId("client-list")).toBeInTheDocument();
    expect(screen.getByText("Lista de Clientes")).toBeInTheDocument();
  });

  it("should render null fallback by default when access denied", () => {
    const userRole = createMockUser();
    const validToken = createMockJWTToken({
      role: "user",
      user_id: userRole.user_id,
    });

    act(() => {
      setupTestAuth(userRole, validToken);
    });

    renderWithProviders(
      <AuthProvider>
        <ResourceGuard resource="settings" action="update">
          <div data-testid="settings-form">Configurações</div>
        </ResourceGuard>
      </AuthProvider>,
    );

    // User cannot update settings
    expect(screen.queryByTestId("settings-form")).not.toBeInTheDocument();
  });
});

describe("Error Handling and Edge Cases", () => {
  it("should handle context provider without authenticated user", () => {
    const TestChild = () => {
      const context = useAuthContext();
      return (
        <div>
          <div data-testid="can-access-test">
            {context.canAccess("clients", "read").toString()}
          </div>
          <div data-testid="has-role-test">
            {context.hasRole("user").toString()}
          </div>
        </div>
      );
    };

    renderWithProviders(
      <AuthProvider>
        <TestChild />
      </AuthProvider>,
    );

    expect(screen.getByTestId("can-access-test")).toHaveTextContent("false");
    expect(screen.getByTestId("has-role-test")).toHaveTextContent("false");
  });

  it("should handle rapid state changes without errors", () => {
    const TestChild = () => {
      const context = useAuthContext();
      return (
        <div>
          <div data-testid="authenticated">
            {context.isAuthenticated.toString()}
          </div>
          <div data-testid="user-email">
            {context.user?.email || "no-email"}
          </div>
        </div>
      );
    };

    const { rerender } = renderWithProviders(
      <AuthProvider>
        <TestChild />
      </AuthProvider>,
    );

    // Rapid state changes
    const users = [createMockUser(), createMockAdmin(), createMockSysAdmin()];
    const validToken = createMockJWTToken();

    users.forEach((user, index) => {
      act(() => {
        setupTestAuth(user, validToken);
      });

      rerender(
        <AuthProvider>
          <TestChild />
        </AuthProvider>,
      );

      expect(screen.getByTestId("authenticated")).toHaveTextContent("true");
      expect(screen.getByTestId("user-email")).toHaveTextContent(user.email);
    });
  });

  it("should handle component unmounting during token refresh", async () => {
    const mockUser = createMockAdmin();
    const expiredToken = createExpiredJWTToken({
      role: "admin",
      user_id: mockUser.user_id,
    });

    act(() => {
      setupTestAuth(mockUser, expiredToken);
    });

    // Mock slow token refresh
    vi.mocked(global.fetch).mockImplementationOnce(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                ok: true,
                json: () =>
                  Promise.resolve({ access_token: createMockJWTToken() }),
              } as Response),
            100,
          ),
        ),
    );

    const TestChild = () => {
      const context = useAuthContext();
      return (
        <div data-testid="authenticated">
          {context.isAuthenticated.toString()}
        </div>
      );
    };

    const { unmount } = renderWithProviders(
      <AuthProvider>
        <TestChild />
      </AuthProvider>,
    );

    // Unmount before token refresh completes
    unmount();

    // Should not throw errors or cause memory leaks
    await new Promise((resolve) => setTimeout(resolve, 150));
  });
});
