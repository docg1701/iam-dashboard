/**
 * Permission Updates Hook
 * 
 * Hook for managing real-time permission updates via WebSocket connection
 * with automatic reconnection, toast notifications, and cache invalidation.
 */

import { useEffect, useCallback, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { 
  AgentName, 
  PermissionWebSocketMessage,
  PermissionUpdateEvent,
} from '@/types/permissions'
import { toast } from '@/components/ui/toast'
import useAuthStore from '@/store/authStore'

// WebSocket connection management
interface WebSocketManager {
  connection: WebSocket | null
  reconnectAttempts: number
  reconnectTimeout: number | null
  isConnecting: boolean
}

interface UsePermissionUpdatesOptions {
  onPermissionUpdate?: (event: PermissionUpdateEvent) => void
  enableToastNotifications?: boolean
  autoReconnect?: boolean
  maxReconnectAttempts?: number
  reconnectDelay?: number
}

interface UsePermissionUpdatesReturn {
  isConnected: boolean
  isConnecting: boolean
  connectionError: string | null
  reconnectAttempts: number
  connect: () => void
  disconnect: () => void
}

const MAX_RECONNECT_ATTEMPTS = 5
const RECONNECT_DELAY = 5000
const PING_INTERVAL = 30000 // 30 seconds

// Agent display names for notifications
const AGENT_DISPLAY_NAMES: Record<AgentName, string> = {
  [AgentName.CLIENT_MANAGEMENT]: 'Gestão de Clientes',
  [AgentName.PDF_PROCESSING]: 'Processamento PDFs',
  [AgentName.REPORTS_ANALYSIS]: 'Relatórios',
  [AgentName.AUDIO_RECORDING]: 'Gravação de Áudio',
}

/**
 * Hook for real-time permission updates
 */
export function usePermissionUpdates(
  options: UsePermissionUpdatesOptions = {}
): UsePermissionUpdatesReturn {
  const {
    onPermissionUpdate,
    enableToastNotifications = true,
    autoReconnect = true,
    maxReconnectAttempts = MAX_RECONNECT_ATTEMPTS,
    reconnectDelay = RECONNECT_DELAY,
  } = options

  const queryClient = useQueryClient()
  const { user, token } = useAuthStore()
  
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [connectionError, setConnectionError] = useState<string | null>(null)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)

  const wsManagerRef = useRef<WebSocketManager>({
    connection: null,
    reconnectAttempts: 0,
    reconnectTimeout: null,
    isConnecting: false,
  })

  const pingIntervalRef = useRef<number | null>(null)

  // Handle incoming permission update messages
  const handlePermissionUpdate = useCallback((event: PermissionUpdateEvent) => {
    console.log('Permission update received:', event)

    // Invalidate relevant queries
    queryClient.invalidateQueries({
      queryKey: ['permissions', 'user', event.user_id],
    })
    
    queryClient.invalidateQueries({
      queryKey: ['admin-user-permissions'],
    })

    queryClient.invalidateQueries({
      queryKey: ['permission-matrix'],
    })

    // Call custom handler if provided
    onPermissionUpdate?.(event)

    // Show toast notification if enabled
    if (enableToastNotifications) {
      const agentName = AGENT_DISPLAY_NAMES[event.agent_name] || event.agent_name
      
      toast({
        title: 'Permissões atualizadas',
        description: `Permissões de ${agentName} foram atualizadas em tempo real.`,
        variant: 'default',
      })
    }
  }, [queryClient, onPermissionUpdate, enableToastNotifications])

  // WebSocket connection function
  const connect = useCallback(() => {
    if (!user?.user_id || !token) {
      console.warn('Cannot connect to permission updates: user not authenticated')
      return
    }

    if (wsManagerRef.current.connection?.readyState === WebSocket.OPEN) {
      console.log('Permission updates WebSocket already connected')
      return
    }

    if (wsManagerRef.current.isConnecting) {
      console.log('Permission updates WebSocket connection already in progress')
      return
    }

    try {
      setIsConnecting(true)
      setConnectionError(null)
      wsManagerRef.current.isConnecting = true

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/ws/permissions`
      
      console.log('Connecting to permission updates WebSocket:', wsUrl)
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        console.log('Permission updates WebSocket connected')
        setIsConnected(true)
        setIsConnecting(false)
        setConnectionError(null)
        setReconnectAttempts(0)
        wsManagerRef.current.isConnecting = false
        wsManagerRef.current.reconnectAttempts = 0

        // Send authentication
        ws.send(JSON.stringify({
          type: 'auth',
          token: token,
          user_id: user.user_id,
        }))

        // Start ping interval
        pingIntervalRef.current = window.setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }))
          }
        }, PING_INTERVAL)
      }

      ws.onmessage = (event) => {
        try {
          const message: PermissionWebSocketMessage = JSON.parse(event.data)
          
          if (message.event.type === 'permission_update') {
            handlePermissionUpdate(message.event)
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.onclose = (event) => {
        console.log('Permission updates WebSocket closed:', event.code, event.reason)
        setIsConnected(false)
        setIsConnecting(false)
        wsManagerRef.current.isConnecting = false
        
        // Clear ping interval
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current)
          pingIntervalRef.current = null
        }

        // Attempt reconnection if enabled and not manually closed
        if (autoReconnect && event.code !== 1000 && wsManagerRef.current.reconnectAttempts < maxReconnectAttempts) {
          const attempts = wsManagerRef.current.reconnectAttempts + 1
          wsManagerRef.current.reconnectAttempts = attempts
          setReconnectAttempts(attempts)
          
          console.log(`Attempting to reconnect (${attempts}/${maxReconnectAttempts})...`)
          
          wsManagerRef.current.reconnectTimeout = window.setTimeout(() => {
            connect()
          }, reconnectDelay * attempts)
        } else if (wsManagerRef.current.reconnectAttempts >= maxReconnectAttempts) {
          setConnectionError('Máximo de tentativas de reconexão atingido')
          
          if (enableToastNotifications) {
            toast({
              title: 'Conexão perdida',
              description: 'Não foi possível reconectar às atualizações em tempo real.',
              variant: 'error',
            })
          }
        }
      }

      ws.onerror = (error) => {
        console.error('Permission updates WebSocket error:', error)
        setConnectionError('Erro de conexão WebSocket')
        setIsConnecting(false)
        wsManagerRef.current.isConnecting = false
      }

      wsManagerRef.current.connection = ws
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      setConnectionError('Falha ao criar conexão WebSocket')
      setIsConnecting(false)
      wsManagerRef.current.isConnecting = false
    }
  }, [user, token, handlePermissionUpdate, autoReconnect, maxReconnectAttempts, reconnectDelay, enableToastNotifications])

  // WebSocket disconnection function
  const disconnect = useCallback(() => {
    console.log('Disconnecting permission updates WebSocket')
    
    // Clear reconnect timeout
    if (wsManagerRef.current.reconnectTimeout) {
      clearTimeout(wsManagerRef.current.reconnectTimeout)
      wsManagerRef.current.reconnectTimeout = null
    }

    // Clear ping interval
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
      pingIntervalRef.current = null
    }

    // Close WebSocket connection
    if (wsManagerRef.current.connection) {
      wsManagerRef.current.connection.close(1000, 'Manual disconnect')
      wsManagerRef.current.connection = null
    }

    setIsConnected(false)
    setIsConnecting(false)
    setConnectionError(null)
    setReconnectAttempts(0)
    wsManagerRef.current.reconnectAttempts = 0
    wsManagerRef.current.isConnecting = false
  }, [])

  // Auto-connect on mount and reconnect when auth changes
  useEffect(() => {
    if (user?.user_id && token) {
      connect()
    } else {
      disconnect()
    }

    return () => {
      disconnect()
    }
  }, [user?.user_id, token, connect, disconnect])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  return {
    isConnected,
    isConnecting,
    connectionError,
    reconnectAttempts,
    connect,
    disconnect,
  }
}

/**
 * Hook for permission update notifications
 * Simplified version that just handles notifications
 */
export function usePermissionNotifications(enabled: boolean = true) {
  return usePermissionUpdates({
    enableToastNotifications: enabled,
    autoReconnect: true,
  })
}

/**
 * Hook for specific user permission updates
 */
export function useUserPermissionUpdates(
  userId: string,
  onUpdate?: (event: PermissionUpdateEvent) => void
) {
  return usePermissionUpdates({
    onPermissionUpdate: (event) => {
      if (event.user_id === userId) {
        onUpdate?.(event)
      }
    },
    enableToastNotifications: true,
  })
}