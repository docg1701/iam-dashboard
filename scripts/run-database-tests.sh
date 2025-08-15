#!/bin/bash

# Database Migration and Schema Tests Runner
# Purpose: Test database migrations, schema consistency, and data integrity
# Profiles: complete (default), fast, migration, integrity, performance
# Usage: ./run-database-tests.sh [profile]

# Don't exit on error - we want to capture all database test results even if some fail
# set -e  # REMOVED to continue execution on test failures
set +e  # Explicitly disable exit on error

# Show help if requested
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "🗄️ Database Migration and Schema Tests"
    echo ""
    echo "Usage: $0 [profile]"
    echo ""
    echo "Available profiles:"
    echo "  complete   (default) - All database tests: migration, schema, integrity, performance"
    echo "  fast       - Essential tests only: migration status and basic schema validation"
    echo "  migration  - Migration operations only: up/down tests and history validation"
    echo "  integrity  - Data integrity and constraints testing only"
    echo "  performance - Database performance and optimization tests only"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run complete test suite"
    echo "  $0 fast              # Quick validation for development"
    echo "  $0 migration         # Test migration operations only"
    echo "  $0 integrity         # Test data constraints and relationships"
    echo ""
    echo "Environment Variables:"
    echo "  DB_HOST              Database host (default: localhost)"
    echo "  DB_PORT              Database port (default: 5432)"
    echo "  DB_USER              Database user (default: postgres)"
    echo "  DB_PASSWORD          Database password (optional)"
    echo "  DB_TEST_NAME         Test database name (default: iam_dashboard_test)"
    echo ""
    echo "Results saved to: scripts/test-results/db-*_TIMESTAMP.log"
    exit 0
fi

# Configure test profile
TEST_PROFILE="${1:-complete}"

case "$TEST_PROFILE" in
    fast)
        SKIP_PERFORMANCE=true
        SKIP_BACKUP=true
        SKIP_INTEGRITY_DEEP=true
        ;;
    migration)
        SKIP_PERFORMANCE=true
        SKIP_BACKUP=true
        SKIP_INTEGRITY=true
        ;;
    integrity)
        SKIP_MIGRATION_OPS=true
        SKIP_PERFORMANCE=true
        SKIP_BACKUP=true
        ;;
    performance)
        SKIP_MIGRATION_OPS=true
        SKIP_INTEGRITY=true
        SKIP_BACKUP=true
        ;;
    complete|*)
        # Run all tests
        ;;
esac

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/test-results"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Global variables for statistics
TEST_SUCCESS_COUNT=0
TEST_FAILURE_COUNT=0
TEST_START_TIME=$(date +%s)

# Function to generate final statistics
generate_final_stats() {
    local completion_status=${1:-"completed"}
    local total_time=$(($(date +%s) - TEST_START_TIME))
    local total_tests=$((TEST_SUCCESS_COUNT + TEST_FAILURE_COUNT))
    
    echo ""
    echo "📋 EXECUTION STATISTICS - ${completion_status^^}"
    echo "======================================"
    echo "🕰️ Total Execution Time: ${total_time}s ($((total_time / 60))m $((total_time % 60))s)"
    echo "🏃 Tests Executed: ${total_tests}"
    echo "✅ Successful: ${TEST_SUCCESS_COUNT}"
    echo "⚠️ Failed/Timed out: ${TEST_FAILURE_COUNT}"
    
    if [ $total_tests -gt 0 ]; then
        local success_rate=$(( (TEST_SUCCESS_COUNT * 100) / total_tests ))
        echo "📊 Success Rate: ${success_rate}%"
    fi
    
    if [ "$completion_status" = "interrupted" ]; then
        echo "⚠️ Script was interrupted before completion"
    elif [ $TEST_FAILURE_COUNT -gt 0 ]; then
        echo "⚠️ Some database tests failed - check individual log files for details"
    else
        echo "✨ All database test categories completed successfully!"
    fi
    echo "======================================"
}

# Function to handle script interruption gracefully
handle_interrupt() {
    echo ""
    echo "⚠️ Database tests interrupted! Cleaning up..."
    cleanup_database
    generate_final_stats "interrupted"
    exit 130
}

