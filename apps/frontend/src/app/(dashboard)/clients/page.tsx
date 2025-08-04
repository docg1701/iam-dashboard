"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Plus, Users, Search } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"

export default function ClientsPage() {
  const router = useRouter()
  const [searchTerm, setSearchTerm] = useState("")

  const handleNewClient = () => {
    router.push("/clients/new")
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Users className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Clientes</h1>
              <p className="text-muted-foreground">
                Gerencie os clientes registrados no sistema
              </p>
            </div>
          </div>
          
          <Button onClick={handleNewClient} className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Novo Cliente
          </Button>
        </div>

        {/* Search Bar */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar clientes..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Empty State - Since this is just for navigation demo */}
      <Card className="p-8 text-center">
        <div className="flex flex-col items-center gap-4">
          <div className="p-3 bg-muted rounded-full">
            <Users className="h-8 w-8 text-muted-foreground" />
          </div>
          <div>
            <h3 className="font-semibold text-lg mb-2">Nenhum cliente encontrado</h3>
            <p className="text-muted-foreground mb-4">
              Comece criando o primeiro cliente do sistema.
            </p>
            <Button onClick={handleNewClient} className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              Criar Primeiro Cliente
            </Button>
          </div>
        </div>
      </Card>

      {/* Info Card */}
      <Card className="p-4 mt-6 bg-blue-50 border-blue-200">
        <h4 className="font-medium text-blue-800 mb-2">💡 Sobre o Sistema de Clientes</h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• Registre clientes com nome completo, CPF e data de nascimento</li>
          <li>• Todas as informações são validadas automaticamente</li>
          <li>• CPF deve ser único no sistema para cada cliente</li>
          <li>• Clientes devem ter pelo menos 13 anos de idade</li>
          <li>• Todas as operações são registradas no log de auditoria</li>
        </ul>
      </Card>
    </div>
  )
}