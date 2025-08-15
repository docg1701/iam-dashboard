/**
 * QR Code Display Component for 2FA setup
 * Displays QR code with fallback text and copy functionality
 */

'use client'

import { Copy, Eye, EyeOff, CheckCheck } from 'lucide-react'
import { QRCodeSVG } from 'qrcode.react'
import * as React from 'react'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { useToast } from '@/hooks/use-toast'
import { cn } from '@/utils/cn'

export interface QRCodeDisplayProps {
  value: string
  title?: string
  description?: string
  showSecret?: boolean
  className?: string
  size?: number
  level?: 'L' | 'M' | 'Q' | 'H'
  onSecretToggle?: (visible: boolean) => void
}

const QRCodeDisplay = React.forwardRef<HTMLDivElement, QRCodeDisplayProps>(
  (
    {
      value,
      title = 'Configurar Autenticação em Dois Fatores',
      description = 'Escaneie o código QR com seu aplicativo autenticador ou digite a chave secreta manualmente.',
      showSecret = false,
      className,
      size = 200,
      level = 'M',
      onSecretToggle,
      ...props
    },
    ref
  ) => {
    const [secretVisible, setSecretVisible] = React.useState(showSecret)
    const [copied, setCopied] = React.useState(false)
    const { toast } = useToast()

    // Extract secret from TOTP URL for manual entry
    const getSecretFromUrl = (url: string): string => {
      try {
        const urlObj = new URL(url)
        return urlObj.searchParams.get('secret') || ''
      } catch {
        return ''
      }
    }

    const secret = getSecretFromUrl(value)

    const toggleSecretVisibility = () => {
      const newState = !secretVisible
      setSecretVisible(newState)
      onSecretToggle?.(newState)
    }

    const copySecret = async () => {
      if (!secret) {
        toast({
          title: 'Erro',
          description: 'Não foi possível encontrar a chave secreta.',
          variant: 'destructive',
        })
        return
      }

      try {
        await navigator.clipboard.writeText(secret)
        setCopied(true)
        toast({
          title: 'Copiado!',
          description:
            'A chave secreta foi copiada para a área de transferência.',
        })

        setTimeout(() => setCopied(false), 2000)
      } catch (error) {
        toast({
          title: 'Erro ao copiar',
          description: 'Não foi possível copiar a chave secreta.',
          variant: 'destructive',
        })
      }
    }

    const formatSecret = (secret: string): string => {
      // Format secret in groups of 4 characters for better readability
      return secret.replace(/(.{4})/g, '$1 ').trim()
    }

    if (!value) {
      return (
        <Card
          className={cn('mx-auto w-full max-w-md', className)}
          ref={ref}
          {...props}
        >
          <CardHeader className="text-center">
            <CardTitle className="text-destructive">Erro</CardTitle>
            <CardDescription>
              Não foi possível gerar o código QR. Tente novamente.
            </CardDescription>
          </CardHeader>
        </Card>
      )
    }

    return (
      <Card
        className={cn('mx-auto w-full max-w-md', className)}
        ref={ref}
        {...props}
      >
        <CardHeader className="text-center">
          <CardTitle className="text-lg">{title}</CardTitle>
          <CardDescription className="text-sm">{description}</CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* QR Code */}
          <div className="flex justify-center rounded-lg bg-white p-4">
            <QRCodeSVG
              value={value}
              size={size}
              level={level}
              includeMargin={true}
              className="rounded border border-gray-200"
            />
          </div>

          {/* Manual Entry Section */}
          {secret && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium">Configuração Manual</h4>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={toggleSecretVisibility}
                  className="h-8 px-2"
                >
                  {secretVisible ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                  <span className="ml-1 text-xs">
                    {secretVisible ? 'Ocultar' : 'Mostrar'}
                  </span>
                </Button>
              </div>

              <div className="space-y-2">
                <label className="text-xs text-muted-foreground">
                  Chave Secreta:
                </label>
                <div className="relative">
                  <div
                    className={cn(
                      'min-h-[2.5rem] w-full rounded border bg-muted p-2 font-mono text-sm',
                      'flex items-center break-all',
                      !secretVisible && 'select-none blur-sm'
                    )}
                  >
                    {secretVisible
                      ? formatSecret(secret)
                      : '••••••••••••••••••••••••••••••••'}
                  </div>

                  {secretVisible && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={copySecret}
                      className="absolute right-1 top-1 h-6 w-6 p-0"
                      title="Copiar chave secreta"
                    >
                      {copied ? (
                        <CheckCheck className="h-3 w-3 text-green-600" />
                      ) : (
                        <Copy className="h-3 w-3" />
                      )}
                    </Button>
                  )}
                </div>
              </div>

              <div className="space-y-1 text-xs text-muted-foreground">
                <p>
                  • Abra seu aplicativo autenticador (Google Authenticator,
                  Authy, etc.)
                </p>
                <p>• Adicione uma nova conta manualmente</p>
                <p>• Digite a chave secreta acima</p>
                <p>• Use &quot;Dashboard IAM&quot; como nome da conta</p>
              </div>
            </div>
          )}

          {/* Recommended Apps */}
          <div className="border-t pt-2">
            <h5 className="mb-2 text-xs font-medium text-muted-foreground">
              Aplicativos Recomendados:
            </h5>
            <div className="flex flex-wrap gap-1 text-xs text-muted-foreground">
              <span className="rounded-full bg-muted px-2 py-1">
                Google Authenticator
              </span>
              <span className="rounded-full bg-muted px-2 py-1">Authy</span>
              <span className="rounded-full bg-muted px-2 py-1">
                Microsoft Authenticator
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }
)

QRCodeDisplay.displayName = 'QRCodeDisplay'

export { QRCodeDisplay }
