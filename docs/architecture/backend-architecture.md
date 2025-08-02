# Backend Architecture

Backend-specific architecture details based on FastAPI + SQLModel + PostgreSQL with Agno agent framework integration:

### Service Architecture

**FastAPI Application Structure:**
```
apps/backend/src/
├── main.py                       # FastAPI application entry point
├── core/                         # Core system modules
│   ├── config.py                 # Environment configuration
│   ├── database.py               # Database connection and session management
│   ├── security.py               # Authentication and JWT handling
│   ├── exceptions.py             # Custom exception classes
│   └── middleware.py             # Custom middleware (CORS, logging, etc.)
├── api/                          # REST API routes
│   └── v1/                       # API version 1
│       ├── auth.py               # Authentication endpoints
│       ├── clients.py            # Client management endpoints
│       ├── users.py              # User management endpoints
│       └── audit.py              # Audit trail endpoints
├── services/                     # Business logic layer
├── models/                       # SQLModel database models
├── agents/                       # Agno agent implementations
├── schemas/                      # Pydantic request/response schemas
└── utils/                        # Utility functions
```

### Database Architecture

**SQLModel Integration:**
```python
class ClientBase(SQLModel):
    """Base client fields for sharing between models"""
    full_name: str = Field(min_length=2, max_length=255)
    ssn: str = Field(regex=r'^\d{3}-\d{2}-\d{4}$'
    birth_date: date
    status: ClientStatus = ClientStatus.ACTIVE
    notes: Optional[str] = Field(default=None, max_length=1000)

class Client(BaseModel, ClientBase, table=True):
    """Client database model"""
    __tablename__ = "clients"
    
    client_id: UUID = Field(primary_key=True, alias="id")
    created_by: UUID = Field(foreign_key="users.user_id")
    updated_by: UUID = Field(foreign_key="users.user_id")
    
    # Relationships
    creator: User = Relationship(back_populates="created_clients")
    documents: List["Agent2Document"] = Relationship(back_populates="client")
```

### Authentication and Authorization

**JWT Authentication Flow:**
```python
class AuthService:
    def create_access_token(self, user_id: str, user_role: str) -> dict:
        """Create secure JWT token with session tracking"""
        payload = {
            "sub": user_id,
            "role": user_role,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=15),
        }
        
        access_token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 900
        }

    def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return TokenData(user_id=UUID(payload["sub"]), role=payload["role"])
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
```
