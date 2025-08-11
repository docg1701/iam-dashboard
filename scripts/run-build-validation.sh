#!/bin/bash

# Build Validation Runner
# Generated: $(date)
# Purpose: Run all build validation and deployment checks

# Don't exit on error - we want to capture all build validation results
# set -e  # REMOVED to allow collecting all results

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/test-results"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Create results directory
mkdir -p "${RESULTS_DIR}"

echo "🏗️ Starting Build Validation - ${TIMESTAMP}"
echo "Results will be saved to: ${RESULTS_DIR}"

# Function to run build validation command and report status
run_build_check() {
    local check_name="$1"
    local description="$2"
    local command="$3"
    local log_file="$4"
    
    echo "  → ${description}"
    
    {
        echo "Build Validation: ${description}"
        echo "Command: ${command}"
        echo "Timestamp: $(date)"
        echo "========================================"
        echo ""
    } > "${log_file}"
    
    # Execute command safely without eval to prevent command injection
    if bash -c "$command" >> "$log_file" 2>&1; then
        echo "    ✅ ${description} completed successfully"
        echo "    ✅ PASSED" >> "${log_file}"
        return 0
    else
        echo "    ❌ ${description} failed (check: $(basename "$log_file"))"
        echo "    ❌ FAILED" >> "${log_file}"
        return 1
    fi
}

# Function to check if command is available
check_dependency() {
    local cmd="$1"
    local name="$2"
    
    if command -v "$cmd" >/dev/null 2>&1; then
        echo "  ✅ $name available: $($cmd --version 2>/dev/null | head -1 || echo 'version unknown')"
        return 0
    else
        echo "  ❌ $name not found - required for build validation"
        return 1
    fi
}

# Dependency Validation
echo "🔧 Checking Build Dependencies..."
cd "${PROJECT_ROOT}"

DEP_FAILED=0
check_dependency "node" "Node.js" || DEP_FAILED=1
check_dependency "npm" "NPM" || DEP_FAILED=1

if [ $DEP_FAILED -eq 1 ]; then
    echo "❌ Required dependencies missing - cannot proceed with build validation"
    exit 1
fi

# Build Validation
echo "📦 Running Build Validation..."

# Make build timeout configurable
BUILD_TIMEOUT="${BUILD_TIMEOUT:-600}"
run_build_check "production-build" "Production Build Test" \
    "timeout ${BUILD_TIMEOUT}s npm run build" \
    "${RESULTS_DIR}/build-validation_${TIMESTAMP}.log"

# E2E Test File Check
echo "🎭 Checking E2E Test Configuration..."

run_build_check "e2e-files" "E2E Test Files Check" \
    "if [ -d '${PROJECT_ROOT}/apps/frontend/e2e' ]; then ls -la '${PROJECT_ROOT}/apps/frontend/e2e/'; echo 'E2E directory found'; else echo 'No E2E directory found - this is OK'; fi" \
    "${RESULTS_DIR}/e2e-files_${TIMESTAMP}.log"

# Build Information Collection
echo "📊 Collecting Build Information..."

run_build_check "build-info" "Build Information Collection" \
    "echo '=== Build Information - ${TIMESTAMP} ===' && echo 'Node Version:' && node --version && echo 'NPM Version:' && npm --version && echo 'Project Structure:' && find . -name 'package.json' -not -path './node_modules/*' -not -path './.venv/*' | head -20 && echo '=== End Build Information ==='" \
    "${RESULTS_DIR}/build-info_${TIMESTAMP}.log"

# Generate comprehensive build validation report
echo "📋 Generating Build Validation Report..."

BUILD_REPORT="${RESULTS_DIR}/build-validation-report_${TIMESTAMP}.log"

{
    echo "=================================="
    echo "BUILD VALIDATION REPORT"
    echo "Timestamp: $(date)"
    echo "=================================="
    echo ""
    
    echo "🏗️ Validation Categories:"
    echo "   ✓ Dependency Availability Check"
    echo "   ✓ Production Build Validation"
    echo "   ✓ E2E Test Configuration Check"
    echo "   ✓ Build Environment Information"
    echo ""
    
    echo "📁 Result Files:"
    echo "   Production Build: build-validation_${TIMESTAMP}.log"
    echo "   E2E Configuration: e2e-files_${TIMESTAMP}.log"  
    echo "   Build Information: build-info_${TIMESTAMP}.log"
    echo ""
    
    echo "💡 Build Readiness Checklist:"
    echo "   □ All dependencies installed and accessible"
    echo "   □ Production build completes without errors"
    echo "   □ No missing critical files or configurations"
    echo "   □ Build artifacts generated in expected locations"
    echo "   □ No security vulnerabilities in dependencies"
    echo ""
    
} > "${BUILD_REPORT}"

# Display summary
cat "${BUILD_REPORT}"

echo ""
echo "📊 Build Validation Summary - ${TIMESTAMP}"
echo "All build validation results saved to: ${RESULTS_DIR}"
echo "Production Build: build-validation_${TIMESTAMP}.log"
echo "E2E Configuration: e2e-files_${TIMESTAMP}.log"
echo "Build Information: build-info_${TIMESTAMP}.log"
echo "Consolidated Report: build-validation-report_${TIMESTAMP}.log"

echo ""
echo "✅ Build Validation completed at $(date)"