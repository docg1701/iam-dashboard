#!/bin/bash

# Code Quality Checks Runner
# Generated: $(date)
# Purpose: Run all linting, formatting, and type checking

# Don't exit on error - we want to collect all results
# set -e  # REMOVED to allow collecting all results

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/test-results"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Create results directory
mkdir -p "${RESULTS_DIR}"

echo "✨ Starting Code Quality Checks - ${TIMESTAMP}"
echo "Results will be saved to: ${RESULTS_DIR}"

# Function to run command and report status
run_check() {
    local check_name="$1"
    local command="$2"
    local log_file="$3"
    
    echo "  → ${check_name}"
    if eval "$command" > "$log_file" 2>&1; then
        echo "    ✅ ${check_name} passed"
        return 0
    else
        echo "    ❌ ${check_name} failed (check: $(basename "$log_file"))"
        return 1
    fi
}

# Frontend Quality Checks
echo "📱 Running Frontend Quality Checks..."
cd "${PROJECT_ROOT}/apps/frontend"

run_check "Frontend Linting" \
    "npx next lint" \
    "${RESULTS_DIR}/frontend-lint_${TIMESTAMP}.log"

cd "${PROJECT_ROOT}"
run_check "Frontend Formatting Check" \
    "npx prettier --check apps/frontend --ignore-unknown --ignore-path apps/frontend/.prettierignore" \
    "${RESULTS_DIR}/frontend-formatting_${TIMESTAMP}.log"

run_check "TypeScript Validation" \
    "npm run type-check" \
    "${RESULTS_DIR}/typescript-check_${TIMESTAMP}.log"

# Backend Quality Checks
echo "🔧 Running Backend Quality Checks..."
cd "${PROJECT_ROOT}/apps/backend"

run_check "Backend Linting (Ruff)" \
    "uv run ruff check" \
    "${RESULTS_DIR}/backend-lint_${TIMESTAMP}.log"

run_check "Backend Formatting Check (Ruff)" \
    "uv run ruff format --check" \
    "${RESULTS_DIR}/backend-formatting_${TIMESTAMP}.log"

run_check "Backend Type Checking (MyPy)" \
    "uv run mypy src --config-file=pyproject.toml" \
    "${RESULTS_DIR}/backend-mypy_${TIMESTAMP}.log"

# Database Validation
echo "🗄️ Running Database Validation..."

run_check "Alembic Migration Consistency Check" \
    "uv run alembic check" \
    "${RESULTS_DIR}/alembic-check_${TIMESTAMP}.log"

run_check "Alembic Migration History" \
    "uv run alembic history" \
    "${RESULTS_DIR}/alembic-history_${TIMESTAMP}.log"

# Summary
echo ""
echo "📊 Code Quality Checks Summary - ${TIMESTAMP}"
echo "All quality check results saved to: ${RESULTS_DIR}"
echo ""
echo "📁 Generated Log Files:"
echo "   Frontend Linting: frontend-lint_${TIMESTAMP}.log"
echo "   Frontend Formatting: frontend-formatting_${TIMESTAMP}.log"
echo "   TypeScript Check: typescript-check_${TIMESTAMP}.log"
echo "   Backend Linting: backend-lint_${TIMESTAMP}.log"
echo "   Backend Formatting: backend-formatting_${TIMESTAMP}.log"
echo "   Backend MyPy: backend-mypy_${TIMESTAMP}.log"
echo "   Alembic Check: alembic-check_${TIMESTAMP}.log"
echo "   Alembic History: alembic-history_${TIMESTAMP}.log"
echo ""
echo "💡 To view detailed results:"
echo "   cat ${RESULTS_DIR}/backend-mypy_${TIMESTAMP}.log  # View MyPy type errors"
echo "   cat ${RESULTS_DIR}/backend-lint_${TIMESTAMP}.log  # View Ruff linting issues"
echo ""
echo "✅ Code Quality Checks completed at $(date)"