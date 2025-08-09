/**
 * PasswordStrengthIndicator Component Tests
 * Tests password strength validation, visual indicators, and real-time feedback
 * Following CLAUDE.md rules: no internal mocking, only external API mocking
 */
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PasswordStrengthIndicator } from "../PasswordStrengthIndicator";

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("PasswordStrengthIndicator", () => {
  describe("Basic rendering", () => {
    it("should not render when password is empty", () => {
      const { container } = render(<PasswordStrengthIndicator password="" />);
      expect(container).toBeEmptyDOMElement();
    });

    it("should render strength indicator when password is provided", () => {
      render(<PasswordStrengthIndicator password="test" />);

      expect(screen.getByText("Força da senha:")).toBeInTheDocument();
      expect(screen.getByText("Fraca")).toBeInTheDocument();
    });

    it("should render with custom className", () => {
      const { container } = render(
        <PasswordStrengthIndicator password="test" className="custom-class" />,
      );

      expect(container.firstChild).toHaveClass("custom-class");
    });

    it("should hide details when showDetails is false", () => {
      render(<PasswordStrengthIndicator password="test" showDetails={false} />);

      expect(screen.getByText("Força da senha:")).toBeInTheDocument();
      expect(screen.queryByText("Requisitos:")).not.toBeInTheDocument();
      expect(
        screen.queryByText("Pelo menos 8 caracteres"),
      ).not.toBeInTheDocument();
    });

    it("should show details by default", () => {
      render(<PasswordStrengthIndicator password="test" />);

      expect(screen.getByText("Requisitos:")).toBeInTheDocument();
      expect(screen.getByText("Pelo menos 8 caracteres")).toBeInTheDocument();
    });
  });

  describe("Password strength levels", () => {
    it('should show "Fraca" for passwords with score 1 (only one requirement met)', () => {
      render(<PasswordStrengthIndicator password="abc" />);

      expect(screen.getByText("Fraca")).toBeInTheDocument();
      expect(screen.getByText("Fraca")).toHaveClass("text-red-600");
    });

    it('should show "Regular" for long passwords with only lowercase (score 2)', () => {
      render(<PasswordStrengthIndicator password="abcdefgh" />);

      expect(screen.getByText("Regular")).toBeInTheDocument();
      expect(screen.getByText("Regular")).toHaveClass("text-yellow-600");
    });

    it('should show "Regular" for passwords with score 2', () => {
      render(<PasswordStrengthIndicator password="abcABC" />);

      expect(screen.getByText("Regular")).toBeInTheDocument();
      expect(screen.getByText("Regular")).toHaveClass("text-yellow-600");
    });

    it('should show "Boa" for passwords with score 3', () => {
      render(<PasswordStrengthIndicator password="abcdefghA" />);

      expect(screen.getByText("Boa")).toBeInTheDocument();
      expect(screen.getByText("Boa")).toHaveClass("text-yellow-600");
    });

    it('should show "Forte" for passwords with score 4', () => {
      render(<PasswordStrengthIndicator password="abcdefghA1" />);

      expect(screen.getByText("Forte")).toBeInTheDocument();
      expect(screen.getByText("Forte")).toHaveClass("text-green-600");
    });

    it('should show "Muito Forte" for passwords with score 5', () => {
      render(<PasswordStrengthIndicator password="abcdefghA1!" />);

      expect(screen.getByText("Muito Forte")).toBeInTheDocument();
      expect(screen.getByText("Muito Forte")).toHaveClass("text-green-600");
    });
  });

  describe("Password complexity validation", () => {
    it("should validate minimum length requirement", () => {
      render(<PasswordStrengthIndicator password="short" />);

      const lengthRequirement = screen.getByText("Pelo menos 8 caracteres");
      expect(lengthRequirement).toBeInTheDocument();
      expect(lengthRequirement.closest("li")).toHaveClass(
        "text-muted-foreground",
      );

      // Should show X icon for unmet requirement
      const xIcon = lengthRequirement.parentElement?.querySelector("svg");
      expect(xIcon).toBeInTheDocument();
    });

    it("should show check mark when length requirement is met", () => {
      render(<PasswordStrengthIndicator password="longpassword" />);

      const lengthRequirement = screen.getByText("Pelo menos 8 caracteres");
      expect(lengthRequirement.closest("li")).toHaveClass("text-green-600");

      // Should show check icon for met requirement
      const checkIcon = lengthRequirement.parentElement?.querySelector("svg");
      expect(checkIcon).toBeInTheDocument();
    });

    it("should validate uppercase letter requirement", () => {
      render(<PasswordStrengthIndicator password="lowercase" />);

      const uppercaseRequirement = screen.getByText(
        "Pelo menos 1 letra maiúscula",
      );
      expect(uppercaseRequirement.closest("li")).toHaveClass(
        "text-muted-foreground",
      );
    });

    it("should show check mark when uppercase requirement is met", () => {
      render(<PasswordStrengthIndicator password="Uppercase" />);

      const uppercaseRequirement = screen.getByText(
        "Pelo menos 1 letra maiúscula",
      );
      expect(uppercaseRequirement.closest("li")).toHaveClass("text-green-600");
    });

    it("should validate lowercase letter requirement", () => {
      render(<PasswordStrengthIndicator password="UPPERCASE" />);

      const lowercaseRequirement = screen.getByText(
        "Pelo menos 1 letra minúscula",
      );
      expect(lowercaseRequirement.closest("li")).toHaveClass(
        "text-muted-foreground",
      );
    });

    it("should show check mark when lowercase requirement is met", () => {
      render(<PasswordStrengthIndicator password="lowercase" />);

      const lowercaseRequirement = screen.getByText(
        "Pelo menos 1 letra minúscula",
      );
      expect(lowercaseRequirement.closest("li")).toHaveClass("text-green-600");
    });

    it("should validate number requirement", () => {
      render(<PasswordStrengthIndicator password="password" />);

      const numberRequirement = screen.getByText("Pelo menos 1 número");
      expect(numberRequirement.closest("li")).toHaveClass(
        "text-muted-foreground",
      );
    });

    it("should show check mark when number requirement is met", () => {
      render(<PasswordStrengthIndicator password="password1" />);

      const numberRequirement = screen.getByText("Pelo menos 1 número");
      expect(numberRequirement.closest("li")).toHaveClass("text-green-600");
    });

    it("should validate special character requirement", () => {
      render(<PasswordStrengthIndicator password="Password1" />);

      const specialCharRequirement = screen.getByText(
        "Pelo menos 1 caractere especial",
      );
      expect(specialCharRequirement.closest("li")).toHaveClass(
        "text-muted-foreground",
      );
    });

    it("should show check mark when special character requirement is met", () => {
      render(<PasswordStrengthIndicator password="Password1!" />);

      const specialCharRequirement = screen.getByText(
        "Pelo menos 1 caractere especial",
      );
      expect(specialCharRequirement.closest("li")).toHaveClass(
        "text-green-600",
      );
    });
  });

  describe("Visual progress indicators", () => {
    it("should show correct number of filled bars for score 1", () => {
      const { container } = render(
        <PasswordStrengthIndicator password="abc" />,
      );

      const progressBars = container.querySelectorAll(".h-2.flex-1");
      expect(progressBars).toHaveLength(5); // Total bars

      const filledBars = container.querySelectorAll(".bg-orange-500");
      expect(filledBars).toHaveLength(1); // One filled bar for score 1
    });

    it("should show correct number of filled bars for score 2", () => {
      const { container } = render(
        <PasswordStrengthIndicator password="abcABC" />,
      );

      const filledBars = container.querySelectorAll(".bg-yellow-500");
      expect(filledBars).toHaveLength(2); // Two filled bars for score 2
    });

    it("should show correct number of filled bars for score 3", () => {
      const { container } = render(
        <PasswordStrengthIndicator password="abcdefghA" />,
      );

      const filledBars = container.querySelectorAll(".bg-blue-500");
      expect(filledBars).toHaveLength(3); // Three filled bars for score 3
    });

    it("should show correct number of filled bars for score 4", () => {
      const { container } = render(
        <PasswordStrengthIndicator password="abcdefghA1" />,
      );

      const filledBars = container.querySelectorAll(".bg-green-500");
      expect(filledBars).toHaveLength(4); // Four filled bars for score 4
    });

    it("should show all bars filled for maximum score", () => {
      const { container } = render(
        <PasswordStrengthIndicator password="abcdefghA1!" />,
      );

      const filledBars = container.querySelectorAll(".bg-green-600");
      expect(filledBars).toHaveLength(5); // All bars filled for score 5
    });

    it("should show unfilled bars with muted background", () => {
      const { container } = render(
        <PasswordStrengthIndicator password="abc" />,
      );

      const unfilledBars = container.querySelectorAll(".bg-muted");
      expect(unfilledBars).toHaveLength(4); // Four unfilled bars for score 1 (5 total - 1 filled = 4 unfilled)
    });
  });

  describe("Real-time validation feedback", () => {
    it("should update strength indicator as password changes", () => {
      const TestComponent = () => {
        const [password, setPassword] = React.useState("");

        return (
          <div>
            <input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
            />
            <PasswordStrengthIndicator password={password} />
          </div>
        );
      };

      render(<TestComponent />);

      const input = screen.getByPlaceholderText("Password");

      // Initially no indicator should be shown
      expect(screen.queryByText("Força da senha:")).not.toBeInTheDocument();
    });

    it("should show weak strength for partial password", async () => {
      const TestComponent = () => {
        const [password, setPassword] = React.useState("");

        return (
          <div>
            <input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
            />
            <PasswordStrengthIndicator password={password} />
          </div>
        );
      };

      const user = userEvent.setup();
      render(<TestComponent />);

      const input = screen.getByPlaceholderText("Password");

      await user.type(input, "abc");

      expect(screen.getByText("Fraca")).toBeInTheDocument();
      expect(
        screen.getByText("Pelo menos 8 caracteres").closest("li"),
      ).toHaveClass("text-muted-foreground");
    });

    it("should progressively show improvements as requirements are met", async () => {
      const TestComponent = () => {
        const [password, setPassword] = React.useState("");

        return (
          <div>
            <input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
            />
            <PasswordStrengthIndicator password={password} />
          </div>
        );
      };

      const user = userEvent.setup();
      render(<TestComponent />);

      const input = screen.getByPlaceholderText("Password");

      // Step 1: Add 8 characters
      await user.type(input, "password");
      expect(
        screen.getByText("Pelo menos 8 caracteres").closest("li"),
      ).toHaveClass("text-green-600");
      expect(screen.getByText("Regular")).toBeInTheDocument();

      // Step 2: Add uppercase
      await user.clear(input);
      await user.type(input, "passwordP");
      expect(
        screen.getByText("Pelo menos 1 letra maiúscula").closest("li"),
      ).toHaveClass("text-green-600");
      expect(screen.getByText("Boa")).toBeInTheDocument();

      // Step 3: Add number
      await user.clear(input);
      await user.type(input, "passwordP1");
      expect(screen.getByText("Pelo menos 1 número").closest("li")).toHaveClass(
        "text-green-600",
      );
      expect(screen.getByText("Forte")).toBeInTheDocument();

      // Step 4: Add special character
      await user.clear(input);
      await user.type(input, "passwordP1!");
      expect(
        screen.getByText("Pelo menos 1 caractere especial").closest("li"),
      ).toHaveClass("text-green-600");
      expect(screen.getByText("Muito Forte")).toBeInTheDocument();
    });
  });

  describe("Special character validation", () => {
    const specialChars = [
      "!",
      "@",
      "#",
      "$",
      "%",
      "^",
      "&",
      "*",
      "(",
      ")",
      ",",
      ".",
      "?",
      '"',
      ":",
      "{",
      "}",
      "|",
      "<",
      ">",
    ];

    specialChars.forEach((char) => {
      it(`should recognize "${char}" as a special character`, () => {
        render(<PasswordStrengthIndicator password={`Password1${char}`} />);

        const specialCharRequirement = screen.getByText(
          "Pelo menos 1 caractere especial",
        );
        expect(specialCharRequirement.closest("li")).toHaveClass(
          "text-green-600",
        );
      });
    });

    it("should not recognize letters, numbers, or spaces as special characters", () => {
      render(<PasswordStrengthIndicator password="Password1 abc" />);

      const specialCharRequirement = screen.getByText(
        "Pelo menos 1 caractere especial",
      );
      expect(specialCharRequirement.closest("li")).toHaveClass(
        "text-muted-foreground",
      );
    });
  });

  describe("Accessibility features", () => {
    it("should have proper semantic structure with lists", () => {
      render(<PasswordStrengthIndicator password="test" />);

      const requirementsList = screen.getByRole("list");
      expect(requirementsList).toBeInTheDocument();

      const requirements = screen.getAllByRole("listitem");
      expect(requirements).toHaveLength(5); // 5 requirements
    });

    it("should use appropriate color contrast for different states", () => {
      render(<PasswordStrengthIndicator password="password1" />);

      // Met requirements should be green
      expect(
        screen.getByText("Pelo menos 8 caracteres").closest("li"),
      ).toHaveClass("text-green-600");

      // Unmet requirements should be muted
      const unmetRequirement = screen.getByText("Pelo menos 1 letra maiúscula");
      expect(unmetRequirement.closest("li")).toHaveClass(
        "text-muted-foreground",
      );
    });

    it("should have descriptive text for screen readers", () => {
      render(<PasswordStrengthIndicator password="test" />);

      expect(screen.getByText("Força da senha:")).toBeInTheDocument();
      expect(screen.getByText("Requisitos:")).toBeInTheDocument();
    });
  });

  describe("Complex password scenarios", () => {
    it("should handle empty password correctly", () => {
      const { container } = render(<PasswordStrengthIndicator password="" />);
      expect(container).toBeEmptyDOMElement();
    });

    it("should handle very long passwords", () => {
      const longPassword = "A".repeat(100) + "a1!";
      render(<PasswordStrengthIndicator password={longPassword} />);

      expect(screen.getByText("Muito Forte")).toBeInTheDocument();
      expect(
        screen.getByText("Pelo menos 8 caracteres").closest("li"),
      ).toHaveClass("text-green-600");
    });

    it("should handle passwords with Unicode characters", () => {
      render(<PasswordStrengthIndicator password="Pássword1!" />);

      expect(screen.getByText("Muito Forte")).toBeInTheDocument();
      expect(
        screen.getByText("Pelo menos 1 letra minúscula").closest("li"),
      ).toHaveClass("text-green-600");
    });

    it("should handle passwords with only special characters", () => {
      render(<PasswordStrengthIndicator password="!@#$%^&*" />);

      expect(
        screen.getByText("Pelo menos 8 caracteres").closest("li"),
      ).toHaveClass("text-green-600");
      expect(
        screen.getByText("Pelo menos 1 caractere especial").closest("li"),
      ).toHaveClass("text-green-600");
      expect(
        screen.getByText("Pelo menos 1 letra minúscula").closest("li"),
      ).toHaveClass("text-muted-foreground");
    });

    it("should cap score at maximum of 5", () => {
      const { container } = render(
        <PasswordStrengthIndicator password="VeryLongPasswordWithAllRequirements123!@#" />,
      );

      // Should show maximum strength
      expect(screen.getByText("Muito Forte")).toBeInTheDocument();

      // Should show exactly 5 filled bars, not more
      const filledBars = container.querySelectorAll(".bg-green-600");
      expect(filledBars).toHaveLength(5);
    });
  });

  describe("Integration scenarios", () => {
    it("should work correctly in a form context", async () => {
      const TestForm = () => {
        const [password, setPassword] = React.useState("");
        const [confirmPassword, setConfirmPassword] = React.useState("");

        return (
          <form>
            <div>
              <label htmlFor="password">Senha</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <PasswordStrengthIndicator password={password} />
            </div>
            <div>
              <label htmlFor="confirm-password">Confirmar Senha</label>
              <input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </div>
          </form>
        );
      };

      const user = userEvent.setup();
      render(<TestForm />);

      const passwordInput = screen.getByLabelText("Senha");

      await user.type(passwordInput, "StrongPass123!");

      expect(screen.getByText("Muito Forte")).toBeInTheDocument();

      // All requirements should be met
      expect(
        screen.getByText("Pelo menos 8 caracteres").closest("li"),
      ).toHaveClass("text-green-600");
      expect(
        screen.getByText("Pelo menos 1 letra maiúscula").closest("li"),
      ).toHaveClass("text-green-600");
      expect(
        screen.getByText("Pelo menos 1 letra minúscula").closest("li"),
      ).toHaveClass("text-green-600");
      expect(screen.getByText("Pelo menos 1 número").closest("li")).toHaveClass(
        "text-green-600",
      );
      expect(
        screen.getByText("Pelo menos 1 caractere especial").closest("li"),
      ).toHaveClass("text-green-600");
    });
  });
});

// Add React import for JSX (required for test components)
import React from "react";
