#!/bin/bash

# Code Quality Checks Runner with Profile Support
# Generated: $(date)
# Purpose: Run linting, formatting, and type checking with configurable profiles

# Don't exit on error - we want to collect all results
# set -e  # REMOVED to allow collecting all results

# Configuration
TEST_PROFILE="${1:-complete}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/test-results"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Global variables for statistics
CHECK_SUCCESS_COUNT=0
CHECK_FAILURE_COUNT=0
CHECK_START_TIME=$(date +%s)

# Function to generate final statistics
generate_final_stats() {
    local completion_status=${1:-"completed"}
    local total_time=$(($(date +%s) - CHECK_START_TIME))
    local total_checks=$((CHECK_SUCCESS_COUNT + CHECK_FAILURE_COUNT))
    
    echo ""
    echo "📋 EXECUTION STATISTICS - ${completion_status^^}"
    echo "======================================"
    echo "🕰️ Total Execution Time: ${total_time}s ($((total_time / 60))m $((total_time % 60))s)"
    echo "🏃 Quality Checks Executed: ${total_checks}"
    echo "✅ Successful: ${CHECK_SUCCESS_COUNT}"
    echo "⚠️ Failed: ${CHECK_FAILURE_COUNT}"
    
    if [ $total_checks -gt 0 ]; then
        local success_rate=$(( (CHECK_SUCCESS_COUNT * 100) / total_checks ))
        echo "📊 Success Rate: ${success_rate}%"
    fi
    
    if [ "$completion_status" = "interrupted" ]; then
        echo "⚠️ Script was interrupted before completion"
    elif [ $CHECK_FAILURE_COUNT -gt 0 ]; then
        echo "⚠️ Some quality checks failed - review detailed logs"
    else
        echo "✨ All quality checks passed successfully!"
    fi
    echo "======================================"
}

# Function to handle script interruption gracefully
handle_interrupt() {
    echo ""
    echo "⚠️ Quality checks interrupted! Cleaning up..."
    generate_final_stats "interrupted"
    exit 130
}

# Set trap for graceful interruption handling
trap handle_interrupt SIGINT SIGTERM

# Create results directory
mkdir -p "${RESULTS_DIR}"

# Usage function
usage() {
    echo "Usage: $0 [PROFILE] [OPTIONS]"
    echo ""
    echo "PROFILES:"
    echo "  complete    Run all quality checks (default)"
    echo "  fast        Run basic lint and format checks only"
    echo "  fix         Run checks and auto-fix where possible"
    echo "  lint        Run linting only"
    echo "  format      Run formatting only"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help  Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 complete         # Run all quality checks"
    echo "  $0 fast            # Quick lint and format check"
    echo "  $0 fix             # Run checks with auto-fix"
    echo "  $0 lint            # Linting only"
    echo "  $0 format          # Formatting only"
    exit 0
}

# Check for help flags
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    usage
fi

# Profile validation and description
case "$TEST_PROFILE" in
    complete)
        PROFILE_DESCRIPTION="Complete quality checks (all linting, formatting, type checking)"
        ;;
    fast)
        PROFILE_DESCRIPTION="Fast quality checks (basic lint and format only)"
        ;;
    fix)
        PROFILE_DESCRIPTION="Quality checks with auto-fix (fix issues where possible)"
        ;;
    lint)
        PROFILE_DESCRIPTION="Linting only (code quality analysis)"
        ;;
    format)
        PROFILE_DESCRIPTION="Formatting only (code style validation)"
        ;;
    *)
        echo "❌ Error: Unknown profile '$TEST_PROFILE'"
        echo "Available profiles: complete, fast, fix, lint, format"
        echo "Use '$0 --help' for more information"
        exit 1
        ;;
esac

echo "✨ Starting Code Quality Checks - ${TIMESTAMP}"
echo "Profile: ${TEST_PROFILE} - ${PROFILE_DESCRIPTION}"
echo "Results will be saved to: ${RESULTS_DIR}"

# Function to run command and report status with statistics
run_check() {
    local check_name="$1"
    local command="$2"
    local log_file="$3"
    local start_time=$(date +%s)
    
    echo "  → ${check_name}"
    if eval "$command" > "$log_file" 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo "    ✅ ${check_name} passed (${duration}s)"
        CHECK_SUCCESS_COUNT=$((CHECK_SUCCESS_COUNT + 1))
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo "    ❌ ${check_name} failed (${duration}s) - check: $(basename "$log_file")"
        CHECK_FAILURE_COUNT=$((CHECK_FAILURE_COUNT + 1))
        return 1
    fi
}

