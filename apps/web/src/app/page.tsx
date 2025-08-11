import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function HomePage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold tracking-tight mb-4">
            Dashboard IAM
          </h1>
          <p className="text-xl text-muted-foreground">
            Sistema revolucionário de gerenciamento de permissões com arquitetura multi-agente
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle>Gerenciamento de Clientes</CardTitle>
              <CardDescription>
                Cadastro e administração completa de clientes com metadados personalizáveis
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full">
                Acessar Clientes
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Controle de Permissões</CardTitle>
              <CardDescription>
                Sistema avançado de permissões com validação em tempo real
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full">
                Gerenciar Permissões
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Implementações Personalizadas</CardTitle>
              <CardDescription>
                Serviços customizados com workflow automatizado
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full">
                Ver Implementações
              </Button>
            </CardContent>
          </Card>
        </div>

        <div className="mt-12 text-center">
          <div className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300">
            <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse" />
            Sistema Online
          </div>
        </div>
      </div>
    </div>
  )
}