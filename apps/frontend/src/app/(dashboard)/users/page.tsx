"use client"

import { useState } from "react"
import { Plus, Users, Search, MoreHorizontal, UserCheck, UserX, Key } from "lucide-react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

import { usersAPI, type UserListFilters } from "@/lib/api/users"
import { useToast } from "@/hooks/use-toast"
import { UserCreateForm } from "@/components/forms/UserCreateForm"
import { UserEditForm } from "@/components/forms/UserEditForm"
import type { User, UserRole } from "@iam-dashboard/shared"

interface ConfirmDialogState {
  isOpen: boolean
  title: string
  description: string
  action: () => void
}

export default function UsersPage() {
  // const router = useRouter() // Not used yet
  const { toast } = useToast()
  const queryClient = useQueryClient()
  
  // Search and filter state
  const [searchTerm, setSearchTerm] = useState("")
  const [roleFilter, setRoleFilter] = useState<UserRole | "">("")
  const [statusFilter, setStatusFilter] = useState<string>("")
  
  // Dialog state
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [confirmDialog, setConfirmDialog] = useState<ConfirmDialogState>({
    isOpen: false,
    title: "",
    description: "",
    action: () => {}
  })

  // Prepare filters for API call
  const filters: UserListFilters = {
    query: searchTerm || undefined,
    role: roleFilter || undefined,
    is_active: statusFilter === "active" ? true : statusFilter === "inactive" ? false : undefined,
    page: 1,
    limit: 50
  }

  // Fetch users
  const { data: usersData, isLoading, error } = useQuery({
    queryKey: ['users', filters],
    queryFn: () => usersAPI.getUsers(filters),
    refetchOnWindowFocus: false
  })

  // Mutations
  const deactivateUserMutation = useMutation({
    mutationFn: (userId: string) => usersAPI.deactivateUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      toast({
        title: "Usuário desativado",
        description: "O usuário foi desativado com sucesso.",
      })
    },
    onError: () => {
      toast({
        title: "Erro",
        description: "Não foi possível desativar o usuário.",
        variant: "error",
      })
    }
  })

  const activateUserMutation = useMutation({
    mutationFn: (userId: string) => usersAPI.activateUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      toast({
        title: "Usuário ativado",
        description: "O usuário foi ativado com sucesso.",
      })
    },
    onError: () => {
      toast({
        title: "Erro", 
        description: "Não foi possível ativar o usuário.",
        variant: "error",
      })
    }
  })

  const resetPasswordMutation = useMutation({
    mutationFn: ({ userId, password }: { userId: string; password: string }) => 
      usersAPI.resetPassword(userId, password),
    onSuccess: () => {
      toast({
        title: "Senha redefinida",
        description: "A senha do usuário foi redefinida com sucesso.",
      })
    },
    onError: () => {
      toast({
        title: "Erro",
        description: "Não foi possível redefinir a senha do usuário.",
        variant: "error",
      })
    }
  })

  // Action handlers
  const handleDeactivateUser = (user: User) => {
    setConfirmDialog({
      isOpen: true,
      title: "Desativar usuário",
      description: `Tem certeza que deseja desativar o usuário ${user.full_name}? Esta ação pode ser revertida posteriormente.`,
      action: () => {
        deactivateUserMutation.mutate(user.user_id)
        setConfirmDialog(prev => ({ ...prev, isOpen: false }))
      }
    })
  }

  const handleActivateUser = (user: User) => {
    setConfirmDialog({
      isOpen: true,
      title: "Ativar usuário",
      description: `Tem certeza que deseja ativar o usuário ${user.full_name}?`,
      action: () => {
        activateUserMutation.mutate(user.user_id)
        setConfirmDialog(prev => ({ ...prev, isOpen: false }))
      }
    })
  }

  const handleResetPassword = (user: User) => {
    // For now, generate a temporary password - in production this should be more secure
    const tempPassword = `Temp${Math.random().toString(36).slice(-8)}!`
    
    setConfirmDialog({
      isOpen: true,
      title: "Redefinir senha",
      description: `Tem certeza que deseja redefinir a senha do usuário ${user.full_name}? Uma nova senha temporária será gerada.`,
      action: () => {
        resetPasswordMutation.mutate({ userId: user.user_id, password: tempPassword })
        setConfirmDialog(prev => ({ ...prev, isOpen: false }))
      }
    })
  }

  const getRoleDisplayName = (role: UserRole) => {
    const roleNames = {
      sysadmin: 'Administrador do Sistema',
      admin: 'Administrador',
      user: 'Usuário'
    }
    return roleNames[role] || role
  }

  const getRoleBadgeVariant = (role: UserRole) => {
    const variants = {
      sysadmin: 'destructive',
      admin: 'default',
      user: 'secondary'
    } as const
    return variants[role] || 'secondary'
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Users className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Usuários</h1>
              <p className="text-muted-foreground">
                Gerencie os usuários e suas permissões no sistema
              </p>
            </div>
          </div>
          
          <Button onClick={() => setShowCreateDialog(true)} className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Novo Usuário
          </Button>
        </div>

        {/* Search and Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Buscar por email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          
          <Select value={roleFilter} onValueChange={(value) => setRoleFilter(value as UserRole | "")}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Filtrar por role" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">Todos os roles</SelectItem>
              <SelectItem value="sysadmin">Sysadmin</SelectItem>
              <SelectItem value="admin">Admin</SelectItem>
              <SelectItem value="user">Usuário</SelectItem>
            </SelectContent>
          </Select>

          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Filtrar por status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">Todos os status</SelectItem>
              <SelectItem value="active">Ativo</SelectItem>
              <SelectItem value="inactive">Inativo</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Users Table */}
      <Card>
        <div className="overflow-hidden rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Usuário</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Criado em</TableHead>
                <TableHead className="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-24 text-center">
                    Carregando usuários...
                  </TableCell>
                </TableRow>
              ) : error ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-24 text-center text-destructive">
                    Erro ao carregar usuários
                  </TableCell>
                </TableRow>
              ) : !usersData?.users?.length ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-24 text-center">
                    Nenhum usuário encontrado
                  </TableCell>
                </TableRow>
              ) : (
                usersData.users.map((user) => (
                  <TableRow key={user.user_id}>
                    <TableCell className="font-medium">{user.full_name}</TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      <Badge variant={getRoleBadgeVariant(user.role)}>
                        {getRoleDisplayName(user.role)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={user.status === 'active' ? 'default' : 'secondary'}>
                        {user.status === 'active' ? 'Ativo' : 'Inativo'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {new Date(user.created_at).toLocaleDateString('pt-BR')}
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" className="h-8 w-8 p-0">
                            <span className="sr-only">Abrir menu</span>
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>Ações</DropdownMenuLabel>
                          <DropdownMenuItem onClick={() => setEditingUser(user)}>
                            Editar usuário
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          {user.status === 'active' ? (
                            <DropdownMenuItem 
                              onClick={() => handleDeactivateUser(user)}
                              className="text-destructive"
                            >
                              <UserX className="mr-2 h-4 w-4" />
                              Desativar
                            </DropdownMenuItem>
                          ) : (
                            <DropdownMenuItem onClick={() => handleActivateUser(user)}>
                              <UserCheck className="mr-2 h-4 w-4" />
                              Ativar
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuItem onClick={() => handleResetPassword(user)}>
                            <Key className="mr-2 h-4 w-4" />
                            Redefinir senha
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </Card>

      {/* Summary */}
      {usersData?.users && (
        <div className="mt-4 text-sm text-muted-foreground">
          Mostrando {usersData.users.length} de {usersData.total} usuário(s)
        </div>
      )}

      {/* Create User Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Criar Novo Usuário</DialogTitle>
            <DialogDescription>
              Preencha os dados para criar um novo usuário no sistema.
            </DialogDescription>
          </DialogHeader>
          <UserCreateForm 
            onSuccess={() => {
              setShowCreateDialog(false)
              queryClient.invalidateQueries({ queryKey: ['users'] })
            }}
            onCancel={() => setShowCreateDialog(false)}
          />
        </DialogContent>
      </Dialog>

      {/* Edit User Dialog */}
      <Dialog open={!!editingUser} onOpenChange={(open) => !open && setEditingUser(null)}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Editar Usuário</DialogTitle>
            <DialogDescription>
              Atualize as informações do usuário.
            </DialogDescription>
          </DialogHeader>
          {editingUser && (
            <UserEditForm 
              user={editingUser}
              onSuccess={() => {
                setEditingUser(null)
                queryClient.invalidateQueries({ queryKey: ['users'] })
              }}
              onCancel={() => setEditingUser(null)}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Confirmation Dialog */}
      <Dialog open={confirmDialog.isOpen} onOpenChange={(open) => 
        setConfirmDialog(prev => ({ ...prev, isOpen: open }))
      }>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{confirmDialog.title}</DialogTitle>
            <DialogDescription>
              {confirmDialog.description}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => 
              setConfirmDialog(prev => ({ ...prev, isOpen: false }))
            }>
              Cancelar
            </Button>
            <Button onClick={confirmDialog.action}>
              Confirmar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}