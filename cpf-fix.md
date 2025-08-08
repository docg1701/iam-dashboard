# CPF Migration Roadmap - SSN → CPF Fix

**Winston's Architectural Migration Plan**  
*Status*: 🟢 **Phase 1 + Documentation Complete - Ready for Phase 2A**  
*Created*: 2025-08-08  
*Target*: Complete migration from US SSN format to Brazilian CPF format

## 🚨 Critical Status

**CRITICAL**: System is currently in **PARTIALLY MIGRATED STATE** and cannot remain so. This migration MUST be completed to maintain system integrity.

### Current State
- ✅ **Library Added**: `cnpj-cpf-validator` installed and documented
- ✅ **Backend Utils**: `validate_cpf()` function implemented 
- ✅ **Frontend Types**: `packages/shared/types/index.ts` migrated
- ✅ **Documentation**: All 22+ documentation files corrected (SSN→CPF)
- 🚫 **Database**: Still using SSN schema and constraints
- 🚫 **Backend Models**: Still referencing SSN fields
- 🚫 **Tests**: 25+ test files using SSN format
- 🚫 **Frontend Components**: Still using SSN masks and validation

## 📊 Complete File Inventory

### ✅ FILES ALREADY MIGRATED (Phase 1 + Documentation)
```
✅ docs/architecture.md (tech stack + all interface definitions)
✅ docs/architecture/tech-stack.md (library documented)  
✅ docs/architecture/api-specification.md (OpenAPI specs corrected)
✅ docs/architecture/database-schema.md (schema + constraints)
✅ docs/architecture/testing-strategy.md (20+ test examples)
✅ docs/architecture/permission-integration-guide.md (code examples)
✅ docs/architecture/components.md (component descriptions)
✅ docs/architecture/error-handling-strategy.md (error messages)
✅ docs/brief.md (project brief)
✅ docs/prd.md (requirements + stories)
✅ packages/shared/types/index.ts (interfaces migrated)
✅ apps/backend/src/utils/validation.py (validate_cpf implemented)
✅ apps/backend/pyproject.toml (cnpj-cpf-validator added)
```

### 🔴 BACKEND FILES REQUIRING MIGRATION

#### Core Models & Schemas
```
🔴 apps/backend/src/models/client.py
   - ClientBase.ssn field → cpf
   - Field regex validation
   - Field validators  
   - Comments and documentation

🔴 apps/backend/src/schemas/clients.py  
   - All schema classes with ssn fields
   - Validation patterns and messages
   - Field descriptions

🔴 apps/backend/src/api/v1/clients.py
   - API endpoint parameter handling
   - Response field mapping
   - Error messages
```

#### Database Migration
```
🔴 apps/backend/alembic/versions/07ec9e9b9bff_create_initial_schemas_for_users_.py
   - Review existing migration (reference only)

🔴 NEW: apps/backend/alembic/versions/[new]_migrate_ssn_to_cpf.py
   - Column rename: ssn → cpf
   - Update constraints and indexes  
   - Data format conversion
   - Rollback strategy
```

#### Services & Business Logic
```
🔴 apps/backend/src/services/client_service.py
   - Service methods using ssn parameters
   - Search and filter logic
   - Data masking logic for responses

🔴 apps/backend/src/core/exceptions.py
   - Exception messages mentioning SSN
```

### 🟡 FRONTEND FILES REQUIRING MIGRATION

#### Components & Forms  
```
🟡 apps/frontend/src/components/forms/ClientRegistrationForm.tsx
   - Input field names and validation
   - Form masks and formatting
   - Error messages

🟡 apps/frontend/src/app/(dashboard)/clients/[id]/page.tsx
   - Display field mapping
   - Edit form integration

🟡 apps/frontend/src/app/(dashboard)/clients/new/page.tsx  
   - New client form integration

🟡 apps/frontend/src/app/(dashboard)/clients/page.tsx
   - List view field display
   - Search functionality

🟡 Other frontend components referencing ssn fields
```

### 🔴 CRITICAL TEST FILES (25+ files)

