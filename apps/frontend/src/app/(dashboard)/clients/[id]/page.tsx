"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { ArrowLeft, User, FileText, Edit } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ToastProvider, useToast } from "@/components/ui/toast";
import { clientsAPI } from "@/lib/api/clients";
import { formatDateBR, extractErrorMessage } from "@/lib/utils";
import type { ClientResponse } from "@iam-dashboard/shared";

function ClientDetailPageContent() {
  const router = useRouter();
  const params = useParams();
  const { addToast } = useToast();
  const [client, setClient] = useState<ClientResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const clientId = params.id as string;

  useEffect(() => {
    const loadClient = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const clientData = await clientsAPI.getClient(clientId);
        setClient(clientData);
      } catch (err) {
        const errorMessage = extractErrorMessage(err);
        setError(errorMessage);

        addToast({
          title: "Erro ao carregar cliente",
          description: errorMessage,
          variant: "error",
          duration: 7000,
        });
      } finally {
        setIsLoading(false);
      }
    };

    if (clientId) {
      loadClient();
    }
  }, [clientId, addToast]);

  const handleBackToClients = () => {
    router.push("/clients");
  };

  const handleEditClient = () => {
    router.push(`/clients/${clientId}/edit`);
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <Card className="p-8 text-center">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-muted-foreground">
            Carregando informações do cliente...
          </p>
        </Card>
      </div>
    );
  }

  if (error || !client) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="mb-6">
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

        <Card className="p-8 text-center border-red-200 bg-red-50">
          <div className="flex flex-col items-center gap-4">
            <div className="p-3 bg-red-100 rounded-full">
              <User className="h-8 w-8 text-red-600" />
            </div>
            <div>
              <h3 className="font-semibold text-lg mb-2 text-red-800">
                Cliente não encontrado
              </h3>
              <p className="text-red-700 mb-4">
                {error ||
                  "O cliente solicitado não foi encontrado ou você não tem permissão para visualizá-lo."}
              </p>
              <Button onClick={handleBackToClients}>
                Voltar para Lista de Clientes
              </Button>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {/* Header */}
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

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <User className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">
                {client.full_name}
              </h1>
              <p className="text-muted-foreground">
                Cliente registrado em {formatDateBR(client.created_at)}
              </p>
            </div>
          </div>

          <Button
            onClick={handleEditClient}
            className="flex items-center gap-2"
          >
            <Edit className="h-4 w-4" />
            Editar Cliente
          </Button>
        </div>
      </div>

      {/* Client Information */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Basic Information */}
        <Card className="p-6">
          <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
            <User className="h-5 w-5" />
            Informações Básicas
          </h3>

          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-muted-foreground">
                Nome Completo
              </label>
              <p className="text-base font-medium">{client.full_name}</p>
            </div>

            <div>
              <label className="text-sm font-medium text-muted-foreground">
                CPF
              </label>
              <p className="text-base font-medium">{client.cpf}</p>
            </div>

            <div>
              <label className="text-sm font-medium text-muted-foreground">
                Data de Nascimento
              </label>
              <p className="text-base font-medium">
                {formatDateBR(client.birth_date)}
              </p>
            </div>

            <div>
              <label className="text-sm font-medium text-muted-foreground">
                Status
              </label>
              <span
                className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                  client.status === "active"
                    ? "bg-green-100 text-green-800"
                    : client.status === "inactive"
                      ? "bg-yellow-100 text-yellow-800"
                      : "bg-gray-100 text-gray-800"
                }`}
              >
                {client.status === "active"
                  ? "Ativo"
                  : client.status === "inactive"
                    ? "Inativo"
                    : "Arquivado"}
              </span>
            </div>
          </div>
        </Card>

        {/* Additional Information */}
        <Card className="p-6">
          <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Informações Adicionais
          </h3>

          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-muted-foreground">
                Observações
              </label>
              <p className="text-base">
                {client.notes || (
                  <span className="text-muted-foreground italic">
                    Nenhuma observação registrada
                  </span>
                )}
              </p>
            </div>

            <div>
              <label className="text-sm font-medium text-muted-foreground">
                Data de Criação
              </label>
              <p className="text-base">{formatDateBR(client.created_at)}</p>
            </div>

            <div>
              <label className="text-sm font-medium text-muted-foreground">
                Última Atualização
              </label>
              <p className="text-base">{formatDateBR(client.updated_at)}</p>
            </div>

            <div>
              <label className="text-sm font-medium text-muted-foreground">
                ID do Cliente
              </label>
              <p className="text-base font-mono text-sm bg-muted px-2 py-1 rounded">
                {client.client_id}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Actions */}
      <Card className="p-4 mt-6 bg-blue-50 border-blue-200">
        <h4 className="font-medium text-blue-800 mb-2">🔧 Ações Disponíveis</h4>
        <div className="flex gap-2 text-sm">
          <Button variant="outline" size="sm" onClick={handleEditClient}>
            Editar Informações
          </Button>
          <Button variant="outline" size="sm" disabled>
            Histórico de Alterações
          </Button>
          <Button variant="outline" size="sm" disabled>
            Relatórios
          </Button>
        </div>
      </Card>
    </div>
  );
}

export default function ClientDetailPage() {
  return (
    <ToastProvider>
      <ClientDetailPageContent />
    </ToastProvider>
  );
}
