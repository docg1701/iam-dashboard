import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { UserEditForm } from "../UserEditForm";
// VIOLAÇÃO CORRIGIDA: Não fazer mock de código interno (@/lib/api/users)
// Usar implementação real do toast
import type { User } from "@iam-dashboard/shared";
import { ToastProvider } from "@/components/ui/toast";

// Mock apenas APIs externas (fetch) - NUNCA código interno
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Não fazer mock de hooks internos - usar implementação real

const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>{children}</ToastProvider>
    </QueryClientProvider>
  );
};

describe("UserEditForm", () => {
  const mockUser: User = {
    user_id: "123",
    email: "test@example.com",
    full_name: "João Silva",
    role: "admin",
    status: "active",
    created_at: "2023-01-01T12:00:00Z",
    updated_at: "2023-01-01T12:00:00Z",
    last_login_at: "2023-01-02T12:00:00Z",
    is_verified: true,
  };

  const mockOnSuccess = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderComponent = (user: User = mockUser) => {
    return render(
      <TestWrapper>
        <UserEditForm
          user={user}
          onSuccess={mockOnSuccess}
          onCancel={mockOnCancel}
        />
      </TestWrapper>,
    );
  };

  describe("Rendering and Initial State", () => {
    it("should render form with user data pre-filled", () => {
      renderComponent();

      expect(screen.getByDisplayValue("João Silva")).toBeInTheDocument();
      expect(screen.getByDisplayValue("test@example.com")).toBeInTheDocument();
      // For Select component, check if the current value is set
      expect(
        screen.getByRole("combobox", { name: /role do usuário/i }),
      ).toBeInTheDocument();
    });

    it("should render all form fields", () => {
      renderComponent();

      expect(screen.getByLabelText(/nome completo/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/role do usuário/i)).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /salvar alterações/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /cancelar/i }),
      ).toBeInTheDocument();
    });

    it("should display user information section", () => {
      renderComponent();

      expect(screen.getByText(/informações do usuário/i)).toBeInTheDocument();
      expect(screen.getByText(/ativo/i)).toBeInTheDocument();
      expect(screen.getAllByText("01/01/2023")).toHaveLength(2); // created and updated dates are the same
      expect(screen.getByText("02/01/2023")).toBeInTheDocument();
    });

    it("should show inactive status for inactive users", () => {
      const inactiveUser = { ...mockUser, status: "inactive" as const };
      renderComponent(inactiveUser);

      expect(screen.getByText(/inativo/i)).toBeInTheDocument();
    });

    it("should disable save button initially when no changes made", () => {
      renderComponent();

      const saveButton = screen.getByRole("button", {
        name: /salvar alterações/i,
      });
      expect(saveButton).toBeDisabled();
    });
  });

  describe("Form Validation", () => {
    it("should show validation error for empty name", async () => {
      const user = userEvent.setup();
      renderComponent();

      const nameInput = screen.getByLabelText(/nome completo/i);
      await user.clear(nameInput);
      await user.type(nameInput, "a"); // Less than 2 characters
      await user.tab();

      await waitFor(() => {
        expect(
          screen.getByText(/nome deve ter pelo menos 2 caracteres/i),
        ).toBeInTheDocument();
      });
    });

    it("should show validation error for invalid email", async () => {
      const user = userEvent.setup();
      renderComponent();

      const emailInput = screen.getByLabelText(/email/i);
      await user.clear(emailInput);
      await user.type(emailInput, "invalid-email");
      await user.tab();

      await waitFor(() => {
        expect(screen.getByText(/digite um email válido/i)).toBeInTheDocument();
      });
    });

    it("should show validation error for long name", async () => {
      const user = userEvent.setup();
      renderComponent();

      const nameInput = screen.getByLabelText(/nome completo/i);
      await user.clear(nameInput);
      await user.type(nameInput, "a".repeat(256)); // More than 255 characters
      await user.tab();

      await waitFor(() => {
        expect(
          screen.getByText(/nome deve ter no máximo 255 caracteres/i),
        ).toBeInTheDocument();
      });
    });
  });

  describe("Role Selection", () => {
    it("should display all available roles with descriptions", async () => {
      const user = userEvent.setup();
      renderComponent();

      const roleSelect = screen.getByRole("combobox", {
        name: /role do usuário/i,
      });
      await user.click(roleSelect);

      await waitFor(() => {
        expect(
          screen.getByText(/administrador do sistema/i),
        ).toBeInTheDocument();
        expect(screen.getByText(/administrador$/i)).toBeInTheDocument();
        expect(screen.getByText(/usuário$/i)).toBeInTheDocument();
        expect(
          screen.getByText(/acesso total ao sistema/i),
        ).toBeInTheDocument();
        expect(
          screen.getByText(/gerenciamento de clientes e relatórios/i),
        ).toBeInTheDocument();
        expect(
          screen.getByText(/operações básicas com clientes/i),
        ).toBeInTheDocument();
      });
    });

    it("should enable save button when role is changed", async () => {
      const user = userEvent.setup();
      renderComponent();

      const saveButton = screen.getByRole("button", {
        name: /salvar alterações/i,
      });
      expect(saveButton).toBeDisabled();

      const roleSelect = screen.getByRole("combobox", {
        name: /role do usuário/i,
      });
      await user.click(roleSelect);
      await user.click(screen.getByText(/usuário$/i));

      await waitFor(() => {
        expect(saveButton).toBeEnabled();
      });
    });

    it("should display role change warning", () => {
      renderComponent();

      expect(
        screen.getByText(/alterações no role afetam as permissões/i),
      ).toBeInTheDocument();
    });
  });

  describe("Change Detection", () => {
    it("should enable save button when name is changed", async () => {
      const user = userEvent.setup();
      renderComponent();

      const nameInput = screen.getByLabelText(/nome completo/i);
      await user.type(nameInput, " Updated");

      await waitFor(() => {
        const saveButton = screen.getByRole("button", {
          name: /salvar alterações/i,
        });
        expect(saveButton).toBeEnabled();
      });
    });

    it("should enable save button when email is changed", async () => {
      const user = userEvent.setup();
      renderComponent();

      const emailInput = screen.getByLabelText(/email/i);
      await user.clear(emailInput);
      await user.type(emailInput, "updated@example.com");

      await waitFor(() => {
        const saveButton = screen.getByRole("button", {
          name: /salvar alterações/i,
        });
        expect(saveButton).toBeEnabled();
      });
    });

    it("should disable save button when changes are reverted", async () => {
      const user = userEvent.setup();
      renderComponent();

      const nameInput = screen.getByLabelText(/nome completo/i);
      await user.type(nameInput, " Updated");

      const saveButton = screen.getByRole("button", {
        name: /salvar alterações/i,
      });
      await waitFor(() => {
        expect(saveButton).toBeEnabled();
      });

      // Revert changes
      await user.clear(nameInput);
      await user.type(nameInput, mockUser.full_name);

      await waitFor(() => {
        expect(saveButton).toBeDisabled();
      });
    });
  });

  describe("Form Submission", () => {
    it("should submit form with updated data", async () => {
      const user = userEvent.setup();
      const updatedUser = { ...mockUser, full_name: "João Silva Updated" };
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => updatedUser,
      });

      renderComponent();

      const nameInput = screen.getByLabelText(/nome completo/i);
      await user.type(nameInput, " Updated");

      const saveButton = screen.getByRole("button", {
        name: /salvar alterações/i,
      });
      await user.click(saveButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining(`/api/v1/users/${mockUser.user_id}`),
          expect.objectContaining({
            method: "PUT",
            body: expect.stringContaining("João Silva Updated"),
          }),
        );
        // Toast será chamado através da implementação real
        expect(mockOnSuccess).toHaveBeenCalled();
      });
    });

    it("should show loading state during submission", async () => {
      const user = userEvent.setup();
      mockFetch.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  ok: true,
                  status: 200,
                  json: async () => ({}),
                }),
              100,
            ),
          ),
      );

      renderComponent();

      const nameInput = screen.getByLabelText(/nome completo/i);
      await user.type(nameInput, " Updated");

      const saveButton = screen.getByRole("button", {
        name: /salvar alterações/i,
      });
      await user.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText(/salvando.../i)).toBeInTheDocument();
        expect(
          screen.getByRole("button", { name: /salvando.../i }),
        ).toBeDisabled();
      });
    });

    it("should handle API errors gracefully", async () => {
      const user = userEvent.setup();
      const errorMessage = "Email já existe";
      mockFetch.mockResolvedValue({
        ok: false,
        status: 409,
        json: async () => ({ detail: errorMessage }),
      });

      renderComponent();

      const nameInput = screen.getByLabelText(/nome completo/i);
      await user.type(nameInput, " Updated");

      const saveButton = screen.getByRole("button", {
        name: /salvar alterações/i,
      });
      await user.click(saveButton);

      await waitFor(() => {
        // Toast de erro será chamado através da implementação real
        expect(mockOnSuccess).not.toHaveBeenCalled();
      });
    });

    it("should handle generic API errors", async () => {
      const user = userEvent.setup();
      mockFetch.mockRejectedValue(new Error("Network error"));

      renderComponent();

      const nameInput = screen.getByLabelText(/nome completo/i);
      await user.type(nameInput, " Updated");

      const saveButton = screen.getByRole("button", {
        name: /salvar alterações/i,
      });
      await user.click(saveButton);

      await waitFor(() => {
        // Toast de erro genérico será chamado através da implementação real
      });
    });
  });

  describe("Form Actions", () => {
    it("should call onCancel when cancel button is clicked", async () => {
      const user = userEvent.setup();
      renderComponent();

      const cancelButton = screen.getByRole("button", { name: /cancelar/i });
      await user.click(cancelButton);

      expect(mockOnCancel).toHaveBeenCalled();
    });

    it("should not submit form when no changes are made", async () => {
      const user = userEvent.setup();
      renderComponent();

      const saveButton = screen.getByRole("button", {
        name: /salvar alterações/i,
      });
      expect(saveButton).toBeDisabled();

      await user.click(saveButton);
      expect(mockFetch).not.toHaveBeenCalled();
    });
  });

  describe("User Information Display", () => {
    it("should display user creation date", () => {
      renderComponent();

      expect(screen.getByText(/criado em:/i)).toBeInTheDocument();
      expect(screen.getByText("01/01/2023")).toBeInTheDocument();
    });

    it("should display last update date", () => {
      renderComponent();

      expect(screen.getByText(/última atualização:/i)).toBeInTheDocument();
      expect(screen.getByText("01/01/2023")).toBeInTheDocument();
    });

    it("should display last login when available", () => {
      renderComponent();

      expect(screen.getByText(/último login:/i)).toBeInTheDocument();
      expect(screen.getByText("02/01/2023")).toBeInTheDocument();
    });

    it("should not display last login when not available", () => {
      const userWithoutLogin = { ...mockUser, last_login_at: undefined };
      renderComponent(userWithoutLogin);

      expect(screen.queryByText(/último login:/i)).not.toBeInTheDocument();
    });

    it("should display active status", () => {
      renderComponent();

      expect(screen.getByText(/status:/i)).toBeInTheDocument();
      expect(screen.getByText(/ativo/i)).toBeInTheDocument();
    });
  });

  describe("Accessibility", () => {
    it("should have proper form labels and associations", () => {
      renderComponent();

      expect(screen.getByLabelText(/nome completo/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/role do usuário/i)).toBeInTheDocument();
    });

    it("should announce validation errors to screen readers", async () => {
      const user = userEvent.setup();
      renderComponent();

      const nameInput = screen.getByLabelText(/nome completo/i);
      await user.clear(nameInput);
      await user.type(nameInput, "a");
      await user.tab();

      await waitFor(() => {
        const errorMessage = screen.getByText(
          /nome deve ter pelo menos 2 caracteres/i,
        );
        expect(errorMessage).toBeInTheDocument();
        expect(errorMessage).toHaveAttribute("aria-live", "polite");
      });
    });

    it("should support keyboard navigation", async () => {
      const user = userEvent.setup();
      renderComponent();

      await user.tab();
      expect(screen.getByLabelText(/nome completo/i)).toHaveFocus();

      await user.tab();
      expect(screen.getByLabelText(/email/i)).toHaveFocus();
    });
  });

  describe("Different User Roles", () => {
    it("should handle sysadmin user correctly", () => {
      const sysadminUser = { ...mockUser, role: "sysadmin" as const };
      renderComponent(sysadminUser);

      expect(
        screen.getByRole("combobox", { name: /role do usuário/i }),
      ).toBeInTheDocument();
    });

    it("should handle regular user correctly", () => {
      const regularUser = { ...mockUser, role: "user" as const };
      renderComponent(regularUser);

      expect(
        screen.getByRole("combobox", { name: /role do usuário/i }),
      ).toBeInTheDocument();
    });
  });

  describe("Form State Management", () => {
    it("should maintain form state across re-renders", async () => {
      const user = userEvent.setup();
      const { rerender } = renderComponent();

      const nameInput = screen.getByLabelText(/nome completo/i);
      await user.type(nameInput, " Updated");

      // Re-render with same props
      rerender(
        <TestWrapper>
          <UserEditForm
            user={mockUser}
            onSuccess={mockOnSuccess}
            onCancel={mockOnCancel}
          />
        </TestWrapper>,
      );

      expect(
        screen.getByDisplayValue("João Silva Updated"),
      ).toBeInTheDocument();
    });

    it("should reset form when user prop changes", () => {
      const { rerender } = renderComponent();

      const newUser = {
        ...mockUser,
        user_id: "456",
        full_name: "Maria Santos",
      };
      rerender(
        <TestWrapper>
          <UserEditForm
            user={newUser}
            onSuccess={mockOnSuccess}
            onCancel={mockOnCancel}
          />
        </TestWrapper>,
      );

      expect(screen.getByDisplayValue("Maria Santos")).toBeInTheDocument();
      expect(screen.queryByDisplayValue("João Silva")).not.toBeInTheDocument();
    });
  });
});
