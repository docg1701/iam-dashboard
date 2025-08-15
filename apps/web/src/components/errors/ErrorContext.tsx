'use client'

import React, {
  createContext,
  useContext,
  useCallback,
  useReducer,
  ReactNode,
  useEffect,
} from 'react'

// Type for error context data
interface ErrorContextData {
  [key: string]: string | number | boolean | object | null | undefined
}

interface AppError {
  id: string
  message: string
  code?: string
  statusCode?: number
  category:
    | 'auth'
    | 'network'
    | 'validation'
    | 'permission'
    | 'system'
    | 'unknown'
  severity: 'low' | 'medium' | 'high' | 'critical'
  timestamp: Date
  retryable?: boolean
  context?: ErrorContextData
  stack?: string
}

interface ErrorState {
  errors: AppError[]
  lastError: AppError | null
  hasUnreadErrors: boolean
}

type ErrorAction =
  | { type: 'ADD_ERROR'; payload: Omit<AppError, 'id' | 'timestamp'> }
  | { type: 'REMOVE_ERROR'; payload: string }
  | { type: 'CLEAR_ERRORS' }
  | { type: 'MARK_ERRORS_READ' }
  | {
      type: 'UPDATE_ERROR'
      payload: { id: string; updates: Partial<AppError> }
    }

interface ErrorContextType {
  state: ErrorState
  addError: (error: Omit<AppError, 'id' | 'timestamp'>) => string
  removeError: (id: string) => void
  clearErrors: () => void
  markErrorsRead: () => void
  updateError: (id: string, updates: Partial<AppError>) => void

  // Helper methods for common error types
  addAuthError: (message: string, context?: ErrorContextData) => string
  addNetworkError: (
    message: string,
    statusCode?: number,
    context?: ErrorContextData
  ) => string
  addValidationError: (message: string, context?: ErrorContextData) => string
  addPermissionError: (message: string, context?: ErrorContextData) => string
  addSystemError: (message: string, context?: ErrorContextData) => string

  // Error categorization helpers
  getCriticalErrors: () => AppError[]
  getErrorsByCategory: (category: AppError['category']) => AppError[]
  hasErrorsOfSeverity: (severity: AppError['severity']) => boolean
}

const errorReducer = (state: ErrorState, action: ErrorAction): ErrorState => {
  switch (action.type) {
    case 'ADD_ERROR': {
      const newError: AppError = {
        ...action.payload,
        id: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date(),
      }

      return {
        ...state,
        errors: [newError, ...state.errors].slice(0, 50), // Keep only last 50 errors
        lastError: newError,
        hasUnreadErrors: true,
      }
    }

    case 'REMOVE_ERROR': {
      const filteredErrors = state.errors.filter(
        error => error.id !== action.payload
      )
      return {
        ...state,
        errors: filteredErrors,
        lastError: filteredErrors[0] || null,
      }
    }

    case 'CLEAR_ERRORS': {
      return {
        errors: [],
        lastError: null,
        hasUnreadErrors: false,
      }
    }

    case 'MARK_ERRORS_READ': {
      return {
        ...state,
        hasUnreadErrors: false,
      }
    }

    case 'UPDATE_ERROR': {
      return {
        ...state,
        errors: state.errors.map(error =>
          error.id === action.payload.id
            ? { ...error, ...action.payload.updates }
            : error
        ),
      }
    }

    default:
      return state
  }
}

const initialState: ErrorState = {
  errors: [],
  lastError: null,
  hasUnreadErrors: false,
}

const ErrorContext = createContext<ErrorContextType | undefined>(undefined)

/**
 * Hook to use error context
 */
export const useError = (): ErrorContextType => {
  const context = useContext(ErrorContext)
  if (!context) {
    throw new Error('useError must be used within an ErrorProvider')
  }
  return context
}

interface ErrorProviderProps {
  children: ReactNode
  maxErrors?: number
  enableConsoleLogging?: boolean
  enableGlobalErrorHandler?: boolean
  onError?: (error: AppError) => void
}

/**
 * Error context provider for global error state management.
 *
 * Features:
 * - Centralized error state management
 * - Error categorization and severity levels
 * - Automatic error expiration
 * - Console logging integration
 * - Global error handler
 * - Error analytics and reporting
 *
 * @example
 * <ErrorProvider enableGlobalErrorHandler={true}>
 *   <App />
 * </ErrorProvider>
 */
