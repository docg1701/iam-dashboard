#!/bin/bash

# Backend Tests Runner  
# Generated: $(date)
# Purpose: Run backend unit, integration, and E2E tests with coverage

# Don't exit on error - we want to capture all test results even if some fail
# set -e  # REMOVED to continue execution on test failures
set +e  # Explicitly disable exit on error

# Test profile parameter (default: complete)
TEST_PROFILE="${1:-complete}"

# Usage message
usage() {
    echo "Usage: $0 [profile]"
    echo ""
    echo "Test Profiles:"
    echo "  complete  - Run all tests with coverage (default)"
    echo "  fast      - Run unit tests only for quick feedback"
    echo "  coverage  - Run all tests with detailed coverage analysis"
    echo "  unit      - Run unit tests only"
    echo "  integration - Run integration tests only"
    echo ""
    echo "Examples:"
    echo "  $0                    # Complete execution"
    echo "  $0 fast              # Quick unit tests only"
    echo "  $0 coverage          # Detailed coverage analysis"
    echo "  $0 unit              # Unit tests only"
    echo ""
}

# Check for help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    usage
    exit 0
fi

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/test-results"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Use test timeout configuration for test execution
TEST_TIMEOUT="${TEST_TIMEOUT:-600}"

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
        echo "⚠️ Some tests failed - check individual log files for details"
    else
        echo "✨ All test categories completed successfully!"
    fi
    echo "======================================"
}

# Function to handle script interruption gracefully
handle_interrupt() {
    echo ""
    echo "⚠️ Script interrupted! Cleaning up..."
    cleanup_backend
    generate_final_stats "interrupted"
    exit 130
}

# Set trap for graceful interruption handling
trap handle_interrupt SIGINT SIGTERM

# Cleanup function for backend test artifacts
cleanup_backend() {
    local exit_code=$?
    echo "🧹 Backend cleanup on exit..."
    # Backend cleanup is typically handled by pytest itself
    # But we ensure any hanging processes are terminated
    cd "${PROJECT_ROOT}/apps/api" 2>/dev/null || true
    return $exit_code
}

# Set trap for cleanup on exit (including timeout)
trap cleanup_backend EXIT

# Profile selection logic
case "$TEST_PROFILE" in
    fast)
        PROFILE_DESCRIPTION="Fast Mode (unit tests only)"
        ;;
    coverage)
        PROFILE_DESCRIPTION="Coverage Mode (detailed analysis)"
        ;;
    unit)
        PROFILE_DESCRIPTION="Unit Tests Mode"
        ;;
    integration)
        PROFILE_DESCRIPTION="Integration Tests Mode"
        ;;
    complete|*)
        PROFILE_DESCRIPTION="Complete Mode (all tests with coverage)"
        ;;
esac

# Create results directory
mkdir -p "${RESULTS_DIR}"

echo "🔧 Starting Backend Tests - ${TIMESTAMP}"
echo "📋 Profile: ${PROFILE_DESCRIPTION}"
echo "Results will be saved to: ${RESULTS_DIR}"

# Function to run test with timeout and capture exit status
run_test() {
    local test_name=$1
    local command=$2
    local log_file=$3
    local test_timeout=${4:-$TEST_TIMEOUT}  # Use profile timeout or default
    local start_time=$(date +%s)
    
    echo "  → $test_name (timeout: ${test_timeout}s)"
    
    # Run command with timeout
    if timeout "${test_timeout}" bash -c "eval '$command'" > "$log_file" 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo "    ✅ $test_name completed successfully (${duration}s)"
        TEST_SUCCESS_COUNT=$((TEST_SUCCESS_COUNT + 1))
        return 0
    else
        local exit_code=$?
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        if [ $exit_code -eq 124 ]; then
            echo "    ⏰ $test_name TIMED OUT after ${test_timeout}s"
            echo "TIMEOUT: Test exceeded ${test_timeout} second limit" >> "$log_file"
        else
            echo "    ⚠️ $test_name completed with issues (${duration}s) - check log: $(basename "$log_file")"
        fi
        
        TEST_FAILURE_COUNT=$((TEST_FAILURE_COUNT + 1))
        return 1
    fi
}

# Navigate to backend directory
cd "${PROJECT_ROOT}/apps/api"

