'use client'

import { useRouter } from 'next/navigation'
import { useState } from 'react'

import { ClientForm } from '@/components/forms/ClientForm'
import { toast } from '@/hooks/use-toast'

interface ClientData {
  name: string
  cpf: string
  birthDate: string
}

export default function NewClientPage() {
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()

  const handleSubmit = async (data: ClientData) => {
    setIsLoading(true)

    try {
      // Aqui seria feita a chamada para a API
      // Por enquanto, apenas simulamos o sucesso
      // TODO: Replace with actual API call

      // Simular delay da API
      await new Promise(resolve => setTimeout(resolve, 1000))

      // Simular sucesso
      toast({
        title: '✅ Cliente criado com sucesso!',
        description: `Cliente ${data.name} foi cadastrado com CPF ${data.cpf}`,
        variant: 'default',
      })

      // Redirecionar para lista de clientes (quando implementada)
      router.push('/clients')
    } catch (error) {
      // TODO: Replace with proper error handling

      toast({
        title: '❌ Erro ao criar cliente',
        description: 'Ocorreu um erro inesperado. Tente novamente.',
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
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
              isLoading={isLoading}
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
