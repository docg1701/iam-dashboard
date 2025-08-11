# API Specification

Based on the REST API choice from the Tech Stack, here's the comprehensive OpenAPI 3.0 specification for the Multi-Agent IAM Dashboard:

## REST API Specification

```yaml
openapi: 3.0.0
info:
  title: Multi-Agent IAM Dashboard API
  version: 1.0.0
  description: |
    Complete REST API for the Multi-Agent IAM Dashboard custom implementation service.
    Supports flexible agent-based permissions, client management, and multi-agent workflows.
    
    ## Authentication
    All endpoints require JWT Bearer token authentication except /auth/login and /auth/register.
    
    ## Permission System
    Endpoints are protected by agent-specific permissions:
    - client_management: Client CRUD operations
    - pdf_processing: Document upload and processing
    - reports_analysis: Analytics and reporting
    - audio_recording: Audio capture and transcription
    
    ## Rate Limiting
    - Standard users: 1000 requests/hour
    - Admin users: 5000 requests/hour
    - System admins: Unlimited

servers:
  - url: https://api.{client-domain}.com.br
    description: Client-specific production API
  - url: http://localhost:8000
    description: Local development server

paths:
  # Authentication Endpoints
  /auth/login:
    post:
      summary: User login with optional 2FA
      tags: [Authentication]
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
                  minLength: 8
                totpCode:
                  type: string
                  pattern: '^[0-9]{6}$'
                  description: Required if 2FA is enabled
      responses:
        200:
          description: Login successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  accessToken:
                    type: string
                  refreshToken:
                    type: string
                  user:
                    $ref: '#/components/schemas/User'
                  permissions:
                    type: array
                    items:
                      $ref: '#/components/schemas/UserAgentPermission'
        401:
          description: Invalid credentials or 2FA required
        429:
          description: Rate limit exceeded

  # Client Management Endpoints (Agent 1)
  /clients:
    get:
      summary: List clients with search and filtering
      tags: [Client Management]
      security:
        - BearerAuth: []
      parameters:
        - name: search
          in: query
          schema:
            type: string
          description: Search by name or CPF
        - name: birthDateFrom
          in: query
          schema:
            type: string
            format: date
        - name: birthDateTo
          in: query
          schema:
            type: string
            format: date
        - name: limit
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
        - name: offset
          in: query
          schema:
            type: integer
            minimum: 0
            default: 0
      responses:
        200:
          description: Clients retrieved successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  clients:
                    type: array
                    items:
                      $ref: '#/components/schemas/Client'
                  total:
                    type: integer
                  limit:
                    type: integer
                  offset:
                    type: integer
        403:
          description: Insufficient permissions for client_management agent

    post:
      summary: Create new client
      tags: [Client Management]
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [name, cpf, birthDate]
              properties:
                name:
                  type: string
                  minLength: 2
                  maxLength: 100
                cpf:
                  type: string
                  pattern: '^[0-9]{11}$'
                  description: Brazilian CPF (11 digits)
                birthDate:
                  type: string
                  format: date
      responses:
        201:
          description: Client created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Client'
        400:
          description: Invalid input or CPF validation failed
        409:
          description: CPF already exists
        403:
          description: Insufficient create permissions for client_management agent

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    User:
      type: object
      properties:
        id:
          type: string
          format: uuid
        email:
          type: string
          format: email
        role:
          type: string
          enum: [sysadmin, admin, user]
        isActive:
          type: boolean
        totpEnabled:
          type: boolean
        createdAt:
          type: string
          format: date-time
        updatedAt:
          type: string
          format: date-time

    Client:
      type: object
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
        cpf:
          type: string
          pattern: '^[0-9]{11}$'
        birthDate:
          type: string
          format: date
        createdBy:
          type: string
          format: uuid
        createdAt:
          type: string
          format: date-time
        updatedAt:
          type: string
          format: date-time
        isActive:
          type: boolean

    UserAgentPermission:
      type: object
      properties:
        id:
          type: string
          format: uuid
        userId:
          type: string
          format: uuid
        agentName:
          type: string
          enum: [client_management, pdf_processing, reports_analysis, audio_recording]
        canCreate:
          type: boolean
        canRead:
          type: boolean
        canUpdate:
          type: boolean
        canDelete:
          type: boolean
        grantedBy:
          type: string
          format: uuid
        grantedAt:
          type: string
          format: date-time
        expiresAt:
          type: string
          format: date-time
          nullable: true
```

---
