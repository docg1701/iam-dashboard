#!/bin/bash

# Security and Performance Tests Runner
# Generated: $(date)
# Purpose: Run all security and performance tests

# Don't exit on error - we want to capture all security test results even if some fail
# set -e  # REMOVED to continue execution on test failures

# Test profile parameter (default: complete)
TEST_PROFILE="${1:-complete}"

# Usage message
usage() {
    echo "Usage: $0 [profile]"
    echo ""
    echo "Security Test Profiles:"
    echo "  complete  - Run all security and performance tests (default)"
    echo "  fast      - Run security tests only"
    echo "  audit     - Run dependency audits only"
    echo "  performance - Run performance tests only"
    echo ""
    echo "Examples:"
    echo "  $0                    # Complete security suite"
    echo "  $0 fast              # Quick security tests only"
    echo "  $0 audit             # Dependency audits only"
    echo "  $0 performance       # Performance tests only"
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

# Use test timeout configuration for security and performance tests
TEST_TIMEOUT="${TEST_TIMEOUT:-600}"

# Profile selection logic
case "$TEST_PROFILE" in
    fast)
        PROFILE_DESCRIPTION="Fast Mode (security tests only)"
        ;;
    audit)
        PROFILE_DESCRIPTION="Audit Mode (dependency audits only)"
        ;;
    performance)
        PROFILE_DESCRIPTION="Performance Mode (performance tests only)"
        ;;
    complete|*)
        PROFILE_DESCRIPTION="Complete Mode (security + performance + audits)"
        ;;
esac

# Create results directory
mkdir -p "${RESULTS_DIR}"

echo "🔒 Starting Security and Performance Tests - ${TIMESTAMP}"
echo "📋 Profile: ${PROFILE_DESCRIPTION}"
echo "Results will be saved to: ${RESULTS_DIR}"

# Profile-based execution
case "$TEST_PROFILE" in
    fast)
        echo "🛡️ Running Security Tests (Fast Mode)..."
        cd "${PROJECT_ROOT}/apps/api"
        
        echo "  → Security Vulnerability Tests"
        if timeout ${TEST_TIMEOUT}s uv run pytest tests/security/ --tb=short -q --no-cov --maxfail=1 > "${RESULTS_DIR}/security-tests_${TIMESTAMP}.log" 2>&1; then
            echo "    ✅ Security tests completed successfully"
        else
            echo "    ⚠️ Security tests completed with failures (check log: security-tests_${TIMESTAMP}.log)"
        fi
        ;;
    performance)
        echo "⚡ Running Performance Tests..."
        cd "${PROJECT_ROOT}/apps/api"
        
        echo "  → Performance/Load Tests"
        if timeout ${TEST_TIMEOUT}s uv run pytest tests/performance/ --tb=short -v --no-cov > "${RESULTS_DIR}/performance-tests_${TIMESTAMP}.log" 2>&1; then
            echo "    ✅ Performance tests completed successfully"
        else
            echo "    ⚠️ Performance tests completed with failures (check log: performance-tests_${TIMESTAMP}.log)"
        fi
        ;;
    audit)
        # Skip to audit section only
        ;;
    complete|*)
        echo "🛡️ Running Security Tests..."
        cd "${PROJECT_ROOT}/apps/api"
        
        echo "  → Security Vulnerability Tests"
        if timeout ${TEST_TIMEOUT}s uv run pytest tests/security/ --tb=short -q --no-cov > "${RESULTS_DIR}/security-tests_${TIMESTAMP}.log" 2>&1; then
            echo "    ✅ Security tests completed successfully"
        else
            echo "    ⚠️ Security tests completed with failures (check log: security-tests_${TIMESTAMP}.log)"
        fi

        echo "⚡ Running Performance Tests..."
        echo "  → Performance/Load Tests"
        if timeout ${TEST_TIMEOUT}s uv run pytest tests/performance/ --tb=short -q --no-cov > "${RESULTS_DIR}/performance-tests_${TIMESTAMP}.log" 2>&1; then
            echo "    ✅ Performance tests completed successfully"
        else
            echo "    ⚠️ Performance tests completed with failures (check log: performance-tests_${TIMESTAMP}.log)"
        fi
        ;;
esac

# Function to run security audit with real status reporting
run_security_audit() {
    local audit_name="$1"
    local description="$2" 
    local command="$3"
    local log_file="$4"
    
    echo "  → ${description}"
    
    if eval "$command" > "$log_file" 2>&1; then
        echo "    ✅ ${description} completed successfully"
        return 0
    else
        echo "    ⚠️ ${description} found issues (check: $(basename "$log_file"))"
        return 1
    fi
}

# Dependency Security Audits (run for audit profile or complete profile)
if [[ "$TEST_PROFILE" == "audit" || "$TEST_PROFILE" == "complete" ]]; then
    echo "🔍 Running Security Audits..."
    cd "${PROJECT_ROOT}"

    run_security_audit "frontend-audit" "Frontend Dependency Security Audit" \
        "npm audit" \
        "${RESULTS_DIR}/frontend-security-audit_${TIMESTAMP}.log"

    echo "  → Backend Dependency Security Audit"
    cd "${PROJECT_ROOT}/apps/api"
    if uv run pip-audit --version &> /dev/null; then
        run_security_audit "backend-audit" "Backend Dependency Security Audit" \
            "uv run pip-audit" \
            "${RESULTS_DIR}/backend-security-audit_${TIMESTAMP}.log"
    else
        echo "    ⚠️ pip-audit not available - skipping backend dependency audit"
        echo "pip-audit not available in uv environment" > "${RESULTS_DIR}/backend-security-audit_${TIMESTAMP}.log"
    fi
fi

# Summary
echo "📊 Security and Performance Tests Summary - ${TIMESTAMP}"
echo "Profile: ${PROFILE_DESCRIPTION}"
echo "All test results saved to: ${RESULTS_DIR}"

case "$TEST_PROFILE" in
    fast)
        echo "Security Tests: security-tests_${TIMESTAMP}.log"
        ;;
    performance)
        echo "Performance Tests: performance-tests_${TIMESTAMP}.log"
        ;;
    audit)
        echo "Frontend Security Audit: frontend-security-audit_${TIMESTAMP}.log"
        echo "Backend Security Audit: backend-security-audit_${TIMESTAMP}.log"
        ;;
    complete|*)
        echo "Security Tests: security-tests_${TIMESTAMP}.log"
        echo "Performance Tests: performance-tests_${TIMESTAMP}.log"
        echo "Frontend Security Audit: frontend-security-audit_${TIMESTAMP}.log"
        echo "Backend Security Audit: backend-security-audit_${TIMESTAMP}.log"
        ;;
esac

echo "✅ Security and Performance Tests completed at $(date)"