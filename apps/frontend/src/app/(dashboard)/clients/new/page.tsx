"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, UserPlus } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ClientRegistrationForm } from "@/components/forms/ClientRegistrationForm"
import { ToastProvider, useToast } from "@/components/ui/toast"
import { clientsAPI } from "@/lib/api/clients"
import { formatDateBR } from "@/lib/utils"
import type { ClientCreate, ClientResponse } from "@iam-dashboard/shared"

function NewClientPageContent() {
  const router = useRouter()
  const { addToast } = useToast()
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [createdClient, setCreatedClient] = useState<ClientResponse | null>(null)

  const handleSubmit = async (data: ClientCreate): Promise<ClientResponse> => {
    return await clientsAPI.createClient(data)
  }

  const handleSuccess = (response: ClientResponse) => {
    setCreatedClient(response)
    setSuccessMessage(`Cliente "${response.full_name}" criado com sucesso!`)
    
    // Show success toast
    addToast({
      title: "Cliente criado com sucesso!",
      description: `${response.full_name} foi registrado no sistema.`,
      variant: "success",
      duration: 5000
    })
  }

  const handleError = (error: string) => {
    console.error("Erro ao criar cliente:", error)
    
    // Show error toast
    addToast({
      title: "Erro ao criar cliente",
      description: error,
      variant: "error",
      duration: 7000
    })
  }

  const handleCreateAnother = () => {
    setSuccessMessage(null)
    setCreatedClient(null)
  }

  const handleViewClient = () => {
    if (createdClient) {
      router.push(`/clients/${createdClient.client_id}`)
    }
  }

  const handleBackToClients = () => {
    router.push("/clients")
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-6">
        <div className="flex items-center gap-4 mb-4">
          <Button
            variant="outline"
            size="sm"
            onClick={handleBackToClients}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Voltar para Clientes
          </Button>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <UserPlus className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Novo Cliente</h1>
            <p className="text-muted-foreground">
              Registre um novo cliente no sistema com informações básicas
            </p>
          </div>
        </div>
      </div>

      {/* Success Message */}
      {successMessage && createdClient && (
        <Card className="p-6 mb-6 border-green-200 bg-green-50">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-semibold text-green-800 mb-2">
                ✅ {successMessage}
              </h3>
              <div className="text-sm text-green-700 space-y-1">
                <p><strong>ID:</strong> {createdClient.client_id}</p>
                <p><strong>Nome:</strong> {createdClient.full_name}</p>
                <p><strong>CPF:</strong> {createdClient.ssn}</p>
                <p><strong>Data de Nascimento:</strong> {formatDateBR(createdClient.birth_date)}</p>
              </div>
            </div>
          </div>
          
          <div className="flex gap-3 mt-4">
            <Button
              onClick={handleViewClient}
              className="flex items-center gap-2"
            >
              Ver Cliente
            </Button>
            <Button
              variant="outline"
              onClick={handleCreateAnother}
              className="flex items-center gap-2"
            >
              <UserPlus className="h-4 w-4" />
              Criar Outro Cliente
            </Button>
          </div>
        </Card>
      )}

      {/* Registration Form */}
      {!successMessage && (
        <Card className="p-6">
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-2">Informações do Cliente</h2>
            <p className="text-sm text-muted-foreground">
              Preencha os campos abaixo com as informações do novo cliente. 
              Todos os campos marcados são obrigatórios.
            </p>
          </div>

          <ClientRegistrationForm
            onSubmit={handleSubmit}
            onSuccess={handleSuccess}
            onError={handleError}
          />
        </Card>
      )}

      {/* Help Information */}
      <Card className="p-4 mt-6 bg-blue-50 border-blue-200">
        <h4 className="font-medium text-blue-800 mb-2">ℹ️ Informações Importantes</h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• O CPF deve ser único no sistema</li>
          <li>• Cliente deve ter pelo menos 13 anos de idade</li>
          <li>• Todas as informações podem ser editadas posteriormente</li>
          <li>• O campo &quot;Observações&quot; é opcional e aceita até 1000 caracteres</li>
        </ul>
      </Card>
    </div>
  )
}

export default function NewClientPage() {
  return (
    <ToastProvider>
      <NewClientPageContent />
    </ToastProvider>
  )
}