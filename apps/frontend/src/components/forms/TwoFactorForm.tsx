"use client"

import { useState, useRef, KeyboardEvent } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Loader2, Shield, AlertCircle } from "lucide-react"
import Image from "next/image"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from "@/components/ui/form"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import type { TwoFactorFormData, TwoFactorResponse, TwoFactorSetupResponse } from "@/types/auth"

// 2FA validation schema
const twoFactorSchema = z.object({
  totp_code: z
    .string()
    .min(6, "Código deve ter 6 dígitos")
    .max(6, "Código deve ter 6 dígitos")
    .regex(/^\d{6}$/, "Código deve conter apenas números"),
})

interface TwoFactorFormProps {
  onSubmit: (data: TwoFactorFormData) => Promise<TwoFactorResponse>
  onSuccess?: (response: TwoFactorResponse) => void
  onError?: (error: string) => void
  onBack?: () => void
  setupData?: TwoFactorSetupResponse // For QR code setup flow
  isSetup?: boolean // Whether this is setup or login
  className?: string
}

export function TwoFactorForm({ 
  onSubmit, 
  onSuccess, 
  onError,
  onBack,
  setupData,
  isSetup = false,
  className 
}: TwoFactorFormProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentDigit, setCurrentDigit] = useState(0)
  const inputRefs = useRef<(HTMLInputElement | null)[]>([])

  const form = useForm<TwoFactorFormData>({
    resolver: zodResolver(twoFactorSchema),
    defaultValues: {
      totp_code: "",
    },
  })

  const handleSubmit = async (data: TwoFactorFormData) => {
    try {
      setIsLoading(true)
      setError(null)
      
      const response = await onSubmit(data)
      
      if (onSuccess) {
        onSuccess(response)
      }
    } catch (err) {
      const errorMessage = err instanceof Error 
        ? err.message 
        : "Código de verificação inválido"
      
      setError(errorMessage)
      
      if (onError) {
        onError(errorMessage)
      }
      
      // Clear the form on error
      form.reset()
      setCurrentDigit(0)
      inputRefs.current[0]?.focus()
    } finally {
      setIsLoading(false)
    }
  }

  const handleDigitChange = (index: number, value: string) => {
    // Only allow single digits
    const digit = value.replace(/\D/g, '').slice(-1)
    
    const currentCode = form.getValues('totp_code')
    const newCode = currentCode.split('')
    newCode[index] = digit
    
    const finalCode = newCode.join('').slice(0, 6)
    form.setValue('totp_code', finalCode)
    
    // Move to next input if digit was entered
    if (digit && index < 5) {
      setCurrentDigit(index + 1)
      inputRefs.current[index + 1]?.focus()
    }
    
    // Auto-submit when all 6 digits are entered
    if (finalCode.length === 6) {
      form.handleSubmit(handleSubmit)()
    }
  }

  const handleKeyDown = (index: number, e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace') {
      const currentCode = form.getValues('totp_code')
      const newCode = currentCode.split('')
      
      if (newCode[index]) {
        // Clear current digit
        newCode[index] = ''
      } else if (index > 0) {
        // Move to previous digit and clear it
        newCode[index - 1] = ''
        setCurrentDigit(index - 1)
        inputRefs.current[index - 1]?.focus()
      }
      
      form.setValue('totp_code', newCode.join(''))
    } else if (e.key === 'ArrowLeft' && index > 0) {
      setCurrentDigit(index - 1)
      inputRefs.current[index - 1]?.focus()
    } else if (e.key === 'ArrowRight' && index < 5) {
      setCurrentDigit(index + 1)
      inputRefs.current[index + 1]?.focus()
    }
  }

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault()
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    
    if (pastedData.length === 6) {
      form.setValue('totp_code', pastedData)
      setCurrentDigit(5)
      inputRefs.current[5]?.focus()
      
      // Auto-submit pasted code
      setTimeout(() => {
        form.handleSubmit(handleSubmit)()
      }, 100)
    }
  }

  const currentCode = form.watch('totp_code')
  const digits = (currentCode + '      ').slice(0, 6).split('')

  return (
    <div className={cn("w-full max-w-md mx-auto", className)}>
      <Card>
        <CardHeader className="text-center">
          <div className="mx-auto w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mb-4">
            <Shield className="w-6 h-6 text-primary" />
          </div>
          <CardTitle>
            {isSetup ? "Configurar Autenticação em Duas Etapas" : "Verificação em Duas Etapas"}
          </CardTitle>
          <CardDescription>
            {isSetup 
              ? "Escaneie o código QR abaixo com seu aplicativo autenticador e digite o código de 6 dígitos"
              : "Digite o código de 6 dígitos do seu aplicativo autenticador"
            }
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* QR Code for Setup */}
          {isSetup && setupData?.qr_code && (
            <div className="text-center space-y-4">
              <div className="inline-block p-4 bg-white rounded-lg">
                <Image
                  src={setupData.qr_code}
                  alt="QR Code para configuração do 2FA"
                  width={200}
                  height={200}
                  className="mx-auto"
                />
              </div>
              <p className="text-sm text-muted-foreground">
                Escaneie este código com Google Authenticator, Authy ou outro aplicativo TOTP
              </p>
            </div>
          )}

          <Form {...form}>
            <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
              <FormField
                control={form.control}
                name="totp_code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-center block">
                      Código de Verificação
                    </FormLabel>
                    <FormControl>
                      <div 
                        className="flex gap-2 justify-center"
                        onPaste={handlePaste}
                      >
                        {digits.map((digit, index) => (
                          <Input
                            key={index}
                            ref={(el) => {
                              inputRefs.current[index] = el
                            }}
                            type="text"
                            inputMode="numeric"
                            maxLength={1}
                            value={digit.trim()}
                            onChange={(e) => handleDigitChange(index, e.target.value)}
                            onKeyDown={(e) => handleKeyDown(index, e)}
                            onFocus={() => setCurrentDigit(index)}
                            className={cn(
                              "w-12 h-12 text-center text-lg font-mono",
                              currentDigit === index && "ring-2 ring-primary"
                            )}
                            disabled={isLoading}
                            autoComplete="one-time-code"
                          />
                        ))}
                      </div>
                    </FormControl>
                    <FormDescription className="text-center">
                      Cole o código ou digite dígito por dígito
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Error Message */}
              {error && (
                <div className="flex items-center gap-2 p-3 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-md">
                  <AlertCircle className="h-4 w-4 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <div className="space-y-3">
                {/* Submit Button */}
                <Button 
                  type="submit" 
                  className="w-full" 
                  disabled={isLoading || currentCode.length !== 6}
                  size="lg"
                >
                  {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {isLoading 
                    ? "Verificando..." 
                    : isSetup 
                      ? "Configurar 2FA" 
                      : "Verificar Código"
                  }
                </Button>

                {/* Back Button */}
                {onBack && (
                  <Button 
                    type="button" 
                    variant="outline" 
                    className="w-full" 
                    onClick={onBack}
                    disabled={isLoading}
                  >
                    Voltar
                  </Button>
                )}
              </div>
            </form>
          </Form>

          {/* Backup Codes Display for Setup */}
          {isSetup && setupData?.backup_codes && (
            <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
              <h4 className="font-medium text-yellow-800 mb-2">
                Códigos de Recuperação
              </h4>
              <p className="text-sm text-yellow-700 mb-3">
                Guarde estes códigos em local seguro. Eles podem ser usados para acessar sua conta se você perder seu dispositivo.
              </p>
              <div className="grid grid-cols-2 gap-1 font-mono text-sm">
                {setupData.backup_codes.map((code, index) => (
                  <code key={index} className="bg-white px-2 py-1 rounded border">
                    {code}
                  </code>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}