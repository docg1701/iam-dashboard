/**
 * Permission Audit Log Component
 *
 * Component for displaying comprehensive permission audit trails with filtering,
 * search, and detailed change tracking for administrative oversight.
 */

"use client";

import React, { useState, useMemo, useCallback } from "react";
import {
  History,
  Filter,
  Search,
  Download,
  Calendar,
  User,
  Shield,
  ArrowRight,
  AlertTriangle,
  CheckCircle,
  Clock,
  Eye,
  RefreshCw,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import {
  AgentName,
  PermissionAuditLog as PermissionAuditLogType,
  PermissionActions,
  getPermissionLevel,
  PERMISSION_LEVEL_NAMES,
  PERMISSION_LEVELS,
} from "@/types/permissions";
import { PermissionAPI } from "@/lib/api/permissions";
import { PermissionGuard } from "@/components/common/PermissionGuard";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Calendar as CalendarComponent } from "@/components/ui/calendar";
import { toast } from "@/components/ui/toast";
import { format, subDays } from "date-fns";
import { ptBR } from "date-fns/locale";

// Types for the component
interface PermissionAuditLogProps {
  userId?: string;
  agentFilter?: AgentName;
  className?: string;
  limit?: number;
  showUserColumn?: boolean;
  embedded?: boolean;
}

interface AuditFilters {
  search: string;
  agent: AgentName | "all";
  action: string;
  dateFrom: Date | null;
  dateTo: Date | null;
  changedBy: string;
}

interface AuditStats {
  totalLogs: number;
  recentChanges: number;
  totalAdmins: number;
  mostActiveAgent: AgentName | null;
}

// Agent display names in Portuguese
const AGENT_DISPLAY_NAMES: Record<AgentName, string> = {
  [AgentName.CLIENT_MANAGEMENT]: "Gestão de Clientes",
  [AgentName.PDF_PROCESSING]: "Processamento PDFs",
  [AgentName.REPORTS_ANALYSIS]: "Relatórios",
  [AgentName.AUDIO_RECORDING]: "Gravação de Áudio",
};

// Action display names in Portuguese
const ACTION_DISPLAY_NAMES: Record<string, string> = {
  GRANT: "Concedido",
  REVOKE: "Revogado",
  UPDATE: "Atualizado",
  BULK_GRANT: "Concessão em Lote",
  BULK_REVOKE: "Revogação em Lote",
  TEMPLATE_APPLIED: "Template Aplicado",
};

// Action color mapping
const ACTION_COLORS: Record<string, string> = {
  GRANT: "bg-green-100 text-green-800 border-green-200",
  REVOKE: "bg-red-100 text-red-800 border-red-200",
  UPDATE: "bg-blue-100 text-blue-800 border-blue-200",
  BULK_GRANT: "bg-purple-100 text-purple-800 border-purple-200",
  BULK_REVOKE: "bg-orange-100 text-orange-800 border-orange-200",
  TEMPLATE_APPLIED: "bg-indigo-100 text-indigo-800 border-indigo-200",
};

