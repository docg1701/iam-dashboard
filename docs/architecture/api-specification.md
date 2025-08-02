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
```
