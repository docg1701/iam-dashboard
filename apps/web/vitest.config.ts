/// <reference types="vitest/config" />
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'

export default defineConfig({
  plugins: [react()],
  test: {
    // Test environment
    environment: 'jsdom',
    
    // Setup files
    setupFiles: ['./tests/setup.ts'],
    
    // Global test configuration
    globals: true,
    
    // Automatically restore environment variables between tests
    unstubEnvs: true,
    
    // HANG PREVENTION: Critical configuration to prevent test hanging
    // bail removed - runs all tests by default for complete summaries
    // Use --bail=1 flag when needed for fast development feedback
    
    // TIMEOUT CONFIGURATION: Strict timeouts to prevent hanging
    testTimeout: 10000,      // 10 seconds max per test
    hookTimeout: 10000,      // 10 seconds for setup/teardown
    teardownTimeout: 1000,   // 1 second for cleanup
    
    // CONCURRENCY CONTROL: Limit parallel execution to prevent resource exhaustion
    maxConcurrency: 5,       // Max 5 test files running simultaneously
    
    // RETRY CONFIGURATION: No retries to fail fast
    retry: 0,                // Don't retry failed tests
    
    // POOL CONFIGURATION: Use forks for better stability and React component handling
    pool: 'forks',           // Better stability for React components, prevents hanging
    
    // ISOLATION: Disabled for better performance and less hanging
    isolate: false,          // Faster execution, shared context
    clearMocks: true,
    mockReset: true,
    restoreMocks: true,
    
    // Coverage configuration
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      reportsDirectory: './coverage',
      reportOnFailure: true, // Generate coverage report even when tests fail
      include: [
        'src/**/*.{js,ts,jsx,tsx}',
      ],
      exclude: [
        'node_modules/',
        'tests/',
        '**/*.d.ts',
        '**/*.config.*',
        'dist/',
        '.next/',
        'coverage/',
        '**/__tests__/**',
        '**/test-utils.ts*',
        '**/*.stories.*',
        '**/__mocks__/**',
      ],
      thresholds: {
        global: {
          branches: 60,
          functions: 60,
          lines: 60,
          statements: 60,
        },
      },
    },
    
    // Test file patterns - optimized for faster discovery
    include: [
      'src/**/__tests__/**/*.{test,spec}.{js,ts,jsx,tsx}',
      'src/**/*.{test,spec}.{js,ts,jsx,tsx}',
      'tests/**/*.{test,spec}.{js,ts,jsx,tsx}',
    ],
    
    // Exclude patterns - comprehensive to avoid unnecessary processing
    exclude: [
      'node_modules/',
      'dist/',
      '.next/',
      'coverage/',
      '**/*.stories.*',
      '**/__mocks__/**',
      '**/test-utils.*',
      'build/',
      'public/',
      '**/*.disabled',
    ],
    
    // Reporter configuration - optimized to reduce file size
    reporters: ['default', 'json'],
    outputFile: {
      json: './test-summary.json',
      html: './coverage/test-report.html',
    },
  },
  
  // Path resolution
  resolve: {
    alias: (() => {
      const __dirname = fileURLToPath(new URL('.', import.meta.url))
      return [
        {
          find: '@shared/utils',
          replacement: new URL('../../packages/shared/src/utils/index.ts', import.meta.url).pathname,
        },
        {
          find: '@shared',
          replacement: new URL('../../packages/shared/src', import.meta.url).pathname,
        },
        {
          find: '@ui',
          replacement: new URL('../../packages/ui/src', import.meta.url).pathname,
        },
        {
          find: /^@\/(.*)$/,
          replacement: new URL('./src/$1', import.meta.url).pathname,
        },
      ]
    })(),
  },
  
  // Define global variables for tests
  define: {
    __TEST__: true,
  },
})