# Profile-based execution
case "$TEST_PROFILE" in
    fast)
        echo "🔧 Running Backend Unit Tests (Fast Mode)..."
        run_test "Backend Unit Tests" \
            "uv run pytest tests/unit/ --tb=short -q --no-cov --maxfail=1" \
            "${RESULTS_DIR}/backend-unit-tests_${TIMESTAMP}.log" \
            300  # 5 minutes for fast unit tests
        ;;
    unit)
        echo "🔧 Running Backend Unit Tests..."
        run_test "Backend Unit Tests" \
            "uv run pytest tests/unit/ --tb=short -v --no-cov" \
            "${RESULTS_DIR}/backend-unit-tests_${TIMESTAMP}.log" \
            600  # 10 minutes for unit tests
        ;;
    integration)
        echo "🔧 Running Backend Integration Tests..."
        run_test "Backend Integration Tests" \
            "uv run pytest tests/integration/ --tb=short -v --no-cov" \
            "${RESULTS_DIR}/backend-integration-tests_${TIMESTAMP}.log" \
            900  # 15 minutes for integration tests
        ;;
    coverage)
        echo "🔧 Running Backend Tests with Detailed Coverage..."
        run_test "Backend Unit Tests" \
            "uv run pytest tests/unit/ --tb=short -v --no-cov" \
            "${RESULTS_DIR}/backend-unit-tests_${TIMESTAMP}.log" \
            600  # 10 minutes for unit tests
        
        run_test "Backend Integration Tests" \
            "uv run pytest tests/integration/ --tb=short -v --no-cov" \
            "${RESULTS_DIR}/backend-integration-tests_${TIMESTAMP}.log" \
            900  # 15 minutes for integration tests
        
        run_test "Backend E2E Tests" \
            "uv run pytest tests/e2e/ --tb=short -v --no-cov" \
            "${RESULTS_DIR}/backend-e2e-tests_${TIMESTAMP}.log" \
            1200  # 20 minutes for E2E tests

        echo "📊 Generating Detailed Coverage Report..."
        run_test "Backend Coverage Report" \
            "uv run pytest --cov=src --cov-report=term --cov-report=html --cov-report=xml --tb=short" \
            "${RESULTS_DIR}/backend-coverage-report_${TIMESTAMP}.log" \
            1800  # 30 minutes for coverage analysis
        ;;
    complete|*)
        echo "🔧 Running Backend Unit Tests..."
        run_test "Backend Unit Tests" \
            "uv run pytest tests/unit/ --tb=short -v --no-cov" \
            "${RESULTS_DIR}/backend-unit-tests_${TIMESTAMP}.log" \
            600  # 10 minutes for unit tests

        echo "🔧 Running Backend Integration Tests..."
        run_test "Backend Integration Tests" \
            "uv run pytest tests/integration/ --tb=short -v --no-cov" \
            "${RESULTS_DIR}/backend-integration-tests_${TIMESTAMP}.log" \
            900  # 15 minutes for integration tests

        echo "🔧 Running Backend E2E Tests..."
        run_test "Backend E2E Tests" \
            "uv run pytest tests/e2e/ --tb=short -v --no-cov" \
            "${RESULTS_DIR}/backend-e2e-tests_${TIMESTAMP}.log" \
            1200  # 20 minutes for E2E tests

        echo "📊 Generating Backend Coverage Report..."
        run_test "Backend Coverage Report" \
            "uv run pytest --cov=src --cov-report=term --cov-report=html --tb=short" \
            "${RESULTS_DIR}/backend-coverage-report_${TIMESTAMP}.log" \
            1800  # 30 minutes for coverage analysis
        ;;
esac

echo ""
echo "🔧 Backend Test Analysis..."
generate_final_stats "completed"

# Generate backend test report
BACKEND_REPORT="${RESULTS_DIR}/backend-test-report_${TIMESTAMP}.log"

