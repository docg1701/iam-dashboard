/**
 * Tests for environment configuration.
 * 
 * This module tests environment variable validation and configuration.
 */

import { describe, it, expect } from 'vitest'
import { env } from '@/lib/env'

describe('Environment configuration', () => {
  it('should have required environment variables', () => {
    expect(env).toBeDefined()
    expect(env.NEXT_PUBLIC_API_URL).toBeDefined()
    expect(env.NEXT_PUBLIC_APP_NAME).toBeDefined()
    expect(env.NODE_ENV).toBeDefined()
  })

  it('should have valid default values', () => {
    expect(env.NEXT_PUBLIC_API_URL).toMatch(/^https?:\/\//)
    expect(env.NEXT_PUBLIC_APP_NAME).toContain('Dashboard')
    expect(['development', 'test', 'production']).toContain(env.NODE_ENV)
  })

  it('should have proper API URL format', () => {
    const url = env.NEXT_PUBLIC_API_URL
    expect(url).toMatch(/^https?:\/\/[^\s]+$/)
  })

  it('should have non-empty app name', () => {
    expect(env.NEXT_PUBLIC_APP_NAME.length).toBeGreaterThan(0)
  })
})