"use client"

import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { ClientFormDataSchema } from "@iam-dashboard/shared"
import { User, Calendar, FileText, Loader2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from "@/components/ui/form"
import { cn, extractErrorMessage } from "@/lib/utils"
import type { ClientCreate, ClientResponse } from "@iam-dashboard/shared"

// Client registration form validation schema with Portuguese messages
// Based on shared ClientFormDataSchema but with localized messages
const clientRegistrationSchema = ClientFormDataSchema.extend({
  full_name: z
    .string()
    .min(1, "Nome completo é obrigatório")
    .min(2, "Nome deve ter pelo menos 2 caracteres")
    .max(255, "Nome não pode exceder 255 caracteres")
    .regex(
      /^[a-zA-ZÀ-ÿĀ-žА-я\s'-]+$/,
      "Nome deve conter apenas letras, espaços, hífens e apostrofes"
    ),
  ssn: z
    .string()
    .min(1, "CPF é obrigatório")
    .regex(
      /^\d{3}-\d{2}-\d{4}$/,
      "CPF deve estar no formato XXX-XX-XXXX"
    ),
  birth_date: z
    .string()
    .min(1, "Data de nascimento é obrigatória")
    .regex(
      /^\d{4}-\d{2}-\d{2}$/,
      "Data deve estar no formato AAAA-MM-DD"
    )
    .refine((date) => {
      const birthDate = new Date(date)
      const today = new Date()
      const minAge = new Date(today.getFullYear() - 13, today.getMonth(), today.getDate())
      const maxAge = new Date(today.getFullYear() - 120, today.getMonth(), today.getDate())
      
      return birthDate <= minAge && birthDate >= maxAge
    }, "Idade deve estar entre 13 e 120 anos"),
  notes: z
    .string()
    .max(1000, "Notas não podem exceder 1000 caracteres")
    .optional()
    .or(z.literal(""))
})

type ClientRegistrationFormData = z.infer<typeof clientRegistrationSchema>

interface ClientRegistrationFormProps {
  onSubmit: (data: ClientCreate) => Promise<ClientResponse>
  onSuccess?: (response: ClientResponse) => void
  onError?: (error: string) => void
  className?: string
}

export function ClientRegistrationForm({ 
  onSubmit, 
  onSuccess, 
  onError, 
  className 
}: ClientRegistrationFormProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const form = useForm<ClientRegistrationFormData>({
    resolver: zodResolver(clientRegistrationSchema),
    defaultValues: {
      full_name: "",
      ssn: "",
      birth_date: "",
      notes: "",
    },
  })

  // SSN formatting handler
  const handleSSNChange = (value: string, onChange: (value: string) => void) => {
    // Remove all non-numeric characters
    const cleaned = value.replace(/\D/g, '')
    
    // Apply formatting: XXX-XX-XXXX
    let formatted = cleaned
    if (cleaned.length >= 6) {
      formatted = `${cleaned.slice(0, 3)}-${cleaned.slice(3, 5)}-${cleaned.slice(5, 9)}`
    } else if (cleaned.length >= 4) {
      formatted = `${cleaned.slice(0, 3)}-${cleaned.slice(3)}`
    }
    
    // Limit to 11 digits (formatted as XXX-XX-XXXX)
    if (cleaned.length <= 9) {
      onChange(formatted)
    }
  }

  const handleSubmit = async (data: ClientRegistrationFormData) => {
    try {
      setIsLoading(true)
      setError(null)
      
      // Transform form data to API format
      const clientData: ClientCreate = {
        full_name: data.full_name.trim(),
        ssn: data.ssn,
        birth_date: data.birth_date,
        notes: data.notes?.trim() || undefined,
      }
      
      const response = await onSubmit(clientData)
      
      if (onSuccess) {
        onSuccess(response)
      }
      
      // Reset form on success
      form.reset()
    } catch (err) {
      const errorMessage = extractErrorMessage(err)
      
      setError(errorMessage)
      
      if (onError) {
        onError(errorMessage)
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className={cn("w-full max-w-2xl mx-auto", className)}>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
          {/* Full Name Field */}
          <FormField
            control={form.control}
            name="full_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-sm font-medium">
                  Nome Completo
                </FormLabel>
                <FormControl>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      {...field}
                      placeholder="João Silva Santos"
                      className="pl-10"
                      disabled={isLoading}
                      autoComplete="name"
                    />
                  </div>
                </FormControl>
                <FormDescription>
                  Nome completo do cliente conforme documento de identidade
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          {/* SSN/CPF Field */}
          <FormField
            control={form.control}
            name="ssn"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-sm font-medium">
                  CPF
                </FormLabel>
                <FormControl>
                  <div className="relative">
                    <FileText className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      {...field}
                      placeholder="123-45-6789"
                      className="pl-10"
                      disabled={isLoading}
                      autoComplete="off"
                      onChange={(e) => handleSSNChange(e.target.value, field.onChange)}
                    />
                  </div>
                </FormControl>
                <FormDescription>
                  CPF no formato XXX-XX-XXXX (apenas números)
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          {/* Birth Date Field */}
          <FormField
            control={form.control}
            name="birth_date"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-sm font-medium">
                  Data de Nascimento
                </FormLabel>
                <FormControl>
                  <div className="relative">
                    <Calendar className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      {...field}
                      type="date"
                      className="pl-10"
                      disabled={isLoading}
                      max={new Date(new Date().getFullYear() - 13, new Date().getMonth(), new Date().getDate()).toISOString().split('T')[0]}
                      min={new Date(new Date().getFullYear() - 120, new Date().getMonth(), new Date().getDate()).toISOString().split('T')[0]}
                    />
                  </div>
                </FormControl>
                <FormDescription>
                  Cliente deve ter pelo menos 13 anos de idade
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          {/* Notes Field */}
          <FormField
            control={form.control}
            name="notes"
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-sm font-medium">
                  Observações (Opcional)
                </FormLabel>
                <FormControl>
                  <Textarea
                    {...field}
                    placeholder="Informações adicionais sobre o cliente..."
                    disabled={isLoading}
                    rows={4}
                  />
                </FormControl>
                <FormDescription>
                  Notas ou informações adicionais relevantes (máximo 1000 caracteres)
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          {/* Error Message */}
          {error && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-md">
              {error}
            </div>
          )}

          {/* Submit Button */}
          <div className="flex gap-3 pt-4">
            <Button 
              type="submit" 
              className="flex-1" 
              disabled={isLoading}
              size="lg"
            >
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isLoading ? "Criando Cliente..." : "Criar Cliente"}
            </Button>
            
            <Button 
              type="button" 
              variant="outline"
              className="flex-1" 
              disabled={isLoading}
              size="lg"
              onClick={() => form.reset()}
            >
              Limpar Formulário
            </Button>
          </div>
        </form>
      </Form>
    </div>
  )
}