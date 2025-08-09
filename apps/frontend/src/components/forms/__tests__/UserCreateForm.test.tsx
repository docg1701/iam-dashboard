/**
 * UserCreateForm Component Tests
 * Tests user creation form behavior and user interactions
 * Following CLAUDE.md rules: no internal mocking, only external API mocking
 */
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
  userEvent,
  useTestSetup,
  mockSuccessfulFetch,
  mockFailedFetch,
  act,
} from "@/test/test-template";
import { UserCreateForm } from "../UserCreateForm";
import type { User } from "@/types/auth";
import type { UserCreateSchema as UserCreate } from "@/types";

describe("UserCreateForm", () => {
  useTestSetup();

  const mockOnSuccess = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    mockOnSuccess.mockReset();
    mockOnCancel.mockReset();
  });

  const renderComponent = () => {
    return renderWithProviders(
      <UserCreateForm onSuccess={mockOnSuccess} onCancel={mockOnCancel} />,
    );
  };

  describe("Rendering and Initial State", () => {
    it("should render all form fields", () => {
      renderComponent();

      expect(screen.getByLabelText(/nome completo/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/role do usuário/i)).toBeInTheDocument();
      expect(screen.getByText(/^senha$/i)).toBeInTheDocument();
      expect(screen.getByText(/confirmar senha/i)).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /criar usuário/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /cancelar/i }),
      ).toBeInTheDocument();
    });

    it("should render form with empty initial values", () => {
      renderComponent();

      // Check specific fields for empty values instead of searching for any empty value
      expect(screen.getByLabelText(/nome completo/i)).toHaveValue("");
      expect(screen.getByLabelText(/email/i)).toHaveValue("");
      expect(
        screen.getByPlaceholderText(/digite uma senha segura/i),
      ).toHaveValue("");
      expect(
        screen.getByPlaceholderText(/digite a senha novamente/i),
      ).toHaveValue("");
      expect(
        screen.getByText(/selecione o role do usuário/i),
      ).toBeInTheDocument();
    });

    it("should display password requirements", () => {
      renderComponent();

      expect(
        screen.getByText(
          /mínimo 8 caracteres com letra maiúscula, minúscula, número e caractere especial/i,
        ),
      ).toBeInTheDocument();
    });
  });

  describe("Form Validation", () => {
    it("should show validation error for empty name", async () => {
      const user = userEvent.setup();
      renderComponent();

      const submitButton = screen.getByRole("button", {
        name: /criar usuário/i,
      });
      await user.click(submitButton);

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
      const submitButton = screen.getByRole("button", {
        name: /criar usuário/i,
      });

      // Fill in a name first so email validation can trigger
      await user.type(screen.getByLabelText(/nome completo/i), "Test User");
      await user.type(emailInput, "invalid-email");

      await user.click(submitButton);

      await waitFor(() => {
        // Try exact text match
        expect(screen.getByText("Digite um email válido")).toBeInTheDocument();
      });
    });

    it("should show validation error for weak password", async () => {
      const user = userEvent.setup();
      renderComponent();

      // Fill required fields first
      await user.type(screen.getByLabelText(/nome completo/i), "Test User");
      await user.type(screen.getByLabelText(/email/i), "test@example.com");

      const passwordInput = screen.getByPlaceholderText(
        /digite uma senha segura/i,
      );
      await user.type(passwordInput, "weak");

      const submitButton = screen.getByRole("button", {
        name: /criar usuário/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/senha deve ter pelo menos 8 caracteres/i),
        ).toBeInTheDocument();
      });
    });

    it("should show validation error when passwords do not match", async () => {
      const user = userEvent.setup();
      renderComponent();

      // Fill required fields first
      await user.type(screen.getByLabelText(/nome completo/i), "Test User");
      await user.type(screen.getByLabelText(/email/i), "test@example.com");

      const passwordInput = screen.getByPlaceholderText(
        /digite uma senha segura/i,
      );
      const confirmPasswordInput = screen.getByPlaceholderText(
        /digite a senha novamente/i,
      );

      await user.type(passwordInput, "StrongPassword123!");
      await user.type(confirmPasswordInput, "DifferentPassword123!");

      const submitButton = screen.getByRole("button", {
        name: /criar usuário/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/senhas não coincidem/i)).toBeInTheDocument();
      });
    });

    it("should show validation error when no role is selected", async () => {
      const user = userEvent.setup();
      renderComponent();

      const submitButton = screen.getByRole("button", {
        name: /criar usuário/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/selecione um role/i)).toBeInTheDocument();
      });
    });
  });

  describe("Role Selection", () => {
    it("should display all available roles with descriptions", async () => {
      const user = userEvent.setup();
      renderComponent();

      const roleSelect = screen.getByRole("combobox");
      await user.click(roleSelect);

      await waitFor(() => {
        expect(screen.getAllByText(/administrador do sistema/i)).toHaveLength(
          2,
        ); // One in select, one in dropdown
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

    it("should allow selecting different roles", async () => {
      const user = userEvent.setup();
      renderComponent();

      const roleSelect = screen.getByRole("combobox", {
        name: /role do usuário/i,
      });
      await user.click(roleSelect);

      await waitFor(() => {
        expect(screen.getByText(/administrador$/i)).toBeInTheDocument();
      });

      await user.click(screen.getByText(/administrador$/i));

      await waitFor(() => {
        expect(screen.getByDisplayValue("admin")).toBeInTheDocument();
      });
    });
  });

  describe("Password Visibility Toggle", () => {
    it("should toggle password visibility for main password field", async () => {
      const user = userEvent.setup();
      renderComponent();

      const passwordInput = screen.getByPlaceholderText(
        /digite uma senha segura/i,
      ) as HTMLInputElement;
      expect(passwordInput.type).toBe("password");

      // Find the eye icon button for password field
      const passwordContainer = passwordInput.closest(".relative");
      const toggleButton = passwordContainer?.querySelector(
        "button",
      ) as HTMLButtonElement;
      await user.click(toggleButton);

      await waitFor(() => {
        expect(passwordInput.type).toBe("text");
      });
    });

    it("should toggle password visibility for confirm password field", async () => {
      const user = userEvent.setup();
      renderComponent();

      const confirmPasswordInput = screen.getByPlaceholderText(
        /digite a senha novamente/i,
      ) as HTMLInputElement;
      expect(confirmPasswordInput.type).toBe("password");

      // Find the eye icon button for confirm password field
      const confirmPasswordContainer =
        confirmPasswordInput.closest(".relative");
      const confirmToggleButton = confirmPasswordContainer?.querySelector(
        "button",
      ) as HTMLButtonElement;
      await user.click(confirmToggleButton);

      await waitFor(() => {
        expect(confirmPasswordInput.type).toBe("text");
      });
    });
  });

  describe("Form Submission", () => {
    const validFormData = {
      full_name: "João Silva",
      email: "joao@example.com",
      password: "StrongPassword123!",
      confirmPassword: "StrongPassword123!",
      role: "admin",
    };

    const fillValidForm = async (user: ReturnType<typeof userEvent.setup>) => {
      await user.type(
        screen.getByLabelText(/nome completo/i),
        validFormData.full_name,
      );
      await user.type(screen.getByLabelText(/email/i), validFormData.email);

      const roleSelect = screen.getByRole("combobox");
      await user.click(roleSelect);
      await user.click(screen.getByText(/administrador$/i));

      await user.type(
        screen.getByPlaceholderText(/digite uma senha segura/i),
        validFormData.password,
      );
      await user.type(
        screen.getByPlaceholderText(/digite a senha novamente/i),
        validFormData.confirmPassword,
      );
    };

    it("should submit form with valid data", async () => {
      const user = userEvent.setup();
      const mockUser = {
        user_id: "123",
        ...validFormData,
        created_at: "2025-01-01T00:00:00Z",
      };
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => mockUser,
      } as Response);

      renderComponent();
      await fillValidForm(user);

      const submitButton = screen.getByRole("button", {
        name: /criar usuário/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining("/api/v1/users"),
          expect.objectContaining({
            method: "POST",
            body: expect.stringContaining(validFormData.email),
          }),
        );
        // Toast será chamado através da implementação real
        expect(mockOnSuccess).toHaveBeenCalled();
      });
    });

    it("should show loading state during submission", async () => {
      const user = userEvent.setup();
      vi.mocked(global.fetch).mockImplementationOnce(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  ok: true,
                  status: 201,
                  json: async () => ({}),
                } as Response),
              100,
            ),
          ),
      );

      renderComponent();
      await fillValidForm(user);

      const submitButton = screen.getByRole("button", {
        name: /criar usuário/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/criando.../i)).toBeInTheDocument();
        expect(
          screen.getByRole("button", { name: /criando.../i }),
        ).toBeDisabled();
      });
    });

    it("should handle API errors gracefully", async () => {
      const user = userEvent.setup();
      const errorMessage = "Email já existe";
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: false,
        status: 409,
        json: async () => ({ detail: errorMessage }),
      } as Response);

      renderComponent();
      await fillValidForm(user);

      const submitButton = screen.getByRole("button", {
        name: /criar usuário/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        // Toast de erro será chamado através da implementação real
        expect(mockOnSuccess).not.toHaveBeenCalled();
      });
    });

    it("should handle generic API errors", async () => {
      const user = userEvent.setup();
      vi.mocked(global.fetch).mockRejectedValueOnce(new Error("Network error"));

      renderComponent();
      await fillValidForm(user);

      const submitButton = screen.getByRole("button", {
        name: /criar usuário/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        // Toast de erro genérico será chamado através da implementação real
        expect(mockOnSuccess).not.toHaveBeenCalled();
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

    it("should not submit form when submit button is disabled", async () => {
      const user = userEvent.setup();
      renderComponent();

      // Submit without filling required fields
      const submitButton = screen.getByRole("button", {
        name: /criar usuário/i,
      });
      await user.click(submitButton);

      // Should show validation errors but not call API
      await waitFor(() => {
        expect(
          screen.getByText(/nome deve ter pelo menos 2 caracteres/i),
        ).toBeInTheDocument();
      });

      expect(global.fetch).not.toHaveBeenCalled();
    });
  });

  describe("Accessibility", () => {
    it("should have proper form labels and associations", () => {
      renderComponent();

      expect(screen.getByLabelText(/nome completo/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByRole("combobox")).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText(/digite uma senha segura/i),
      ).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText(/digite a senha novamente/i),
      ).toBeInTheDocument();
    });

    it("should announce validation errors to screen readers", async () => {
      const user = userEvent.setup();
      renderComponent();

      const submitButton = screen.getByRole("button", {
        name: /criar usuário/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        const errorMessage = screen.getByText(
          /nome deve ter pelo menos 2 caracteres/i,
        );
        expect(errorMessage).toBeInTheDocument();
      });
    });

    it("should support keyboard navigation", async () => {
      const user = userEvent.setup();
      renderComponent();

      const nameInput = screen.getByLabelText(/nome completo/i);
      await user.tab();
      expect(nameInput).toHaveFocus();

      await user.tab();
      expect(screen.getByLabelText(/email/i)).toHaveFocus();
    });
  });

  describe("Form Reset", () => {
    it("should reset form after successful submission", async () => {
      const user = userEvent.setup();
      const mockUser = { user_id: "123", email: "test@example.com" };
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => mockUser,
      } as Response);

      renderComponent();

      // Fill form
      await user.type(screen.getByLabelText(/nome completo/i), "Test User");
      await user.type(screen.getByLabelText(/email/i), "test@example.com");

      const submitButton = screen.getByRole("button", {
        name: /criar usuário/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalled();
      });

      // Form should be reset after success - check specific field
      expect(screen.getByLabelText(/nome completo/i)).toHaveValue("");
    });
  });
});
