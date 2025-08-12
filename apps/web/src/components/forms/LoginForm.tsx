/**
 * LoginForm component with 2FA support
 * Based on Story 1.3 requirements for authentication UI
 */

'use client'

import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Eye, EyeOff, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { useAuth } from '@/contexts/AuthContext'
import { useToast } from '@/hooks/use-toast'
import { loginSchema, LoginFormData } from '@/lib/validations/auth'

interface LoginFormProps {
  onSuccess?: () => void
  onError?: (error: string) => void
}

export function LoginForm({ onSuccess, onError }: LoginFormProps) {
  const [showPassword, setShowPassword] = useState(false)
  const [showTotpInput, setShowTotpInput] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { login } = useAuth()
  const { toast } = useToast()

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
    clearErrors,
    watch,
    setValue,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
      totp_code: '',
      remember_me: false,
    },
  })

  const watchedEmail = watch('email')
  const watchedPassword = watch('password')

  const onSubmit = async (data: LoginFormData) => {
    setIsSubmitting(true)
    clearErrors() // Clear form errors only

    try {
      await login({
        email: data.email,
        password: data.password,
        totp_code: data.totp_code,
      })

      toast({
        title: 'Login realizado com sucesso!',
        description: 'Bem-vindo de volta ao Dashboard IAM.',
      })

      onSuccess?.()
    } catch (err: any) {
      const errorMessage = err.message || 'Erro interno do servidor'

      // Handle 2FA requirement
      if (errorMessage.includes('2FA') || errorMessage.includes('two-factor')) {
        setShowTotpInput(true)
        setError('totp_code', {
          type: 'required',
          message: 'Código de autenticação em dois fatores é obrigatório',
        })
        return
      }

      // Handle other validation errors
      if (errorMessage.includes('email')) {
        setError('email', {
          type: 'server',
          message: errorMessage,
        })
      } else if (errorMessage.includes('password')) {
        setError('password', {
          type: 'server',
          message: errorMessage,
        })
      } else if (errorMessage.includes('TOTP') || errorMessage.includes('código')) {
        setError('totp_code', {
          type: 'server',
          message: errorMessage,
        })
      } else {
        toast({
          title: 'Erro no login',
          description: errorMessage,
          variant: 'destructive',
        })
      }

      onError?.(errorMessage)
    } finally {
      setIsSubmitting(false)
    }
  }

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword)
  }

  // Auto-show TOTP input if user has 2FA enabled (you could store this info)
  React.useEffect(() => {
    // In a real app, you might check if user has 2FA enabled based on email
    // For now, we'll show it when there's a 2FA error
  }, [])

  return (
    <Card className="w-full max-w-md mx-auto p-6">
      <div className="space-y-2 text-center mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">
          Entrar no Dashboard IAM
        </h1>
        <p className="text-sm text-muted-foreground">
          Digite suas credenciais para acessar o sistema
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Email Field */}
        <div className="space-y-2">
          <label htmlFor="email" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
            E-mail
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            disabled={isSubmitting}
            placeholder="seu@email.com"
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            {...register('email')}
          />
          {errors.email && (
            <p className="text-sm text-destructive">{errors.email.message}</p>
          )}
        </div>

        {/* Password Field */}
        <div className="space-y-2">
          <label htmlFor="password" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
            Senha
          </label>
          <div className="relative">
            <input
              id="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              disabled={isSubmitting}
              placeholder="Digite sua senha"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 pr-10 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              {...register('password')}
            />
            <button
              type="button"
              className="absolute inset-y-0 right-0 flex items-center pr-3"
              onClick={togglePasswordVisibility}
              disabled={isSubmitting}
            >
              {showPassword ? (
                <EyeOff className="h-4 w-4 text-muted-foreground" />
              ) : (
                <Eye className="h-4 w-4 text-muted-foreground" />
              )}
            </button>
          </div>
          {errors.password && (
            <p className="text-sm text-destructive">{errors.password.message}</p>
          )}
        </div>

        {/* TOTP Code Field (shown when 2FA is required) */}
        {showTotpInput && (
          <div className="space-y-2">
            <label htmlFor="totp_code" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
              Código de Autenticação (2FA)
            </label>
            <input
              id="totp_code"
              type="text"
              maxLength={6}
              pattern="[0-9]{6}"
              autoComplete="one-time-code"
              disabled={isSubmitting}
              placeholder="000000"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-center tracking-widest ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              {...register('totp_code')}
              onChange={(e) => {
                const value = e.target.value.replace(/\D/g, '').slice(0, 6)
                setValue('totp_code', value)
              }}
            />
            {errors.totp_code && (
              <p className="text-sm text-destructive">{errors.totp_code.message}</p>
            )}
            <p className="text-xs text-muted-foreground">
              Digite o código de 6 dígitos do seu aplicativo autenticador
            </p>
          </div>
        )}

        {/* Remember Me Checkbox */}
        <div className="flex items-center space-x-2">
          <input
            id="remember_me"
            type="checkbox"
            disabled={isSubmitting}
            className="peer h-4 w-4 shrink-0 rounded-sm border border-primary ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground"
            {...register('remember_me')}
          />
          <label
            htmlFor="remember_me"
            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
          >
            Lembrar de mim
          </label>
        </div>

        {/* Global Error Message - Removed since error state is not in AuthContext */}

        {/* Submit Button */}
        <Button
          type="submit"
          className="w-full"
          disabled={isSubmitting || !watchedEmail || !watchedPassword}
        >
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Entrando...
            </>
          ) : (
            'Entrar'
          )}
        </Button>
      </form>

      {/* Footer Links */}
      <div className="mt-4 text-center space-y-2">
        <p className="text-sm text-muted-foreground">
          Esqueceu sua senha?{' '}
          <button
            type="button"
            className="text-primary hover:underline"
            onClick={() => {
              // Handle password reset
              toast({
                title: 'Reset de senha',
                description: 'Funcionalidade em desenvolvimento.',
              })
            }}
          >
            Clique aqui
          </button>
        </p>
        <p className="text-sm text-muted-foreground">
          Problemas com 2FA?{' '}
          <button
            type="button"
            className="text-primary hover:underline"
            onClick={() => {
              toast({
                title: 'Suporte 2FA',
                description: 'Entre em contato com o administrador do sistema.',
              })
            }}
          >
            Preciso de ajuda
          </button>
        </p>
      </div>
    </Card>
  )
}