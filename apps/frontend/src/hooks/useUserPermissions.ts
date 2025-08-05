/**
 * User permissions hook with TanStack Query integration
 * 
 * Provides reactive permission management with caching, real-time updates,
 * and comprehensive error handling for the IAM Dashboard.
 */

import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import { useCallback, useMemo, useEffect } from 'react'
import { 
  AgentName, 
  PermissionActions, 
  UserPermissionMatrix,
  PermissionError,
  PermissionOperation,
  UseUserPermissionsState,
  UseUserPermissionsActions,
  PermissionWebSocketMessage,
} from '@/types/permissions'
import { PermissionAPI } from '@/lib/api/permissions'
import useAuthStore from '@/store/authStore'

// Query keys for permission caching
const PERMISSION_QUERY_KEYS = {
  all: ['permissions'] as const,
  user: (userId: string) => ['permissions', 'user', userId] as const,
  userAgent: (userId: string, agent: AgentName) => ['permissions', 'user', userId, 'agent', agent] as const,
  templates: () => ['permissions', 'templates'] as const,
  audit: (userId: string) => ['permissions', 'audit', userId] as const,
} as const

// WebSocket connection for real-time permission updates
let permissionWebSocket: WebSocket | null = null
let wsReconnectAttempts = 0
const MAX_RECONNECT_ATTEMPTS = 5
const RECONNECT_DELAY = 5000

/**
 * Main hook for user permission management
 */