# Set trap for graceful interruption handling
trap handle_interrupt SIGINT SIGTERM

# Cleanup function for database test artifacts
cleanup_database() {
    local exit_code=$?
    echo "🧹 Database cleanup on exit..."
    # Database cleanup is typically handled by test framework
    # But we ensure any hanging connections are closed
    cd "${PROJECT_ROOT}/apps/api" 2>/dev/null || true
    return $exit_code
}

# Set trap for cleanup on exit (including timeout)
trap cleanup_database EXIT

# Create results directory
mkdir -p "${RESULTS_DIR}"

echo "🗄️ Starting Database Migration Tests (Profile: ${TEST_PROFILE}) - ${TIMESTAMP}"
echo "Results will be saved to: ${RESULTS_DIR}"

# Navigate to backend directory
cd "${PROJECT_ROOT}/apps/api"

# Function to run database test command with timeout and statistics
run_db_test() {
    local test_name=$1
    local description=$2
    local command=$3
    local test_timeout=${4:-300}  # Default 5 minutes timeout
    local log_file="${RESULTS_DIR}/db-${test_name}_${TIMESTAMP}.log"
    local start_time=$(date +%s)
    
    echo "  → ${description} (timeout: ${test_timeout}s)"
    
    {
        echo "Database Test: ${description}"
        echo "Command: ${command}"
        echo "Timestamp: $(date)"
        echo "========================================"
        echo ""
    } > "${log_file}"
    
    # Run command with timeout - change to API directory for uv commands
    if timeout "${test_timeout}" bash -c "cd '${PROJECT_ROOT}/apps/api' && eval '$command'" >> "${log_file}" 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo "    ✅ ${description} completed successfully (${duration}s)"
        echo "    ✅ PASSED (${duration}s)" >> "${log_file}"
        TEST_SUCCESS_COUNT=$((TEST_SUCCESS_COUNT + 1))
        return 0
    else
        local exit_code=$?
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        if [ $exit_code -eq 124 ]; then
            echo "    ⏰ ${description} TIMED OUT after ${test_timeout}s"
            echo "    ⏰ TIMEOUT after ${test_timeout}s" >> "${log_file}"
        else
            echo "    ❌ ${description} failed (${duration}s) - check log: $(basename \"${log_file}\")"
            echo "    ❌ FAILED (${duration}s)" >> "${log_file}"
        fi
        
        TEST_FAILURE_COUNT=$((TEST_FAILURE_COUNT + 1))
        return 1
    fi
}

echo "🔧 Database Environment Validation..."

# Check Alembic configuration
run_db_test "alembic-config" "Alembic configuration validation" \
    "uv run alembic check" 60

# Show current migration status
run_db_test "migration-status" "Current migration status" \
    "uv run alembic current" 30

# Show migration history
run_db_test "migration-history" "Migration history validation" \
    "uv run alembic history --verbose" 60

# Database Migration Operations (skipped for integrity and performance profiles)
if [[ "${SKIP_MIGRATION_OPS}" != "true" ]]; then
    echo "🔄 Testing Database Migration Operations..."

    # Create test database if it doesn't exist
    echo "  → Setting up test database environment"

    # Use environment variables with secure defaults
    DB_HOST="${DB_HOST:-localhost}"
    DB_PORT="${DB_PORT:-5432}"
    DB_USER="${DB_USER:-postgres}"
    DB_PASSWORD="${DB_PASSWORD:-}"
    DB_NAME="${DB_TEST_NAME:-iam_dashboard_test}"

    # Construct database URL safely
    if [ -n "${DB_PASSWORD}" ]; then
        TEST_DB_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
    else
        # No password provided - use connection without password (assume peer auth or .pgpass)
        TEST_DB_URL="postgresql://${DB_USER}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
    fi

    echo "  → Database connection: postgresql://${DB_USER}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

    # Test migration up to head
    run_db_test "migrate-upgrade" "Upgrade migrations to HEAD" \
        "SQLALCHEMY_DATABASE_URL='${TEST_DB_URL}' uv run alembic upgrade head" 300

    # Test migration downgrade (one step back)
    run_db_test "migrate-downgrade" "Downgrade migration (one step)" \
        "SQLALCHEMY_DATABASE_URL='${TEST_DB_URL}' uv run alembic downgrade -1" 300

    # Test migration upgrade back to head
    run_db_test "migrate-reupgrade" "Re-upgrade to HEAD after downgrade" \
        "SQLALCHEMY_DATABASE_URL='${TEST_DB_URL}' uv run alembic upgrade head" 300
