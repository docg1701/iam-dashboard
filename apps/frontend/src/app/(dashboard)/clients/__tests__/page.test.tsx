/**
 * Clients Page Comprehensive Tests - Phase 3 Coverage Enhancement
 *
 * Following CLAUDE.md testing directives and login page pattern:
 * - NEVER mock internal components, pages, hooks, or application logic
 * - ONLY mock external APIs (fetch calls, third-party services)
 * - Test real page rendering, state management, and user interactions
 * - Focus on achieving high coverage through comprehensive scenarios
 * - Test user-facing functionality and security flows
 * - Use real router navigation and component behavior
 *
 * Coverage targets:
 * - Page structure and layout: 100%
 * - User interactions: 95%+
 * - Navigation flows: 90%+
 * - Responsive design: 85%+
 * - Accessibility: 90%+
 * - Search functionality: 95%+
 * - Button interactions: 100%
 * - Content validation: 100%
 * - Security considerations: 85%+
 */

import {
  renderWithProviders,
  screen,
  fireEvent,
  waitFor,
  userEvent,
  vi,
  expect,
  describe,
  test,
  useTestSetup,
  mockSuccessfulFetch,
  mockFailedFetch,
  mockNetworkError,
  triggerWindowResize,
} from "@/test/test-template";
import {
  setupAuthenticatedUser,
  setupUnauthenticatedUser,
  clearTestAuth,
} from "@/test/auth-helpers";
import ClientsPage from "../page";
import useAuthStore from "@/store/authStore";

