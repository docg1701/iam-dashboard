'use client'

import { zodResolver } from '@hookform/resolvers/zod'
import { validateCPF, formatCPF } from '@shared/utils'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import * as z from 'zod'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

// Esquema de validação usando Zod + @brazilian-utils
const clientSchema = z.object({
  name: z
    .string()
    .min(2, 'Nome deve ter pelo menos 2 caracteres')
    .max(100, 'Nome deve ter no máximo 100 caracteres'),
  cpf: z
    .string()
    .min(11, 'CPF deve ter 11 dígitos')
    .refine(cpf => {
      const cleanCPF = cpf.replace(/\D/g, '')
      return validateCPF(cleanCPF)
    }, 'CPF inválido'),
  birthDate: z
    .string()
    .min(1, 'Data de nascimento é obrigatória')
    .refine(date => {
      const birthDate = new Date(date)
      const today = new Date()
      const age = today.getFullYear() - birthDate.getFullYear()
      return age >= 16 && age <= 120
    }, 'Cliente deve ter entre 16 e 120 anos'),
})

export type ClientFormData = z.infer<typeof clientSchema>

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
  const [cpfValue, setCpfValue] = useState(initialData?.cpf || '')

  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    setValue,
    watch,
  } = useForm<ClientFormData>({
    resolver: zodResolver(clientSchema),
    defaultValues: initialData,
    mode: 'onChange',
  })

  // Formatação em tempo real do CPF
  const handleCPFChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value.replace(/\D/g, '')
    const formattedCPF = formatCPF(value)
    setCpfValue(formattedCPF)
    setValue('cpf', value, { shouldValidate: true })
  }

  // Validação em tempo real do CPF
  const cpfInput = watch('cpf')
  const isCPFValid = cpfInput ? validateCPF(cpfInput.replace(/\D/g, '')) : false

  const onFormSubmit = (data: ClientFormData) => {
    // Remove formatação do CPF antes do envio
    const cleanData = {
      ...data,
      cpf: data.cpf.replace(/\D/g, ''),
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
          <div className="relative">
            <Input
              type="text"
              id="cpf"
              value={cpfValue}
              onChange={handleCPFChange}
              placeholder="000.000.000-00"
              maxLength={14}
              className={`${errors.cpf ? 'border-red-500' : isCPFValid ? 'border-green-500' : ''}`}
              disabled={isLoading}
            />
            {/* Indicador visual de validação */}
            {cpfValue && (
              <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                {isCPFValid ? (
                  <span className="text-green-600">✓</span>
                ) : (
                  <span className="text-red-600">✗</span>
                )}
              </div>
            )}
          </div>
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
          <p>CPF Input: {cpfInput}</p>
          <p>CPF Formatado: {cpfValue}</p>
          <p>CPF Válido: {String(isCPFValid)}</p>
          <p>Form Válido: {String(isValid)}</p>
        </div>
      )}
    </div>
  )
}