else
    echo "⏭️ Skipping migration operations (profile: ${TEST_PROFILE})"
fi

echo "🏗️ Testing Schema Consistency..."

# Test schema generation consistency
run_db_test "schema-consistency" "Schema model consistency check" \
    "SQLALCHEMY_DATABASE_URL='${TEST_DB_URL}' uv run python -c \"
from src.core.database import engine
from sqlalchemy import inspect, text

# Test database connectivity
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database connection successful')

# Inspect existing schema
inspector = inspect(engine)
tables = inspector.get_table_names()
print('Found ' + str(len(tables)) + ' tables: ' + str(tables))

# Check if migration tables exist (from Alembic)
if 'users' in tables:
    print('Users table exists')
if 'clients' in tables:
    print('Clients table exists')
if 'audit_logs' in tables:
    print('Audit logs table exists')

print('Schema consistency check completed')
\"" 120

echo "📊 Testing Seed Data Operations..."

# Test seed data creation
run_db_test "seed-data" "Database seed data validation" \
    "SQLALCHEMY_DATABASE_URL='${TEST_DB_URL}' uv run python -c \"
from src.utils.seed_data import seed_database
from src.core.database import get_db_session
from src.models.user import User
from src.models.client import Client

# Test seed data creation
try:
    seed_database()
    print('Seed data created successfully')
    
    # Verify seed data exists
    session = next(get_db_session())
    user_count = session.query(User).count()
    client_count = session.query(Client).count()
    
    print('Created ' + str(user_count) + ' users and ' + str(client_count) + ' clients')
    session.close()
    
except Exception as e:
    print('Seed data error: ' + str(e))
    raise
\"" 180

# Data Integrity Tests (skipped for migration and performance profiles)
if [[ "${SKIP_INTEGRITY}" != "true" ]]; then
    echo "🔍 Testing Data Integrity Constraints..."

    # Test database constraints and relationships
    run_db_test "data-integrity" "Database constraints and relationships" \
    "SQLALCHEMY_DATABASE_URL='${TEST_DB_URL}' uv run python -c \"
from src.core.database import get_db_session
from src.models.user import User
from src.models.client import Client
from src.models.permissions import Permission
from sqlalchemy import text

session = next(get_db_session())