#### Unit Tests
```
🔴 apps/backend/src/tests/unit/test_validation.py
🔴 apps/backend/src/tests/unit/test_validation_utilities.py  
🔴 apps/backend/src/tests/unit/test_client_model.py
🔴 apps/backend/src/tests/unit/test_client_schemas.py
🔴 apps/backend/src/tests/unit/test_client_service.py
🔴 apps/backend/src/tests/unit/test_exceptions.py
🔴 apps/backend/src/tests/unit/test_factories.py
```

#### Integration Tests  
```
🔴 apps/backend/src/tests/integration/test_client_integration.py
🔴 apps/backend/src/tests/integration/test_client_service_comprehensive.py
🔴 apps/backend/src/tests/integration/test_client_service_update_delete.py
🔴 apps/backend/src/tests/integration/test_permission_integration.py
```

#### E2E Tests
```
🔴 apps/backend/src/tests/e2e/test_client_api_comprehensive.py
🔴 apps/backend/src/tests/e2e/test_client_api.py
```

#### Performance & Security Tests
```
🔴 apps/backend/src/tests/performance/test_api_performance_benchmarks.py
🔴 apps/backend/src/tests/performance/test_critical_performance_sla.py
🔴 apps/backend/src/tests/security/test_authorization_bypass_security.py
🔴 apps/backend/src/tests/security/test_data_leakage_security.py  
🔴 apps/backend/src/tests/security/test_input_validation_security.py
🔴 apps/backend/src/tests/security/test_permission_escalation_security.py
```

#### Test Factories
```
🔴 apps/backend/src/tests/factories.py
   - ClientFactory with SSN generation
   - Mock data with SSN format
```

#### Frontend Tests
```
🔴 apps/frontend/src/components/forms/__tests__/ClientRegistrationForm*.test.tsx (multiple files)
🔴 apps/frontend/src/app/(dashboard)/clients/__tests__/page.test.tsx
🔴 apps/frontend/src/app/(dashboard)/users/__tests__/page.test.tsx  
🔴 apps/frontend/src/app/(auth)/login/__tests__/page.test.tsx
🔴 Other frontend test files with SSN references
```

### ✅ DOCUMENTATION FILES COMPLETED

#### Architecture & Specs - ALL CORRECTED
```
✅ README.md (if SSN references exist)
✅ docs/architecture.md (all interface definitions)
✅ docs/architecture/api-specification.md (OpenAPI patterns)
✅ docs/architecture/database-schema.md (schema corrected)
✅ docs/brief.md (project descriptions)
✅ docs/prd.md (requirements and stories)
✅ All major story files with SSN references
✅ All PRD files with client management references
✅ All testing examples and code snippets
```

## 🗺️ EXECUTION ROADMAP

### **PHASE 2A: Backend Core Migration** 
*Priority: CRITICAL - System Breaking*
*Estimated Time: 2-3 hours*

**Step 2A.1: Database Schema Migration**
- [ ] Create new Alembic migration file
- [ ] Implement column rename with data preservation
- [ ] Update constraints and indexes
- [ ] Test rollback procedure

**Step 2A.2: Backend Models & Schemas**
- [ ] Update `src/models/client.py` (ClientBase, validators)
- [ ] Update `src/schemas/clients.py` (all schema classes)
- [ ] Update `src/services/client_service.py` (business logic)
- [ ] Update `src/api/v1/clients.py` (API endpoints)

**Step 2A.3: Backend Exception Handling**
- [ ] Update `src/core/exceptions.py` (error messages)

### **PHASE 2B: Backend Testing Migration**
*Priority: HIGH - Validation Required* 
*Estimated Time: 4-5 hours*

**Step 2B.1: Test Data & Factories**
- [ ] Update `src/tests/factories.py` (CPF generation)
- [ ] Create valid CPF test data sets

**Step 2B.2: Unit Test Migration**
- [ ] Migrate validation tests (`test_validation*.py`)
- [ ] Migrate model tests (`test_client_model.py`) 
- [ ] Migrate schema tests (`test_client_schemas.py`)
- [ ] Migrate service tests (`test_client_service.py`)
- [ ] Migrate exception tests (`test_exceptions.py`)

