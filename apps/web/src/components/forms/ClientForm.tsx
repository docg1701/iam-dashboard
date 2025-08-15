'use client'

import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'

import { Button } from '@/components/ui/button'
import { CPFInput } from '@/components/ui/cpf-input'
import { Input } from '@/components/ui/input'
import {
  clientFormSchema,
  type ClientFormData,
  cleanCPFForAPI,
} from '@/lib/validations/client'

interface ClientFormProps {
  onSubmit: (data: ClientFormData) => void
  onCancel?: () => void
  isLoading?: boolean
  initialData?: Partial<ClientFormData>
}

export function ClientForm({
  onSubmit,
  onCancel,
  isLoading = false,
  initialData,
}: ClientFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    setValue,
    watch,
  } = useForm<ClientFormData>({
    resolver: zodResolver(clientFormSchema),
    defaultValues: initialData,
    mode: 'onChange',
  })

  // Watch CPF value for real-time validation feedback
  const cpfValue = watch('cpf')

  // Handle CPF input changes
  const handleCPFChange = (cleanValue: string) => {
    setValue('cpf', cleanValue, { shouldValidate: true })
  }

  const onFormSubmit = (data: ClientFormData) => {
    // Remove formatação do CPF antes do envio
    const cleanData = {
      ...data,
      cpf: cleanCPFForAPI(data.cpf),
    }
    onSubmit(cleanData)
  }

  return (
    <div className="mx-auto max-w-md rounded-lg bg-white p-6 shadow-md">
      <h2 className="mb-6 text-2xl font-bold text-gray-900">
        {initialData ? 'Editar Cliente' : 'Novo Cliente'}
      </h2>

      <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-4">
        {/* Campo Nome */}
        <div>
          <label
            htmlFor="name"
            className="block text-sm font-medium text-gray-700"
          >
            Nome Completo *
          </label>
          <Input
            {...register('name')}
            type="text"
            id="name"
            placeholder="Ex: João da Silva Santos"
            className={errors.name ? 'border-red-500' : ''}
            disabled={isLoading}
          />
          {errors.name && (
            <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
          )}
        </div>

        {/* Campo CPF com validação em tempo real */}
        <div>
          <label
            htmlFor="cpf"
            className="block text-sm font-medium text-gray-700"
          >
            CPF *
          </label>
          <CPFInput
            id="cpf"
            value={cpfValue || ''}
            onChange={handleCPFChange}
            disabled={isLoading}
            className={errors.cpf ? 'border-red-500' : ''}
          />
          {errors.cpf && (
            <p className="mt-1 text-sm text-red-600">{errors.cpf.message}</p>
          )}
          {cpfValue && !errors.cpf && (
            <p className="mt-1 text-sm text-green-600">
              ✅ CPF válido - Utilizando @brazilian-utils
            </p>
          )}
        </div>

        {/* Campo Data de Nascimento */}
        <div>
          <label
            htmlFor="birthDate"
            className="block text-sm font-medium text-gray-700"
          >
            Data de Nascimento *
          </label>
          <Input
            {...register('birthDate')}
            type="date"
            id="birthDate"
            className={errors.birthDate ? 'border-red-500' : ''}
            disabled={isLoading}
          />
          {errors.birthDate && (
            <p className="mt-1 text-sm text-red-600">
              {errors.birthDate.message}
            </p>
          )}
        </div>

        {/* Botões de Ação */}
        <div className="flex gap-3 pt-4">
          <Button
            type="submit"
            disabled={!isValid || isLoading}
            className="flex-1"
          >
            {isLoading ? 'Salvando...' : 'Salvar Cliente'}
          </Button>

          {onCancel && (
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              disabled={isLoading}
            >
              Cancelar
            </Button>
          )}
        </div>
      </form>

      {/* Informações de Debugging em Desenvolvimento */}
      {process.env.NODE_ENV === 'development' && (
        <div className="mt-6 rounded bg-gray-100 p-4 text-xs">
          <h4 className="font-semibold">Debug Info:</h4>
          <p>CPF Value: {cpfValue || 'empty'}</p>
          <p>Form Válido: {String(isValid)}</p>
          <p>
            Has Errors:{' '}
            {Object.keys(errors).length > 0
              ? Object.keys(errors).join(', ')
              : 'none'}
          </p>
        </div>
      )}
    </div>
  )
}
