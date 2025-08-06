// Minimal test to check if vitest works
import { describe, it, expect } from 'vitest'

describe('basic functionality', () => {
  it('should pass a simple test', () => {
    expect(1 + 1).toBe(2)
  })
})