#!/bin/bash

# Backend Tests Runner  
# Generated: $(date)
# Purpose: Run backend unit, integration, and E2E tests with coverage

# Don't exit on error - we want to capture all test results even if some fail
# set -e  # REMOVED to continue execution on test failures

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/test-results"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Use test timeout configuration for test execution
TEST_TIMEOUT="${TEST_TIMEOUT:-600}"

# Create results directory
mkdir -p "${RESULTS_DIR}"

echo "🔧 Starting Backend Tests - ${TIMESTAMP}"
echo "Results will be saved to: ${RESULTS_DIR}"

# Function to run test and capture exit status
run_test() {
    local test_name=$1
    local command=$2
    local log_file=$3
    
    echo "  → $test_name"
    if eval "$command" > "$log_file" 2>&1; then
        echo "    ✅ $test_name completed successfully"
        return 0
    else
        echo "    ⚠️ $test_name completed with issues (check log: $(basename "$log_file"))"
        return 1
    fi
}

# Navigate to backend directory
cd "${PROJECT_ROOT}/apps/backend"

echo "🔧 Running Backend Unit Tests..."

run_test "Backend Unit Tests" \
    "timeout ${TEST_TIMEOUT}s uv run pytest src/tests/unit/ --tb=short -v --no-cov" \
    "${RESULTS_DIR}/backend-unit-tests_${TIMESTAMP}.log"

echo "🔧 Running Backend Integration Tests..."

run_test "Backend Integration Tests" \
    "timeout ${TEST_TIMEOUT}s uv run pytest src/tests/integration/ --tb=short -v --no-cov" \
    "${RESULTS_DIR}/backend-integration-tests_${TIMESTAMP}.log"

echo "🔧 Running Backend E2E Tests..."

run_test "Backend E2E Tests" \
    "timeout ${TEST_TIMEOUT}s uv run pytest src/tests/e2e/ --tb=short -v --no-cov" \
    "${RESULTS_DIR}/backend-e2e-tests_${TIMESTAMP}.log"

echo "📊 Generating Backend Coverage Report..."

run_test "Backend Coverage Report" \
    "timeout ${TEST_TIMEOUT}s uv run pytest --cov=src --cov-report=term --cov-report=html --tb=short" \
    "${RESULTS_DIR}/backend-coverage-report_${TIMESTAMP}.log"

echo "🔧 Backend Test Analysis..."

# Generate backend test report
BACKEND_REPORT="${RESULTS_DIR}/backend-test-report_${TIMESTAMP}.log"

{
    echo "=================================="
    echo "BACKEND TEST EXECUTION REPORT"
    echo "Timestamp: $(date)"
    echo "=================================="
    echo ""
    
    echo "🔧 Test Categories Executed:"
    echo "   ✓ Unit Tests (Business Logic)"
    echo "   ✓ Integration Tests (API Endpoints)"  
    echo "   ✓ End-to-End Tests (Full Workflows)"
    echo "   ✓ Coverage Analysis"
    echo ""
    
    echo "📁 Test Result Files:"
    echo "   Unit Tests: backend-unit-tests_${TIMESTAMP}.log"
    echo "   Integration Tests: backend-integration-tests_${TIMESTAMP}.log"
    echo "   E2E Tests: backend-e2e-tests_${TIMESTAMP}.log"
    echo "   Coverage Report: backend-coverage-report_${TIMESTAMP}.log"
    echo ""
    
    echo "🔍 Backend Analysis:"
    
    # Check test files count
    UNIT_TESTS=$(find src/tests/unit -name "*.py" 2>/dev/null | wc -l)
    INTEGRATION_TESTS=$(find src/tests/integration -name "*.py" 2>/dev/null | wc -l)
    E2E_TESTS=$(find src/tests/e2e -name "*.py" 2>/dev/null | wc -l)
    SECURITY_TESTS=$(find src/tests/security -name "*.py" 2>/dev/null | wc -l)
    
    echo "   Unit Test Files: $UNIT_TESTS"
    echo "   Integration Test Files: $INTEGRATION_TESTS"
    echo "   E2E Test Files: $E2E_TESTS"
    echo "   Security Test Files: $SECURITY_TESTS"
    
    # Check coverage directory
    if [ -d "htmlcov" ]; then
        echo "   ✅ HTML Coverage reports generated"
        echo "   📊 Coverage Report: ./htmlcov/index.html"
    else
        echo "   ⚠️ HTML Coverage reports not found"
    fi
    
    # Check for key test areas
    if [ -f "src/tests/unit/test_permission_service.py" ]; then
        echo "   ✅ Permission service tests found"
    else
        echo "   ⚠️ Permission service tests missing"
    fi
    
    if [ -f "src/tests/unit/test_auth_unit.py" ]; then
        echo "   ✅ Authentication tests found"
    else
        echo "   ⚠️ Authentication tests missing"
    fi
    
    echo ""
    echo "💡 Recommendations:"
    echo "   1. Maintain >80% coverage for core business logic"
    echo "   2. Add more integration tests for API endpoints"
    echo "   3. Ensure E2E tests cover critical user workflows"
    echo "   4. Regular security test execution"
    echo "   5. Mock external dependencies, not internal logic"
    
    echo ""
    echo "🚀 Backend Quality Checklist:"
    echo "   □ Unit tests cover all service classes"
    echo "   □ Integration tests validate API contracts" 
    echo "   □ E2E tests verify business workflows"
    echo "   □ Security tests prevent vulnerabilities"
    echo "   □ Coverage reports identify gaps"
    echo "   □ Tests follow mocking best practices"
    
} > "${BACKEND_REPORT}"

# Display report
cat "${BACKEND_REPORT}"

# Summary
echo ""
echo "📊 Backend Tests Summary - ${TIMESTAMP}"
echo "All test results saved to: ${RESULTS_DIR}"
echo "Unit Tests: backend-unit-tests_${TIMESTAMP}.log"
echo "Integration Tests: backend-integration-tests_${TIMESTAMP}.log"
echo "E2E Tests: backend-e2e-tests_${TIMESTAMP}.log"
echo "Coverage Report: backend-coverage-report_${TIMESTAMP}.log"
echo "Test Analysis: backend-test-report_${TIMESTAMP}.log"
echo "HTML Coverage: ${PROJECT_ROOT}/apps/backend/htmlcov/index.html"

echo ""
echo "✅ Backend Tests completed at $(date)"