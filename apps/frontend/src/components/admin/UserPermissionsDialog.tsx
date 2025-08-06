/**
 * User Permissions Dialog Component
 * 
 * Dialog component for managing individual user permissions across all agents
 * with form validation, real-time updates, and comprehensive error handling.
 */

'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { Save, X, Eye, EyeOff, User, Shield, Clock, AlertTriangle } from 'lucide-react'
import {
  AgentName,
  PermissionActions,
  PermissionLevel,
  getPermissionLevel,
  getPermissionsForLevel,
  PERMISSION_LEVELS,
  PERMISSION_LEVEL_NAMES,
  DEFAULT_PERMISSIONS,
} from '@/types/permissions'
import { useUserPermissions, usePermissionMutations, usePermissionAudit } from '@/hooks/useUserPermissions'
import { PermissionGuard, UpdatePermissionGuard } from '@/components/common/PermissionGuard'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { toast } from '@/components/ui/toast'
import { Alert, AlertDescription } from '@/components/ui/alert'

// Types for the component
interface User {
  user_id: string
  name: string
  email: string
  role: 'sysadmin' | 'admin' | 'user'
  is_active: boolean
  created_at: string
  last_login?: string
}

interface UserPermissionsDialogProps {
  user: User | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onPermissionsChanged?: (userId: string) => void
  className?: string
}

interface PermissionFormData {
  permissions: Record<AgentName, PermissionActions>
  changeReason: string
}

// Agent display names in Portuguese
const AGENT_DISPLAY_NAMES: Record<AgentName, string> = {
  [AgentName.CLIENT_MANAGEMENT]: 'Gestão de Clientes',
  [AgentName.PDF_PROCESSING]: 'Processamento de PDFs',
  [AgentName.REPORTS_ANALYSIS]: 'Relatórios e Análises',
  [AgentName.AUDIO_RECORDING]: 'Gravação de Áudio',
}

// Permission level colors
const PERMISSION_LEVEL_COLORS: Record<PermissionLevel, string> = {
  [PERMISSION_LEVELS.NONE]: 'bg-gray-100 text-gray-800 border-gray-200',
  [PERMISSION_LEVELS.READ_ONLY]: 'bg-blue-100 text-blue-800 border-blue-200',
  [PERMISSION_LEVELS.STANDARD]: 'bg-green-100 text-green-800 border-green-200',
  [PERMISSION_LEVELS.FULL]: 'bg-purple-100 text-purple-800 border-purple-200',
}

/**
 * Individual Agent Permission Editor
 */