export function useUserPermissions(userId?: string): UseUserPermissionsState & UseUserPermissionsActions {
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  
  // Use provided userId or current user's id
  const targetUserId = userId || user?.user_id
  
  // Query for user permission matrix
  const {
    data: permissionMatrix,
    isLoading,
    error,
    refetch,
    dataUpdatedAt,
  } = useQuery({
    queryKey: PERMISSION_QUERY_KEYS.user(targetUserId || ''),
    queryFn: () => {
      if (!targetUserId) {
        throw new PermissionError('User ID is required', 'MISSING_USER_ID')
      }
      return PermissionAPI.User.getUserPermissions(targetUserId)
    },
    enabled: !!targetUserId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    retry: (failureCount, error) => {
      // Don't retry on permission errors
      if (error instanceof PermissionError) {
        return false
      }
      return failureCount < 3
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  })

  // WebSocket connection for real-time updates
  useEffect(() => {
    const authState = useAuthStore.getState()
    if (!targetUserId || !authState.token) return

    const connectWebSocket = () => {
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const wsUrl = `${protocol}//${window.location.host}/ws/permissions/${targetUserId}`
        
        permissionWebSocket = new WebSocket(wsUrl)
        
        permissionWebSocket.onopen = () => {
          console.log('Permission WebSocket connected')
          wsReconnectAttempts = 0
          
          // Send authentication token
          const currentAuthState = useAuthStore.getState()
          if (permissionWebSocket && currentAuthState.token) {
            permissionWebSocket.send(JSON.stringify({
              type: 'auth',
              token: currentAuthState.token,
            }))
          }
        }
        
        permissionWebSocket.onmessage = (event) => {
          try {
            const message: PermissionWebSocketMessage = JSON.parse(event.data)
            
            if (message.event.type === 'permission_update' && message.user_id === targetUserId) {
              // Invalidate and refetch permissions on update
              queryClient.invalidateQueries({
                queryKey: PERMISSION_QUERY_KEYS.user(targetUserId),
              })
              
              console.log('Permission update received:', message.event)
            }
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }
        
        permissionWebSocket.onclose = () => {
          console.log('Permission WebSocket disconnected')
          
          // Attempt to reconnect
          if (wsReconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            wsReconnectAttempts++
            setTimeout(connectWebSocket, RECONNECT_DELAY * wsReconnectAttempts)
          }
        }
        
        permissionWebSocket.onerror = (error) => {
          console.error('Permission WebSocket error:', error)
        }
      } catch (error) {
        console.error('Failed to connect to permission WebSocket:', error)
      }
    }
    
    connectWebSocket()
    
    return () => {
      if (permissionWebSocket) {
        permissionWebSocket.close()
        permissionWebSocket = null
      }
    }
  }, [targetUserId, queryClient])

  // Permission checking functions
  const hasPermission = useCallback(
    (agent: AgentName, operation: PermissionOperation): boolean => {
      return PermissionAPI.Utils.hasPermission(
        permissionMatrix?.permissions || null,
        agent,
        operation
      )
    },
    [permissionMatrix?.permissions]
  )

  const hasAgentPermission = useCallback(
    (agent: AgentName): boolean => {
      return PermissionAPI.Utils.hasAgentPermission(
        permissionMatrix?.permissions || null,
        agent
      )
    },
    [permissionMatrix?.permissions]
  )

  const getUserMatrix = useCallback(
    (): UserPermissionMatrix | null => {
      return permissionMatrix || null
    },
    [permissionMatrix]
  )

  // Cache invalidation function
  const invalidate = useCallback(() => {
    if (targetUserId) {
      queryClient.invalidateQueries({
        queryKey: PERMISSION_QUERY_KEYS.user(targetUserId),
      })
    }
  }, [queryClient, targetUserId])

  // Memoized state values
  const state = useMemo((): UseUserPermissionsState => ({
    permissions: permissionMatrix?.permissions || null,
    isLoading,
    error: error instanceof Error ? error : null,
    lastUpdated: dataUpdatedAt ? new Date(dataUpdatedAt) : null,
  }), [permissionMatrix?.permissions, isLoading, error, dataUpdatedAt])

  const actions = useMemo((): UseUserPermissionsActions => ({
    hasPermission,
    hasAgentPermission,
    getUserMatrix,
    refetch,
    invalidate,
  }), [hasPermission, hasAgentPermission, getUserMatrix, refetch, invalidate])

  return { ...state, ...actions }
}

/**
 * Hook for checking specific permission
 */
export function usePermissionCheck(
  agent: AgentName,
  operation: PermissionOperation,
  userId?: string
) {
  const { hasPermission, isLoading, error } = useUserPermissions(userId)
  
  return useMemo(() => ({
    allowed: hasPermission(agent, operation),
    isLoading,
    error,
    agent,
    operation,
  }), [hasPermission, agent, operation, isLoading, error])
}

/**
 * Hook for checking agent access
 */
export function useAgentAccess(agent: AgentName, userId?: string) {
  const { hasAgentPermission, permissions, isLoading, error } = useUserPermissions(userId)
  
  return useMemo(() => {
    const agentPermissions = permissions?.[agent] || null
    
    return {
      hasAccess: hasAgentPermission(agent),
      permissions: agentPermissions,
      isLoading,
      error,
      agent,
    }
  }, [hasAgentPermission, permissions, agent, isLoading, error])
}

/**
 * Hook for permission mutations (update, create, delete)
 */
export function usePermissionMutations(userId?: string) {
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const targetUserId = userId || user?.user_id

  // Update permission mutation
  const updatePermission = useMutation({
    mutationFn: ({
      agent,
      permissions,
    }: {
      agent: AgentName
      permissions: PermissionActions
    }) => {
      if (!targetUserId) {
        throw new PermissionError('User ID is required', 'MISSING_USER_ID')
      }
      // This would need to be updated to find the permission ID first
      // For now, we'll throw an error indicating this needs implementation
      console.log('Update permission requested for:', { targetUserId, agent, permissions })
      throw new PermissionError('Update permission implementation needed', 'NOT_IMPLEMENTED')
    },
    onSuccess: () => {
      if (targetUserId) {
        queryClient.invalidateQueries({
          queryKey: PERMISSION_QUERY_KEYS.user(targetUserId),
        })
      }
    },
    onError: (error) => {
      console.error('Failed to update permission:', error)
    },
  })

  // Create permission mutation
  const createPermission = useMutation({
    mutationFn: ({
      agent,
      permissions,
    }: {
      agent: AgentName
      permissions: PermissionActions
    }) => {
      if (!targetUserId || !user?.user_id) {
        throw new PermissionError('User ID is required', 'MISSING_USER_ID')
      }
      return PermissionAPI.User.createUserPermission({
        user_id: targetUserId,
        agent_name: agent,
        permissions,
        created_by_user_id: user.user_id,
      })
    },
    onSuccess: () => {
      if (targetUserId) {
        queryClient.invalidateQueries({
          queryKey: PERMISSION_QUERY_KEYS.user(targetUserId),
        })
      }
    },
    onError: (error) => {
      console.error('Failed to create permission:', error)
    },
  })

  // Delete permission mutation
  const deletePermission = useMutation({
    mutationFn: (agent: AgentName) => {
      if (!targetUserId) {
        throw new PermissionError('User ID is required', 'MISSING_USER_ID')
      }
      // This would need to be updated to find the permission ID first
      // For now, we'll throw an error indicating this needs implementation
      console.log('Delete permission requested for:', { targetUserId, agent })
      throw new PermissionError('Delete permission implementation needed', 'NOT_IMPLEMENTED')
    },
    onSuccess: () => {
      if (targetUserId) {
        queryClient.invalidateQueries({
          queryKey: PERMISSION_QUERY_KEYS.user(targetUserId),
        })
      }
    },
    onError: (error) => {
      console.error('Failed to delete permission:', error)
    },
  })

  return {
    updatePermission,
    createPermission,
    deletePermission,
    isLoading: updatePermission.isPending || createPermission.isPending || deletePermission.isPending,
    error: updatePermission.error || createPermission.error || deletePermission.error,
  }
}

/**
 * Hook for permission templates
 */
export function usePermissionTemplates() {
  const queryClient = useQueryClient()

  const {
    data: templates,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: PERMISSION_QUERY_KEYS.templates(),
    queryFn: () => PermissionAPI.Template.getTemplates(),
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
  })

  const applyTemplate = useMutation({
    mutationFn: ({
      templateId,
      userId,
      changeReason,
    }: {
      templateId: string
      userId: string
      changeReason?: string
    }) => {
      return PermissionAPI.Template.applyTemplateToUser(templateId, userId, changeReason)
    },
    onSuccess: (_, variables) => {
      // Invalidate user permissions
      queryClient.invalidateQueries({
        queryKey: PERMISSION_QUERY_KEYS.user(variables.userId),
      })
    },
    onError: (error) => {
      console.error('Failed to apply template:', error)
    },
  })

  return {
    templates: templates?.templates || [],
    total: templates?.total || 0,
    isLoading,
    error,
    refetch,
    applyTemplate,
    isApplying: applyTemplate.isPending,
    applyError: applyTemplate.error,
  }
}

/**
 * Hook for permission audit logs
 */
export function usePermissionAudit(userId?: string) {
  const { user } = useAuthStore()
  const targetUserId = userId || user?.user_id

  const {
    data: auditData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: PERMISSION_QUERY_KEYS.audit(targetUserId || ''),
    queryFn: () => {
      if (!targetUserId) {
        throw new PermissionError('User ID is required', 'MISSING_USER_ID')
      }
      return PermissionAPI.Audit.getUserAuditLogs(targetUserId, { limit: 50 })
    },
    enabled: !!targetUserId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 5 * 60 * 1000, // 5 minutes
  })

  return {
    logs: auditData?.logs || [],
    total: auditData?.total || 0,
    isLoading,
    error,
    refetch,
  }
}

// Export query keys for external use
export { PERMISSION_QUERY_KEYS }