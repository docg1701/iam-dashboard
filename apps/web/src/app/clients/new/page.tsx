'use client'

import { useRouter } from 'next/navigation'

import { ClientForm } from '@/components/forms/ClientForm'
import { toast } from '@/hooks/use-toast'
import { useCreateClient } from '@/hooks/useClients'
import { type ClientFormData } from '@/lib/validations/client'

export default function NewClientPage() {
  const router = useRouter()
  const createClientMutation = useCreateClient()

  const handleSubmit = async (data: ClientFormData) => {
    try {
      const result = await createClientMutation.mutateAsync({
        name: data.name,
        cpf: data.cpf,
        birth_date: data.birthDate,
      })

      toast({
        title: '✅ Cliente criado com sucesso!',
        description: `Cliente ${result.name} foi cadastrado com CPF ${result.cpf}`,
        variant: 'default',
      })

      // Redirecionar para lista de clientes
      router.push('/clients')
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : 'Ocorreu um erro inesperado. Tente novamente.'

      toast({
        title: '❌ Erro ao criar cliente',
        description: errorMessage,
        variant: 'destructive',
      })
    }
  }

  const handleCancel = () => {
    router.back()
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="mx-auto max-w-2xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Cadastro de Cliente
          </h1>
          <p className="mt-2 text-gray-600">
            Cadastre um novo cliente no sistema com validação automática de CPF
          </p>
        </div>

        {/* Formulário */}
        <div className="rounded-lg bg-white shadow">
          <div className="p-6">
            <ClientForm
              onSubmit={handleSubmit}
              onCancel={handleCancel}
              isLoading={createClientMutation.isPending}
            />
          </div>
        </div>

        {/* Informações Técnicas */}
        <div className="mt-8 rounded-lg border border-blue-200 bg-blue-50 p-4">
          <h3 className="mb-2 text-sm font-semibold text-blue-800">
            🔧 Informações Técnicas
          </h3>
          <ul className="space-y-1 text-sm text-blue-700">
            <li>
              • <strong>Frontend:</strong> Validação CPF com @brazilian-utils
            </li>
            <li>
              • <strong>Backend:</strong> Validação CPF com validate_docbr
            </li>
            <li>
              • <strong>Shared Utils:</strong> Validação consistente entre
              frontend e backend
            </li>
            <li>
              • <strong>Testing:</strong> Testes seguindo diretrizes CLAUDE.md
              (não mock internal code)
            </li>
          </ul>
        </div>

        {/* Debug em Desenvolvimento */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mt-6 rounded-lg border border-gray-300 bg-gray-100 p-4">
            <h4 className="mb-2 text-sm font-semibold text-gray-800">
              🐛 Debug Mode (Development Only)
            </h4>
            <div className="space-y-1 text-xs text-gray-600">
              <p>• Formulário integrado com shared utils</p>
              <p>• Validação em tempo real habilitada</p>
              <p>• Formatação automática de CPF ativa</p>
              <p>• Indicadores visuais de validação funcionando</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
