import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    globals: true,
    css: true,
    env: {
      IS_REACT_ACT_ENVIRONMENT: "true",
    },
    onConsoleLog: (log: string, type: "stdout" | "stderr") => {
      if (
        type === "stderr" &&
        (log.includes(
          "An update to Select inside a test was not wrapped in act",
        ) ||
          log.includes(
            "An update to SelectItemText inside a test was not wrapped in act",
          ))
      ) {
        return false; // Suppress these specific warnings
      }
      return true;
    },
    // Pattern que funciona com a estrutura existente
    include: ["src/**/*.{test,spec}.{js,ts,jsx,tsx}"],
    exclude: [
      "**/node_modules/**",
      "**/e2e/**/*",
      "**/playwright.config.ts",
      "**/*.spec.ts",
    ],
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "json", "clover"],
      include: ["src/**/*.{js,ts,jsx,tsx}"],
      exclude: [
        "src/test/**",
        "src/**/*.test.{ts,tsx}",
        "src/**/__tests__/**",
        "**/*.d.ts",
        "**/*.config.*",
        "src/app/layout.tsx",
        "src/app/page.tsx",
      ],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80,
      },
      reportOnFailure: true,
      clean: false,
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
