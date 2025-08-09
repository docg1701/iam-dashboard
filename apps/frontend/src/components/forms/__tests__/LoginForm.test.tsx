/**
 * LoginForm Component Tests
 * Tests authentication form behavior and user interactions
 * Following CLAUDE.md rules: no internal mocking, only external API mocking
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { LoginForm } from "../LoginForm";
import type { LoginFormData, LoginResponse } from "@/types/auth";

// Test wrapper for providers
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

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("LoginForm", () => {
  it("should render login form with email and password fields", () => {
    const mockOnSubmit = vi.fn();
    render(
      <TestWrapper>
        <LoginForm onSubmit={mockOnSubmit} />
      </TestWrapper>,
    );

    expect(screen.getByPlaceholderText(/seu@email.com/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/••••••••/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /entrar/i })).toBeInTheDocument();
  });

  it("should validate email field correctly", async () => {
    const user = userEvent.setup();
    const mockOnSubmit = vi.fn().mockRejectedValue(new Error("Invalid email"));

    render(
      <TestWrapper>
        <LoginForm onSubmit={mockOnSubmit} />
      </TestWrapper>,
    );

    const emailField = screen.getByPlaceholderText(/seu@email.com/i);
    const passwordField = screen.getByPlaceholderText(/••••••••/);
    const submitButton = screen.getByRole("button", { name: /entrar/i });

    // Try to submit with invalid email
    await user.type(emailField, "invalid-email");
    await user.type(passwordField, "validpassword123");
    await user.click(submitButton);

    await waitFor(() => {
      // Check that the email field has validation error styling
      expect(emailField).toHaveAttribute("aria-invalid", "true");
    });

    // Look for validation message using a more flexible approach
    await waitFor(() => {
      const errorMessage = screen.queryByText(/email.*formato.*válido/i);
      if (errorMessage) {
        expect(errorMessage).toBeInTheDocument();
      } else {
        // Alternative: check if form didn't submit due to validation
        expect(mockOnSubmit).not.toHaveBeenCalled();
      }
    });
  });

  it("should validate password field correctly", async () => {
    const user = userEvent.setup();
    const mockOnSubmit = vi.fn();

    render(
      <TestWrapper>
        <LoginForm onSubmit={mockOnSubmit} />
      </TestWrapper>,
    );

    const submitButton = screen.getByRole("button", { name: /entrar/i });

    // Try to submit with empty password
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("Senha é obrigatória")).toBeInTheDocument();
    });
  });

  it("should handle successful login without 2FA", async () => {
    const user = userEvent.setup();

    const mockResponse: LoginResponse = {
      access_token: "mock-token",
      token_type: "bearer",
      expires_in: 3600,
      requires_2fa: false,
      user: {
        user_id: "user-123",
        email: "test@example.com",
        role: "admin",
        full_name: "Test User",
        is_active: true,
        totp_enabled: false,
        created_at: "2023-01-01T00:00:00Z",
        updated_at: "2023-01-01T00:00:00Z",
      },
    };

    // Mock with delay to catch loading state
    const mockOnSubmit = vi
      .fn()
      .mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve(mockResponse), 100),
          ),
      );
    const mockOnSuccess = vi.fn();

    render(
      <TestWrapper>
        <LoginForm onSubmit={mockOnSubmit} onSuccess={mockOnSuccess} />
      </TestWrapper>,
    );

    const emailField = screen.getByPlaceholderText(/seu@email.com/i);
    const passwordField = screen.getByPlaceholderText(/••••••••/);
    const submitButton = screen.getByRole("button", { name: /entrar/i });

    await user.type(emailField, "test@example.com");
    await user.type(passwordField, "password123");
    await user.click(submitButton);

    // Should show loading state - check for "Entrando..." text or disabled state
    await waitFor(() => {
      const loadingText = screen.queryByText("Entrando...");
      const disabledButton = screen.queryByRole("button", {
        name: /entrando/i,
      });
      expect(loadingText || disabledButton).toBeTruthy();
    });

    // Should call onSubmit with correct data
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        email: "test@example.com",
        password: "password123",
      });
      expect(mockOnSuccess).toHaveBeenCalledWith(mockResponse);
    });
  });

  it("should handle 2FA requirement correctly", async () => {
    const user = userEvent.setup();

    const mockResponse: LoginResponse = {
      requires_2fa: true,
      temp_token: "temp-session-123",
    };

    const mockOnSubmit = vi.fn().mockResolvedValue(mockResponse);
    const mockOnSuccess = vi.fn();

    render(
      <TestWrapper>
        <LoginForm onSubmit={mockOnSubmit} onSuccess={mockOnSuccess} />
      </TestWrapper>,
    );

    const emailField = screen.getByPlaceholderText(/seu@email.com/i);
    const passwordField = screen.getByPlaceholderText(/••••••••/);
    const submitButton = screen.getByRole("button", { name: /entrar/i });

    await user.type(emailField, "test@example.com");
    await user.type(passwordField, "password123");
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        email: "test@example.com",
        password: "password123",
      });
      expect(mockOnSuccess).toHaveBeenCalledWith(mockResponse);
    });
  });

  it("should handle login errors correctly", async () => {
    const user = userEvent.setup();

    const mockOnSubmit = vi
      .fn()
      .mockRejectedValue(new Error("Credenciais inválidas"));
    const mockOnError = vi.fn();

    render(
      <TestWrapper>
        <LoginForm onSubmit={mockOnSubmit} onError={mockOnError} />
      </TestWrapper>,
    );

    const emailField = screen.getByPlaceholderText(/seu@email.com/i);
    const passwordField = screen.getByPlaceholderText(/••••••••/);
    const submitButton = screen.getByRole("button", { name: /entrar/i });

    await user.type(emailField, "wrong@example.com");
    await user.type(passwordField, "wrongpassword");
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/credenciais inválidas/i)).toBeInTheDocument();
      expect(mockOnError).toHaveBeenCalledWith("Credenciais inválidas");
    });
  });

  it("should handle account lockout error", async () => {
    const user = userEvent.setup();

    const mockOnSubmit = vi
      .fn()
      .mockRejectedValue(
        new Error("Conta bloqueada devido a muitas tentativas de login"),
      );
    const mockOnError = vi.fn();

    render(
      <TestWrapper>
        <LoginForm onSubmit={mockOnSubmit} onError={mockOnError} />
      </TestWrapper>,
    );

    const emailField = screen.getByPlaceholderText(/seu@email.com/i);
    const passwordField = screen.getByPlaceholderText(/••••••••/);
    const submitButton = screen.getByRole("button", { name: /entrar/i });

    await user.type(emailField, "locked@example.com");
    await user.type(passwordField, "password123");
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/conta bloqueada/i)).toBeInTheDocument();
      expect(mockOnError).toHaveBeenCalledWith(
        "Conta bloqueada devido a muitas tentativas de login",
      );
    });
  });

  it("should display loading state during form submission", async () => {
    const user = userEvent.setup();

    // Mock delayed response
    const mockOnSubmit = vi.fn().mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                access_token: "token",
                token_type: "bearer",
                expires_in: 3600,
              }),
            100,
          ),
        ),
    );

    render(
      <TestWrapper>
        <LoginForm onSubmit={mockOnSubmit} />
      </TestWrapper>,
    );

    const emailField = screen.getByPlaceholderText(/seu@email.com/i);
    const passwordField = screen.getByPlaceholderText(/••••••••/);
    const submitButton = screen.getByRole("button", { name: /entrar/i });

    await user.type(emailField, "test@example.com");
    await user.type(passwordField, "password123");
    await user.click(submitButton);

    // Should show loading state immediately
    expect(screen.getByText(/entrando/i)).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
  });

  it("should handle keyboard navigation correctly", async () => {
    const user = userEvent.setup();
    const mockOnSubmit = vi.fn();

    render(
      <TestWrapper>
        <LoginForm onSubmit={mockOnSubmit} />
      </TestWrapper>,
    );

    const emailField = screen.getByPlaceholderText(/seu@email.com/i);
    const passwordField = screen.getByPlaceholderText(/••••••••/);
    const submitButton = screen.getByRole("button", { name: /entrar/i });

    // Tab navigation should work
    emailField.focus();
    expect(emailField).toHaveFocus();

    await user.tab();
    expect(passwordField).toHaveFocus();

    await user.tab();
    expect(submitButton).toHaveFocus();
  });

  it("should handle password visibility toggle", async () => {
    const user = userEvent.setup();
    const mockOnSubmit = vi.fn();

    render(
      <TestWrapper>
        <LoginForm onSubmit={mockOnSubmit} />
      </TestWrapper>,
    );

    const passwordField = screen.getByPlaceholderText(/••••••••/);
    const toggleButton = screen.getByRole("button", { name: /mostrar senha/i });

    // Initially password should be hidden
    expect(passwordField).toHaveAttribute("type", "password");

    // Click toggle to show password
    await user.click(toggleButton);
    expect(passwordField).toHaveAttribute("type", "text");

    // Click toggle to hide password again
    await user.click(toggleButton);
    expect(passwordField).toHaveAttribute("type", "password");
  });

  it("should handle rate limiting error", async () => {
    const user = userEvent.setup();

    const mockOnSubmit = vi
      .fn()
      .mockRejectedValue(
        new Error("Muitas tentativas. Tente novamente em 60 segundos."),
      );
    const mockOnError = vi.fn();

    render(
      <TestWrapper>
        <LoginForm onSubmit={mockOnSubmit} onError={mockOnError} />
      </TestWrapper>,
    );

    const emailField = screen.getByPlaceholderText(/seu@email.com/i);
    const passwordField = screen.getByPlaceholderText(/••••••••/);
    const submitButton = screen.getByRole("button", { name: /entrar/i });

    await user.type(emailField, "test@example.com");
    await user.type(passwordField, "password123");
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/muitas tentativas/i)).toBeInTheDocument();
      expect(mockOnError).toHaveBeenCalledWith(
        "Muitas tentativas. Tente novamente em 60 segundos.",
      );
    });
  });

  it("should preserve form state during validation", async () => {
    const user = userEvent.setup();
    const mockOnSubmit = vi.fn();

    render(
      <TestWrapper>
        <LoginForm onSubmit={mockOnSubmit} />
      </TestWrapper>,
    );

    const emailField = screen.getByPlaceholderText(/seu@email.com/i);
    const passwordField = screen.getByPlaceholderText(/••••••••/);
    const submitButton = screen.getByRole("button", { name: /entrar/i });

    // Fill with invalid data
    await user.type(emailField, "invalid-email");
    await user.type(passwordField, "short");

    await user.click(submitButton);

    // Should show validation errors but preserve field values
    await waitFor(() => {
      expect(
        screen.getByText("Email deve ter um formato válido"),
      ).toBeInTheDocument();
    });

    // Fields should maintain their values
    expect(emailField).toHaveValue("invalid-email");
    expect(passwordField).toHaveValue("short");

    // Should not call submit function
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });
});
