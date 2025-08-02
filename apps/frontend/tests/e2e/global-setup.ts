/**
 * Global setup for Playwright E2E tests.
 * 
 * This file runs once before all tests to set up the test environment,
 * including database seeding and authentication setup.
 */

import { chromium, FullConfig } from '@playwright/test'

async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting global setup for E2E tests...')
  
  // Create a browser instance for setup
  const browser = await chromium.launch()
  const page = await browser.newPage()
  
  try {
    // Wait for backend to be ready
    console.log('⏳ Waiting for backend to be ready...')
    await page.goto('http://localhost:8000/health')
    await page.waitForSelector('text=healthy', { timeout: 30000 })
    console.log('✅ Backend is ready')
    
    // Wait for frontend to be ready
    console.log('⏳ Waiting for frontend to be ready...')
    await page.goto('http://localhost:3000')
    await page.waitForLoadState('networkidle', { timeout: 30000 })
    console.log('✅ Frontend is ready')
    
    // TODO: Add database seeding logic here
    // TODO: Add test user creation here
    
    console.log('✅ Global setup completed successfully')
    
  } catch (error) {
    console.error('❌ Global setup failed:', error)
    throw error
  } finally {
    await browser.close()
  }
}

export default globalSetup