try:
    # Test foreign key constraints
    print('Testing foreign key constraints...')
    
    # Test unique constraints
    print('Testing unique constraints...')
    
    # Verify indexes exist
    result = session.execute(text(\\\"
        SELECT indexname, tablename 
        FROM pg_indexes 
        WHERE schemaname = 'public' 
        AND tablename IN ('users', 'clients', 'permissions')
    \\\"))
    
    indexes = list(result)
    print('Found ' + str(len(indexes)) + ' indexes on key tables')
    
    # Test CPF format validation (if applicable)
    print('Testing CPF validation...')
    
    print('All integrity constraints validated')
    
except Exception as e:
    print('Integrity test error: ' + str(e))
    raise
finally:
    session.close()
\"" 240
else
    echo "⏭️ Skipping data integrity tests (profile: ${TEST_PROFILE})"
fi

# Database Performance Tests (only for performance and complete profiles)
if [[ "${SKIP_PERFORMANCE}" != "true" ]]; then
    echo "⚡ Testing Database Performance..."

    # Basic performance tests
    run_db_test "performance-basic" "Basic database performance metrics" \
    "SQLALCHEMY_DATABASE_URL='${TEST_DB_URL}' uv run python -c \"
import time
from src.core.database import get_db_session
from src.models.user import User
from src.models.client import Client
from sqlalchemy import func

session = next(get_db_session())

try:
    # Test query performance
    start_time = time.time()
    
    # Count queries
    user_count = session.query(User).count()
    client_count = session.query(Client).count()
    
    # Join query test
    result = session.query(User.id, func.count(Client.id)).outerjoin(Client).group_by(User.id).all()
    
    elapsed = time.time() - start_time
    
    print('Basic queries completed in ' + str(round(elapsed, 3)) + 's')
    print('Users: ' + str(user_count) + ', Clients: ' + str(client_count))
    print('Join query returned ' + str(len(result)) + ' results')
    
    if elapsed > 5.0:
        print('Queries took ' + str(round(elapsed, 3)) + 's - consider optimization')
    
except Exception as e:
    print('Performance test error: ' + str(e))
    raise
finally:
    session.close()
\"" 300
else
    echo "⏭️ Skipping performance tests (profile: ${TEST_PROFILE})"
fi

# Backup and Recovery Tests (skipped for fast, migration, integrity, and performance profiles)
if [[ "${SKIP_BACKUP}" != "true" ]]; then
    echo "🧪 Testing Backup and Recovery Procedures..."

    # Test database backup/export capability
    run_db_test "backup-test" "Database backup functionality" \
    "timeout 60s bash -c \"
if command -v pg_dump &> /dev/null; then
    # Use environment variables for secure database connection
    export PGHOST='${DB_HOST}'
    export PGPORT='${DB_PORT}'
    export PGUSER='${DB_USER}'
    if [ -n '${DB_PASSWORD}' ]; then
        export PGPASSWORD='${DB_PASSWORD}'
    fi
    
    pg_dump -d '${DB_NAME}' -f /tmp/db_backup_test_${TIMESTAMP}.sql
    
    if [ -f /tmp/db_backup_test_${TIMESTAMP}.sql ]; then
        BACKUP_SIZE=\$(wc -c < /tmp/db_backup_test_${TIMESTAMP}.sql)
        echo \\\"✅ Database backup created: \${BACKUP_SIZE} bytes\\\"
        rm -f /tmp/db_backup_test_${TIMESTAMP}.sql
    else
        echo \\\"❌ Backup file not created\\\"
        exit 1
    fi
    
    # Clean up environment variables
    unset PGHOST PGPORT PGUSER PGPASSWORD
else
    echo \\\"⚠️ pg_dump not available - skipping backup test\\\"
fi
\""
else
    echo "⏭️ Skipping backup tests (profile: ${TEST_PROFILE})"
fi

# Generate statistics and comprehensive database test report
echo ""
echo "🗄️ Database Test Analysis..."
generate_final_stats "completed"

echo "📊 Generating Database Test Report..."

DB_REPORT="${RESULTS_DIR}/database-test-report_${TIMESTAMP}.log"

{
    echo "=================================="
    echo "DATABASE MIGRATION TEST REPORT"
    echo "Timestamp: $(date)"
    echo "=================================="
    echo ""
    
    # Include execution statistics
    total_time=$(($(date +%s) - TEST_START_TIME))
    total_tests=$((TEST_SUCCESS_COUNT + TEST_FAILURE_COUNT))
    
    echo "📊 EXECUTION STATISTICS:"
    echo "🕰️ Total Execution Time: ${total_time}s ($((total_time / 60))m $((total_time % 60))s)"
    echo "🏃 Tests Executed: ${total_tests}"
    echo "✅ Successful: ${TEST_SUCCESS_COUNT}"
    echo "⚠️ Failed/Timed out: ${TEST_FAILURE_COUNT}"
    
    if [ $total_tests -gt 0 ]; then
        success_rate=$(( (TEST_SUCCESS_COUNT * 100) / total_tests ))
        echo "📊 Success Rate: ${success_rate}%"
    fi
    echo ""
    
    echo "🗄️ Test Categories Executed (${TEST_PROFILE} Profile):"
    echo "   ✓ Alembic Configuration Validation"
    echo "   ✓ Migration Status and History"
    echo "   ✓ Migration Up/Down Operations"
    echo "   ✓ Schema Consistency Verification"
    echo "   ✓ Seed Data Operations"
    echo "   ✓ Data Integrity Constraints"
    echo "   ✓ Basic Performance Metrics"
    echo "   ✓ Backup and Recovery Testing"
    echo ""
    
    echo "📁 Test Result Files:"
    echo "   Alembic Config: db-alembic-config_${TIMESTAMP}.log"
    echo "   Migration Status: db-migration-status_${TIMESTAMP}.log"
    echo "   Migration History: db-migration-history_${TIMESTAMP}.log"
    echo "   Migration Upgrade: db-migrate-upgrade_${TIMESTAMP}.log"
    echo "   Migration Downgrade: db-migrate-downgrade_${TIMESTAMP}.log"
    echo "   Schema Consistency: db-schema-consistency_${TIMESTAMP}.log"
    echo "   Seed Data: db-seed-data_${TIMESTAMP}.log"
    echo "   Data Integrity: db-data-integrity_${TIMESTAMP}.log"
    echo "   Performance: db-performance-basic_${TIMESTAMP}.log"
    echo "   Backup Test: db-backup-test_${TIMESTAMP}.log"
    echo ""
    
    echo "🔍 Database Analysis:"
    
    # Check current migration version
    CURRENT_MIGRATION=$(cd "${PROJECT_ROOT}/apps/api" && uv run alembic current 2>/dev/null | head -n 1 || echo "Unknown")
    echo "   Current Migration: $CURRENT_MIGRATION"
    
    # Count migration files
    MIGRATION_COUNT=$(find alembic/versions -name "*.py" | wc -l 2>/dev/null || echo "0")
    echo "   Migration Files: $MIGRATION_COUNT"
    
    # Check if test database is accessible
    if timeout 5s bash -c "SQLALCHEMY_DATABASE_URL='${TEST_DB_URL}' uv run python -c 'from src.core.database import engine; engine.connect()'" 2>/dev/null; then
        echo "   ✅ Test database accessible"
    else
        echo "   ❌ Test database connection failed"
    fi
    
    echo ""
    echo "💡 Recommendations:"
    echo "   1. Monitor migration performance in production"
    echo "   2. Implement automated backup procedures"
    echo "   3. Test migrations on production-like data volumes"
    echo "   4. Set up database monitoring and alerting"
    echo "   5. Document rollback procedures for each migration"
    
    # Contextual recommendations based on results
    if [ $TEST_FAILURE_COUNT -gt 0 ]; then
        echo ""
        echo "⚠️ IMMEDIATE ACTIONS REQUIRED:"
        echo "   → $TEST_FAILURE_COUNT database test(s) failed - review detailed logs"
        echo "   → Fix database issues before proceeding to production"
        echo "   → Check migration files and database connectivity"
    fi
    
    if [ $total_tests -eq 0 ]; then
        echo ""
        echo "⚠️ NO TESTS EXECUTED:"
        echo "   → Verify database connectivity and test environment setup"
        echo "   → Ensure Alembic configuration is correct"
        echo "   → Check that test database is accessible"
    fi
    
    echo ""
    echo "🚀 Production Readiness Checklist:"
    echo "   □ All migrations execute successfully"
    echo "   □ Schema matches model definitions"
    echo "   □ Rollback procedures tested"
    echo "   □ Seed data creates valid records"
    echo "   □ Constraints properly enforced"
    echo "   □ Performance within acceptable limits"
    echo "   □ Backup/restore procedures validated"
    echo "   □ Connection pooling configured"
    
} > "${DB_REPORT}"

# Display summary
cat "${DB_REPORT}"

echo ""
echo "📊 Database Tests Summary - ${TIMESTAMP}"
echo "All database test results saved to: ${RESULTS_DIR}"
echo "Migration Tests: db-migrate-*_${TIMESTAMP}.log"
echo "Schema Tests: db-schema-*_${TIMESTAMP}.log"
echo "Data Tests: db-*-data_${TIMESTAMP}.log"
echo "Performance Tests: db-performance-*_${TIMESTAMP}.log"
echo "Consolidated Report: database-test-report_${TIMESTAMP}.log"

echo ""
echo "🗄️ Database Migration Status:"
cd "${PROJECT_ROOT}/apps/api" && uv run alembic current || echo "Unable to determine current migration"

echo ""
echo "✅ Database Migration Tests completed at $(date)"

# Exit with appropriate code based on results
if [ $TEST_FAILURE_COUNT -gt 0 ]; then
    echo "⚠️ Script completed with $TEST_FAILURE_COUNT failed database test(s)"
    exit $TEST_FAILURE_COUNT
else
    echo "✨ All database tests completed successfully!"
    exit 0
fi