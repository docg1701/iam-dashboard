/**
 * Bulk Permission Dialog Component
 *
 * Dialog component for performing bulk permission operations on multiple users
 * with template application, batch updates, and progress tracking.
 */

"use client";

import React, { useState, useCallback, useMemo } from "react";
import {
  Users,
  Layout,
  Save,
  X,
  AlertTriangle,
  Clock,
  Shield,
  Download,
} from "lucide-react";
import {
  AgentName,
  PermissionActions,
  BulkPermissionAssignResponse,
  PermissionTemplate,
  PermissionLevel,
  getPermissionLevel,
  getPermissionsForLevel,
  PERMISSION_LEVELS,
  PERMISSION_LEVEL_NAMES,
} from "@/types/permissions";
import { PermissionAPI } from "@/lib/api/permissions";
import { usePermissionTemplates } from "@/hooks/useUserPermissions";
import { PermissionGuard } from "@/components/common/PermissionGuard";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { toast } from "@/components/ui/toast";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";

// Types for the component
interface User {
  user_id: string;
  full_name: string;
  email: string;
  role: "sysadmin" | "admin" | "user";
  is_active: boolean;
  totp_enabled: boolean;
  created_at: string;
  updated_at: string;
}

interface BulkPermissionDialogProps {
  selectedUsers: User[];
  open: boolean;
  onClose: () => void;
  onComplete?: (results: string[]) => void;
  className?: string;
}

interface BulkOperation {
  type: "template" | "grant_all" | "revoke_all" | "custom";
  templateId?: string;
  permissions?: Record<AgentName, PermissionActions>;
  changeReason: string;
}

interface OperationProgress {
  total: number;
  completed: number;
  failed: number;
  currentUser?: string;
  isRunning: boolean;
  errors: Array<{ user_id: string; error: string }>;
}

// Agent display names in Portuguese
const AGENT_DISPLAY_NAMES: Record<AgentName, string> = {
  [AgentName.CLIENT_MANAGEMENT]: "Gestão de Clientes",
  [AgentName.PDF_PROCESSING]: "Processamento de PDFs",
  [AgentName.REPORTS_ANALYSIS]: "Relatórios e Análises",
  [AgentName.AUDIO_RECORDING]: "Gravação de Áudio",
};

// Permission level colors
const PERMISSION_LEVEL_COLORS: Record<PermissionLevel, string> = {
  [PERMISSION_LEVELS.NONE]: "bg-gray-100 text-gray-800 border-gray-200",
  [PERMISSION_LEVELS.READ_ONLY]: "bg-blue-100 text-blue-800 border-blue-200",
  [PERMISSION_LEVELS.STANDARD]: "bg-green-100 text-green-800 border-green-200",
  [PERMISSION_LEVELS.FULL]: "bg-purple-100 text-purple-800 border-purple-200",
};

/**
 * Progress Tracker Component
 */
