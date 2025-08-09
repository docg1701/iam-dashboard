/**
 * Admin Permissions Management Page
 * 
 * Main dashboard page for administrators to manage user permissions across all agents
 * with comprehensive filtering, bulk operations, and real-time updates.
 */

'use client'

import React, { useState, useCallback, useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { 
  Users, 
  Shield, 
  Settings, 
  Plus, 
  Filter,
  Download,
  Upload,
  AlertTriangle,
  Search,
} from 'lucide-react'
import { PermissionAPI } from '@/lib/api/permissions'
import { PermissionGuard } from '@/components/common/PermissionGuard'
import { PermissionMatrix } from '@/components/admin/PermissionMatrix'
import { UserPermissionsDialog } from '@/components/admin/UserPermissionsDialog'
import { BulkPermissionDialog } from '@/components/admin/BulkPermissionDialog'
import { PermissionTemplates } from '@/components/admin/PermissionTemplates'
import {
  AgentName,
  UserPermissionMatrix,
  BulkPermissionAssignResponse,
} from '@/types/permissions'
import { User } from '@/types/auth'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { toast } from '@/components/ui/toast'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

// Types for the page - User interface imported from @/types/auth

interface PageFilters {
  search: string
  role: string
  status: 'all' | 'active' | 'inactive'
  permissionStatus: 'all' | 'with_access' | 'no_access'
}

interface PermissionStats {
  totalUsers: number
  activeUsers: number
  usersWithAccess: number
  usersWithoutAccess: number
  adminUsers: number
  regularUsers: number
}

/**
 * Permission Statistics Component
 */
const PermissionStatistics: React.FC<{ 
  users: User[] 
  userPermissions: Record<string, UserPermissionMatrix> 
}> = ({ users, userPermissions }) => {
  const stats = useMemo((): PermissionStats => {
    const totalUsers = users.length
    const activeUsers = users.filter(u => u.is_active).length
    const adminUsers = users.filter(u => u.role === 'admin' || u.role === 'sysadmin').length
    const regularUsers = users.filter(u => u.role === 'user').length
    
    const usersWithAccess = users.filter(user => {
      const userPerms = userPermissions[user.user_id]
      return userPerms && Object.values(userPerms.permissions).some(agentPerms => 
        Object.values(agentPerms).some(Boolean)
      )
    }).length
    
    const usersWithoutAccess = totalUsers - usersWithAccess
    
    return {
      totalUsers,
      activeUsers,
      usersWithAccess,
      usersWithoutAccess,
      adminUsers,
      regularUsers,
    }
  }, [users, userPermissions])

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total de Usuários</CardTitle>
          <Users className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.totalUsers}</div>
          <p className="text-xs text-muted-foreground">
            {stats.activeUsers} ativos, {stats.totalUsers - stats.activeUsers} inativos
          </p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Com Permissões</CardTitle>
          <Shield className="h-4 w-4 text-green-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">{stats.usersWithAccess}</div>
          <p className="text-xs text-muted-foreground">
            {stats.totalUsers > 0 ? Math.round((stats.usersWithAccess / stats.totalUsers) * 100) : 0}% do total
          </p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Sem Acesso</CardTitle>
          <AlertTriangle className="h-4 w-4 text-orange-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-orange-600">{stats.usersWithoutAccess}</div>
          <p className="text-xs text-muted-foreground">
            Usuários sem permissões ativas
          </p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Administradores</CardTitle>
          <Settings className="h-4 w-4 text-purple-600" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-purple-600">{stats.adminUsers}</div>
          <p className="text-xs text-muted-foreground">
            {stats.regularUsers} usuários regulares
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

/**
 * Quick Actions Toolbar Component
 */
const QuickActionsToolbar: React.FC<{
  selectedUsers: User[]
  onBulkOperation: () => void
  onTemplateManagement: () => void
  onUserCreate: () => void
  onExportPermissions: () => void
  onImportPermissions: () => void
}> = ({ 
  selectedUsers, 
  onBulkOperation, 
  onTemplateManagement, 
  onUserCreate,
  onExportPermissions,
  onImportPermissions,
}) => {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button
        variant="default"
        size="sm"
        onClick={onUserCreate}
      >
        <Plus className="h-4 w-4 mr-2" />
        Novo Usuário
      </Button>
      
      <Button
        variant="outline"
        size="sm"
        onClick={onTemplateManagement}
      >
        <Settings className="h-4 w-4 mr-2" />
        Templates
      </Button>
      
      <Button
        variant="outline"
        size="sm"
        onClick={onExportPermissions}
      >
        <Download className="h-4 w-4 mr-2" />
        Exportar
      </Button>
      
      <Button
        variant="outline"
        size="sm"
        onClick={onImportPermissions}
      >
        <Upload className="h-4 w-4 mr-2" />
        Importar
      </Button>
      
      {selectedUsers.length > 0 && (
        <Button
          variant="secondary"
          size="sm"
          onClick={onBulkOperation}
        >
          <Users className="h-4 w-4 mr-2" />
          Operações ({selectedUsers.length})
        </Button>
      )}
    </div>
  )
}

