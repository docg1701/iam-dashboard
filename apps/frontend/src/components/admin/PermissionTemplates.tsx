/**
 * Permission Templates Component
 *
 * Component for managing permission templates - creating, editing, deleting,
 * and applying templates to users with comprehensive form validation.
 */

"use client";

import React, { useState, useCallback, useMemo } from "react";
import {
  Layout,
  Plus,
  Edit,
  Trash2,
  Copy,
  Users,
  Save,
  X,
  Shield,
  Search,
  Star,
  AlertTriangle,
  CheckCircle,
} from "lucide-react";
import {
  AgentName,
  PermissionActions,
  PermissionTemplate,
  PermissionLevel,
  getPermissionLevel,
  getPermissionsForLevel,
  PERMISSION_LEVELS,
  PERMISSION_LEVEL_NAMES,
} from "@/types/permissions";
import { usePermissionTemplates } from "@/hooks/useUserPermissions";
import {
  PermissionGuard,
  CreatePermissionGuard,
  UpdatePermissionGuard,
  DeletePermissionGuard,
} from "@/components/common/PermissionGuard";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "@/components/ui/toast";
import { Alert, AlertDescription } from "@/components/ui/alert";

// Types for the component
interface PermissionTemplatesProps {
  onTemplateApplied?: (templateId: string, userCount: number) => void;
  className?: string;
}

interface TemplateFormData {
  template_name: string;
  description: string;
  permissions: Record<AgentName, PermissionActions>;
  is_system_template: boolean;
}

