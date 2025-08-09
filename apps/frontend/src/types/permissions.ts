/**
 * Permission system types for the IAM Dashboard
 *
 * Provides TypeScript interfaces for agent-based permission management,
 * supporting CRUD operations and role-based access control.
 */

import { z } from "zod";

// Agent names enum matching backend
export enum AgentName {
  CLIENT_MANAGEMENT = "client_management",
  PDF_PROCESSING = "pdf_processing",
  REPORTS_ANALYSIS = "reports_analysis",
  AUDIO_RECORDING = "audio_recording",
}

// Permission operations
export interface PermissionActions {
  create: boolean;
  read: boolean;
  update: boolean;
  delete: boolean;
}

// Zod schema for runtime validation
export const PermissionActionsSchema = z.object({
  create: z.boolean(),
  read: z.boolean(),
  update: z.boolean(),
  delete: z.boolean(),
});

// User agent permission interfaces
export interface UserAgentPermission {
  permission_id: string;
  user_id: string;
  agent_name: AgentName;
  permissions: PermissionActions;
  created_by_user_id: string;
  created_at: string;
  updated_at: string | null;
}

export interface UserAgentPermissionCreate {
  user_id: string;
  agent_name: AgentName;
  permissions: PermissionActions;
  created_by_user_id: string;
}

export interface UserAgentPermissionUpdate {
  permissions: PermissionActions;
}

// Zod schemas for API validation
export const UserAgentPermissionCreateSchema = z.object({
  user_id: z.string().uuid(),
  agent_name: z.nativeEnum(AgentName),
  permissions: PermissionActionsSchema,
  created_by_user_id: z.string().uuid(),
});

export const UserAgentPermissionUpdateSchema = z.object({
  permissions: PermissionActionsSchema,
});

// Permission template interfaces
export interface PermissionTemplate {
  template_id: string;
  template_name: string;
  description: string | null;
  permissions: Record<AgentName, PermissionActions>;
  is_system_template: boolean;
  created_by_user_id: string;
  created_at: string;
  updated_at: string | null;
}

export interface PermissionTemplateCreate {
  template_name: string;
  description?: string;
  permissions: Record<AgentName, PermissionActions>;
  is_system_template?: boolean;
  created_by_user_id: string;
}

export interface PermissionTemplateUpdate {
  template_name?: string;
  description?: string;
  permissions?: Record<AgentName, PermissionActions>;
}

// Zod schemas for templates
export const PermissionTemplateCreateSchema = z.object({
  template_name: z.string().min(1).max(100),
  description: z.string().optional(),
  permissions: z.record(z.nativeEnum(AgentName), PermissionActionsSchema),
  is_system_template: z.boolean().optional().default(false),
  created_by_user_id: z.string().uuid(),
});

export const PermissionTemplateUpdateSchema = z.object({
  template_name: z.string().min(1).max(100).optional(),
  description: z.string().optional(),
  permissions: z
    .record(z.nativeEnum(AgentName), PermissionActionsSchema)
    .optional(),
});

// Permission audit log interface
export interface PermissionAuditLog {
  audit_id: string;
  user_id: string;
  agent_name: AgentName;
  action: string;
  old_permissions: PermissionActions | null;
  new_permissions: PermissionActions | null;
  changed_by_user_id: string;
  change_reason: string | null;
  created_at: string;
}

// Permission matrix for user (all agents at once)
export interface UserPermissionMatrix {
  user_id: string;
  permissions: Record<AgentName, PermissionActions>;
  last_updated: string;
}

// API request/response types
export interface PermissionCheckRequest {
  user_id: string;
  agent_name: AgentName;
  operation: keyof PermissionActions;
}

export interface PermissionCheckResponse {
  allowed: boolean;
  user_id: string;
  agent_name: AgentName;
  operation: keyof PermissionActions;
}

export interface BulkPermissionAssignRequest {
  user_ids: string[];
  template_id?: string;
  permissions?: Record<AgentName, PermissionActions>;
  change_reason?: string;
}

export interface BulkPermissionAssignResponse {
  success_count: number;
  error_count: number;
  errors: Array<{
    user_id: string;
    error: string;
  }>;
}

// Hook state types
export interface UseUserPermissionsState {
  permissions: Record<AgentName, PermissionActions> | null;
  isLoading: boolean;
  error: Error | null;
  lastUpdated: Date | null;
}