describe("ClientsPage - Comprehensive Coverage", () => {
  useTestSetup();

  const renderClientsPage = (
    userRole: "user" | "admin" | "sysadmin" = "admin",
  ) => {
    setupAuthenticatedUser(userRole);
    return renderWithProviders(<ClientsPage />);
  };

  const renderUnauthenticatedClientsPage = () => {
    setupUnauthenticatedUser();
    return renderWithProviders(<ClientsPage />);
  };

  describe("Page Structure and Layout", () => {
    test("renders complete page structure with proper semantic hierarchy", () => {
      renderClientsPage();

      // Main heading structure
      expect(
        screen.getByRole("heading", { level: 1, name: /clientes/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByText(/gerencie os clientes registrados no sistema/i),
      ).toBeInTheDocument();

      // Check header icon is present
      const usersIcons = document.querySelectorAll('[class*="lucide-users"]');
      expect(usersIcons.length).toBeGreaterThan(0);

      // Verify main container has proper responsive classes
      const mainContainer = document.querySelector(".container.mx-auto");
      expect(mainContainer).toBeInTheDocument();
      expect(mainContainer).toHaveClass("px-4", "py-8", "max-w-6xl");
    });

    test("renders header action section with all interactive elements", () => {
      renderClientsPage();

      // Header button with icon
      const headerButton = screen.getByRole("button", {
        name: /novo cliente/i,
      });
      expect(headerButton).toBeInTheDocument();
      expect(headerButton).toHaveClass("flex", "items-center", "gap-2");

      // Check Plus icon is present
      const plusIcons = document.querySelectorAll('[class*="lucide-plus"]');
      expect(plusIcons.length).toBeGreaterThan(0);
    });

    test("renders search interface with proper structure", () => {
      renderClientsPage();

      // Search input
      const searchInput = screen.getByPlaceholderText(/buscar clientes/i);
      expect(searchInput).toBeInTheDocument();
      expect(searchInput).toHaveClass("pl-10");

      // Search container
      const searchContainer = document.querySelector(".max-w-md");
      expect(searchContainer).toBeInTheDocument();
      expect(searchContainer).toHaveClass("relative");

      // Search icon
      const searchIcon = document.querySelector('[class*="lucide-search"]');
      expect(searchIcon).toBeInTheDocument();
    });

    test("renders with proper responsive design classes", () => {
      renderClientsPage();

      // Main container
      expect(
        document.querySelector(".container.mx-auto.px-4.py-8.max-w-6xl"),
      ).toBeInTheDocument();

      // Header section
      expect(document.querySelector(".mb-6")).toBeInTheDocument();
      expect(
        document.querySelector(".flex.items-center.justify-between.mb-4"),
      ).toBeInTheDocument();

      // Search section
      expect(document.querySelector(".relative.max-w-md")).toBeInTheDocument();
    });

    test("maintains layout structure across different viewport sizes", () => {
      // Test desktop layout
      triggerWindowResize(1920, 1080);
      renderClientsPage();
      expect(screen.getByText("Clientes")).toBeInTheDocument();

      // Test tablet layout
      triggerWindowResize(768, 1024);
      expect(screen.getByText("Clientes")).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText(/buscar clientes/i),
      ).toBeInTheDocument();

      // Test mobile layout
      triggerWindowResize(375, 667);
      expect(
        screen.getByRole("button", { name: /novo cliente/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /criar primeiro cliente/i }),
      ).toBeInTheDocument();
    });

    test("has proper header section layout with icon and text alignment", () => {
      renderClientsPage();

      // Check text section
      expect(screen.getByText("Clientes")).toBeInTheDocument();
      expect(
        screen.getByText("Gerencie os clientes registrados no sistema"),
      ).toBeInTheDocument();

      // Check that the main header elements exist
      const headerButton = screen.getByRole("button", {
        name: /novo cliente/i,
      });
      expect(headerButton).toBeInTheDocument();

      const searchInput = screen.getByPlaceholderText(/buscar clientes/i);
      expect(searchInput).toBeInTheDocument();
    });
  });

  describe("Empty State Display", () => {
    test("shows complete empty state structure with proper Card styling", () => {
      renderClientsPage();

      // Main empty state card
      const emptyCard = document.querySelector(".p-8.text-center");
      expect(emptyCard).toBeInTheDocument();

      // Empty state content structure
      expect(
        screen.getByText(/nenhum cliente encontrado/i),
      ).toBeInTheDocument();
      expect(
        screen.getByText(/comece criando o primeiro cliente/i),
      ).toBeInTheDocument();

      // Check flex column layout
      const flexContainer = document.querySelector(
        ".flex.flex-col.items-center.gap-4",
      );
      expect(flexContainer).toBeInTheDocument();
    });

    test("displays empty state icon with proper styling", () => {
      renderClientsPage();

      // Icon container
      const iconContainer = document.querySelector(
        ".p-3.bg-muted.rounded-full",
      );
      expect(iconContainer).toBeInTheDocument();

      // Users icon in empty state
      const emptyStateIcon = iconContainer?.querySelector(
        '[class*="lucide-users"]',
      );
      expect(emptyStateIcon).toBeInTheDocument();
    });

    test("shows empty state call-to-action with proper button styling", () => {
      renderClientsPage();

      const ctaButton = screen.getByRole("button", {
        name: /criar primeiro cliente/i,
      });
      expect(ctaButton).toBeInTheDocument();
      expect(ctaButton).toHaveClass("flex", "items-center", "gap-2");
      expect(ctaButton).toBeEnabled();
    });

    test("displays complete educational information card with proper styling", () => {
      renderClientsPage();

      // Info card with proper background and border
      const infoCard = document.querySelector(
        ".p-4.mt-6.bg-blue-50.border-blue-200",
      );
      expect(infoCard).toBeInTheDocument();

      // Info card title
      const infoTitle = screen.getByText(/sobre o sistema de clientes/i);
      expect(infoTitle).toBeInTheDocument();
      expect(infoTitle).toHaveClass("font-medium", "text-blue-800", "mb-2");

      // Info list
      const infoList = document.querySelector(
        ".text-sm.text-blue-700.space-y-1",
      );
      expect(infoList).toBeInTheDocument();
    });

    test("shows all required educational content points", () => {
      renderClientsPage();

      const requiredInfo = [
        /registre clientes com nome completo, cpf e data de nascimento/i,
        /todas as informações são validadas automaticamente/i,
        /cpf deve ser único no sistema para cada cliente/i,
        /clientes devem ter pelo menos 13 anos de idade/i,
        /todas as operações são registradas no log de auditoria/i,
      ];

      requiredInfo.forEach((info) => {
        expect(screen.getByText(info)).toBeInTheDocument();
      });
    });

    test("validates educational content structure with bullet points", () => {
      renderClientsPage();

      // Each bullet point should start with •
      const bulletPoints = document.querySelectorAll("li");
      expect(bulletPoints.length).toBe(5); // Should have 5 bullet points

      // Check bullet point content
      const listItems = screen.getAllByText(/•/);
      expect(listItems.length).toBe(5);
    });

    test("shows appropriate icon distribution across page sections", () => {
      renderClientsPage();

      // Check that icons are present by checking for elements we know exist
      const headerButton = screen.getByRole("button", {
        name: /novo cliente/i,
      });
      expect(headerButton).toBeInTheDocument();

      const emptyStateButton = screen.getByRole("button", {
        name: /criar primeiro cliente/i,
      });
      expect(emptyStateButton).toBeInTheDocument();

      const searchInput = screen.getByPlaceholderText(/buscar clientes/i);
      expect(searchInput).toBeInTheDocument();

      // Check icons exist in the DOM (they're there as part of the components)
      const allLucideIcons = document.querySelectorAll('[class*="lucide-"]');
      expect(allLucideIcons.length).toBeGreaterThanOrEqual(4); // At least 4 icons should be present
    });
  });

  describe("User Interactions and Navigation", () => {
    test("handles search input interactions comprehensively", async () => {
      renderClientsPage();

      const searchInput = screen.getByPlaceholderText(/buscar clientes/i);

      // Initial state
      expect(searchInput).toHaveValue("");
      expect(searchInput).toBeEnabled();

      // Type different scenarios
      await userEvent.type(searchInput, "João Silva");
      expect(searchInput).toHaveValue("João Silva");

      // Clear and type again
      await userEvent.clear(searchInput);
      expect(searchInput).toHaveValue("");

      // Type special characters
      await userEvent.type(searchInput, "Empresa & Cia. LTDA");
      expect(searchInput).toHaveValue("Empresa & Cia. LTDA");

      // Test with numbers and symbols
      await userEvent.clear(searchInput);
      await userEvent.type(searchInput, "Cliente 123 - (Test)");
      expect(searchInput).toHaveValue("Cliente 123 - (Test)");
    });

    test("handles keyboard navigation in search field", async () => {
      renderClientsPage();

      const searchInput = screen.getByPlaceholderText(/buscar clientes/i);

      // Focus search input
      searchInput.focus();
      expect(document.activeElement).toBe(searchInput);

      // Test keyboard events
      await userEvent.type(searchInput, "test search");

      // Test selection
      await userEvent.keyboard("{Control>}a{/Control}");
      expect(searchInput).toHaveValue("test search");

      // Test deletion
      await userEvent.keyboard("{Backspace}");
      expect(searchInput).toHaveValue("");
    });

    test('header "Novo Cliente" button is clickable and functional', async () => {
      renderClientsPage();

      const headerButton = screen.getByRole("button", {
        name: /novo cliente/i,
      });
      expect(headerButton).toBeEnabled();
      expect(headerButton).toHaveClass("flex", "items-center", "gap-2");

      await userEvent.click(headerButton);

      // Button should remain functional after click
      expect(headerButton).toBeInTheDocument();
      expect(headerButton).toBeEnabled();
    });

    test('empty state "Criar Primeiro Cliente" button is clickable and functional', async () => {
      renderClientsPage();

      const emptyStateButton = screen.getByRole("button", {
        name: /criar primeiro cliente/i,
      });
      expect(emptyStateButton).toBeEnabled();
      expect(emptyStateButton).toHaveClass("flex", "items-center", "gap-2");

      await userEvent.click(emptyStateButton);

      // Button should remain functional after click
      expect(emptyStateButton).toBeInTheDocument();
      expect(emptyStateButton).toBeEnabled();
    });

    test("both navigation buttons work independently", async () => {
      renderClientsPage();

      const headerButton = screen.getByRole("button", {
        name: /novo cliente/i,
      });
      const emptyStateButton = screen.getByRole("button", {
        name: /criar primeiro cliente/i,
      });

      // Both buttons should be functional
      expect(headerButton).toBeEnabled();
      expect(emptyStateButton).toBeEnabled();

      // Click header button first
      await userEvent.click(headerButton);
      expect(headerButton).toBeEnabled();

      // Click empty state button
      await userEvent.click(emptyStateButton);
      expect(emptyStateButton).toBeEnabled();

      // Both should remain functional
      expect(headerButton).toBeInTheDocument();
      expect(emptyStateButton).toBeInTheDocument();
    });

    test("handles button interaction states correctly", async () => {
      renderClientsPage();

      const headerButton = screen.getByRole("button", {
        name: /novo cliente/i,
      });
      const emptyStateButton = screen.getByRole("button", {
        name: /criar primeiro cliente/i,
      });

      // Test hover states (buttons should remain enabled)
      await userEvent.hover(headerButton);
      expect(headerButton).toBeEnabled();

      await userEvent.hover(emptyStateButton);
      expect(emptyStateButton).toBeEnabled();

      // Test focus states
      headerButton.focus();
      expect(document.activeElement).toBe(headerButton);

      emptyStateButton.focus();
      expect(document.activeElement).toBe(emptyStateButton);
    });

    test("validates button accessibility attributes", () => {
      renderClientsPage();

      const headerButton = screen.getByRole("button", {
        name: /novo cliente/i,
      });
      const emptyStateButton = screen.getByRole("button", {
        name: /criar primeiro cliente/i,
      });

      // Both buttons should be accessible
      expect(headerButton).toBeInTheDocument();
      expect(headerButton).toBeEnabled();
      expect(headerButton.getAttribute("type")).not.toBe("submit"); // Should not be form submit

      expect(emptyStateButton).toBeInTheDocument();
      expect(emptyStateButton).toBeEnabled();
      expect(emptyStateButton.getAttribute("type")).not.toBe("submit");
    });
  });

  describe("Navigation Structure", () => {
    test("has proper semantic structure", () => {
      renderClientsPage();

      // Main heading
      expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
        /clientes/i,
      );

      // Section headings
      expect(screen.getByRole("heading", { level: 3 })).toHaveTextContent(
        /nenhum cliente encontrado/i,
      );
      expect(screen.getByRole("heading", { level: 4 })).toHaveTextContent(
        /sobre o sistema de clientes/i,
      );
    });

    test("maintains consistent spacing and layout classes", () => {
      renderClientsPage();

      // Check main container has expected classes
      const mainContainer = document.querySelector(".container.mx-auto");
      expect(mainContainer).toBeInTheDocument();

      // Check buttons have consistent styling
      const buttons = screen.getAllByRole("button");
      buttons.forEach((button) => {
        expect(button).toHaveClass("flex", "items-center", "gap-2");
      });
    });
  });

  describe("Content Validation", () => {
    test("displays complete client system information", () => {
      renderClientsPage();

      const requiredInfo = [
        /registre clientes com nome completo, cpf e data de nascimento/i,
        /todas as informações são validadas automaticamente/i,
        /cpf deve ser único no sistema/i,
        /clientes devem ter pelo menos 13 anos/i,
        /todas as operações são registradas no log/i,
      ];

      requiredInfo.forEach((info) => {
        expect(screen.getByText(info)).toBeInTheDocument();
      });
    });

    test("uses consistent Portuguese language", () => {
      renderClientsPage();

      // Check Portuguese text elements
      expect(screen.getByText("Clientes")).toBeInTheDocument();
      expect(screen.getByText("Novo Cliente")).toBeInTheDocument();
      expect(screen.getByText("Criar Primeiro Cliente")).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText("Buscar clientes..."),
      ).toBeInTheDocument();
    });
  });

  describe("Responsive Design Elements", () => {
    test("has responsive layout classes", () => {
      renderClientsPage();

      const mainContainer = document.querySelector(".max-w-6xl");
      expect(mainContainer).toBeInTheDocument();

      const searchContainer = document.querySelector(".max-w-md");
      expect(searchContainer).toBeInTheDocument();
    });
  });

  describe("Accessibility", () => {
    test("has accessible form controls", () => {
      renderClientsPage();

      const searchInput = screen.getByPlaceholderText(/buscar clientes/i);
      expect(searchInput).toBeInTheDocument();

      const buttons = screen.getAllByRole("button");
      expect(buttons.length).toBe(2); // Header button + empty state button
    });

    test("has proper heading hierarchy", () => {
      renderClientsPage();

      expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
      expect(screen.getByRole("heading", { level: 3 })).toBeInTheDocument();
      expect(screen.getByRole("heading", { level: 4 })).toBeInTheDocument();
    });

    test("uses semantic HTML structure", () => {
      renderClientsPage();

      // Should have proper button roles
      const buttons = screen.getAllByRole("button");
      expect(buttons.length).toBeGreaterThan(0);

      // Should have proper input
      const textbox = screen.getByRole("textbox");
      expect(textbox).toBeInTheDocument();
    });
  });
});
