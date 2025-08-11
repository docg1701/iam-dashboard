#!/bin/bash

# Frontend Tests Runner
# Generated: $(date)
# Purpose: Run frontend unit and integration tests with coverage

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

echo "🧪 Starting Frontend Tests - ${TIMESTAMP}"
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

# Navigate to frontend directory
cd "${PROJECT_ROOT}/apps/web"

echo "📱 Running Frontend Unit Tests..."

run_test "Frontend Unit Tests with Coverage" \
    "timeout ${TEST_TIMEOUT}s npx vitest run --coverage --reporter=default" \
    "${RESULTS_DIR}/frontend-unit-tests_${TIMESTAMP}.log"

echo "📱 Running Frontend Integration Tests..."

run_test "Frontend Integration Tests" \
    "timeout ${TEST_TIMEOUT}s npx vitest run --reporter=default '**/*.integration.test.*'" \
    "${RESULTS_DIR}/frontend-integration-tests_${TIMESTAMP}.log"

echo "📱 Running Frontend Responsive Tests..."

run_test "Frontend Responsive Tests" \
    "timeout ${TEST_TIMEOUT}s npx vitest run --reporter=default '**/*.responsive.test.*'" \
    "${RESULTS_DIR}/frontend-responsive-tests_${TIMESTAMP}.log"

echo "📱 Frontend Test Analysis..."

# Generate frontend test report
FRONTEND_REPORT="${RESULTS_DIR}/frontend-test-report_${TIMESTAMP}.log"

{
    echo "=================================="
    echo "FRONTEND TEST EXECUTION REPORT"
    echo "Timestamp: $(date)"
    echo "=================================="
    echo ""
    
    echo "🧪 Test Categories Executed:"
    echo "   ✓ Unit Tests with Coverage"
    echo "   ✓ Integration Tests"
    echo "   ✓ Responsive Design Tests"
    echo ""
    
    echo "📁 Test Result Files:"
    echo "   Unit Tests: frontend-unit-tests_${TIMESTAMP}.log"
    echo "   Integration Tests: frontend-integration-tests_${TIMESTAMP}.log"
    echo "   Responsive Tests: frontend-responsive-tests_${TIMESTAMP}.log"
    echo ""
    
    echo "📊 Frontend Analysis:"
    
    # Check test files count
    TEST_FILES=$(find . -name "*.test.*" -o -name "*.spec.*" | wc -l)
    echo "   Test Files Found: $TEST_FILES"
    
    # Check coverage directory
    if [ -d "coverage" ]; then
        echo "   ✅ Coverage reports generated"
        echo "   📊 Coverage Report: ./coverage/index.html"
    else
        echo "   ⚠️ Coverage reports not found"
    fi
    
    # Check for common test patterns
    UNIT_TESTS=$(find . -name "*.test.*" | grep -v integration | grep -v responsive | wc -l)
    INTEGRATION_TESTS=$(find . -name "*.integration.test.*" | wc -l)
    RESPONSIVE_TESTS=$(find . -name "*.responsive.test.*" | wc -l)
    
    echo "   Unit Test Files: $UNIT_TESTS"
    echo "   Integration Test Files: $INTEGRATION_TESTS"
    echo "   Responsive Test Files: $RESPONSIVE_TESTS"
    
    echo ""
    echo "💡 Recommendations:"
    echo "   1. Review test coverage reports for gaps"
    echo "   2. Add more integration tests for complex components"
    echo "   3. Ensure responsive tests cover all breakpoints"
    echo "   4. Consider adding visual regression tests"
    
    echo ""
    echo "🚀 Test Quality Checklist:"
    echo "   □ Unit tests cover core functionality"
    echo "   □ Integration tests verify component interactions"
    echo "   □ Responsive tests validate mobile experience"
    echo "   □ Coverage meets minimum thresholds"
    echo "   □ Tests run consistently without flakiness"
    
} > "${FRONTEND_REPORT}"

# Display report
cat "${FRONTEND_REPORT}"

# Summary
echo ""
echo "📊 Frontend Tests Summary - ${TIMESTAMP}"
echo "All test results saved to: ${RESULTS_DIR}"
echo "Unit Tests: frontend-unit-tests_${TIMESTAMP}.log"
echo "Integration Tests: frontend-integration-tests_${TIMESTAMP}.log" 
echo "Responsive Tests: frontend-responsive-tests_${TIMESTAMP}.log"
echo "Test Report: frontend-test-report_${TIMESTAMP}.log"
echo "HTML Coverage: ${PROJECT_ROOT}/apps/web/coverage/index.html"

echo ""
echo "✅ Frontend Tests completed at $(date)"