# Function to run frontend linting checks
run_frontend_lint() {
    echo "📱 Running Frontend Linting..."
    cd "${PROJECT_ROOT}/apps/web"
    
    if [[ "$TEST_PROFILE" == "fix" ]]; then
        run_check "Frontend Linting (with auto-fix)" \
            "timeout 30s npx next lint --fix" \
            "${RESULTS_DIR}/frontend-lint_${TIMESTAMP}.log"
    else
        run_check "Frontend Linting" \
            "timeout 30s npx next lint" \
            "${RESULTS_DIR}/frontend-lint_${TIMESTAMP}.log"
    fi
}

# Function to run frontend formatting checks
run_frontend_format() {
    echo "📱 Running Frontend Formatting..."
    cd "${PROJECT_ROOT}"
    
    if [[ "$TEST_PROFILE" == "fix" ]]; then
        run_check "Frontend Formatting (with auto-fix)" \
            "timeout 30s npx prettier --write apps/web --ignore-unknown --ignore-path apps/web/.prettierignore" \
            "${RESULTS_DIR}/frontend-formatting_${TIMESTAMP}.log"
    else
        run_check "Frontend Formatting Check" \
            "timeout 30s npx prettier --check apps/web --ignore-unknown --ignore-path apps/web/.prettierignore" \
            "${RESULTS_DIR}/frontend-formatting_${TIMESTAMP}.log"
    fi
}

# Function to run TypeScript validation
run_typescript_check() {
    echo "📝 Running TypeScript Validation..."
    cd "${PROJECT_ROOT}"
    
    run_check "TypeScript Validation" \
        "npm run type-check" \
        "${RESULTS_DIR}/typescript-check_${TIMESTAMP}.log"
}

# Function to run backend linting checks
run_backend_lint() {
    echo "🔧 Running Backend Linting..."
    cd "${PROJECT_ROOT}/apps/api"
    
    if [[ "$TEST_PROFILE" == "fix" ]]; then
        run_check "Backend Linting (with auto-fix)" \
            "uv run ruff check --fix" \
            "${RESULTS_DIR}/backend-lint_${TIMESTAMP}.log"
    else
        run_check "Backend Linting (Ruff)" \
            "uv run ruff check" \
            "${RESULTS_DIR}/backend-lint_${TIMESTAMP}.log"
    fi
}

# Function to run backend formatting checks
run_backend_format() {
    echo "🔧 Running Backend Formatting..."
    cd "${PROJECT_ROOT}/apps/api"
    
    if [[ "$TEST_PROFILE" == "fix" ]]; then
        run_check "Backend Formatting (with auto-fix)" \
            "uv run ruff format" \
            "${RESULTS_DIR}/backend-formatting_${TIMESTAMP}.log"
    else
        run_check "Backend Formatting Check (Ruff)" \
            "uv run ruff format --check" \
            "${RESULTS_DIR}/backend-formatting_${TIMESTAMP}.log"
    fi
}

# Function to run backend type checking
run_backend_type_check() {
    echo "🔧 Running Backend Type Checking..."
    cd "${PROJECT_ROOT}/apps/api"
    
    run_check "Backend Type Checking (MyPy)" \
        "uv run mypy src --config-file=pyproject.toml" \
        "${RESULTS_DIR}/backend-mypy_${TIMESTAMP}.log"
}

# Function to run database validation
run_database_validation() {
    echo "🗄️ Running Database Validation..."
    cd "${PROJECT_ROOT}/apps/api"
    
    run_check "Alembic Migration Consistency Check" \
        "uv run alembic check" \
        "${RESULTS_DIR}/alembic-check_${TIMESTAMP}.log"
    
    run_check "Alembic Migration History" \
        "uv run alembic history" \
        "${RESULTS_DIR}/alembic-history_${TIMESTAMP}.log"
}

# Profile-based execution
case "$TEST_PROFILE" in
    complete)
        run_frontend_lint
        run_frontend_format
        run_typescript_check
        run_backend_lint
        run_backend_format
        run_backend_type_check
        run_database_validation
        ;;
    fast)
        run_frontend_lint
        run_frontend_format
        run_backend_lint
        run_backend_format
        ;;
    fix)
        run_frontend_lint
        run_frontend_format
        run_backend_lint
        run_backend_format
        ;;
    lint)
        run_frontend_lint
        run_backend_lint
        ;;
    format)
        run_frontend_format
        run_backend_format
        ;;
esac

# Generate statistics
echo ""
echo "✨ Quality Checks Analysis..."
generate_final_stats "completed"

# Profile-aware summary
echo ""
echo "📊 Code Quality Checks Summary - ${TIMESTAMP}"
echo "Profile: ${TEST_PROFILE} - ${PROFILE_DESCRIPTION}"
echo "All quality check results saved to: ${RESULTS_DIR}"
echo ""