**Step 2B.3: Integration Test Migration**
- [ ] Migrate client integration tests
- [ ] Migrate service integration tests  
- [ ] Migrate permission integration tests

**Step 2B.4: E2E & Security Test Migration**
- [ ] Migrate API E2E tests
- [ ] Migrate performance tests
- [ ] Migrate security tests

### **PHASE 2C: Frontend Migration**
*Priority: MEDIUM - User Experience*
*Estimated Time: 3-4 hours*

**Step 2C.1: Component Updates**
- [ ] Update ClientRegistrationForm (masks, validation)
- [ ] Update client detail pages
- [ ] Update client list pages  
- [ ] Update search functionality

**Step 2C.2: Frontend Test Migration**
- [ ] Migrate component tests
- [ ] Migrate page tests
- [ ] Update E2E test data

### **PHASE 2D: Documentation & Cleanup**
*Priority: ✅ COMPLETED*
*Estimated Time: 2 hours*

**Step 2D.1: Architecture Documentation**
- [x] Update API specifications
- [x] Update database schema docs
- [x] Update README and brief

**Step 2D.2: Story & PRD Updates**
- [x] Update all story files
- [x] Update PRD documentation
- [x] Update error message references

### **PHASE 2E: Validation & Deployment**
*Priority: CRITICAL - System Integrity*
*Estimated Time: 1-2 hours*

**Step 2E.1: System Testing**
- [ ] Run complete test suite
- [ ] Validate API endpoints with Postman/curl
- [ ] Test client registration flow E2E
- [ ] Validate data migration integrity

**Step 2E.2: Deployment Preparation**
- [ ] Create deployment checklist
- [ ] Prepare rollback plan
- [ ] Document breaking changes

## 🎯 SUCCESS CRITERIA

### ✅ Completion Checklist
- [ ] All SSN references replaced with CPF
- [ ] Database successfully migrated without data loss
- [ ] All tests passing (unit, integration, E2E)
- [ ] Frontend forms using CPF masks (XXX.XXX.XXX-XX)
- [ ] API endpoints accepting CPF format
- [ ] Documentation updated and consistent
- [ ] No breaking changes for existing data

### 🚨 Risk Mitigation
- **Database Backup**: Create full backup before migration
- **Rollback Plan**: Tested rollback procedure for each phase
- **Progressive Testing**: Run tests after each phase completion
- **Data Validation**: Verify CPF check digit validation working
- **Performance Testing**: Ensure no performance degradation

## 📈 Progress Tracking

### Phase 1 + Documentation: ✅ COMPLETED 
- [x] Library installation and documentation
- [x] Basic validation function
- [x] TypeScript interface migration
- [x] All documentation files corrected (22+ files)
- [x] API specifications and database schema docs
- [x] Test examples and code snippets updated

### Phase 2A: 🔴 PENDING
- [ ] Database migration
- [ ] Backend models
- [ ] Backend schemas  
- [ ] API endpoints

### Phase 2B: 🔴 PENDING
- [ ] Test factories  
- [ ] Unit tests (7 files)
- [ ] Integration tests (4 files)
- [ ] E2E tests (2 files)
- [ ] Performance tests (2 files)
- [ ] Security tests (4 files)

### Phase 2C: 🔴 PENDING
- [ ] Frontend components
- [ ] Frontend tests
- [ ] UI masks and validation

### Phase 2D: ✅ COMPLETED
- [x] Documentation updates (22+ files)
- [x] API specs (OpenAPI patterns corrected)
- [x] Stories and PRDs (all major references)

### Phase 2E: 🔴 PENDING  
- [ ] System validation
- [ ] Deployment prep

---

**Total Estimated Time**: 10-14 hours (2 hours documentation completed)
**Critical Path**: Database → Backend Models → Tests → Frontend
**Risk Level**: 🟡 MEDIUM (with proper testing and backups)

*This roadmap ensures systematic, traceable migration with minimal risk to system integrity.*