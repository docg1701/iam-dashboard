import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
    css: true,
    exclude: [
      '**/node_modules/**',
      '**/e2e/**',
      '**/*.spec.ts',
      '**/playwright.config.ts'
    ],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      include: ['src/**'],
      exclude: [
        'node_modules/',
        'src/test/',
        'e2e/**',
        '**/*.d.ts',
        '**/*.config.*',
        '.next/**',
        'dist/**',
        'coverage/**',
        'test-debug.js',
        'src/**/*.test.{ts,tsx}',
        'src/**/__tests__/**'
      ],
      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80
        }
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})