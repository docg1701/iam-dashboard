#!/bin/bash

# Frontend Tests Runner
# Generated: $(date)
# Purpose: Run frontend unit and integration tests with coverage

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
    echo "  complete  - Run all tests without bail (default)"
    echo "  fast      - Stop at first failure for quick feedback"
    echo "  coverage  - Generate detailed coverage reports"
    echo "  debug     - Run with hanging-process detection"
    echo "  single    - Single fork mode for debugging"
    echo ""
    echo "Examples:"
    echo "  $0                    # Complete execution"
    echo "  $0 fast              # Fast development feedback"
    echo "  $0 coverage          # With coverage reports"
    echo "  $0 debug             # Debug hanging tests"
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

# Use test timeout configuration for test execution - shortened to prevent hanging
TEST_TIMEOUT="${TEST_TIMEOUT:-30}"

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
    cleanup_coverage
    generate_final_stats "interrupted"
    exit 130
}

# Set trap for graceful interruption handling
trap handle_interrupt SIGINT SIGTERM

# Cleanup function for partial coverage consolidation
cleanup_coverage() {
    local exit_code=$?
    echo "🧹 Attempting coverage cleanup..."
    cd "${PROJECT_ROOT}/apps/web" 2>/dev/null || true
    if [ -d "coverage/.tmp" ] && [ ! -f "coverage/index.html" ]; then
        echo "   → Consolidating partial coverage data..."
        timeout 30 node ../../scripts/clean-test-summary.js 2>/dev/null || {
            echo "   ⚠️ Coverage cleanup timed out or failed"
        }
    fi
    return $exit_code
}

# Set trap for cleanup on exit (including timeout)
trap cleanup_coverage EXIT

# Profile selection logic
case "$TEST_PROFILE" in
    fast)
        TEST_COMMAND="test:fast"
        PROFILE_DESCRIPTION="Fast Mode (bail on first failure)"
        ;;
    coverage)
        TEST_COMMAND="test:coverage"
        PROFILE_DESCRIPTION="Coverage Mode (detailed reports)"
        ;;
    debug)
        TEST_COMMAND="test:debug"
        PROFILE_DESCRIPTION="Debug Mode (hanging detection)"
        ;;
    single)
        TEST_COMMAND="test:single"
        PROFILE_DESCRIPTION="Single Fork Mode (debugging)"
        ;;
    complete|*)
        TEST_COMMAND="test:run"
        PROFILE_DESCRIPTION="Complete Mode (all tests)"
        ;;
esac

# Create results directory
mkdir -p "${RESULTS_DIR}"

echo "🧪 Starting Frontend Tests - ${TIMESTAMP}"
echo "📋 Profile: ${PROFILE_DESCRIPTION}"
echo "Results will be saved to: ${RESULTS_DIR}"

# Function to run test with timeout and capture exit status
run_test() {
    local test_name=$1
    local command=$2
    local log_file=$3
    local test_timeout=${4:-600}  # Default 10 minutes timeout
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

# Navigate to frontend directory
cd "${PROJECT_ROOT}/apps/web"

echo "📱 Running Frontend Unit Tests..."

run_test "Frontend Unit Tests - ${PROFILE_DESCRIPTION}" \
    "npm run ${TEST_COMMAND}" \
    "${RESULTS_DIR}/frontend-unit-tests_${TIMESTAMP}.log" \
    900  # 15 minutes timeout for unit tests

echo "📱 Running Frontend Integration Tests..."

run_test "Frontend Integration Tests" \
    "npm run test -- --run --reporter=default '**/*.integration.test.*'" \
    "${RESULTS_DIR}/frontend-integration-tests_${TIMESTAMP}.log" \
    600  # 10 minutes timeout for integration tests

echo "📱 Running Frontend Responsive Tests..."

run_test "Frontend Responsive Tests" \
    "npm run test -- --run --reporter=default '**/*.responsive.test.*'" \
    "${RESULTS_DIR}/frontend-responsive-tests_${TIMESTAMP}.log" \
    300  # 5 minutes timeout for responsive tests

echo ""
echo "📱 Frontend Test Analysis..."
generate_final_stats "completed"

# Generate frontend test report
FRONTEND_REPORT="${RESULTS_DIR}/frontend-test-report_${TIMESTAMP}.log"

{
    total_time=$(($(date +%s) - TEST_START_TIME))
    total_tests=$((TEST_SUCCESS_COUNT + TEST_FAILURE_COUNT))
    
    echo "=================================="
    echo "FRONTEND TEST EXECUTION REPORT"
    echo "Timestamp: $(date)"
    echo "=================================="
    echo ""
    
    echo "📊 Execution Summary:"
    echo "   🕰️ Total Time: ${total_time}s ($((total_time / 60))m $((total_time % 60))s)"
    echo "   🏃 Test Categories Run: ${total_tests}"
    echo "   ✅ Successful: ${TEST_SUCCESS_COUNT}"
    echo "   ⚠️ Failed/Timed out: ${TEST_FAILURE_COUNT}"
    if [ $total_tests -gt 0 ]; then
        success_rate=$(( (TEST_SUCCESS_COUNT * 100) / total_tests ))
        echo "   📊 Success Rate: ${success_rate}%"
    fi
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
    if [ $TEST_FAILURE_COUNT -gt 0 ]; then
        echo "   🔥 PRIORITY: Fix failing tests - check logs for specific issues"
        echo "   1. Review timeout errors first (look for TIMEOUT messages)"
        echo "   2. Check test setup and mocking issues"
        echo "   3. Verify component rendering and DOM queries"
        echo "   4. Consider increasing timeouts for slow tests"
    else
        echo "   1. Review test coverage reports for gaps"
        echo "   2. Add more integration tests for complex components"
        echo "   3. Ensure responsive tests cover all breakpoints"
        echo "   4. Consider adding visual regression tests"
    fi
    
    echo ""
    echo "🚀 Test Quality Status:"
    if [ $TEST_FAILURE_COUNT -eq 0 ]; then
        echo "   ✅ All test categories completed successfully"
        echo "   ✅ No timeouts detected"
        echo "   ✅ Script executed without interruption"
    else
        echo "   ❌ ${TEST_FAILURE_COUNT} test categories failed or timed out"
        echo "   ⚠️ Check individual log files for specific errors"
        echo "   ⚠️ Some tests may need timeout adjustments or fixes"
    fi
    
} > "${FRONTEND_REPORT}"

# Display report
cat "${FRONTEND_REPORT}"

# Final Summary
echo ""
echo "📊 Frontend Tests Summary - ${TIMESTAMP}"
echo "All test results saved to: ${RESULTS_DIR}"
echo "Unit Tests: frontend-unit-tests_${TIMESTAMP}.log"
echo "Integration Tests: frontend-integration-tests_${TIMESTAMP}.log" 
echo "Responsive Tests: frontend-responsive-tests_${TIMESTAMP}.log"
echo "Test Report: frontend-test-report_${TIMESTAMP}.log"
echo "HTML Coverage: ${PROJECT_ROOT}/apps/web/coverage/index.html"

echo ""
if [ $TEST_FAILURE_COUNT -eq 0 ]; then
    echo "🎉 All frontend tests completed successfully at $(date)"
    echo "✨ No failures or timeouts detected - script execution was perfect!"
else
    echo "⚠️ Frontend tests completed with ${TEST_FAILURE_COUNT} issues at $(date)"
    echo "📋 Check the test report and individual logs for detailed error analysis"
    echo "💡 Script executed completely - no hanging or premature termination"
fi

# Exit with appropriate code
exit $TEST_FAILURE_COUNT