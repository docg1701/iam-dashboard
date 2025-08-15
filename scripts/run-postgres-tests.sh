#!/bin/bash

# PostgreSQL Testing Script for IAM Dashboard
# Tests enum compatibility and production-like behavior
# Uses actual PostgreSQL database instead of SQLite

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
API_DIR="$PROJECT_ROOT/apps/api"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test execution mode (default: all)
MODE="${1:-all}"

echo -e "${BLUE}🐘 PostgreSQL Testing Script${NC}"
echo -e "${BLUE}============================${NC}"

# Check if PostgreSQL is running
check_postgres() {
    echo -e "${BLUE}📋 Checking PostgreSQL availability...${NC}"
    
    if ! docker ps | grep -q "iam-dashboard-postgres"; then
        echo -e "${YELLOW}⚠️  PostgreSQL container not running. Starting...${NC}"
        cd "$PROJECT_ROOT"
        docker-compose up -d postgres
        
        # Wait for PostgreSQL to be ready
        echo -e "${BLUE}⏳ Waiting for PostgreSQL to be ready...${NC}"
        timeout 60s bash -c 'until docker-compose exec -T postgres pg_isready -U postgres; do sleep 2; done'
        echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
    else
        echo -e "${GREEN}✅ PostgreSQL is already running${NC}"
    fi
}

# Run enum validation tests
run_enum_tests() {
    echo -e "${BLUE}🔤 Running enum validation tests...${NC}"
    
    cd "$API_DIR"
    
    # Run specific enum tests with PostgreSQL configuration
    python -m pytest tests/unit/test_*.py::*enum* \
        --confcutdir=tests \
        -o python_files=conftest_postgres.py \
        -v \
        -m "not slow" \
        --tb=short \
        --strict-markers \
        || {
        echo -e "${RED}❌ Enum tests failed${NC}"
        return 1
    }
    
    echo -e "${GREEN}✅ Enum tests passed${NC}"
}

# Run model tests with PostgreSQL
run_model_tests() {
    echo -e "${BLUE}🏗️  Running model tests with PostgreSQL...${NC}"
    
    cd "$API_DIR"
    
    # Run model tests using PostgreSQL conftest
    PYTHONPATH="$API_DIR/src" python -m pytest tests/unit/test_audit.py tests/unit/test_user.py tests/unit/test_permission.py \
        --confcutdir=tests \
        -c pytest.ini \
        -v \
        --tb=short \
        --strict-markers \
        || {
        echo -e "${RED}❌ Model tests failed${NC}"
        return 1
    }
    
    echo -e "${GREEN}✅ Model tests passed${NC}"
}

# Run integration tests 
run_integration_tests() {
    echo -e "${BLUE}🔗 Running integration tests...${NC}"
    
    cd "$API_DIR"
    
    # Run integration tests with PostgreSQL
    PYTHONPATH="$API_DIR/src" python -m pytest tests/integration/ \
        --confcutdir=tests \
        -v \
        --tb=short \
        --strict-markers \
        -m "not slow" \
        || {
        echo -e "${RED}❌ Integration tests failed${NC}"
        return 1
    }
    
    echo -e "${GREEN}✅ Integration tests passed${NC}"
}

# Test enum storage and retrieval specifically
test_enum_storage() {
    echo -e "${BLUE}💾 Testing enum storage and retrieval...${NC}"
    
    cd "$API_DIR"
    
    # Create a specific test for enum values
    cat > /tmp/test_enum_storage.py << 'EOF'
"""Test enum storage with PostgreSQL."""

import asyncio
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlmodel import SQLModel, select

# Import our models
import sys
sys.path.append('src')
from models.user import User, UserRole
from models.audit import AuditLog, AuditAction  
from models.permission import UserAgentPermission, AgentName

# Test database URL
TEST_DB_URL = "postgresql+asyncpg://postgres:password@localhost:5432/iam_dashboard_test"

async def test_enum_storage():
    """Test that enums are stored as lowercase values."""
    # Create test engine
    engine = create_async_engine(TEST_DB_URL, echo=True)
    
    # Create test database 
    postgres_engine = create_async_engine(
        "postgresql+asyncpg://postgres:password@localhost:5432/postgres",
        isolation_level="AUTOCOMMIT"
    )
    
    async with postgres_engine.connect() as conn:
        await conn.execute("DROP DATABASE IF EXISTS iam_dashboard_test")
        await conn.execute("CREATE DATABASE iam_dashboard_test")
    
    await postgres_engine.dispose()
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # Test enum values
    async with AsyncSession(engine) as session:
        # Test UserRole enum
        user = User(
            email="test@example.com",
            password_hash="hash123",
            role=UserRole.ADMIN
        )
        session.add(user)
        await session.commit()
        
        # Verify stored value
        result = await session.execute(select(User).where(User.email == "test@example.com"))
        stored_user = result.scalar_one()
        
        print(f"Stored UserRole: {stored_user.role}")
        print(f"UserRole value: {stored_user.role.value}")
        assert stored_user.role == UserRole.ADMIN
        assert stored_user.role.value == "admin"
        
        # Test AuditAction enum
        audit = AuditLog(
            action=AuditAction.LOGIN,
            resource_type="user"
        )
        session.add(audit)
        await session.commit()
        
        result = await session.execute(select(AuditLog))
        stored_audit = result.scalar_one()
        
        print(f"Stored AuditAction: {stored_audit.action}")
        print(f"AuditAction value: {stored_audit.action.value}")
        assert stored_audit.action == AuditAction.LOGIN
        assert stored_audit.action.value == "login"
        
    await engine.dispose()
    print("✅ All enum storage tests passed!")

if __name__ == "__main__":
    asyncio.run(test_enum_storage())
EOF
    
    # Run the enum storage test
    PYTHONPATH="$API_DIR/src" python /tmp/test_enum_storage.py
    
    echo -e "${GREEN}✅ Enum storage test completed${NC}"
}

# Clean up test databases
cleanup() {
    echo -e "${BLUE}🧹 Cleaning up test databases...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Drop test database
    docker-compose exec -T postgres psql -U postgres -c "DROP DATABASE IF EXISTS iam_dashboard_test;" || true
    
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Main execution
main() {
    case "$MODE" in
        "all")
            check_postgres
            test_enum_storage
            run_model_tests
            run_integration_tests
            cleanup
            ;;
        "enum")
            check_postgres
            test_enum_storage
            cleanup
            ;;
        "models")
            check_postgres
            run_model_tests
            cleanup
            ;;
        "integration")
            check_postgres
            run_integration_tests  
            cleanup
            ;;
        "cleanup")
            cleanup
            ;;
        *)
            echo -e "${YELLOW}Usage: $0 [all|enum|models|integration|cleanup]${NC}"
            echo -e "${YELLOW}  all         - Run all PostgreSQL tests${NC}"
            echo -e "${YELLOW}  enum        - Test enum storage only${NC}" 
            echo -e "${YELLOW}  models      - Test models only${NC}"
            echo -e "${YELLOW}  integration - Test integration only${NC}"
            echo -e "${YELLOW}  cleanup     - Clean up test databases${NC}"
            exit 1
            ;;
    esac
    
    echo -e "${GREEN}🎉 PostgreSQL testing completed successfully!${NC}"
}

# Run main function
main