/**
 * Main Admin Permissions Page Component
 */
export default function AdminPermissionsPage() {
  // State management
  const [filters, setFilters] = useState<PageFilters>({
    search: '',
    role: 'all',
    status: 'all',
    permissionStatus: 'all',
  })
  const [selectedUsers, setSelectedUsers] = useState<User[]>([])
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [showUserDialog, setShowUserDialog] = useState(false)
  const [showBulkDialog, setShowBulkDialog] = useState(false)
  const [activeTab, setActiveTab] = useState('matrix')

  const queryClient = useQueryClient()

  // Fetch all users
  const { data: users = [], isLoading: usersLoading, error: usersError } = useQuery({
    queryKey: ['admin-users'],
    queryFn: async (): Promise<User[]> => {
      try {
        // Use actual API call to get all users for admin management
        const response = await fetch('/api/v1/admin/users', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
        })
        
        if (!response.ok) {
          throw new Error(`Failed to fetch users: ${response.statusText}`)
        }
        
        return await response.json()
      } catch (error) {
        console.error('Failed to fetch admin users:', error)
        throw error
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  // Fetch user permissions for all users
  const userIds = useMemo(() => users.map(user => user.user_id), [users])
  
  const { data: userPermissions = {}, isLoading: permissionsLoading } = useQuery({
    queryKey: ['admin-user-permissions', userIds],
    queryFn: async (): Promise<Record<string, UserPermissionMatrix>> => {
      const permissionMap: Record<string, UserPermissionMatrix> = {}
      
      // Fetch permissions for all users in parallel
      const permissionPromises = userIds.map(async (userId) => {
        try {
          const userMatrix = await PermissionAPI.User.getUserPermissions(userId)
          return { userId, userMatrix }
        } catch (error) {
          console.error(`Failed to fetch permissions for user ${userId}:`, error)
          return null
        }
      })
      
      const results = await Promise.allSettled(permissionPromises)
      
      results.forEach((result) => {
        if (result.status === 'fulfilled' && result.value) {
          const { userId, userMatrix } = result.value
          permissionMap[userId] = userMatrix
        }
      })
      
      return permissionMap
    },
    enabled: userIds.length > 0,
    staleTime: 2 * 60 * 1000, // 2 minutes
  })

  // Filter users based on current filters
  const filteredUsers = useMemo(() => {
    return users.filter(user => {
      // Search filter
      if (filters.search) {
        const searchLower = filters.search.toLowerCase()
        if (!user.full_name.toLowerCase().includes(searchLower) &&
            !user.email.toLowerCase().includes(searchLower)) {
          return false
        }
      }

      // Role filter
      if (filters.role !== 'all' && user.role !== filters.role) {
        return false
      }

      // Status filter
      if (filters.status !== 'all') {
        if (filters.status === 'active' && !user.is_active) return false
        if (filters.status === 'inactive' && user.is_active) return false
      }

      // Permission status filter
      if (filters.permissionStatus !== 'all') {
        const userPerms = userPermissions[user.user_id]
        const hasPermissions = userPerms && Object.values(userPerms.permissions).some(agentPerms => 
          Object.values(agentPerms).some(Boolean)
        )
        
        if (filters.permissionStatus === 'with_access' && !hasPermissions) return false
        if (filters.permissionStatus === 'no_access' && hasPermissions) return false
      }

      return true
    })
  }, [users, filters, userPermissions])

  // These handlers are part of the future matrix enhancement
  // Currently handled through row click actions in the matrix component

  // Handle bulk operations
  const handleBulkOperation = useCallback(() => {
    if (selectedUsers.length === 0) {
      toast({
        title: 'Nenhum usuário selecionado',
        description: 'Selecione pelo menos um usuário para executar operações em lote.',
        variant: 'error',
      })
      return
    }
    setShowBulkDialog(true)
  }, [selectedUsers])

  // Handle bulk operation completion
  const handleBulkOperationComplete = useCallback((result: BulkPermissionAssignResponse) => {
    // Refresh user permissions
    queryClient.invalidateQueries({ queryKey: ['admin-user-permissions'] })
    setSelectedUsers([])
    setShowBulkDialog(false)
    
    toast({
      title: 'Operação concluída',
      description: `${result.success_count} usuários atualizados com sucesso.`,
      variant: result.error_count === 0 ? 'success' : 'warning',
    })
  }, [queryClient])

  // Handle permission matrix changes
  const handlePermissionMatrixChange = useCallback((userId: string) => {
    // Refresh user permissions for the specific user
    queryClient.invalidateQueries({ 
      queryKey: ['user-permissions', userId] 
    })
    queryClient.invalidateQueries({ 
      queryKey: ['admin-user-permissions'] 
    })
  }, [queryClient])

  // Export permissions
  const handleExportPermissions = useCallback(() => {
    const exportData = {
      users: filteredUsers.map(user => ({
        ...user,
        permissions: userPermissions[user.user_id] || null,
      })),
      exportDate: new Date().toISOString(),
      totalUsers: filteredUsers.length,
    }
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { 
      type: 'application/json' 
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `permissions-export-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    toast({
      title: 'Exportação concluída',
      description: `Permissões de ${filteredUsers.length} usuários exportadas.`,
      variant: 'success',
    })
  }, [filteredUsers, userPermissions])

  // Import permissions (placeholder)
  const handleImportPermissions = useCallback(() => {
    toast({
      title: 'Funcionalidade em desenvolvimento',
      description: 'A importação de permissões será implementada em breve.',
      variant: 'default',
    })
  }, [])

  const isLoading = usersLoading || permissionsLoading

  return (
    <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="read">
      <div className="container mx-auto p-6 space-y-6">
        {/* Page Header */}
        <div className="flex flex-col space-y-4 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Gerenciar Permissões</h1>
            <p className="text-muted-foreground">
              Administre permissões de usuários por agente de forma centralizada
            </p>
          </div>
          
          <QuickActionsToolbar
            selectedUsers={selectedUsers}
            onBulkOperation={handleBulkOperation}
            onTemplateManagement={() => setActiveTab('templates')}
            onUserCreate={() => {/* TODO: Implement user creation */}}
            onExportPermissions={handleExportPermissions}
            onImportPermissions={handleImportPermissions}
          />
        </div>

        {/* Loading State */}
        {isLoading && (
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
                <span className="ml-2">Carregando dados de permissões...</span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Error State */}
        {usersError && (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-8">
                <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium mb-2">Erro ao carregar dados</h3>
                <p className="text-muted-foreground">
                  Não foi possível carregar os dados de usuários e permissões.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Main Content */}
        {!isLoading && !usersError && (
          <>
            {/* Statistics */}
            <PermissionStatistics users={filteredUsers} userPermissions={userPermissions} />

            {/* Filters */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center">
                  <Filter className="h-5 w-5 mr-2" />
                  Filtros
                </CardTitle>
                <CardDescription>
                  Filtre usuários por diferentes critérios para facilitar o gerenciamento
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Buscar</label>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      <Input
                        placeholder="Nome ou email..."
                        value={filters.search}
                        onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                        className="pl-10"
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Cargo</label>
                    <Select
                      value={filters.role}
                      onValueChange={(value) => setFilters(prev => ({ ...prev, role: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todos os Cargos</SelectItem>
                        <SelectItem value="sysadmin">Sysadmin</SelectItem>
                        <SelectItem value="admin">Administrador</SelectItem>
                        <SelectItem value="user">Usuário</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Status</label>
                    <Select
                      value={filters.status}
                      onValueChange={(value) => setFilters(prev => ({ 
                        ...prev, 
                        status: value as 'all' | 'active' | 'inactive' 
                      }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todos</SelectItem>
                        <SelectItem value="active">Ativos</SelectItem>
                        <SelectItem value="inactive">Inativos</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Permissões</label>
                    <Select
                      value={filters.permissionStatus}
                      onValueChange={(value) => setFilters(prev => ({ 
                        ...prev, 
                        permissionStatus: value as 'all' | 'with_access' | 'no_access' 
                      }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todos</SelectItem>
                        <SelectItem value="with_access">Com Acesso</SelectItem>
                        <SelectItem value="no_access">Sem Acesso</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Tabs for different views */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="matrix">Matriz de Permissões</TabsTrigger>
                <TabsTrigger value="templates">Templates</TabsTrigger>
              </TabsList>
              
              <TabsContent value="matrix" className="space-y-4">
                <PermissionMatrix
                  users={filteredUsers}
                  onUserPermissionsChange={handlePermissionMatrixChange}
                  onBulkAction={(userIds, action) => {
                    const selectedUsersForBulk = filteredUsers.filter(u => userIds.includes(u.user_id))
                    setSelectedUsers(selectedUsersForBulk)
                    if (action === 'apply_template' || action === 'bulk_edit') {
                      setShowBulkDialog(true)
                    }
                  }}
                />
              </TabsContent>
              
              <TabsContent value="templates" className="space-y-4">
                <PermissionTemplates 
                  onTemplateApplied={() => {
                    queryClient.invalidateQueries({ queryKey: ['admin-user-permissions'] })
                  }}
                />
              </TabsContent>
            </Tabs>
          </>
        )}

        {/* Dialogs */}
        <UserPermissionsDialog
          user={selectedUser}
          open={showUserDialog}
          onOpenChange={(open) => {
            setShowUserDialog(open)
            if (!open) setSelectedUser(null)
          }}
          onPermissionsChanged={handlePermissionMatrixChange}
        />

        <BulkPermissionDialog
          selectedUsers={selectedUsers}
          open={showBulkDialog}
          onClose={() => setShowBulkDialog(false)}
          onComplete={(results) => {
            // Refresh permissions data
            queryClient.invalidateQueries({ queryKey: ['admin-user-permissions'] })
            setSelectedUsers([])
            
            toast({
              title: 'Operação concluída',
              description: `${results.length} usuários processados com sucesso.`,
              variant: 'success',
            })
          }}
        />
      </div>
    </PermissionGuard>
  )
}