/**
 * Permission Change Comparison Component
 * Used for displaying detailed permission changes in audit logs
 * TODO: Integrate this component into audit log details view
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const PermissionChangeComparison: React.FC<{
  oldPermissions: PermissionActions | null;
  newPermissions: PermissionActions | null;
}> = ({ oldPermissions, newPermissions }) => {
  const oldLevel = oldPermissions
    ? getPermissionLevel(oldPermissions)
    : PERMISSION_LEVELS.NONE;
  const newLevel = newPermissions
    ? getPermissionLevel(newPermissions)
    : PERMISSION_LEVELS.NONE;

  const changes = useMemo(() => {
    if (!oldPermissions || !newPermissions) {
      return [];
    }

    const changeList: Array<{
      operation: keyof PermissionActions;
      old: boolean;
      new: boolean;
      changed: boolean;
    }> = [];

    Object.entries(newPermissions).forEach(
      ([operation, newValue]: [string, boolean]) => {
        const oldValue =
          oldPermissions[operation as keyof PermissionActions] || false;
        changeList.push({
          operation: operation as keyof PermissionActions,
          old: oldValue,
          new: newValue,
          changed: oldValue !== newValue,
        });
      },
    );

    return changeList;
  }, [oldPermissions, newPermissions]);

  const operationNames = {
    create: "Criar",
    read: "Visualizar",
    update: "Editar",
    delete: "Excluir",
  };

  return (
    <div className="space-y-2">
      {/* Level Change */}
      <div className="flex items-center space-x-2 text-sm">
        <Badge variant="outline" className="text-xs">
          {PERMISSION_LEVEL_NAMES[oldLevel]}
        </Badge>
        <ArrowRight className="h-3 w-3 text-muted-foreground" />
        <Badge variant="outline" className="text-xs">
          {PERMISSION_LEVEL_NAMES[newLevel]}
        </Badge>
      </div>

      {/* Detailed Changes */}
      <div className="grid grid-cols-2 gap-1 text-xs">
        {changes.map((change) => (
          <div
            key={change.operation}
            className={`flex items-center justify-between p-1 rounded ${
              change.changed ? "bg-yellow-50" : "bg-gray-50"
            }`}
          >
            <span className="capitalize">
              {operationNames[change.operation]}
            </span>
            <div className="flex items-center space-x-1">
              {change.old ? (
                <CheckCircle className="h-3 w-3 text-green-600" />
              ) : (
                <div className="h-3 w-3 rounded-full bg-gray-300" />
              )}
              <ArrowRight className="h-2 w-2 text-muted-foreground" />
              {change.new ? (
                <CheckCircle className="h-3 w-3 text-green-600" />
              ) : (
                <div className="h-3 w-3 rounded-full bg-gray-300" />
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

/**
 * Audit Log Entry Component
 */
const AuditLogEntry: React.FC<{
  log: PermissionAuditLogType;
  showUser?: boolean;
}> = ({ log, showUser = false }) => {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <TableRow>
      <TableCell>
        <div className="text-sm text-muted-foreground">
          {format(new Date(log.created_at), "dd/MM/yyyy HH:mm", {
            locale: ptBR,
          })}
        </div>
      </TableCell>

      {showUser && (
        <TableCell>
          <div className="flex items-center space-x-2">
            <User className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">{log.user_id}</span>
          </div>
        </TableCell>
      )}

      <TableCell>
        <Badge variant="outline">{AGENT_DISPLAY_NAMES[log.agent_name]}</Badge>
      </TableCell>

      <TableCell>
        <Badge
          variant="outline"
          className={ACTION_COLORS[log.action] || "bg-gray-100 text-gray-800"}
        >
          {ACTION_DISPLAY_NAMES[log.action] || log.action}
        </Badge>
      </TableCell>

      <TableCell>
        <div className="text-sm font-medium">{log.changed_by_user_id}</div>
      </TableCell>

      <TableCell>
        {log.change_reason ? (
          <div className="text-sm text-muted-foreground max-w-xs truncate">
            {log.change_reason}
          </div>
        ) : (
          <span className="text-xs text-muted-foreground">-</span>
        )}
      </TableCell>

      <TableCell>
        <div className="flex items-center space-x-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowDetails(!showDetails)}
          >
            <Eye className="h-4 w-4" />
          </Button>
        </div>
      </TableCell>
    </TableRow>
  );
};

/**
 * Main Permission Audit Log Component
 */
export const PermissionAuditLog: React.FC<PermissionAuditLogProps> = ({
  userId,
  agentFilter,
  className,
  limit = 50,
  showUserColumn = true,
  embedded = false,
}) => {
  const [filters, setFilters] = useState<AuditFilters>({
    search: "",
    agent: agentFilter || "all",
    action: "all",
    dateFrom: subDays(new Date(), 30), // Default to last 30 days
    dateTo: new Date(),
    changedBy: "",
  });

  // Fetch audit logs
  const {
    data: auditData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["permission-audit", userId, filters, limit],
    queryFn: async () => {
      const queryParams = {
        user_id: userId,
        agent_name: filters.agent !== "all" ? filters.agent : undefined,
        action: filters.action !== "all" ? filters.action : undefined,
        date_from: filters.dateFrom?.toISOString(),
        date_to: filters.dateTo?.toISOString(),
        changed_by: filters.changedBy || undefined,
        limit,
      };

      if (userId) {
        return PermissionAPI.Audit.getUserAuditLogs(userId, queryParams);
      } else {
        // Get recent changes when no specific user is selected
        const recentLogs = await PermissionAPI.Audit.getRecentChanges(limit);
        return {
          logs: recentLogs,
          total: recentLogs.length,
          limit,
          offset: 0,
        };
      }
    },
    staleTime: 1 * 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
  });

  // Filter logs based on search
  const filteredLogs = useMemo(() => {
    if (!auditData?.logs) return [];

    return auditData.logs.filter((log: PermissionAuditLogType) => {
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        return (
          log.user_id.toLowerCase().includes(searchLower) ||
          log.changed_by_user_id.toLowerCase().includes(searchLower) ||
          (log.change_reason &&
            log.change_reason.toLowerCase().includes(searchLower))
        );
      }
      return true;
    });
  }, [auditData?.logs, filters.search]);

  // Calculate audit statistics
  const auditStats = useMemo((): AuditStats => {
    if (!auditData?.logs) {
      return {
        totalLogs: 0,
        recentChanges: 0,
        totalAdmins: 0,
        mostActiveAgent: null,
      };
    }

    const recentChanges = auditData.logs.filter(
      (log: PermissionAuditLogType) => {
        const logDate = new Date(log.created_at);
        const yesterday = subDays(new Date(), 1);
        return logDate >= yesterday;
      },
    ).length;

    const admins = new Set(
      auditData.logs.map(
        (log: PermissionAuditLogType) => log.changed_by_user_id,
      ),
    );

    const agentCounts = auditData.logs.reduce(
      (acc: Record<AgentName, number>, log: PermissionAuditLogType) => {
        acc[log.agent_name] = (acc[log.agent_name] || 0) + 1;
        return acc;
      },
      {} as Record<AgentName, number>,
    );

    const mostActiveAgent =
      (Object.entries(agentCounts).reduce(
        (max: [string, number], [agent, count]: [string, number]) => {
          return count > (max[1] || 0) ? [agent, count] : max;
        },
        ["", 0],
      )[0] as AgentName) || null;

    return {
      totalLogs: auditData.logs.length,
      recentChanges,
      totalAdmins: admins.size,
      mostActiveAgent,
    };
  }, [auditData?.logs]);

  // Export audit logs
  const handleExport = useCallback(() => {
    const exportData = {
      logs: filteredLogs,
      filters,
      exportDate: new Date().toISOString(),
      total: filteredLogs.length,
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `audit-log-${format(new Date(), "yyyy-MM-dd-HHmm")}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    toast({
      title: "Exportação concluída",
      description: `${filteredLogs.length} registros de auditoria exportados.`,
      variant: "success",
    });
  }, [filteredLogs, filters]);

  if (!embedded) {
    return (
      <PermissionGuard agent={AgentName.CLIENT_MANAGEMENT} operation="read">
        <div className={`space-y-6 ${className}`}>
          {/* Header */}
          <div className="flex flex-col space-y-4 sm:flex-row sm:items-center sm:justify-between sm:space-y-0">
            <div>
              <h2 className="text-2xl font-bold tracking-tight flex items-center">
                <History className="h-6 w-6 mr-2" />
                Log de Auditoria de Permissões
              </h2>
              <p className="text-muted-foreground">
                Histórico completo de alterações de permissões no sistema
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm" onClick={() => refetch()}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Atualizar
              </Button>
              <Button variant="outline" size="sm" onClick={handleExport}>
                <Download className="h-4 w-4 mr-2" />
                Exportar
              </Button>
            </div>
          </div>

          {/* Statistics */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center">
                  <History className="h-4 w-4 text-muted-foreground" />
                  <div className="ml-2">
                    <p className="text-sm font-medium leading-none">
                      Total de Registros
                    </p>
                    <p className="text-2xl font-bold">{auditStats.totalLogs}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <div className="ml-2">
                    <p className="text-sm font-medium leading-none">
                      Últimas 24h
                    </p>
                    <p className="text-2xl font-bold">
                      {auditStats.recentChanges}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <div className="ml-2">
                    <p className="text-sm font-medium leading-none">
                      Administradores Ativos
                    </p>
                    <p className="text-2xl font-bold">
                      {auditStats.totalAdmins}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center">
                  <Shield className="h-4 w-4 text-muted-foreground" />
                  <div className="ml-2">
                    <p className="text-sm font-medium leading-none">
                      Agente Mais Ativo
                    </p>
                    <p className="text-sm font-bold">
                      {auditStats.mostActiveAgent
                        ? AGENT_DISPLAY_NAMES[auditStats.mostActiveAgent]
                        : "N/A"}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Filters */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center">
                <Filter className="h-5 w-5 mr-2" />
                Filtros
              </CardTitle>
              <CardDescription>
                Filtre os registros de auditoria por diferentes critérios
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Buscar</label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Usuário, admin ou motivo..."
                      value={filters.search}
                      onChange={(e) =>
                        setFilters((prev) => ({
                          ...prev,
                          search: e.target.value,
                        }))
                      }
                      className="pl-10"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Agente</label>
                  <Select
                    value={filters.agent}
                    onValueChange={(value) =>
                      setFilters((prev) => ({
                        ...prev,
                        agent: value as AgentName | "all",
                      }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todos os Agentes</SelectItem>
                      {Object.entries(AGENT_DISPLAY_NAMES).map(
                        ([key, name]) => (
                          <SelectItem key={key} value={key}>
                            {name}
                          </SelectItem>
                        ),
                      )}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Ação</label>
                  <Select
                    value={filters.action}
                    onValueChange={(value) =>
                      setFilters((prev) => ({ ...prev, action: value }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todas as Ações</SelectItem>
                      {Object.entries(ACTION_DISPLAY_NAMES).map(
                        ([key, name]) => (
                          <SelectItem key={key} value={key}>
                            {name}
                          </SelectItem>
                        ),
                      )}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Data Inicial</label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className="w-full justify-start text-left font-normal"
                      >
                        <Calendar className="mr-2 h-4 w-4" />
                        {filters.dateFrom
                          ? format(filters.dateFrom, "dd/MM/yyyy", {
                              locale: ptBR,
                            })
                          : "Selecionar"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <CalendarComponent
                        mode="single"
                        selected={filters.dateFrom || undefined}
                        onSelect={(date) =>
                          setFilters((prev) => ({
                            ...prev,
                            dateFrom: date || null,
                          }))
                        }
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Data Final</label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className="w-full justify-start text-left font-normal"
                      >
                        <Calendar className="mr-2 h-4 w-4" />
                        {filters.dateTo
                          ? format(filters.dateTo, "dd/MM/yyyy", {
                              locale: ptBR,
                            })
                          : "Selecionar"}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <CalendarComponent
                        mode="single"
                        selected={filters.dateTo || undefined}
                        onSelect={(date) =>
                          setFilters((prev) => ({
                            ...prev,
                            dateTo: date || null,
                          }))
                        }
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </PermissionGuard>
    );
  }

  // Embedded view for dialogs
  return (
    <div className={`space-y-4 ${className}`}>
      {error && (
        <div className="text-center py-4">
          <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
          <p className="text-sm text-muted-foreground">
            Erro ao carregar logs de auditoria
          </p>
        </div>
      )}

      {isLoading ? (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-4"></div>
          <p className="text-sm text-muted-foreground">
            Carregando histórico...
          </p>
        </div>
      ) : (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Data/Hora</TableHead>
                  {showUserColumn && <TableHead>Usuário</TableHead>}
                  <TableHead>Agente</TableHead>
                  <TableHead>Ação</TableHead>
                  <TableHead>Alterado por</TableHead>
                  <TableHead>Motivo</TableHead>
                  <TableHead>Detalhes</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredLogs.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={showUserColumn ? 7 : 6}
                      className="text-center py-8"
                    >
                      <History className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                      <p className="text-sm text-muted-foreground">
                        Nenhum registro de auditoria encontrado
                      </p>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredLogs.map((log: PermissionAuditLogType) => (
                    <AuditLogEntry
                      key={log.audit_id}
                      log={log}
                      showUser={showUserColumn}
                    />
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default PermissionAuditLog;
