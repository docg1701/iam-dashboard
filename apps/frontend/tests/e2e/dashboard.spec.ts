/**
 * Dashboard E2E tests.
 * 
 * Tests for main dashboard functionality and navigation.
 */

import { test, expect } from '@playwright/test'

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // TODO: Login as admin user before each test
    // await loginAsAdmin(page)
    await page.goto('/dashboard')
  })

  test('should display dashboard home page', async ({ page }) => {
    // Check main dashboard elements
    await expect(page.locator('h1')).toContainText('Dashboard')
    await expect(page.locator('[data-testid="sidebar"]')).toBeVisible()
    await expect(page.locator('[data-testid="main-content"]')).toBeVisible()
  })

  test('should navigate to client management', async ({ page }) => {
    // Click on clients navigation
    await page.click('text=Clients')
    
    // Should navigate to clients page
    await expect(page).toHaveURL('/dashboard/clients')
    await expect(page.locator('h1')).toContainText('Clients')
  })

  test('should navigate to user management (admin only)', async ({ page }) => {
    // Click on users navigation
    await page.click('text=Users')
    
    // Should navigate to users page
    await expect(page).toHaveURL('/dashboard/users')
    await expect(page.locator('h1')).toContainText('Users')
  })

  test('should show system information', async ({ page }) => {
    // Navigate to system page
    await page.click('text=System')
    
    // Should show system information
    await expect(page).toHaveURL('/dashboard/system')
    await expect(page.locator('text=System Information')).toBeVisible()
  })

  test('should be responsive on mobile', async ({ page }) => {
    // Resize to mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })
    
    // Should show mobile navigation
    await expect(page.locator('[data-testid="mobile-menu-button"]')).toBeVisible()
    
    // Sidebar should be hidden by default on mobile
    await expect(page.locator('[data-testid="sidebar"]')).toBeHidden()
    
    // Click mobile menu
    await page.click('[data-testid="mobile-menu-button"]')
    
    // Sidebar should now be visible
    await expect(page.locator('[data-testid="sidebar"]')).toBeVisible()
  })

  test('should handle theme switching', async ({ page }) => {
    // TODO: Test theme switching when implemented
    
    // Find theme toggle
    const themeToggle = page.locator('[data-testid="theme-toggle"]')
    
    if (await themeToggle.isVisible()) {
      // Click theme toggle
      await themeToggle.click()
      
      // Check that theme class changed
      const body = page.locator('body')
      await expect(body).toHaveClass(/dark|light/)
    }
  })
})