const AgentPermissionEditor: React.FC<{
  agent: AgentName
  permissions: PermissionActions
  onChange: (agent: AgentName, permissions: PermissionActions) => void
  disabled?: boolean
}> = ({ agent, permissions, onChange, disabled = false }) => {
  const currentLevel = getPermissionLevel(permissions)
  
  const handleLevelChange = useCallback((level: PermissionLevel) => {
    const newPermissions = getPermissionsForLevel(level)
    onChange(agent, newPermissions)
  }, [agent, onChange])

  const handleIndividualPermissionChange = useCallback((
    operation: keyof PermissionActions,
    value: boolean
  ) => {
    const newPermissions = {
      ...permissions,
      [operation]: value,
    }
    onChange(agent, newPermissions)
  }, [agent, permissions, onChange])

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">
            {AGENT_DISPLAY_NAMES[agent]}
          </CardTitle>
          <Badge variant="outline" className={PERMISSION_LEVEL_COLORS[currentLevel]}>
            {PERMISSION_LEVEL_NAMES[currentLevel]}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Quick Level Selection */}
        <div>
          <Label className="text-xs text-muted-foreground">Nível de Acesso</Label>
          <Select
            value={currentLevel}
            onValueChange={handleLevelChange}
            disabled={disabled}
          >
            <SelectTrigger className="h-8">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(PERMISSION_LEVEL_NAMES).map(([levelKey, levelName]) => (
                <SelectItem key={levelKey} value={levelKey}>
                  {levelName}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Individual Permissions */}
        <div className="space-y-2">
          <Label className="text-xs text-muted-foreground">Permissões Detalhadas</Label>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(permissions).map(([operation, value]) => (
              <div key={operation} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id={`${agent}-${operation}`}
                  checked={value}
                  onChange={(e) => handleIndividualPermissionChange(
                    operation as keyof PermissionActions, 
                    e.target.checked
                  )}
                  disabled={disabled}
                  className="rounded border-gray-300"
                />
                <Label 
                  htmlFor={`${agent}-${operation}`}
                  className="text-xs capitalize cursor-pointer"
                >
                  {operation === 'create' && 'Criar'}
                  {operation === 'read' && 'Visualizar'}
                  {operation === 'update' && 'Editar'}
                  {operation === 'delete' && 'Excluir'}
                </Label>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Permission History Component
 */
const PermissionHistory: React.FC<{ userId: string }> = ({ userId }) => {
  const { logs, isLoading, error } = usePermissionAudit(userId)

  if (isLoading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center py-4">
            <div className="animate-spin h-6 w-6 border-b-2 border-gray-900 mx-auto mb-2"></div>
            <p className="text-sm text-muted-foreground">Carregando histórico...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Erro ao carregar histórico de permissões: {error.message}
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm flex items-center">
          <Clock className="h-4 w-4 mr-2" />
          Histórico de Alterações
        </CardTitle>
        <CardDescription className="text-xs">
          Últimas alterações nas permissões deste usuário
        </CardDescription>
      </CardHeader>
      <CardContent>
        {logs.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">
            Nenhuma alteração registrada
          </p>
        ) : (
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {logs.slice(0, 10).map((log) => (
              <div key={log.audit_id} className="border-l-2 border-gray-200 pl-3 py-2">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-medium">
                    {AGENT_DISPLAY_NAMES[log.agent_name]} - {log.action}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {new Date(log.created_at).toLocaleDateString('pt-BR', {
                      day: '2-digit',
                      month: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </div>
                </div>
                {log.change_reason && (
                  <p className="text-xs text-muted-foreground mt-1">
                    {log.change_reason}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

/**
 * Main User Permissions Dialog Component
 */
export const UserPermissionsDialog: React.FC<UserPermissionsDialogProps> = ({
  user,
  open,
  onOpenChange,
  onPermissionsChanged,
  className,
}) => {
  const [formData, setFormData] = useState<PermissionFormData>({
    permissions: {
      [AgentName.CLIENT_MANAGEMENT]: { create: false, read: false, update: false, delete: false },
      [AgentName.PDF_PROCESSING]: { create: false, read: false, update: false, delete: false },
      [AgentName.REPORTS_ANALYSIS]: { create: false, read: false, update: false, delete: false },
      [AgentName.AUDIO_RECORDING]: { create: false, read: false, update: false, delete: false },
    },
    changeReason: '',
  })
  const [hasChanges, setHasChanges] = useState(false)
  const [showHistory, setShowHistory] = useState(false)

  // Get current user permissions
  const { 
    permissions: currentPermissions, 
    isLoading, 
    error: permissionsError 
  } = useUserPermissions(user?.user_id)

  // Permission mutations
  const { 
    updatePermission, 
    createPermission, 
    isLoading: isSaving 
  } = usePermissionMutations(user?.user_id)

  // Load current permissions when user changes
  useEffect(() => {
    if (user && currentPermissions) {
      setFormData({
        permissions: currentPermissions,
        changeReason: '',
      })
      setHasChanges(false)
    }
  }, [user, currentPermissions])

  // Handle permission changes
  const handlePermissionChange = useCallback((
    agent: AgentName, 
    permissions: PermissionActions
  ) => {
    setFormData(prev => ({
      ...prev,
      permissions: {
        ...prev.permissions,
        [agent]: permissions,
      },
    }))
    setHasChanges(true)
  }, [])

  // Handle form submission
  const handleSave = useCallback(async () => {
    if (!user || !hasChanges) return

    try {
      // Update permissions for each agent
      const updatePromises = Object.entries(formData.permissions).map(
        async ([agentName, permissions]) => {
          const agent = agentName as AgentName
          
          // Check if this agent has existing permissions
          const currentAgentPerms = currentPermissions?.[agent]
          
          if (currentAgentPerms) {
            // Update existing permission
            await updatePermission.mutateAsync({
              agent,
              permissions,
            })
          } else {
            // Create new permission
            await createPermission.mutateAsync({
              agent,
              permissions,
            })
          }
        }
      )

      await Promise.all(updatePromises)

      toast({
        title: 'Permissões atualizadas',
        description: `Permissões de ${user.name} foram atualizadas com sucesso.`,
        variant: 'success',
      })

      setHasChanges(false)
      onPermissionsChanged?.(user.user_id)
      onOpenChange(false)
    } catch (error) {
      toast({
        title: 'Erro ao salvar',
        description: 'Não foi possível atualizar as permissões. Tente novamente.',
        variant: 'error',
      })
      console.error('Error saving permissions:', error)
    }
  }, [
    user, 
    hasChanges, 
    formData.permissions, 
    currentPermissions,
    updatePermission,
    createPermission,
    onPermissionsChanged,
    onOpenChange
  ])

  // Reset form when dialog closes
  const handleOpenChange = useCallback((newOpen: boolean) => {
    if (!newOpen && hasChanges) {
      // Show confirmation dialog
      if (window.confirm('Você tem alterações não salvas. Deseja descartar?')) {
        setHasChanges(false)
        onOpenChange(false)
      }
    } else {
      onOpenChange(newOpen)
    }
  }, [hasChanges, onOpenChange])

  if (!user) return null

  return (
    <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="read">
      <Dialog open={open} onOpenChange={handleOpenChange}>
        <DialogContent className={`max-w-4xl max-h-[90vh] overflow-y-auto ${className}`}>
          <DialogHeader>
            <DialogTitle className="flex items-center">
              <User className="h-5 w-5 mr-2" />
              Permissões de {user.name}
            </DialogTitle>
            <DialogDescription>
              Gerencie as permissões de acesso aos agentes para este usuário
            </DialogDescription>
          </DialogHeader>

          {/* User Info */}
          <Card>
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <Label className="text-xs text-muted-foreground">Nome Completo</Label>
                  <p className="font-medium">{user.name}</p>
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Email</Label>
                  <p className="font-medium">{user.email}</p>
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Cargo</Label>
                  <Badge variant={user.role === 'sysadmin' ? 'default' : 'outline'}>
                    {user.role}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Loading State */}
          {isLoading && (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8">
                  <div className="animate-spin h-8 w-8 border-b-2 border-gray-900 mx-auto mb-4"></div>
                  <p className="text-muted-foreground">Carregando permissões...</p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Error State */}
          {permissionsError && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                Erro ao carregar permissões: {permissionsError.message}
              </AlertDescription>
            </Alert>
          )}

          {/* Permissions Form */}
          {!isLoading && !permissionsError && (
            <div className="space-y-6">
              {/* Change Reason */}
              <div>
                <Label htmlFor="changeReason">Motivo da Alteração</Label>
                <Textarea
                  id="changeReason"
                  placeholder="Descreva o motivo desta alteração de permissões..."
                  value={formData.changeReason}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    changeReason: e.target.value 
                  }))}
                  rows={2}
                />
              </div>

              {/* Agent Permissions */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium">Permissões por Agente</h3>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowHistory(!showHistory)}
                  >
                    {showHistory ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    {showHistory ? 'Ocultar' : 'Ver'} Histórico
                  </Button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {Object.entries(AgentName).map(([, agentValue]) => (
                    <UpdatePermissionGuard key={agentValue} agent={AgentName.CLIENT_MANAGEMENT}>
                      <AgentPermissionEditor
                        agent={agentValue}
                        permissions={formData.permissions[agentValue] || DEFAULT_PERMISSIONS}
                        onChange={handlePermissionChange}
                        disabled={isSaving}
                      />
                    </UpdatePermissionGuard>
                  ))}
                </div>
              </div>

              {/* Permission History */}
              {showHistory && (
                <PermissionHistory userId={user.user_id} />
              )}

              {/* Changes Summary */}
              {hasChanges && (
                <Alert>
                  <Shield className="h-4 w-4" />
                  <AlertDescription>
                    Você tem alterações não salvas. Clique em &quot;Salvar Alterações&quot; para aplicar.
                  </AlertDescription>
                </Alert>
              )}
            </div>
          )}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => handleOpenChange(false)}
              disabled={isSaving}
            >
              <X className="h-4 w-4 mr-2" />
              Cancelar
            </Button>
            
            <UpdatePermissionGuard agent={AgentName.CLIENT_MANAGEMENT}>
              <Button
                onClick={handleSave}
                disabled={!hasChanges || isSaving || !formData.changeReason.trim()}
                className="min-w-[140px]"
              >
                {isSaving ? (
                  <>
                    <div className="animate-spin h-4 w-4 border-b-2 border-white mr-2"></div>
                    Salvando...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Salvar Alterações
                  </>
                )}
              </Button>
            </UpdatePermissionGuard>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </PermissionGuard>
  )
}

export default UserPermissionsDialog