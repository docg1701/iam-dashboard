/**
 * Index Types Tests
 *
 * Following CLAUDE.md testing directives:
 * - NEVER mock internal frontend code, components, hooks, or utilities
 * - ONLY mock external APIs (third-party services, etc.)
 * - Test actual behavior, not implementation details
 */

import { describe, it, expect } from "vitest";
import type {
  AuthState,
  ApiResponse,
  PaginatedResponse,
  ThemeConfig,
  BrandingConfig,
} from "../index";

describe("Index Types", () => {
  describe("AuthState Type", () => {
    it("should represent unauthenticated state", () => {
      const unauthenticatedState: AuthState = {
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      };

      expect(unauthenticatedState.isAuthenticated).toBe(false);
      expect(unauthenticatedState.user).toBeNull();
      expect(unauthenticatedState.token).toBeNull();
      expect(unauthenticatedState.isLoading).toBe(false);
    });

    it("should represent loading state", () => {
      const loadingState: AuthState = {
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: true,
      };

      expect(loadingState.isLoading).toBe(true);
    });
  });

  describe("ApiResponse Type", () => {
    it("should handle successful response with data", () => {
      const successResponse: ApiResponse<{ id: string; name: string }> = {
        data: { id: "123", name: "Test" },
        message: "Success",
        status: 200,
      };

      expect(successResponse.status).toBe(200);
      expect(successResponse.data).toBeDefined();
      expect(successResponse.data?.id).toBe("123");
      expect(successResponse.message).toBe("Success");
    });

    it("should handle error response", () => {
      const errorResponse: ApiResponse = {
        error: "Not found",
        status: 404,
      };

      expect(errorResponse.status).toBe(404);
      expect(errorResponse.error).toBe("Not found");
      expect(errorResponse.data).toBeUndefined();
    });

    it("should handle response with only status", () => {
      const minimalResponse: ApiResponse = {
        status: 204,
      };

      expect(minimalResponse.status).toBe(204);
      expect(minimalResponse.data).toBeUndefined();
      expect(minimalResponse.message).toBeUndefined();
      expect(minimalResponse.error).toBeUndefined();
    });

    it("should support generic typing", () => {
      interface UserData {
        id: string;
        email: string;
      }

      const userResponse: ApiResponse<UserData> = {
        data: {
          id: "user-123",
          email: "user@example.com",
        },
        status: 200,
      };

      expect(userResponse.data?.email).toBe("user@example.com");
      expect(typeof userResponse.data?.id).toBe("string");
    });
  });

  describe("PaginatedResponse Type", () => {
    it("should handle paginated data", () => {
      const paginatedUsers: PaginatedResponse<{ id: string; name: string }> = {
        items: [
          { id: "1", name: "User 1" },
          { id: "2", name: "User 2" },
          { id: "3", name: "User 3" },
        ],
        total: 25,
        page: 1,
        size: 3,
        pages: 9,
      };

      expect(paginatedUsers.items).toHaveLength(3);
      expect(paginatedUsers.total).toBe(25);
      expect(paginatedUsers.page).toBe(1);
      expect(paginatedUsers.size).toBe(3);
      expect(paginatedUsers.pages).toBe(9);
    });

    it("should handle empty paginated response", () => {
      const emptyResponse: PaginatedResponse<any> = {
        items: [],
        total: 0,
        page: 1,
        size: 10,
        pages: 0,
      };

      expect(emptyResponse.items).toHaveLength(0);
      expect(emptyResponse.total).toBe(0);
      expect(emptyResponse.pages).toBe(0);
    });

    it("should calculate pagination correctly", () => {
      const response: PaginatedResponse<string> = {
        items: ["item1", "item2"],
        total: 100,
        page: 3,
        size: 20,
        pages: 5,
      };

      // Verify pagination math
      expect(Math.ceil(response.total / response.size)).toBe(response.pages);
      expect(response.page).toBeLessThanOrEqual(response.pages);
      expect(response.items.length).toBeLessThanOrEqual(response.size);
    });

    it("should support different item types", () => {
      interface Product {
        id: number;
        name: string;
        price: number;
      }

      const productResponse: PaginatedResponse<Product> = {
        items: [
          { id: 1, name: "Product A", price: 99.99 },
          { id: 2, name: "Product B", price: 149.99 },
        ],
        total: 50,
        page: 1,
        size: 2,
        pages: 25,
      };

      expect(productResponse.items[0].price).toBe(99.99);
      expect(typeof productResponse.items[0].id).toBe("number");
    });
  });

  describe("ThemeConfig Type", () => {
    it("should define complete theme configuration", () => {
      const lightTheme: ThemeConfig = {
        primary: "#000000",
        secondary: "#64748b",
        accent: "#f59e0b",
        background: "#ffffff",
        foreground: "#0f172a",
        card: "#ffffff",
        cardForeground: "#0f172a",
        popover: "#ffffff",
        popoverForeground: "#0f172a",
        muted: "#f1f5f9",
        mutedForeground: "#64748b",
        border: "#e2e8f0",
        input: "#e2e8f0",
        ring: "#000000",
        radius: "0.5rem",
      };

      expect(lightTheme.primary).toBe("#000000");
      expect(lightTheme.background).toBe("#ffffff");
      expect(lightTheme.radius).toBe("0.5rem");
      expect(Object.keys(lightTheme)).toHaveLength(14);
    });

    it("should support dark theme configuration", () => {
      const darkTheme: ThemeConfig = {
        primary: "#ffffff",
        secondary: "#94a3b8",
        accent: "#fbbf24",
        background: "#0f172a",
        foreground: "#f8fafc",
        card: "#1e293b",
        cardForeground: "#f8fafc",
        popover: "#1e293b",
        popoverForeground: "#f8fafc",
        muted: "#334155",
        mutedForeground: "#94a3b8",
        border: "#334155",
        input: "#334155",
        ring: "#ffffff",
        radius: "0.75rem",
      };

      expect(darkTheme.primary).toBe("#ffffff");
      expect(darkTheme.background).toBe("#0f172a");
      expect(darkTheme.radius).toBe("0.75rem");
    });

    it("should validate color format", () => {
      const theme: ThemeConfig = {
        primary: "#3b82f6",
        secondary: "#6b7280",
        accent: "#10b981",
        background: "#ffffff",
        foreground: "#1f2937",
        card: "#f9fafb",
        cardForeground: "#1f2937",
        popover: "#ffffff",
        popoverForeground: "#1f2937",
        muted: "#f3f4f6",
        mutedForeground: "#6b7280",
        border: "#d1d5db",
        input: "#d1d5db",
        ring: "#3b82f6",
        radius: "0.375rem",
      };

      // Basic hex color validation
      const hexColorRegex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/;
      expect(hexColorRegex.test(theme.primary)).toBe(true);
      expect(hexColorRegex.test(theme.background)).toBe(true);
      
      // Radius should be a valid CSS value
      expect(theme.radius).toMatch(/^[\d.]+rem$|^[\d.]+px$/);
    });
  });

  describe("BrandingConfig Type", () => {
    it("should define complete branding configuration", () => {
      const brandConfig: BrandingConfig = {
        logo: "/logo.svg",
        favicon: "/favicon.ico",
        companyName: "Acme Corporation",
        theme: {
          primary: "#000000",
          secondary: "#64748b",
          accent: "#f59e0b",
          background: "#ffffff",
          foreground: "#0f172a",
          card: "#ffffff",
          cardForeground: "#0f172a",
          popover: "#ffffff",
          popoverForeground: "#0f172a",
          muted: "#f1f5f9",
          mutedForeground: "#64748b",
          border: "#e2e8f0",
          input: "#e2e8f0",
          ring: "#000000",
          radius: "0.5rem",
        },
      };

      expect(brandConfig.companyName).toBe("Acme Corporation");
      expect(brandConfig.logo).toBe("/logo.svg");
      expect(brandConfig.favicon).toBe("/favicon.ico");
      expect(brandConfig.theme.primary).toBe("#000000");
    });

    it("should support minimal branding configuration", () => {
      const minimalBrand: BrandingConfig = {
        companyName: "StartupCo",
        theme: {
          primary: "#3b82f6",
          secondary: "#6b7280",
          accent: "#10b981",
          background: "#ffffff",
          foreground: "#1f2937",
          card: "#f9fafb",
          cardForeground: "#1f2937",
          popover: "#ffffff",
          popoverForeground: "#1f2937",
          muted: "#f3f4f6",
          mutedForeground: "#6b7280",
          border: "#d1d5db",
          input: "#d1d5db",
          ring: "#3b82f6",
          radius: "0.375rem",
        },
      };

      expect(minimalBrand.companyName).toBe("StartupCo");
      expect(minimalBrand.logo).toBeUndefined();
      expect(minimalBrand.favicon).toBeUndefined();
      expect(minimalBrand.theme).toBeDefined();
    });

    it("should validate company name", () => {
      const config: BrandingConfig = {
        companyName: "Test Company Ltd.",
        theme: {
          primary: "#000000",
          secondary: "#64748b",
          accent: "#f59e0b",
          background: "#ffffff",
          foreground: "#0f172a",
          card: "#ffffff",
          cardForeground: "#0f172a",
          popover: "#ffffff",
          popoverForeground: "#0f172a",
          muted: "#f1f5f9",
          mutedForeground: "#64748b",
          border: "#e2e8f0",
          input: "#e2e8f0",
          ring: "#000000",
          radius: "0.5rem",
        },
      };

      expect(typeof config.companyName).toBe("string");
      expect(config.companyName.length).toBeGreaterThan(0);
    });
  });

  describe("Type Exports", () => {
    it("should export types correctly", () => {
      // These tests verify that imports work correctly
      const authState: AuthState = {
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      };

      const apiResponse: ApiResponse = {
        status: 200,
      };

      const paginatedResponse: PaginatedResponse = {
        items: [],
        total: 0,
        page: 1,
        size: 10,
        pages: 0,
      };

      expect(authState).toBeDefined();
      expect(apiResponse).toBeDefined();
      expect(paginatedResponse).toBeDefined();
    });
  });
});