const ProgressTracker: React.FC<{
  progress: OperationProgress;
  users: User[];
}> = ({ progress, users }) => {
  const progressPercentage =
    progress.total > 0
      ? Math.round((progress.completed / progress.total) * 100)
      : 0;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center">
          <Clock className="h-4 w-4 mr-2" />
          Progresso da Operação
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Processando usuários...</span>
            <span>
              {progress.completed}/{progress.total}
            </span>
          </div>
          <Progress value={progressPercentage} className="w-full" />
        </div>

        {progress.currentUser && (
          <div className="text-sm text-muted-foreground">
            Processando: {progress.currentUser}
          </div>
        )}

        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-green-600">
              {progress.completed}
            </div>
            <div className="text-xs text-muted-foreground">Concluídos</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-red-600">
              {progress.failed}
            </div>
            <div className="text-xs text-muted-foreground">Falhas</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-blue-600">
              {progress.total - progress.completed}
            </div>
            <div className="text-xs text-muted-foreground">Restantes</div>
          </div>
        </div>

        {progress.errors.length > 0 && (
          <div className="space-y-2">
            <Label className="text-xs text-red-600">Erros:</Label>
            <div className="max-h-32 overflow-y-auto space-y-1">
              {progress.errors.map((error, index) => (
                <div key={index} className="text-xs bg-red-50 p-2 rounded">
                  <div className="font-medium">
                    {users.find((u: User) => u.user_id === error.user_id)
                      ?.full_name || error.user_id}
                  </div>
                  <div className="text-red-600">{error.error}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

/**
 * Template Preview Component
 */
const TemplatePreview: React.FC<{ template: PermissionTemplate | null }> = ({
  template,
}) => {
  if (!template) return null;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center">
          <Layout className="h-4 w-4 mr-2" />
          Pré-visualização do Template
        </CardTitle>
        <CardDescription className="text-xs">
          {template.description}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-2">
          {Object.entries(template.permissions).map(
            ([agentName, permissions]) => {
              const agent = agentName as AgentName;
              const level = getPermissionLevel(permissions);

              return (
                <div
                  key={agent}
                  className="flex items-center justify-between p-2 bg-gray-50 rounded"
                >
                  <span className="text-xs font-medium">
                    {AGENT_DISPLAY_NAMES[agent]}
                  </span>
                  <Badge
                    variant="outline"
                    className={PERMISSION_LEVEL_COLORS[level]}
                  >
                    {PERMISSION_LEVEL_NAMES[level]}
                  </Badge>
                </div>
              );
            },
          )}
        </div>
      </CardContent>
    </Card>
  );
};

/**
 * Custom Permissions Editor
 */
const CustomPermissionsEditor: React.FC<{
  permissions: Record<AgentName, PermissionActions>;
  onChange: (permissions: Record<AgentName, PermissionActions>) => void;
  disabled?: boolean;
}> = ({ permissions, onChange, disabled = false }) => {
  const handleAgentLevelChange = useCallback(
    (agent: AgentName, level: PermissionLevel) => {
      const newPermissions = getPermissionsForLevel(level);
      onChange({
        ...permissions,
        [agent]: newPermissions,
      });
    },
    [permissions, onChange],
  );

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center">
          <Shield className="h-4 w-4 mr-2" />
          Permissões Personalizadas
        </CardTitle>
        <CardDescription className="text-xs">
          Configure permissões específicas para cada agente
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(AgentName).map(([, agentValue]) => {
            const agentPermissions = permissions[agentValue];
            const currentLevel = getPermissionLevel(agentPermissions);

            return (
              <div key={agentValue} className="space-y-2">
                <Label className="text-xs font-medium">
                  {AGENT_DISPLAY_NAMES[agentValue]}
                </Label>
                <Select
                  value={currentLevel}
                  onValueChange={(level) =>
                    handleAgentLevelChange(agentValue, level as PermissionLevel)
                  }
                  disabled={disabled}
                >
                  <SelectTrigger className="h-8">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(PERMISSION_LEVEL_NAMES).map(
                      ([levelKey, levelName]) => (
                        <SelectItem key={levelKey} value={levelKey}>
                          {levelName}
                        </SelectItem>
                      ),
                    )}
                  </SelectContent>
                </Select>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

/**
 * Main Bulk Permission Dialog Component
 */
export const BulkPermissionDialog: React.FC<BulkPermissionDialogProps> = ({
  selectedUsers,
  open,
  onClose,
  onComplete,
  className,
}) => {
  const [operation, setOperation] = useState<BulkOperation>({
    type: "template",
    changeReason: "",
  });
  const [progress, setProgress] = useState<OperationProgress>({
    total: 0,
    completed: 0,
    failed: 0,
    isRunning: false,
    errors: [],
  });
  const [selectedTemplate, setSelectedTemplate] =
    useState<PermissionTemplate | null>(null);

  // Get permission templates
  const { templates, isLoading: templatesLoading } = usePermissionTemplates();

  // Memoized user summary
  const userSummary = useMemo(() => {
    const activeUsers = selectedUsers.filter((u) => u.is_active).length;
    const inactiveUsers = selectedUsers.length - activeUsers;
    const roleCount = selectedUsers.reduce(
      (acc, user) => {
        acc[user.role] = (acc[user.role] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>,
    );

    return { activeUsers, inactiveUsers, roleCount };
  }, [selectedUsers]);

  // Handle template selection
  const handleTemplateSelect = useCallback(
    (templateId: string) => {
      const template = templates.find((t) => t.template_id === templateId);
      setSelectedTemplate(template || null);
      setOperation((prev) => ({
        ...prev,
        type: "template",
        templateId,
        permissions: template?.permissions,
      }));
    },
    [templates],
  );

  // Handle operation type change
  const handleOperationTypeChange = useCallback(
    (type: BulkOperation["type"]) => {
      setOperation((prev) => {
        const newOp: BulkOperation = {
          ...prev,
          type,
        };

        if (type === "grant_all") {
          newOp.permissions = Object.values(AgentName).reduce(
            (acc, agent) => {
              acc[agent] = getPermissionsForLevel(PERMISSION_LEVELS.FULL);
              return acc;
            },
            {} as Record<AgentName, PermissionActions>,
          );
        } else if (type === "revoke_all") {
          newOp.permissions = Object.values(AgentName).reduce(
            (acc, agent) => {
              acc[agent] = getPermissionsForLevel(PERMISSION_LEVELS.NONE);
              return acc;
            },
            {} as Record<AgentName, PermissionActions>,
          );
        } else if (type === "custom") {
          newOp.permissions = Object.values(AgentName).reduce(
            (acc, agent) => {
              acc[agent] = getPermissionsForLevel(PERMISSION_LEVELS.READ_ONLY);
              return acc;
            },
            {} as Record<AgentName, PermissionActions>,
          );
        }

        return newOp;
      });
      setSelectedTemplate(null);
    },
    [],
  );

  // Execute bulk operation
  const executeBulkOperation = useCallback(async () => {
    if (!operation.changeReason.trim()) {
      toast({
        title: "Motivo obrigatório",
        description: "Por favor, informe o motivo da alteração.",
        variant: "error",
      });
      return;
    }

    setProgress({
      total: selectedUsers.length,
      completed: 0,
      failed: 0,
      isRunning: true,
      errors: [],
    });

    try {
      const results: BulkPermissionAssignResponse = {
        success_count: 0,
        error_count: 0,
        errors: [],
      };

      // Process users one by one for better progress tracking
      for (let i = 0; i < selectedUsers.length; i++) {
        const user = selectedUsers[i];

        setProgress((prev) => ({
          ...prev,
          currentUser: user.full_name,
        }));

        try {
          // Real API call to update user permissions
          await PermissionAPI.User.bulkAssignPermissions({
            user_ids: [user.user_id],
            permissions: operation.permissions,
            change_reason: operation.changeReason,
          });

          results.success_count++;
          setProgress((prev) => ({
            ...prev,
            completed: prev.completed + 1,
          }));
        } catch (error) {
          const errorObj = {
            user_id: user.user_id,
            error: error instanceof Error ? error.message : "Erro desconhecido",
          };
          results.errors.push(errorObj);
          results.error_count++;
          setProgress((prev) => ({
            ...prev,
            failed: prev.failed + 1,
            errors: [...prev.errors, errorObj],
          }));
        }
      }

      setProgress((prev) => ({
        ...prev,
        isRunning: false,
        currentUser: undefined,
      }));

      toast({
        title: "Operação concluída",
        description: `${results.success_count} usuários atualizados com sucesso. ${results.error_count} falhas.`,
        variant: results.error_count === 0 ? "success" : "warning",
      });

      onComplete?.(selectedUsers.map((u) => u.user_id));

      // Auto-close after successful completion
      if (results.error_count === 0) {
        setTimeout(() => {
          onClose();
        }, 2000);
      }
    } catch (error) {
      setProgress((prev) => ({
        ...prev,
        isRunning: false,
      }));

      toast({
        title: "Erro na operação",
        description: "Falha ao executar a operação em lote. Tente novamente.",
        variant: "error",
      });
      console.error("Bulk operation failed:", error);
    }
  }, [operation, selectedUsers, onComplete, onClose]);

  // Export current permissions
  const exportPermissions = useCallback(() => {
    const data = {
      users: selectedUsers.map((u) => ({
        id: u.user_id,
        name: u.full_name,
        email: u.email,
      })),
      timestamp: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `permissions-export-${new Date().toISOString().split("T")[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    toast({
      title: "Exportação concluída",
      description: "Lista de usuários exportada com sucesso.",
      variant: "success",
    });
  }, [selectedUsers]);

  const canExecute = useMemo(() => {
    return (
      operation.changeReason.trim() &&
      selectedUsers.length > 0 &&
      !progress.isRunning &&
      ((operation.type === "template" && operation.templateId) ||
        operation.type !== "template")
    );
  }, [operation, selectedUsers.length, progress.isRunning]);

  return (
    <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="update">
      <Dialog open={open} onOpenChange={(newOpen) => !newOpen && onClose()}>
        <DialogContent
          className={`max-w-5xl max-h-[90vh] overflow-y-auto ${className}`}
        >
          <DialogHeader>
            <DialogTitle className="flex items-center">
              <Users className="h-5 w-5 mr-2" />
              Operações em Lote - {selectedUsers.length} usuários selecionados
            </DialogTitle>
            <DialogDescription>
              Execute operações de permissão em múltiplos usuários
              simultaneamente
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6">
            {/* User Summary */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Resumo dos Usuários</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-green-600">
                      {userSummary.activeUsers}
                    </div>
                    <div className="text-xs text-muted-foreground">Ativos</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-gray-600">
                      {userSummary.inactiveUsers}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Inativos
                    </div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-blue-600">
                      {userSummary.roleCount.admin || 0}
                    </div>
                    <div className="text-xs text-muted-foreground">Admins</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-purple-600">
                      {userSummary.roleCount.user || 0}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Usuários
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Operation Type Selection */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Tipo de Operação</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Select
                  value={operation.type}
                  onValueChange={handleOperationTypeChange}
                  disabled={progress.isRunning}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="template">Aplicar Template</SelectItem>
                    <SelectItem value="grant_all">
                      Conceder Todas as Permissões
                    </SelectItem>
                    <SelectItem value="revoke_all">
                      Revogar Todas as Permissões
                    </SelectItem>
                    <SelectItem value="custom">
                      Permissões Personalizadas
                    </SelectItem>
                  </SelectContent>
                </Select>

                {/* Template Selection */}
                {operation.type === "template" && (
                  <div className="space-y-2">
                    <Label>Selecionar Template</Label>
                    <Select
                      value={operation.templateId || ""}
                      onValueChange={handleTemplateSelect}
                      disabled={progress.isRunning || templatesLoading}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Escolha um template..." />
                      </SelectTrigger>
                      <SelectContent>
                        {templates.map((template) => (
                          <SelectItem
                            key={template.template_id}
                            value={template.template_id}
                          >
                            {template.template_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                {/* Change Reason */}
                <div>
                  <Label htmlFor="changeReason">Motivo da Alteração *</Label>
                  <Textarea
                    id="changeReason"
                    placeholder="Descreva o motivo desta operação em lote..."
                    value={operation.changeReason}
                    onChange={(e) =>
                      setOperation((prev) => ({
                        ...prev,
                        changeReason: e.target.value,
                      }))
                    }
                    disabled={progress.isRunning}
                    rows={2}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Template Preview */}
            {operation.type === "template" && selectedTemplate && (
              <TemplatePreview template={selectedTemplate} />
            )}

            {/* Custom Permissions Editor */}
            {operation.type === "custom" && operation.permissions && (
              <CustomPermissionsEditor
                permissions={operation.permissions}
                onChange={(permissions) =>
                  setOperation((prev) => ({ ...prev, permissions }))
                }
                disabled={progress.isRunning}
              />
            )}

            {/* Progress Tracker */}
            {progress.isRunning ||
            progress.completed > 0 ||
            progress.failed > 0 ? (
              <ProgressTracker progress={progress} users={selectedUsers} />
            ) : null}

            {/* Warning for dangerous operations */}
            {(operation.type === "grant_all" ||
              operation.type === "revoke_all") && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  <strong>Atenção:</strong> Esta operação afetará{" "}
                  {selectedUsers.length} usuários.
                  {operation.type === "grant_all" &&
                    " Todos receberão permissões completas em todos os agentes."}
                  {operation.type === "revoke_all" &&
                    " Todas as permissões serão removidas."}
                </AlertDescription>
              </Alert>
            )}
          </div>

          <DialogFooter className="flex justify-between">
            <div className="flex space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={exportPermissions}
                disabled={progress.isRunning}
              >
                <Download className="h-4 w-4 mr-2" />
                Exportar Lista
              </Button>
            </div>

            <div className="flex space-x-2">
              <Button
                variant="outline"
                onClick={onClose}
                disabled={progress.isRunning}
              >
                <X className="h-4 w-4 mr-2" />
                Cancelar
              </Button>

              <Button
                onClick={executeBulkOperation}
                disabled={!canExecute}
                className="min-w-[160px]"
              >
                {progress.isRunning ? (
                  <>
                    <div className="animate-spin h-4 w-4 border-b-2 border-white mr-2"></div>
                    Aplicando...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Aplicar Alterações
                  </>
                )}
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </PermissionGuard>
  );
};

export default BulkPermissionDialog;
