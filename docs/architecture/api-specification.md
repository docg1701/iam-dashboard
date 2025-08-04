# API Specification

Based on the chosen REST API style, comprehensive OpenAPI 3.0 specification covering all endpoints from PRD requirements:

### REST API Specification

```yaml
openapi: 3.0.3
info:
  title: Multi-Agent IAM Dashboard API
  version: 1.0.0
  description: |
    REST API for the Multi-Agent IAM Dashboard - a custom implementation service
    providing dedicated VPS instances with independent AI agents for client management.

servers:
  - url: https://api.{client-domain}.com/v1
    description: Production client instance
  - url: http://localhost:8000/v1
    description: Local development server

security:
  - BearerAuth: []

paths:
  /auth/login:
    post:
      tags: [Authentication]
      summary: User login with email and password
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [email, password]
              properties:
                email:
                  type: string
                  format: email
                password:
                  type: string
                  format: password
      responses:
        '200':
          description: Login successful, returns JWT token
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token:
                    type: string
                  token_type:
                    type: string
                    example: "bearer"
                  expires_in:
                    type: integer
                    example: 3600
                  requires_2fa:
                    type: boolean

  /clients:
    get:
      tags: [Clients]
      summary: List and search clients
      parameters:
        - name: query
          in: query
          schema:
            type: string
        - name: status
          in: query
          schema:
            type: string
            enum: [active, inactive, archived]
        - name: page
          in: query
          schema:
            type: integer
            minimum: 1
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
      responses:
        '200':
          description: List of clients with pagination
          content:
            application/json:
              schema:
                type: object
                properties:
                  items:
                    type: array
                    items:
                      $ref: '#/components/schemas/Client'
                  total:
                    type: integer
                  page:
                    type: integer
                  limit:
                    type: integer
                  pages:
                    type: integer

    post:
      tags: [Clients]
      summary: Create a new client
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ClientCreate'
      responses:
        '201':
          description: Client created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Client'

  /clients/{client_id}:
    get:
      tags: [Clients]
      summary: Get a single client by ID
      parameters:
        - name: client_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Client details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Client'
        '404':
          description: Client not found
    put:
      tags: [Clients]
      summary: Update an existing client
      parameters:
        - name: client_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ClientUpdate'
      responses:
        '200':
          description: Client updated successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Client'
        '404':
          description: Client not found
    delete:
      tags: [Clients]
      summary: Delete a client
      parameters:
        - name: client_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '204':
          description: Client deleted successfully
        '404':
          description: Client not found

  /users/{user_id}/permissions:
    get:
      tags: [Permissions]
      summary: Get user's agent permissions
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: User's permission matrix
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserPermissions'
        '403':
          description: Insufficient permissions to view user permissions
        '404':
          description: User not found
      security:
        - BearerAuth: []
          x-required-permission: "admin"

    put:
      tags: [Permissions]
      summary: Update user's agent permissions
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserPermissionsUpdate'
      responses:
        '200':
          description: Permissions updated successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  message:
                    type: string
                  updated_permissions:
                    $ref: '#/components/schemas/UserPermissions'
        '403':
          description: Insufficient permissions to modify user permissions
        '404':
          description: User not found
      security:
        - BearerAuth: []
          x-required-permission: "admin"

  /permissions/bulk:
    put:
      tags: [Permissions]
      summary: Bulk update permissions for multiple users
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/BulkPermissionRequest'
      responses:
        '200':
          description: Bulk operation completed
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BulkPermissionResponse'
        '403':
          description: Insufficient permissions for bulk operations
      security:
        - BearerAuth: []
          x-required-permission: "admin"

  /permissions/agents:
    get:
      tags: [Permissions]
      summary: Get available agents and operations
      responses:
        '200':
          description: List of available agents and their operations
          content:
            application/json:
              schema:
                type: object
                properties:
                  agents:
                    type: array
                    items:
                      $ref: '#/components/schemas/AgentInfo'
      security:
        - BearerAuth: []
          x-required-permission: "admin"

  /permissions/templates:
    get:
      tags: [Permission Templates]
      summary: Get all permission templates
      responses:
        '200':
          description: List of permission templates
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/PermissionTemplate'
      security:
        - BearerAuth: []
          x-required-permission: "admin"

    post:
      tags: [Permission Templates]
      summary: Create a new permission template
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PermissionTemplateCreate'
      responses:
        '201':
          description: Template created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PermissionTemplate'
        '400':
          description: Invalid template data
        '403':
          description: Insufficient permissions to create templates
      security:
        - BearerAuth: []
          x-required-permission: "admin"

  /permissions/templates/{template_id}/apply:
    post:
      tags: [Permission Templates]
      summary: Apply permission template to users
      parameters:
        - name: template_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [user_ids]
              properties:
                user_ids:
                  type: array
                  items:
                    type: string
                    format: uuid
      responses:
        '200':
          description: Template applied successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BulkPermissionResponse'
        '404':
          description: Template not found
        '403':
          description: Insufficient permissions to apply templates
      security:
        - BearerAuth: []
          x-required-permission: "admin"

  /permissions/audit:
    get:
      tags: [Permission Audit]
      summary: Get permission change audit log
      parameters:
        - name: user_id
          in: query
          schema:
            type: string
            format: uuid
        - name: agent_name
          in: query
          schema:
            type: string
            enum: [client_management, pdf_processing, reports_analysis, audio_recording]
        - name: start_date
          in: query
          schema:
            type: string
            format: date-time
        - name: end_date
          in: query
          schema:
            type: string
            format: date-time
        - name: page
          in: query
          schema:
            type: integer
            minimum: 1
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 50
      responses:
        '200':
          description: Permission audit log
          content:
            application/json:
              schema:
                type: object
                properties:
                  items:
                    type: array
                    items:
                      $ref: '#/components/schemas/PermissionAuditEntry'
                  total:
                    type: integer
                  page:
                    type: integer
                  limit:
                    type: integer
                  pages:
                    type: integer
        '403':
          description: Insufficient permissions to view audit log
      security:
        - BearerAuth: []
          x-required-permission: "admin"

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    Client:
      type: object
      required: [client_id, full_name, ssn, birth_date, status]
      properties:
        client_id:
          type: string
          format: uuid
        full_name:
          type: string
        ssn:
          type: string
          pattern: '^\d{3}-\d{2}-\d{4}$'
        birth_date:
          type: string
          format: date
        status:
          type: string
          enum: [active, inactive, archived]
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    ClientUpdate:
      type: object
      properties:
        full_name:
          type: string
          minLength: 2
          maxLength: 255
        ssn:
          type: string
          pattern: '^\d{3}-\d{2}-\d{4}$'
        birth_date:
          type: string
          format: date
        status:
          type: string
          enum: [active, inactive, archived]
        notes:
          type: string
          maxLength: 1000

    ClientCreate:
      type: object
      required: [full_name, ssn, birth_date]
      properties:
        full_name:
          type: string
          minLength: 2
          maxLength: 255
        ssn:
          type: string
          pattern: '^\d{3}-\d{2}-\d{4}$'
        birth_date:
          type: string
          format: date
        notes:
          type: string
          maxLength: 1000

    # Permission System Schemas
    AgentPermissions:
      type: object
      required: [create, read, update, delete]
      properties:
        create:
          type: boolean
          description: Permission to create new records
        read:
          type: boolean
          description: Permission to read/view records
        update:
          type: boolean
          description: Permission to modify existing records
        delete:
          type: boolean
          description: Permission to delete records

    UserPermissions:
      type: object
      properties:
        client_management:
          $ref: '#/components/schemas/AgentPermissions'
        pdf_processing:
          $ref: '#/components/schemas/AgentPermissions'
        reports_analysis:
          $ref: '#/components/schemas/AgentPermissions'
        audio_recording:
          $ref: '#/components/schemas/AgentPermissions'

    UserPermissionsUpdate:
      type: object
      required: [permissions]
      properties:
        permissions:
          $ref: '#/components/schemas/UserPermissions'

    BulkPermissionRequest:
      type: object
      required: [user_ids, permissions]
      properties:
        user_ids:
          type: array
          items:
            type: string
            format: uuid
          minItems: 1
          maxItems: 200
        permissions:
          $ref: '#/components/schemas/UserPermissions'
        operation:
          type: string
          enum: [grant, revoke, replace]
          default: replace
          description: "grant: add permissions, revoke: remove permissions, replace: completely replace permissions"

    BulkPermissionResponse:
      type: object
      properties:
        results:
          type: array
          items:
            type: object
            properties:
              user_id:
                type: string
                format: uuid
              status:
                type: string
                enum: [success, error]
              error:
                type: string
                description: Error message if status is error
        success_count:
          type: integer
        error_count:
          type: integer

    AgentInfo:
      type: object
      required: [name, display_name, operations]
      properties:
        name:
          type: string
          enum: [client_management, pdf_processing, reports_analysis, audio_recording]
        display_name:
          type: string
          example: "Client Management"
        description:
          type: string
          example: "Manage client information and records"
        operations:
          type: array
          items:
            type: string
            enum: [create, read, update, delete]

    PermissionTemplate:
      type: object
      required: [template_id, template_name, permissions, is_system_template]
      properties:
        template_id:
          type: string
          format: uuid
        template_name:
          type: string
          minLength: 3
          maxLength: 100
        description:
          type: string
          maxLength: 500
        permissions:
          $ref: '#/components/schemas/UserPermissions'
        is_system_template:
          type: boolean
          description: Whether this is a system-defined template (read-only)
        created_by_user_id:
          type: string
          format: uuid
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    PermissionTemplateCreate:
      type: object
      required: [template_name, permissions]
      properties:
        template_name:
          type: string
          minLength: 3
          maxLength: 100
        description:
          type: string
          maxLength: 500
        permissions:
          $ref: '#/components/schemas/UserPermissions'

    PermissionAuditEntry:
      type: object
      required: [audit_id, user_id, agent_name, action, changed_by_user_id, timestamp]
      properties:
        audit_id:
          type: string
          format: uuid
        user_id:
          type: string
          format: uuid
        agent_name:
          type: string
          enum: [client_management, pdf_processing, reports_analysis, audio_recording]
        action:
          type: string
          enum: [GRANT, REVOKE, UPDATE, BULK_GRANT, BULK_REVOKE, TEMPLATE_APPLIED]
        old_permissions:
          $ref: '#/components/schemas/AgentPermissions'
        new_permissions:
          $ref: '#/components/schemas/AgentPermissions'
        changed_by_user_id:
          type: string
          format: uuid
        change_reason:
          type: string
        ip_address:
          type: string
          format: ipv4
        user_agent:
          type: string
        timestamp:
          type: string
          format: date-time

    # Error Response Schema
    ErrorResponse:
      type: object
      required: [error, message]
      properties:
        error:
          type: string
          description: Error type identifier
        message:
          type: string
          description: Human-readable error message
        details:
          type: object
          description: Additional error details
        required_permission:
          type: string
          description: Required permission for protected endpoints
          example: "client_management:create"
        user_role:
          type: string
          description: Current user's role
          enum: [sysadmin, admin, user]

# WebSocket Events Documentation
# Note: WebSocket events are not part of OpenAPI spec but documented here for reference

# Permission Update WebSocket Events:
# Event Type: permission_update
# {
#   "type": "permission_update",
#   "user_id": "uuid",
#   "permissions": UserPermissions,
#   "timestamp": "ISO8601 datetime"
# }
```

### Permission System Integration

All client-related endpoints now include permission validation:

#### Client Endpoints with Permission Requirements

- `GET /clients` - Requires: `client_management:read`
- `POST /clients` - Requires: `client_management:create`  
- `GET /clients/{id}` - Requires: `client_management:read`
- `PUT /clients/{id}` - Requires: `client_management:update`
- `DELETE /clients/{id}` - Requires: `client_management:delete`

#### Permission Validation Headers

All protected endpoints return additional headers for permission context:

```yaml
# Response Headers for Permission Context
X-User-Role: sysadmin|admin|user
X-Permission-Check-Duration: 5ms
X-Permission-Cache-Hit: true|false
```

#### Error Responses for Permission Violations

```yaml
# 403 Forbidden Response for Permission Violations
{
  "error": "Insufficient permissions",
  "message": "Access denied for create operation on client_management agent",
  "required_permission": "client_management:create",
  "user_role": "user",
  "details": {
    "available_permissions": ["client_management:read"],
    "contact_admin": "Request additional permissions from your administrator"
  }
}
```