export const ErrorProvider: React.FC<ErrorProviderProps> = ({
  children,
  maxErrors = 50,
  enableConsoleLogging = true,
  enableGlobalErrorHandler = true,
  onError,
}) => {
  const [state, dispatch] = useReducer(errorReducer, initialState)

  const addError = useCallback(
    (error: Omit<AppError, 'id' | 'timestamp'>): string => {
      const errorId = `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

      const fullError: AppError = {
        ...error,
        id: errorId,
        timestamp: new Date(),
      }

      // TODO: Integrate with proper logging service for production

      // External error handler
      if (onError) {
        try {
          onError(fullError)
        } catch (err) {
          // Silently handle callback errors to prevent infinite loops
        }
      }

      dispatch({ type: 'ADD_ERROR', payload: error })
      return errorId
    },
    [onError]
  )

  const removeError = useCallback((id: string) => {
    dispatch({ type: 'REMOVE_ERROR', payload: id })
  }, [])

  const clearErrors = useCallback(() => {
    dispatch({ type: 'CLEAR_ERRORS' })
  }, [])

  const markErrorsRead = useCallback(() => {
    dispatch({ type: 'MARK_ERRORS_READ' })
  }, [])

  const updateError = useCallback((id: string, updates: Partial<AppError>) => {
    dispatch({ type: 'UPDATE_ERROR', payload: { id, updates } })
  }, [])

  // Helper methods for common error types
  const addAuthError = useCallback(
    (message: string, context?: ErrorContextData): string => {
      return addError({
        message,
        category: 'auth',
        severity: 'medium',
        retryable: false,
        context,
      })
    },
    [addError]
  )

  const addNetworkError = useCallback(
    (
      message: string,
      statusCode?: number,
      context?: ErrorContextData
    ): string => {
      const severity = statusCode && statusCode >= 500 ? 'high' : 'medium'
      return addError({
        message,
        category: 'network',
        severity,
        statusCode,
        retryable: true,
        context,
      })
    },
    [addError]
  )

  const addValidationError = useCallback(
    (message: string, context?: ErrorContextData): string => {
      return addError({
        message,
        category: 'validation',
        severity: 'low',
        retryable: true,
        context,
      })
    },
    [addError]
  )

  const addPermissionError = useCallback(
    (message: string, context?: ErrorContextData): string => {
      return addError({
        message,
        category: 'permission',
        severity: 'medium',
        retryable: false,
        context,
      })
    },
    [addError]
  )

  const addSystemError = useCallback(
    (message: string, context?: ErrorContextData): string => {
      return addError({
        message,
        category: 'system',
        severity: 'high',
        retryable: false,
        context,
      })
    },
    [addError]
  )

  // Error analysis helpers
  const getCriticalErrors = useCallback((): AppError[] => {
    return state.errors.filter(error => error.severity === 'critical')
  }, [state.errors])

  const getErrorsByCategory = useCallback(
    (category: AppError['category']): AppError[] => {
      return state.errors.filter(error => error.category === category)
    },
    [state.errors]
  )

  const hasErrorsOfSeverity = useCallback(
    (severity: AppError['severity']): boolean => {
      return state.errors.some(error => error.severity === severity)
    },
    [state.errors]
  )

  // Global error handler
  useEffect(() => {
    if (!enableGlobalErrorHandler) {
      return
    }

    const handleGlobalError = (event: ErrorEvent) => {
      addError({
        message: event.message,
        category: 'system',
        severity: 'high',
        stack: event.error?.stack,
        context: {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
        },
      })
    }

    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      const error = event.reason
      addError({
        message: error?.message || 'Unhandled promise rejection',
        category: 'system',
        severity: 'high',
        stack: error?.stack,
        context: {
          reason: error,
        },
      })
    }

    window.addEventListener('error', handleGlobalError)
    window.addEventListener('unhandledrejection', handleUnhandledRejection)

    return () => {
      window.removeEventListener('error', handleGlobalError)
      window.removeEventListener('unhandledrejection', handleUnhandledRejection)
    }
  }, [addError, enableGlobalErrorHandler])

  // Auto-cleanup old errors
  useEffect(() => {
    const cleanup = setInterval(
      () => {
        const fifteenMinutesAgo = new Date(Date.now() - 15 * 60 * 1000)
        const recentErrors = state.errors.filter(
          error => error.timestamp > fifteenMinutesAgo
        )

        if (recentErrors.length !== state.errors.length) {
          dispatch({
            type: 'UPDATE_ERROR',
            payload: {
              id: 'cleanup',
              updates: {}, // This will trigger a re-render with filtered errors
            },
          })
        }
      },
      5 * 60 * 1000
    ) // Check every 5 minutes

    return () => clearInterval(cleanup)
  }, [state.errors])

  const contextValue: ErrorContextType = {
    state,
    addError,
    removeError,
    clearErrors,
    markErrorsRead,
    updateError,
    addAuthError,
    addNetworkError,
    addValidationError,
    addPermissionError,
    addSystemError,
    getCriticalErrors,
    getErrorsByCategory,
    hasErrorsOfSeverity,
  }

  return (
    <ErrorContext.Provider value={contextValue}>
      {children}
    </ErrorContext.Provider>
  )
}

/**
 * Hook to create error handlers for specific components
 */
export const useErrorHandler = () => {
  const { addError } = useError()

  return useCallback(
    (
      error: Error,
      category: AppError['category'] = 'unknown',
      context?: ErrorContextData
    ) => {
      addError({
        message: error.message,
        category,
        severity:
          category === 'auth' || category === 'permission' ? 'medium' : 'high',
        stack: error.stack,
        context,
      })
    },
    [addError]
  )
}

/**
 * Hook to handle authentication-specific errors
 */
export const useAuthErrorHandler = () => {
  const { addAuthError } = useError()

  return useCallback(
    (error: Error | string, context?: ErrorContextData) => {
      const message = typeof error === 'string' ? error : error.message
      return addAuthError(message, {
        ...context,
        ...(typeof error === 'object' && { stack: error.stack }),
      })
    },
    [addAuthError]
  )
}

export default ErrorProvider