# Function to display generated log files based on profile
display_log_files() {
    echo "📁 Generated Log Files:"
    
    case "$TEST_PROFILE" in
        complete)
            echo "   Frontend Linting: frontend-lint_${TIMESTAMP}.log"
            echo "   Frontend Formatting: frontend-formatting_${TIMESTAMP}.log"
            echo "   TypeScript Check: typescript-check_${TIMESTAMP}.log"
            echo "   Backend Linting: backend-lint_${TIMESTAMP}.log"
            echo "   Backend Formatting: backend-formatting_${TIMESTAMP}.log"
            echo "   Backend MyPy: backend-mypy_${TIMESTAMP}.log"
            echo "   Alembic Check: alembic-check_${TIMESTAMP}.log"
            echo "   Alembic History: alembic-history_${TIMESTAMP}.log"
            ;;
        fast)
            echo "   Frontend Linting: frontend-lint_${TIMESTAMP}.log"
            echo "   Frontend Formatting: frontend-formatting_${TIMESTAMP}.log"
            echo "   Backend Linting: backend-lint_${TIMESTAMP}.log"
            echo "   Backend Formatting: backend-formatting_${TIMESTAMP}.log"
            ;;
        fix)
            echo "   Frontend Linting (auto-fixed): frontend-lint_${TIMESTAMP}.log"
            echo "   Frontend Formatting (auto-fixed): frontend-formatting_${TIMESTAMP}.log"
            echo "   Backend Linting (auto-fixed): backend-lint_${TIMESTAMP}.log"
            echo "   Backend Formatting (auto-fixed): backend-formatting_${TIMESTAMP}.log"
            ;;
        lint)
            echo "   Frontend Linting: frontend-lint_${TIMESTAMP}.log"
            echo "   Backend Linting: backend-lint_${TIMESTAMP}.log"
            ;;
        format)
            echo "   Frontend Formatting: frontend-formatting_${TIMESTAMP}.log"
            echo "   Backend Formatting: backend-formatting_${TIMESTAMP}.log"
            ;;
    esac
}

display_log_files

echo ""
echo "💡 To view detailed results:"
case "$TEST_PROFILE" in
    complete|fast)
        echo "   cat ${RESULTS_DIR}/backend-lint_${TIMESTAMP}.log      # View Ruff linting issues"
        echo "   cat ${RESULTS_DIR}/frontend-lint_${TIMESTAMP}.log     # View ESLint issues"
        echo "   cat ${RESULTS_DIR}/frontend-formatting_${TIMESTAMP}.log # View Prettier formatting issues"
        if [[ "$TEST_PROFILE" == "complete" ]]; then
            echo "   cat ${RESULTS_DIR}/backend-mypy_${TIMESTAMP}.log      # View MyPy type errors"
            echo "   cat ${RESULTS_DIR}/alembic-check_${TIMESTAMP}.log     # View migration consistency"
        fi
        ;;
    fix)
        echo "   cat ${RESULTS_DIR}/backend-lint_${TIMESTAMP}.log      # View auto-fix results"
        echo "   cat ${RESULTS_DIR}/frontend-lint_${TIMESTAMP}.log     # View auto-fix results"
        echo "   💡 Issues that could be auto-fixed have been resolved"
        ;;
    lint)
        echo "   cat ${RESULTS_DIR}/backend-lint_${TIMESTAMP}.log      # View Ruff linting issues"
        echo "   cat ${RESULTS_DIR}/frontend-lint_${TIMESTAMP}.log     # View ESLint issues"
        ;;
    format)
        echo "   cat ${RESULTS_DIR}/backend-formatting_${TIMESTAMP}.log  # View Ruff formatting issues"
        echo "   cat ${RESULTS_DIR}/frontend-formatting_${TIMESTAMP}.log # View Prettier formatting issues"
        ;;
esac

echo ""
if [[ "$TEST_PROFILE" == "fix" ]]; then
    echo "🔧 Auto-fix completed - issues that could be automatically resolved have been fixed"
else
    echo "🔧 To auto-fix issues, run: $0 fix"
fi
echo "✅ Code Quality Checks (${TEST_PROFILE} profile) completed at $(date)"

# Exit with appropriate code based on results
if [ $CHECK_FAILURE_COUNT -gt 0 ]; then
    echo "⚠️ Script completed with $CHECK_FAILURE_COUNT failed quality check(s)"
    exit $CHECK_FAILURE_COUNT
else
    echo "✨ All quality checks passed successfully!"
    exit 0
fi