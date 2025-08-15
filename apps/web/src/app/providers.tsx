'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { useState } from 'react'

import { ErrorProvider } from '@/components/errors/ErrorContext'
import { ThemeProvider } from '@/components/theme-provider'
import { Toaster } from '@/components/ui/toaster'
import { AuthProvider } from '@/contexts/AuthContext'

// Type for HTTP errors with response status
interface HttpError extends Error {
  response?: {
    status: number
  }
}

// Type guard to check if error has HTTP response
function isHttpError(error: unknown): error is HttpError {
  return error instanceof Error && 'response' in error
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
            retry: (failureCount, error) => {
              // Don't retry on 4xx errors except 408, 429
              if (isHttpError(error)) {
                const status = error.response?.status
                if (
                  status &&
                  status >= 400 &&
                  status < 500 &&
                  ![408, 429].includes(status)
                ) {
                  return false
                }
              }
              return failureCount < 3
            },
            retryDelay: attemptIndex =>
              Math.min(1000 * 2 ** attemptIndex, 30000),
          },
          mutations: {
            retry: (failureCount, error) => {
              // Don't retry mutations on client errors
              if (isHttpError(error)) {
                const status = error.response?.status
                if (status && status >= 400 && status < 500) {
                  return false
                }
              }
              return failureCount < 2
            },
          },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>
      <ErrorProvider>
        <AuthProvider>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            {children}
            <Toaster />
            <ReactQueryDevtools initialIsOpen={false} />
          </ThemeProvider>
        </AuthProvider>
      </ErrorProvider>
    </QueryClientProvider>
  )
}
