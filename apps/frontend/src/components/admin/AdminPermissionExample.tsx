/**
 * Admin Permission Components Usage Example
 * 
 * This file demonstrates how to use the admin permission management components
 * together in a complete admin interface. This is for reference purposes.
 */

'use client'

import React, { useState } from 'react'
import { Users, Settings, Layout } from 'lucide-react'
import { BulkPermissionAssignResponse } from '@/types/permissions'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  PermissionMatrix,
  UserPermissionsDialog,
  BulkPermissionDialog,
  PermissionTemplates,
} from './index'

// Example user data - in real implementation, this would come from API
const EXAMPLE_USERS = [
  {
    user_id: '1',
    name: 'João Silva',
    email: 'joao.silva@empresa.com',
    role: 'user' as const,
    is_active: true,
    created_at: '2024-01-15T10:00:00Z',
  },
  {
    user_id: '2',
    name: 'Maria Santos',
    email: 'maria.santos@empresa.com',
    role: 'admin' as const,
    is_active: true,
    created_at: '2024-01-20T14:30:00Z',
  },
  {
    user_id: '3',
    name: 'Pedro Costa',  
    email: 'pedro.costa@empresa.com',
    role: 'user' as const,
    is_active: false,
    created_at: '2024-02-01T09:15:00Z',
  },
]

/**
 * Complete Admin Permission Management Interface
 */
export const AdminPermissionExample: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'matrix' | 'templates'>('matrix')
  const [selectedUser] = useState<typeof EXAMPLE_USERS[0] | null>(null)
  const [selectedUsers, setSelectedUsers] = useState<string[]>([])
  const [userDialogOpen, setUserDialogOpen] = useState(false)
  const [bulkDialogOpen, setBulkDialogOpen] = useState(false)

  // Tab navigation
  const tabs = [
    { id: 'matrix' as const, label: 'Matriz de Permissões', icon: Users },
    { id: 'templates' as const, label: 'Templates', icon: Layout },
  ]


  // Handle bulk operations
  const handleBulkAction = (userIds: string[], _action: string) => {
    setSelectedUsers(userIds)
    setBulkDialogOpen(true)
  }

  // Handle permissions changed
  const handlePermissionsChanged = (userId: string) => {
    console.log('Permissions changed for user:', userId)
    // In real implementation, you'd refresh the data
  }

  // Handle bulk operation complete
  const handleBulkOperationComplete = (results: BulkPermissionAssignResponse) => {
    console.log('Bulk operation results:', results)
    setSelectedUsers([])
    // In real implementation, you'd refresh the data
  }

  // Handle template applied
  const handleTemplateApplied = (templateId: string, userCount: number) => {
    console.log('Template applied:', { templateId, userCount })
    // In real implementation, you'd refresh the user permissions
  }

  return (
    <div className="min-h-screen bg-gray-50/50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col space-y-4 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Gestão de Permissões</h1>
            <p className="text-muted-foreground">
              Interface administrativa para gerenciar permissões de usuários e agentes
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              onClick={() => setBulkDialogOpen(true)}
              disabled={selectedUsers.length === 0}
            >
              <Settings className="h-4 w-4 mr-2" />
              Operações em Lote ({selectedUsers.length})
            </Button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex space-x-1">
              {tabs.map((tab) => {
                const Icon = tab.icon
                return (
                  <Button
                    key={tab.id}
                    variant={activeTab === tab.id ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setActiveTab(tab.id)}
                    className="flex items-center"
                  >
                    <Icon className="h-4 w-4 mr-2" />
                    {tab.label}
                  </Button>
                )
              })}
            </div>
          </CardHeader>
        </Card>

        {/* Tab Content */}
        <div className="space-y-6">
          {activeTab === 'matrix' && (
            <PermissionMatrix
              users={EXAMPLE_USERS}
              onUserPermissionsChange={handlePermissionsChanged}
              onBulkAction={handleBulkAction}
            />
          )}
          
          {activeTab === 'templates' && (
            <PermissionTemplates
              onTemplateApplied={handleTemplateApplied}
            />
          )}
        </div>

        {/* Usage Instructions */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Como usar os componentes</CardTitle>
            <CardDescription>
              Instruções para desenvolvedores sobre como integrar esses componentes
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <h4 className="font-semibold">PermissionMatrix</h4>
                <p className="text-sm text-muted-foreground">
                  Componente principal para visualizar e editar permissões em formato de matriz.
                  Suporta filtros, busca e operações em lote.
                </p>
                <code className="text-xs bg-gray-100 p-2 rounded block">
                  {`<PermissionMatrix users={users} onBulkAction={handleBulk} />`}
                </code>
              </div>
              
              <div className="space-y-2">
                <h4 className="font-semibold">UserPermissionsDialog</h4>
                <p className="text-sm text-muted-foreground">
                  Dialog para edição detalhada de permissões de um usuário específico.
                  Inclui histórico de alterações e validação.
                </p>
                <code className="text-xs bg-gray-100 p-2 rounded block">
                  {`<UserPermissionsDialog user={user} open={open} />`}
                </code>
              </div>
              
              <div className="space-y-2">
                <h4 className="font-semibold">BulkPermissionDialog</h4>
                <p className="text-sm text-muted-foreground">
                  Dialog para operações em lote - aplicar templates, conceder/revogar
                  permissões para múltiplos usuários simultaneamente.
                </p>
                <code className="text-xs bg-gray-100 p-2 rounded block">
                  {`<BulkPermissionDialog users={selectedUsers} />`}
                </code>
              </div>
              
              <div className="space-y-2">
                <h4 className="font-semibold">PermissionTemplates</h4>
                <p className="text-sm text-muted-foreground">
                  Interface para criar, editar e gerenciar templates de permissões
                  reutilizáveis para facilitar a gestão.
                </p>
                <code className="text-xs bg-gray-100 p-2 rounded block">
                  {`<PermissionTemplates onTemplateApplied={handleApply} />`}
                </code>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Dialogs */}
      <UserPermissionsDialog
        user={selectedUser}
        open={userDialogOpen}
        onOpenChange={setUserDialogOpen}
        onPermissionsChanged={handlePermissionsChanged}
      />
      
      <BulkPermissionDialog
        users={EXAMPLE_USERS.filter(u => selectedUsers.includes(u.user_id))}
        open={bulkDialogOpen}
        onOpenChange={setBulkDialogOpen}
        onBulkOperationComplete={handleBulkOperationComplete}
      />
    </div>
  )
}

export default AdminPermissionExample