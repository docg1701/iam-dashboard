"use client"

import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useMutation } from "@tanstack/react-query"

import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

import { usersAPI } from "@/lib/api/users"
import { useToast } from "@/hooks/use-toast"
import type { User, UserRole } from "@iam-dashboard/shared"

const userEditSchema = z.object({
  email: z
    .string()
    .min(1, "Email é obrigatório")
    .email("Digite um email válido"),
  full_name: z
    .string()
    .min(2, "Nome deve ter pelo menos 2 caracteres")
    .max(255, "Nome deve ter no máximo 255 caracteres"),
  role: z.enum(["sysadmin", "admin", "user"], {
    message: "Selecione um role"
  })
})

type UserEditFormData = z.infer<typeof userEditSchema>

interface UserEditFormProps {
  user: User
  onSuccess: () => void
  onCancel: () => void
}

export function UserEditForm({ user, onSuccess, onCancel }: UserEditFormProps) {
  const { toast } = useToast()

  const form = useForm<UserEditFormData>({
    resolver: zodResolver(userEditSchema),
    mode: 'onBlur', // Trigger validation on blur and submit
    defaultValues: {
      email: user.email,
      full_name: user.full_name,
      role: user.role
    }
  })

  const updateUserMutation = useMutation({
    mutationFn: (data: UserEditFormData) => usersAPI.updateUser(user.user_id, data),
    onSuccess: () => {
      toast({
        title: "Usuário atualizado",
        description: "As informações do usuário foram atualizadas com sucesso.",
      })
      onSuccess()
    },
    onError: (error: unknown) => {
      const message = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Erro ao atualizar usuário"
      toast({
        title: "Erro",
        description: message,
        variant: "error",
      })
    }
  })

  const onSubmit = (data: UserEditFormData) => {
    updateUserMutation.mutate(data)
  }

  const getRoleDisplayName = (role: UserRole) => {
    const roleNames = {
      sysadmin: 'Administrador do Sistema',
      admin: 'Administrador',
      user: 'Usuário'
    }
    return roleNames[role] || role
  }

  const getRoleDescription = (role: UserRole) => {
    const roleDescriptions = {
      sysadmin: 'Acesso total ao sistema, incluindo gerenciamento de usuários',
      admin: 'Gerenciamento de clientes e relatórios, visualização limitada de usuários',
      user: 'Operações básicas com clientes baseadas em atribuições'
    }
    return roleDescriptions[role] || ''
  }

  // Check if there are any changes
  const hasChanges = () => {
    const currentValues = form.getValues()
    return (
      currentValues.email !== user.email ||
      currentValues.full_name !== user.full_name ||
      currentValues.role !== user.role
    )
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="full_name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Nome Completo</FormLabel>
              <FormControl>
                <Input placeholder="Digite o nome completo" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input 
                  type="email" 
                  placeholder="usuario@exemplo.com" 
                  {...field} 
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="role"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Role do Usuário</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione o role do usuário" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="sysadmin">
                    <div className="flex flex-col">
                      <span>{getRoleDisplayName('sysadmin')}</span>
                      <span className="text-xs text-muted-foreground">
                        {getRoleDescription('sysadmin')}
                      </span>
                    </div>
                  </SelectItem>
                  <SelectItem value="admin">
                    <div className="flex flex-col">
                      <span>{getRoleDisplayName('admin')}</span>
                      <span className="text-xs text-muted-foreground">
                        {getRoleDescription('admin')}
                      </span>
                    </div>
                  </SelectItem>
                  <SelectItem value="user">
                    <div className="flex flex-col">
                      <span>{getRoleDisplayName('user')}</span>
                      <span className="text-xs text-muted-foreground">
                        {getRoleDescription('user')}
                      </span>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
              <FormDescription>
                Alterações no role afetam as permissões do usuário no sistema
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* User Status Information */}
        <div className="rounded-lg border p-4 bg-muted/50">
          <h4 className="font-semibold text-sm mb-2">Informações do Usuário</h4>
          <div className="space-y-1 text-sm text-muted-foreground">
            <p><strong>Status:</strong> {user.status === 'active' ? 'Ativo' : 'Inativo'}</p>
            <p><strong>Criado em:</strong> {new Date(user.created_at).toLocaleDateString('pt-BR')}</p>
            <p><strong>Última atualização:</strong> {new Date(user.updated_at).toLocaleDateString('pt-BR')}</p>
            {user.last_login_at && (
              <p><strong>Último login:</strong> {new Date(user.last_login_at).toLocaleDateString('pt-BR')}</p>
            )}
          </div>
        </div>

        <div className="flex justify-end space-x-2 pt-4">
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancelar
          </Button>
          <Button 
            type="submit" 
            disabled={updateUserMutation.isPending || !hasChanges()}
          >
            {updateUserMutation.isPending ? "Salvando..." : "Salvar Alterações"}
          </Button>
        </div>
      </form>
    </Form>
  )
}