export interface UseUserPermissionsActions {
  hasPermission: (
    agent: AgentName,
    operation: keyof PermissionActions,
  ) => boolean;
  hasAgentPermission: (agent: AgentName) => boolean;
  getUserMatrix: () => UserPermissionMatrix | null;
  refetch: () => void;
  invalidate: () => void;
}

// Permission guard props
export interface PermissionGuardProps {
  agent: AgentName;
  operation?: keyof PermissionActions;
  userId?: string;
  fallback?: React.ReactNode;
  loading?: React.ReactNode;
  children: React.ReactNode;
}

// Error types
export class PermissionError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly agent?: AgentName,
    public readonly operation?: keyof PermissionActions,
  ) {
    super(message);
    this.name = "PermissionError";
  }
}

// WebSocket types for real-time updates
export interface PermissionUpdateEvent {
  type: "permission_update";
  user_id: string;
  agent_name: AgentName;
  permissions: PermissionActions;
  changed_by: string;
  timestamp: string;
}

export interface PermissionWebSocketMessage {
  event: PermissionUpdateEvent;
  user_id: string;
}

// Permission context types
export interface PermissionContextValue {
  permissions: Record<AgentName, PermissionActions> | null;
  isLoading: boolean;
  error: Error | null;
  hasPermission: (
    agent: AgentName,
    operation: keyof PermissionActions,
  ) => boolean;
  hasAgentPermission: (agent: AgentName) => boolean;
  refetch: () => void;
}

// Utility types
export type PermissionOperation = keyof PermissionActions;
export type AgentPermissions = Record<AgentName, PermissionActions>;
export type PartialAgentPermissions = Partial<
  Record<AgentName, Partial<PermissionActions>>
>;

// Type guards
export const isValidAgentName = (value: string): value is AgentName => {
  return Object.values(AgentName).includes(value as AgentName);
};

export const isValidPermissionOperation = (
  value: string,
): value is PermissionOperation => {
  return ["create", "read", "update", "delete"].includes(value);
};

// Default permission values
export const DEFAULT_PERMISSIONS: PermissionActions = {
  create: false,
  read: false,
  update: false,
  delete: false,
};

export const DEFAULT_AGENT_PERMISSIONS: Record<AgentName, PermissionActions> = {
  [AgentName.CLIENT_MANAGEMENT]: DEFAULT_PERMISSIONS,
  [AgentName.PDF_PROCESSING]: DEFAULT_PERMISSIONS,
  [AgentName.REPORTS_ANALYSIS]: DEFAULT_PERMISSIONS,
  [AgentName.AUDIO_RECORDING]: DEFAULT_PERMISSIONS,
};

// Permission level helpers
export const PERMISSION_LEVELS = {
  NONE: "none" as const,
  READ_ONLY: "read_only" as const,
  STANDARD: "standard" as const,
  FULL: "full" as const,
};

export type PermissionLevel =
  (typeof PERMISSION_LEVELS)[keyof typeof PERMISSION_LEVELS];

export const getPermissionLevel = (
  permissions: PermissionActions,
): PermissionLevel => {
  const { create, read, update, delete: del } = permissions;

  if (!create && !read && !update && !del) {
    return PERMISSION_LEVELS.NONE;
  }

  if (!create && read && !update && !del) {
    return PERMISSION_LEVELS.READ_ONLY;
  }

  if (create && read && update && !del) {
    return PERMISSION_LEVELS.STANDARD;
  }

  if (create && read && update && del) {
    return PERMISSION_LEVELS.FULL;
  }

  return PERMISSION_LEVELS.NONE; // Custom permissions default to none level
};

export const getPermissionsForLevel = (
  level: PermissionLevel,
): PermissionActions => {
  switch (level) {
    case PERMISSION_LEVELS.NONE:
      return { create: false, read: false, update: false, delete: false };
    case PERMISSION_LEVELS.READ_ONLY:
      return { create: false, read: true, update: false, delete: false };
    case PERMISSION_LEVELS.STANDARD:
      return { create: true, read: true, update: true, delete: false };
    case PERMISSION_LEVELS.FULL:
      return { create: true, read: true, update: true, delete: true };
    default:
      return DEFAULT_PERMISSIONS;
  }
};

// Permission level display names
export const PERMISSION_LEVEL_NAMES: Record<PermissionLevel, string> = {
  [PERMISSION_LEVELS.NONE]: "Sem Acesso",
  [PERMISSION_LEVELS.READ_ONLY]: "Leitura",
  [PERMISSION_LEVELS.STANDARD]: "Padrão",
  [PERMISSION_LEVELS.FULL]: "Completo",
};
