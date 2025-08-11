# Core Workflows

The following sequence diagrams illustrate key system workflows that clarify architecture decisions and complex interactions across the fullstack system:

## User Authentication with 2FA and Permission Loading

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant API as FastAPI Gateway
    participant Auth as AuthService
    participant Perm as PermissionService
    participant DB as PostgreSQL
    participant Cache as Redis

    U->>FE: Enter credentials
    FE->>API: POST /auth/login {email, password}
    API->>Auth: validate_credentials()
    Auth->>DB: SELECT user WHERE email=?
    DB-->>Auth: User record
    
    alt 2FA Enabled
        Auth-->>API: 2FA required
        API-->>FE: {requires2FA: true}
        FE-->>U: Show TOTP input
        U->>FE: Enter TOTP code
        FE->>API: POST /auth/login {email, password, totpCode}
        API->>Auth: validate_totp()
    end
    
    Auth->>Perm: load_user_permissions(user_id)
    Perm->>Cache: GET permissions:{user_id}
    
    alt Cache Miss
        Cache-->>Perm: null
        Perm->>DB: SELECT permissions WHERE user_id=?
        DB-->>Perm: Permission records
        Perm->>Cache: SET permissions:{user_id} TTL=300s
    else Cache Hit
        Cache-->>Perm: Cached permissions
    end
    
    Perm-->>Auth: User permissions
    Auth->>Auth: generate_jwt_tokens()
    Auth-->>API: {accessToken, refreshToken, user, permissions}
    API-->>FE: Authentication response
    FE->>FE: Store tokens and permissions
    FE-->>U: Dashboard with permission-based UI
```

## Client Creation with Permission Validation and Audit Trail

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant API as FastAPI Gateway
    participant Perm as PermissionService
    participant Client as ClientService
    participant Audit as AuditService
    participant DB as PostgreSQL
    participant Cache as Redis

    U->>FE: Fill client form
    FE->>FE: Real-time validation
    FE->>API: POST /clients {name, cpf, birthDate}
    
    API->>Perm: validate_permission(user_id, "client_management", "create")
    Perm->>Cache: GET permissions:{user_id}:client_management
    Cache-->>Perm: Permission record
    
    alt No Create Permission
        Perm-->>API: PermissionDenied
        API-->>FE: 403 Forbidden
        FE-->>U: Access denied message
    else Has Permission
        Perm-->>API: Permission granted
        API->>Client: create_client(data, user_id)
        
        Client->>Client: validate_cpf_format()
        Client->>DB: SELECT COUNT(*) WHERE cpf=?
        DB-->>Client: Count result
        
        alt CPF Exists
            Client-->>API: ValidationError: CPF already exists
            API-->>FE: 409 Conflict
            FE-->>U: CPF duplicate error
        else CPF Unique
            Client->>DB: BEGIN TRANSACTION
            Client->>DB: INSERT INTO clients VALUES(...)
            DB-->>Client: Client created
            
            Client->>Audit: log_action("create", "Client", new_values)
            Audit->>DB: INSERT INTO audit_logs VALUES(...)
            Client->>DB: COMMIT TRANSACTION
            
            Client-->>API: Created client record
            API-->>FE: 201 Created {client}
            FE-->>U: Success message + redirect
        end
    end
```

---
