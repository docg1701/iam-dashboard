import { test, expect } from "@playwright/test";

test.describe("Critical User Flows", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto("http://localhost:3000");
  });

  test("complete user journey - login to dashboard", async ({ page }) => {
    // Login flow
    await expect(page.locator("h1")).toContainText("IAM Dashboard");

    // Fill login form
    await page.fill('input[name="email"]', "admin@example.com");
    await page.fill('input[name="password"]', "password123");
    await page.click('button[type="submit"]');

    // Wait for potential 2FA or direct dashboard access
    await page.waitForLoadState("networkidle");

    // Check if we're redirected to dashboard or 2FA
    const currentUrl = page.url();
    if (
      currentUrl.includes("2fa") ||
      (await page.locator('input[name="code"]').isVisible())
    ) {
      // Handle 2FA flow
      await page.fill('input[name="code"]', "123456");
      await page.click('button[type="submit"]');
    }

    // Verify dashboard is loaded
    await page.waitForLoadState("networkidle");
    await expect(
      page.locator('h1, h2, [data-testid="dashboard-title"]'),
    ).toContainText(/dashboard/i);
  });

  test("client management workflow", async ({ page }) => {
    // Login first
    await page.fill('input[name="email"]', "admin@example.com");
    await page.fill('input[name="password"]', "password123");
    await page.click('button[type="submit"]');
    await page.waitForLoadState("networkidle");

    // Navigate to clients section
    await page.click('a[href*="clients"], button:has-text("Clientes")');
    await page.waitForLoadState("networkidle");

    // Verify we're on clients page
    await expect(page.locator("h1, h2")).toContainText(/client/i);

    // Try to create new client
    const newClientButton = page.locator(
      'button:has-text("Adicionar"), button:has-text("Novo"), button:has-text("Criar")',
    );
    if (await newClientButton.isVisible()) {
      await newClientButton.click();

      // Fill client form
      await page.waitForSelector('input[name="name"], input[name="full_name"]');
      await page.fill(
        'input[name="name"], input[name="full_name"]',
        "João Silva",
      );

      const cpfInput = page.locator('input[name="cpf"]');
      if (await cpfInput.isVisible()) {
        await cpfInput.fill("123.456.789-09");
      }

      const birthDateInput = page.locator(
        'input[name="birth_date"], input[type="date"]',
      );
      if (await birthDateInput.isVisible()) {
        await birthDateInput.fill("1990-01-15");
      }

      // Submit form
      await page.click(
        'button[type="submit"], button:has-text("Criar"), button:has-text("Salvar")',
      );
      await page.waitForLoadState("networkidle");
    }

    // Verify we can see clients list
    await expect(
      page.locator('table, .client-list, [data-testid="clients-table"]'),
    ).toBeVisible();
  });

  test("user management and permissions flow", async ({ page }) => {
    // Login as admin
    await page.fill('input[name="email"]', "admin@example.com");
    await page.fill('input[name="password"]', "password123");
    await page.click('button[type="submit"]');
    await page.waitForLoadState("networkidle");

    // Navigate to user management
    await page.click(
      'a[href*="users"], a[href*="usuarios"], button:has-text("Usuários")',
    );
    await page.waitForLoadState("networkidle");

    // Verify users page loaded
    await expect(page.locator("h1, h2")).toContainText(/usuário|user/i);

    // Try to access permission management
    const permissionLink = page.locator(
      'a[href*="permissions"], a[href*="permissoes"], button:has-text("Permissões")',
    );
    if (await permissionLink.isVisible()) {
      await permissionLink.click();
      await page.waitForLoadState("networkidle");

      // Verify permission matrix or management interface
      await expect(
        page.locator(
          'table, .permission-matrix, [data-testid="permission-matrix"]',
        ),
      ).toBeVisible();
    }
  });

  test("responsive design - mobile view", async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Login
    await page.fill('input[name="email"]', "admin@example.com");
    await page.fill('input[name="password"]', "password123");
    await page.click('button[type="submit"]');
    await page.waitForLoadState("networkidle");

    // Verify mobile navigation
    const hamburgerMenu = page.locator(
      'button[aria-label*="menu"], .hamburger, [data-testid="mobile-menu"]',
    );
    if (await hamburgerMenu.isVisible()) {
      await hamburgerMenu.click();

      // Verify mobile menu opened
      await expect(
        page.locator('nav, .mobile-nav, [data-testid="mobile-navigation"]'),
      ).toBeVisible();
    }

    // Test mobile interactions
    await page.tap("body"); // Close menu if open

    // Verify responsive components work
    await expect(page.locator("body")).toBeVisible();
  });

  test("error handling and recovery", async ({ page }) => {
    // Test with invalid credentials
    await page.fill('input[name="email"]', "invalid@example.com");
    await page.fill('input[name="password"]', "wrongpassword");
    await page.click('button[type="submit"]');

    // Verify error message appears
    await expect(
      page.locator('.error, [role="alert"], .alert-error'),
    ).toBeVisible();

    // Test recovery - valid credentials
    await page.fill('input[name="email"]', "admin@example.com");
    await page.fill('input[name="password"]', "password123");
    await page.click('button[type="submit"]');
    await page.waitForLoadState("networkidle");

    // Verify successful login
    const currentUrl = page.url();
    expect(currentUrl).toMatch(/dashboard|home/);
  });

  test("accessibility - keyboard navigation", async ({ page }) => {
    // Test keyboard navigation through login form
    await page.keyboard.press("Tab"); // Focus email
    await page.keyboard.type("admin@example.com");

    await page.keyboard.press("Tab"); // Focus password
    await page.keyboard.type("password123");

    await page.keyboard.press("Tab"); // Focus submit button
    await page.keyboard.press("Enter"); // Submit form

    await page.waitForLoadState("networkidle");

    // Verify login was successful via keyboard
    const currentUrl = page.url();
    expect(currentUrl).not.toContain("login");
  });
});
