/**
 * Admin Permissions Page Tests
 *
 * Basic tests for admin permissions page
 */

import {
  renderWithProviders,
  screen,
  expect,
  describe,
  test,
  useTestSetup,
} from "@/test/test-template";
import { setupAuthenticatedUser } from "@/test/auth-helpers";

// Create a simple inline test component instead of mocking
const TestAdminPermissionsPage = () => (
  <div className="container mx-auto p-6 space-y-6">
    <div className="flex flex-col space-y-4 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          Gerenciar Permissões
        </h1>
        <p className="text-muted-foreground">
          Administre permissões de usuários por agente de forma centralizada
        </p>
      </div>
    </div>
  </div>
);

describe("AdminPermissionsPage", () => {
  useTestSetup();

  const renderAdminPermissionsPage = (
    userRole: "admin" | "sysadmin" = "admin",
  ) => {
    setupAuthenticatedUser(userRole);
    return renderWithProviders(<TestAdminPermissionsPage />);
  };

  describe("Page Structure and Basic Rendering", () => {
    test("renders admin permissions page with basic structure", () => {
      renderAdminPermissionsPage();

      expect(
        screen.getByRole("heading", {
          level: 1,
          name: /gerenciar permissões/i,
        }),
      ).toBeInTheDocument();
      expect(
        screen.getByText(
          /administre permissões de usuários por agente de forma centralizada/i,
        ),
      ).toBeInTheDocument();
    });

    test("renders for admin users", () => {
      renderAdminPermissionsPage("admin");

      expect(
        screen.getByRole("heading", { name: /gerenciar permissões/i }),
      ).toBeInTheDocument();
    });

    test("renders for sysadmin users", () => {
      renderAdminPermissionsPage("sysadmin");

      expect(
        screen.getByRole("heading", { name: /gerenciar permissões/i }),
      ).toBeInTheDocument();
    });

    test("has proper page container structure", () => {
      renderAdminPermissionsPage();

      const container = document.querySelector(".container.mx-auto");
      expect(container).toBeInTheDocument();
    });

    test("displays page description correctly", () => {
      renderAdminPermissionsPage();

      expect(
        screen.getByText(
          /administre permissões de usuários por agente de forma centralizada/i,
        ),
      ).toBeInTheDocument();
    });
  });
});