{
    echo "=================================="
    echo "BACKEND TEST EXECUTION REPORT"
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
    
    echo "🔧 Test Categories Executed (${PROFILE_DESCRIPTION}):"
    case "$TEST_PROFILE" in
        fast)
            echo "   ✓ Unit Tests (Business Logic) - Fast Mode"
            ;;
        unit)
            echo "   ✓ Unit Tests (Business Logic)"
            ;;
        integration)
            echo "   ✓ Integration Tests (API Endpoints)"
            ;;
        coverage)
            echo "   ✓ Unit Tests (Business Logic)"
            echo "   ✓ Integration Tests (API Endpoints)"  
            echo "   ✓ End-to-End Tests (Full Workflows)"
            echo "   ✓ Detailed Coverage Analysis (HTML + XML)"
            ;;
        complete|*)
            echo "   ✓ Unit Tests (Business Logic)"
            echo "   ✓ Integration Tests (API Endpoints)"  
            echo "   ✓ End-to-End Tests (Full Workflows)"
            echo "   ✓ Coverage Analysis"
            ;;
    esac
    echo ""
    
    echo "📁 Test Result Files:"
    echo "   Unit Tests: backend-unit-tests_${TIMESTAMP}.log"
    echo "   Integration Tests: backend-integration-tests_${TIMESTAMP}.log"
    echo "   E2E Tests: backend-e2e-tests_${TIMESTAMP}.log"
    echo "   Coverage Report: backend-coverage-report_${TIMESTAMP}.log"
    echo ""
    
    echo "🔍 Backend Analysis:"
    
    # Check test files count
    UNIT_TESTS=$(find tests/unit -name "*.py" 2>/dev/null | wc -l)
    INTEGRATION_TESTS=$(find tests/integration -name "*.py" 2>/dev/null | wc -l)
    E2E_TESTS=$(find tests/e2e -name "*.py" 2>/dev/null | wc -l)
    SECURITY_TESTS=$(find tests/security -name "*.py" 2>/dev/null | wc -l)
    
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
    if [ -f "tests/unit/test_permission_service.py" ]; then
        echo "   ✅ Permission service tests found"
    else
        echo "   ⚠️ Permission service tests missing"
    fi
    
    if [ -f "tests/unit/test_auth_unit.py" ]; then
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
    
    # Contextual recommendations based on results
    if [ $TEST_FAILURE_COUNT -gt 0 ]; then
        echo ""
        echo "⚠️ IMMEDIATE ACTIONS REQUIRED:"
        echo "   → $TEST_FAILURE_COUNT test(s) failed - review detailed logs"
        echo "   → Fix failing tests before proceeding to production"
        echo "   → Check log files for specific error details"
    fi
    
    if [ $total_tests -eq 0 ]; then
        echo ""
        echo "⚠️ NO TESTS EXECUTED:"
        echo "   → Verify test directory structure and file naming"
        echo "   → Ensure pytest configuration is correct"
        echo "   → Check that test files are properly discovered"
    fi
    
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
echo "Profile: ${PROFILE_DESCRIPTION}"
echo "All test results saved to: ${RESULTS_DIR}"

case "$TEST_PROFILE" in
    fast)
        echo "Unit Tests (Fast): backend-unit-tests_${TIMESTAMP}.log"
        ;;
    unit)
        echo "Unit Tests: backend-unit-tests_${TIMESTAMP}.log"
        ;;
    integration)
        echo "Integration Tests: backend-integration-tests_${TIMESTAMP}.log"
        ;;
    coverage)
        echo "Unit Tests: backend-unit-tests_${TIMESTAMP}.log"
        echo "Integration Tests: backend-integration-tests_${TIMESTAMP}.log"
        echo "E2E Tests: backend-e2e-tests_${TIMESTAMP}.log"
        echo "Coverage Report: backend-coverage-report_${TIMESTAMP}.log"
        echo "HTML Coverage: ${PROJECT_ROOT}/apps/api/htmlcov/index.html"
        echo "XML Coverage: ${PROJECT_ROOT}/apps/api/coverage.xml"
        ;;
    complete|*)
        echo "Unit Tests: backend-unit-tests_${TIMESTAMP}.log"
        echo "Integration Tests: backend-integration-tests_${TIMESTAMP}.log"
        echo "E2E Tests: backend-e2e-tests_${TIMESTAMP}.log"
        echo "Coverage Report: backend-coverage-report_${TIMESTAMP}.log"
        echo "HTML Coverage: ${PROJECT_ROOT}/apps/api/htmlcov/index.html"
        ;;
esac

echo "Test Analysis: backend-test-report_${TIMESTAMP}.log"

echo ""
echo "✅ Backend Tests completed at $(date)"

# Exit with appropriate code based on results
if [ $TEST_FAILURE_COUNT -gt 0 ]; then
    echo "⚠️ Script completed with $TEST_FAILURE_COUNT failed test(s)"
    exit $TEST_FAILURE_COUNT
else
    echo "✨ All backend tests completed successfully!"
    exit 0
fi