import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright configuration for Multi-Agent IAM Dashboard E2E tests.
 *
 * See https://playwright.dev/docs/test-configuration.
 */
export default defineConfig({
  // Test directory
  testDir: "./tests/e2e",

  // Run tests in files in parallel
  fullyParallel: true,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Opt out of parallel tests on CI
  workers: process.env.CI ? 1 : undefined,

  // Reporter to use
  reporter: [
    ["html"],
    ["json", { outputFile: "test-results/results.json" }],
    ["junit", { outputFile: "test-results/results.xml" }],
    ...(process.env.CI ? [["github"]] : [["list"]]),
  ],

  // Shared settings for all the projects below
  use: {
    // Base URL to use in actions like `await page.goto('/')`
    baseURL: process.env.BASE_URL || "http://localhost:3000",

    // Collect trace when retrying the failed test
    trace: "on-first-retry",

    // Take screenshot on failure
    screenshot: "only-on-failure",

    // Record video on failure
    video: "retain-on-failure",

    // Global test timeout
    actionTimeout: 15 * 1000,

    // Expect timeout for assertions
    expect: {
      timeout: 10 * 1000,
    },
  },

  // Configure projects for major browsers
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },

    {
      name: "firefox",
      use: { ...devices["Desktop Firefox"] },
    },

    {
      name: "webkit",
      use: { ...devices["Desktop Safari"] },
    },

    // Test against mobile viewports
    {
      name: "Mobile Chrome",
      use: { ...devices["Pixel 5"] },
    },
    {
      name: "Mobile Safari",
      use: { ...devices["iPhone 12"] },
    },

    // Test against branded browsers
    {
      name: "Microsoft Edge",
      use: { ...devices["Desktop Edge"], channel: "msedge" },
    },
    {
      name: "Google Chrome",
      use: { ...devices["Desktop Chrome"], channel: "chrome" },
    },
  ],

  // Run your local dev server before starting the tests
  webServer: [
    {
      command: "npm run dev",
      url: "http://localhost:3000",
      timeout: 120 * 1000,
      reuseExistingServer: !process.env.CI,
    },
    {
      command:
        "cd ../backend && uv run uvicorn src.main:app --host 0.0.0.0 --port 8000",
      url: "http://localhost:8000/health",
      timeout: 120 * 1000,
      reuseExistingServer: !process.env.CI,
    },
  ],

  // Global setup and teardown
  globalSetup: require.resolve("./tests/e2e/global-setup.ts"),
  globalTeardown: require.resolve("./tests/e2e/global-teardown.ts"),

  // Test timeout
  timeout: 30 * 1000,

  // Output directory for test artifacts
  outputDir: "test-results/",

  // Maximum number of concurrent worker processes
  maxFailures: process.env.CI ? 10 : undefined,
});