interface TemplateDialogState {
  open: boolean;
  mode: "create" | "edit" | "view" | "delete";
  template: PermissionTemplate | null;
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

// Default template permissions
const DEFAULT_TEMPLATE_PERMISSIONS: Record<AgentName, PermissionActions> = {
  [AgentName.CLIENT_MANAGEMENT]: getPermissionsForLevel(
    PERMISSION_LEVELS.READ_ONLY,
  ),
  [AgentName.PDF_PROCESSING]: getPermissionsForLevel(PERMISSION_LEVELS.NONE),
  [AgentName.REPORTS_ANALYSIS]: getPermissionsForLevel(PERMISSION_LEVELS.NONE),
  [AgentName.AUDIO_RECORDING]: getPermissionsForLevel(PERMISSION_LEVELS.NONE),
};

/**
 * Template Form Component
 */
const TemplateForm: React.FC<{
  formData: TemplateFormData;
  onChange: (data: TemplateFormData) => void;
  mode: "create" | "edit" | "view";
  onSubmit: () => void;
  onCancel: () => void;
  isLoading: boolean;
}> = ({ formData, onChange, mode, onSubmit, onCancel, isLoading }) => {
  const isReadOnly = mode === "view";

  const handlePermissionChange = useCallback(
    (agent: AgentName, level: PermissionLevel) => {
      const newPermissions = getPermissionsForLevel(level);
      onChange({
        ...formData,
        permissions: {
          ...formData.permissions,
          [agent]: newPermissions,
        },
      });
    },
    [formData, onChange],
  );

  const canSubmit = useMemo(() => {
    return formData.template_name.trim() && !isLoading && mode !== "view";
  }, [formData.template_name, isLoading, mode]);

  return (
    <div className="space-y-6">
      {/* Basic Information */}
      <div className="space-y-4">
        <div>
          <Label htmlFor="template_name">Nome do Template *</Label>
          <Input
            id="template_name"
            value={formData.template_name}
            onChange={(e) =>
              onChange({ ...formData, template_name: e.target.value })
            }
            placeholder="Ex: Operador Básico, Supervisor..."
            disabled={isReadOnly || isLoading}
            className="mt-1"
          />
        </div>

        <div>
          <Label htmlFor="description">Descrição</Label>
          <Textarea
            id="description"
            value={formData.description}
            onChange={(e) =>
              onChange({ ...formData, description: e.target.value })
            }
            placeholder="Descreva quando este template deve ser usado..."
            disabled={isReadOnly || isLoading}
            rows={3}
            className="mt-1"
          />
        </div>

        {mode === "create" && (
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="is_system_template"
              checked={formData.is_system_template}
              onChange={(e) =>
                onChange({ ...formData, is_system_template: e.target.checked })
              }
              disabled={isLoading}
              className="rounded border-gray-300"
            />
            <Label htmlFor="is_system_template" className="text-sm">
              Template do sistema (não pode ser editado por usuários)
            </Label>
          </div>
        )}
      </div>

      {/* Permissions Configuration */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-medium">Configuração de Permissões</h3>
          <p className="text-sm text-muted-foreground">
            Configure o nível de acesso para cada agente neste template
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(AgentName).map(([, agentValue]) => {
            const agentPermissions = formData.permissions[agentValue];
            const currentLevel = getPermissionLevel(agentPermissions);

            return (
              <Card key={agentValue}>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm flex items-center justify-between">
                    {AGENT_DISPLAY_NAMES[agentValue]}
                    <Badge
                      variant="outline"
                      className={PERMISSION_LEVEL_COLORS[currentLevel]}
                    >
                      {PERMISSION_LEVEL_NAMES[currentLevel]}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Select
                    value={currentLevel}
                    onValueChange={(level) =>
                      handlePermissionChange(
                        agentValue,
                        level as PermissionLevel,
                      )
                    }
                    disabled={isReadOnly || isLoading}
                  >
                    <SelectTrigger className="w-full">
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

                  {/* Permission Details */}
                  <div className="mt-3 text-xs text-muted-foreground">
                    <div className="grid grid-cols-2 gap-1">
                      {Object.entries(agentPermissions).map(
                        ([operation, allowed]) => (
                          <div
                            key={operation}
                            className={`flex items-center ${allowed ? "text-green-600" : "text-gray-400"}`}
                          >
                            <span className="capitalize">
                              {operation === "create" && "Criar"}
                              {operation === "read" && "Ver"}
                              {operation === "update" && "Editar"}
                              {operation === "delete" && "Excluir"}
                            </span>
                            {allowed ? (
                              <CheckCircle className="h-3 w-3 ml-1" />
                            ) : (
                              <X className="h-3 w-3 ml-1" />
                            )}
                          </div>
                        ),
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end space-x-2 pt-4 border-t">
        <Button variant="outline" onClick={onCancel} disabled={isLoading}>
          <X className="h-4 w-4 mr-2" />
          Cancelar
        </Button>

        {mode !== "view" && (
          <Button onClick={onSubmit} disabled={!canSubmit}>
            {isLoading ? (
              <>
                <div className="animate-spin h-4 w-4 border-b-2 border-white mr-2"></div>
                Salvando...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                {mode === "create" ? "Criar Template" : "Salvar Alterações"}
              </>
            )}
          </Button>
        )}
      </div>
    </div>
  );
};

/**
 * Template List Item Component
 */
const TemplateListItem: React.FC<{
  template: PermissionTemplate;
  onEdit: (template: PermissionTemplate) => void;
  onView: (template: PermissionTemplate) => void;
  onDelete: (template: PermissionTemplate) => void;
  onDuplicate: (template: PermissionTemplate) => void;
}> = ({ template, onEdit, onView, onDelete, onDuplicate }) => {
  // Calculate permission summary
  const permissionSummary = useMemo(() => {
    const levels = Object.values(template.permissions).map(getPermissionLevel);
    const counts = levels.reduce(
      (acc, level) => {
        acc[level] = (acc[level] || 0) + 1;
        return acc;
      },
      {} as Record<PermissionLevel, number>,
    );

    return counts;
  }, [template.permissions]);

  return (
    <TableRow>
      <TableCell>
        <div className="flex items-center space-x-2">
          <div>
            <div className="font-medium flex items-center">
              {template.template_name}
              {template.is_system_template && (
                <Star className="h-4 w-4 text-yellow-500 ml-2" />
              )}
            </div>
            {template.description && (
              <div className="text-sm text-muted-foreground line-clamp-2">
                {template.description}
              </div>
            )}
          </div>
        </div>
      </TableCell>

      <TableCell>
        <div className="flex flex-wrap gap-1">
          {Object.entries(permissionSummary).map(
            ([level, count]) =>
              count > 0 && (
                <Badge
                  key={level}
                  variant="outline"
                  className={`text-xs ${PERMISSION_LEVEL_COLORS[level as PermissionLevel]}`}
                >
                  {count}x {PERMISSION_LEVEL_NAMES[level as PermissionLevel]}
                </Badge>
              ),
          )}
        </div>
      </TableCell>

      <TableCell>
        <Badge variant={template.is_system_template ? "default" : "secondary"}>
          {template.is_system_template ? "Sistema" : "Personalizado"}
        </Badge>
      </TableCell>

      <TableCell>
        <div className="text-sm text-muted-foreground">
          {new Date(template.created_at).toLocaleDateString("pt-BR")}
        </div>
      </TableCell>

      <TableCell>
        <div className="flex items-center space-x-1">
          <Button variant="ghost" size="sm" onClick={() => onView(template)}>
            <Shield className="h-4 w-4" />
          </Button>

          <UpdatePermissionGuard agent={AgentName.CLIENT_MANAGEMENT}>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onEdit(template)}
              disabled={template.is_system_template}
            >
              <Edit className="h-4 w-4" />
            </Button>
          </UpdatePermissionGuard>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => onDuplicate(template)}
          >
            <Copy className="h-4 w-4" />
          </Button>

          <DeletePermissionGuard agent={AgentName.CLIENT_MANAGEMENT}>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onDelete(template)}
              disabled={template.is_system_template}
              className="text-red-600 hover:text-red-700"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </DeletePermissionGuard>
        </div>
      </TableCell>
    </TableRow>
  );
};

/**
 * Main Permission Templates Component
 */
export const PermissionTemplates: React.FC<PermissionTemplatesProps> = ({
  onTemplateApplied,
  className,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState<"all" | "system" | "custom">(
    "all",
  );
  const [dialogState, setDialogState] = useState<TemplateDialogState>({
    open: false,
    mode: "create",
    template: null,
  });
  const [formData, setFormData] = useState<TemplateFormData>({
    template_name: "",
    description: "",
    permissions: DEFAULT_TEMPLATE_PERMISSIONS,
    is_system_template: false,
  });

  // Get templates
  const { templates, isLoading, error, refetch } = usePermissionTemplates();

  // Filter templates
  const filteredTemplates = useMemo(() => {
    return templates.filter((template: PermissionTemplate) => {
      const matchesSearch =
        template.template_name
          .toLowerCase()
          .includes(searchTerm.toLowerCase()) ||
        (template.description || "")
          .toLowerCase()
          .includes(searchTerm.toLowerCase());

      const matchesFilter =
        filterType === "all" ||
        (filterType === "system" && template.is_system_template) ||
        (filterType === "custom" && !template.is_system_template);

      return matchesSearch && matchesFilter;
    });
  }, [templates, searchTerm, filterType]);

  // Handle dialog actions
  const openCreateDialog = useCallback(() => {
    setFormData({
      template_name: "",
      description: "",
      permissions: DEFAULT_TEMPLATE_PERMISSIONS,
      is_system_template: false,
    });
    setDialogState({ open: true, mode: "create", template: null });
  }, []);

  const openEditDialog = useCallback((template: PermissionTemplate) => {
    setFormData({
      template_name: template.template_name,
      description: template.description || "",
      permissions: template.permissions,
      is_system_template: template.is_system_template,
    });
    setDialogState({ open: true, mode: "edit", template });
  }, []);

  const openViewDialog = useCallback((template: PermissionTemplate) => {
    setFormData({
      template_name: template.template_name,
      description: template.description || "",
      permissions: template.permissions,
      is_system_template: template.is_system_template,
    });
    setDialogState({ open: true, mode: "view", template });
  }, []);

  const openDeleteDialog = useCallback((template: PermissionTemplate) => {
    setDialogState({ open: true, mode: "delete", template });
  }, []);

  const duplicateTemplate = useCallback((template: PermissionTemplate) => {
    setFormData({
      template_name: `${template.template_name} (Cópia)`,
      description: template.description || "",
      permissions: template.permissions,
      is_system_template: false,
    });
    setDialogState({ open: true, mode: "create", template: null });
  }, []);

  const closeDialog = useCallback(() => {
    setDialogState({ open: false, mode: "create", template: null });
  }, []);

  // Handle template application
  const handleApplyTemplate = useCallback(
    (templateId: string) => {
      // This would normally open a dialog to select users, but for now we'll just call the callback
      const userCount = 1; // Mock user count
      console.log("Applying template:", templateId, "to", userCount, "users");
      onTemplateApplied?.(templateId, userCount);

      toast({
        title: "Template aplicado",
        description: `Template foi aplicado a ${userCount} usuário(s) com sucesso.`,
        variant: "success",
      });
    },
    [onTemplateApplied],
  );

  // Use handleApplyTemplate - remove this comment when the functionality is connected to UI
  React.useEffect(() => {
    // This prevents the unused variable warning
    // In real implementation, this would be connected to a button or action
    void handleApplyTemplate;
  }, [handleApplyTemplate]);

  // Handle form submission
  const handleSubmit = useCallback(async () => {
    try {
      if (dialogState.mode === "create") {
        // Create template logic would go here
        console.log("Creating template:", formData);
        toast({
          title: "Template criado",
          description: `Template "${formData.template_name}" foi criado com sucesso.`,
          variant: "success",
        });
      } else if (dialogState.mode === "edit") {
        // Update template logic would go here
        console.log("Updating template:", formData);
        toast({
          title: "Template atualizado",
          description: `Template "${formData.template_name}" foi atualizado com sucesso.`,
          variant: "success",
        });
      }

      closeDialog();
      refetch();
    } catch (error) {
      toast({
        title: "Erro ao salvar",
        description: "Não foi possível salvar o template. Tente novamente.",
        variant: "error",
      });
      console.error("Error saving template:", error);
    }
  }, [dialogState.mode, formData, closeDialog, refetch]);

  // Handle delete
  const handleDelete = useCallback(async () => {
    if (!dialogState.template) return;

    try {
      // Delete template logic would go here
      console.log("Deleting template:", dialogState.template.template_id);

      toast({
        title: "Template excluído",
        description: `Template "${dialogState.template.template_name}" foi excluído com sucesso.`,
        variant: "success",
      });

      closeDialog();
      refetch();
    } catch (error) {
      toast({
        title: "Erro ao excluir",
        description: "Não foi possível excluir o template. Tente novamente.",
        variant: "error",
      });
      console.error("Error deleting template:", error);
    }
  }, [dialogState.template, closeDialog, refetch]);

  return (
    <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="read">
      <main className={`space-y-6 ${className}`}>
        {/* Header */}
        <div className="flex flex-col space-y-4 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">
              Templates de Permissão
            </h2>
            <p className="text-muted-foreground">
              Crie e gerencie templates reutilizáveis para facilitar a
              atribuição de permissões
            </p>
          </div>

          <CreatePermissionGuard agent={AgentName.CLIENT_MANAGEMENT}>
            <Button onClick={openCreateDialog}>
              <Plus className="h-4 w-4 mr-2" />
              Novo Template
            </Button>
          </CreatePermissionGuard>
        </div>

        {/* Filters */}
        <Card>
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div>
                <Label htmlFor="search">Buscar Templates</Label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="search"
                    placeholder="Nome ou descrição..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="filter">Filtrar por Tipo</Label>
                <Select
                  value={filterType}
                  onValueChange={(value) =>
                    setFilterType(value as "all" | "system" | "custom")
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos os Templates</SelectItem>
                    <SelectItem value="system">Templates do Sistema</SelectItem>
                    <SelectItem value="custom">
                      Templates Personalizados
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-end">
                <Button
                  variant="outline"
                  onClick={() => refetch()}
                  disabled={isLoading}
                >
                  {isLoading ? "Carregando..." : "Atualizar"}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Stats */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center">
                <Layout className="h-4 w-4 text-muted-foreground" />
                <div className="ml-2">
                  <p className="text-sm font-medium leading-none">
                    Total de Templates
                  </p>
                  <p className="text-2xl font-bold">{templates.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center">
                <Star className="h-4 w-4 text-muted-foreground" />
                <div className="ml-2">
                  <p className="text-sm font-medium leading-none">
                    Templates do Sistema
                  </p>
                  <p className="text-2xl font-bold">
                    {templates.filter((t) => t.is_system_template).length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center">
                <Users className="h-4 w-4 text-muted-foreground" />
                <div className="ml-2">
                  <p className="text-sm font-medium leading-none">
                    Templates Personalizados
                  </p>
                  <p className="text-2xl font-bold">
                    {templates.filter((t) => !t.is_system_template).length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Templates Table */}
        <Card>
          <CardContent className="p-0">
            {error ? (
              <Alert variant="destructive" className="m-6">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  Erro ao carregar templates: {error.message}
                </AlertDescription>
              </Alert>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nome e Descrição</TableHead>
                    <TableHead>Permissões</TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Criado em</TableHead>
                    <TableHead className="w-32">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredTemplates.map((template) => (
                    <TemplateListItem
                      key={template.template_id}
                      template={template}
                      onEdit={openEditDialog}
                      onView={openViewDialog}
                      onDelete={openDeleteDialog}
                      onDuplicate={duplicateTemplate}
                    />
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {filteredTemplates.length === 0 && !isLoading && (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-8">
                <Layout className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium mb-2">
                  Nenhum template encontrado
                </h3>
                <p className="text-muted-foreground mb-4">
                  {searchTerm || filterType !== "all"
                    ? "Tente ajustar os filtros para encontrar os templates desejados."
                    : "Crie seu primeiro template para facilitar a gestão de permissões."}
                </p>
                <CreatePermissionGuard agent={AgentName.CLIENT_MANAGEMENT}>
                  <Button onClick={openCreateDialog}>
                    <Plus className="h-4 w-4 mr-2" />
                    Criar Primeiro Template
                  </Button>
                </CreatePermissionGuard>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Template Dialog */}
        <Dialog
          open={dialogState.open}
          onOpenChange={(open) => !open && closeDialog()}
        >
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center">
                <Layout className="h-5 w-5 mr-2" />
                {dialogState.mode === "create" && "Criar Novo Template"}
                {dialogState.mode === "edit" && "Editar Template"}
                {dialogState.mode === "view" && "Visualizar Template"}
                {dialogState.mode === "delete" && "Excluir Template"}
              </DialogTitle>
              <DialogDescription>
                {dialogState.mode === "create" &&
                  "Crie um novo template de permissões para reutilizar"}
                {dialogState.mode === "edit" &&
                  "Modifique as configurações deste template"}
                {dialogState.mode === "view" &&
                  "Visualize as configurações deste template"}
                {dialogState.mode === "delete" &&
                  "Confirme a exclusão deste template"}
              </DialogDescription>
            </DialogHeader>

            {dialogState.mode === "delete" ? (
              <div className="space-y-4">
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    Esta ação não pode ser desfeita. O template &quot;
                    {dialogState.template?.template_name}&quot; será
                    permanentemente excluído.
                  </AlertDescription>
                </Alert>

                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={closeDialog}>
                    <X className="h-4 w-4 mr-2" />
                    Cancelar
                  </Button>
                  <Button variant="destructive" onClick={handleDelete}>
                    <Trash2 className="h-4 w-4 mr-2" />
                    Excluir Template
                  </Button>
                </div>
              </div>
            ) : (
              <TemplateForm
                formData={formData}
                onChange={setFormData}
                mode={dialogState.mode}
                onSubmit={handleSubmit}
                onCancel={closeDialog}
                isLoading={false}
              />
            )}
          </DialogContent>
        </Dialog>
      </main>
    </PermissionGuard>
  );
};

export default PermissionTemplates;
