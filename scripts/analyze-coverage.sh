#!/bin/bash

# Coverage Analysis Script
# Purpose: Analyze coverage reports and generate summary
# Profiles: complete (default), fast, backend, frontend, generate
# Usage: ./analyze-coverage.sh [profile]

# Don't exit on error - we want to capture all coverage information available
# set -e  # REMOVED to allow checking multiple coverage sources

# Show help if requested
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "📊 Coverage Analysis Script"
    echo ""
    echo "Usage: $0 [profile]"
    echo ""
    echo "Available profiles:"
    echo "  complete  (default) - Analyze both backend and frontend coverage reports"
    echo "  fast      - Quick coverage check: existing reports only, no detailed analysis"
    echo "  backend   - Backend coverage analysis only"
    echo "  frontend  - Frontend coverage analysis only"
    echo "  generate  - Generate coverage reports first, then analyze"
    echo ""
    echo "Examples:"
    echo "  $0                    # Analyze existing coverage reports"
    echo "  $0 fast              # Quick coverage check"
    echo "  $0 backend           # Backend coverage analysis only"
    echo "  $0 frontend          # Frontend coverage analysis only"
    echo "  $0 generate          # Generate fresh coverage reports then analyze"
    echo ""
    echo "Note: If no coverage reports exist, run:"
    echo "  ./scripts/run-backend-tests.sh coverage"
    echo "  ./scripts/run-frontend-tests.sh coverage"
    echo ""
    echo "Results saved to: scripts/test-results/coverage-analysis_TIMESTAMP.log"
    exit 0
fi

# Configure analysis profile
ANALYSIS_PROFILE="${1:-complete}"

case "$ANALYSIS_PROFILE" in
    fast)
        SKIP_DETAILED_ANALYSIS=true
        SKIP_COVERAGE_GENERATION=true
        ;;
    backend)
        SKIP_FRONTEND=true
        SKIP_COVERAGE_GENERATION=true
        ;;
    frontend)
        SKIP_BACKEND=true
        SKIP_COVERAGE_GENERATION=true
        ;;
    generate)
        GENERATE_COVERAGE=true
        ;;
    complete|*)
        # Analyze all available coverage
        ;;
esac

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/test-results"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Timing variables for statistics
ANALYSIS_START_TIME=$(date +%s)

# Create results directory
mkdir -p "${RESULTS_DIR}"

echo "📊 Starting Coverage Analysis (Profile: ${ANALYSIS_PROFILE}) - ${TIMESTAMP}"

# Generate coverage if requested
if [[ "${GENERATE_COVERAGE}" == "true" ]]; then
    echo "🔄 Generating fresh coverage reports..."
    
    # Run backend tests with coverage
    if [[ "${SKIP_BACKEND}" != "true" ]]; then
        echo "📊 Generating backend coverage..."
        "${SCRIPT_DIR}/run-backend-tests.sh" coverage
    fi
    
    # Run frontend tests with coverage  
    if [[ "${SKIP_FRONTEND}" != "true" ]]; then
        echo "📊 Generating frontend coverage..."
        "${SCRIPT_DIR}/run-frontend-tests.sh" coverage
    fi
    
    echo "✅ Coverage generation completed"
fi

# Function to safely check and analyze coverage
analyze_coverage() {
    local component_name="$1"
    local component_path="$2"
    local html_path="$3"
    local data_file="$4"
    
    echo "🔍 Analyzing ${component_name} Coverage..."
    
    # Validate path to prevent path traversal attacks
    if [[ "$component_path" =~ \.\. ]] || [[ ! "$component_path" =~ ^[a-zA-Z0-9/_-]+$ ]]; then
        echo "❌ Invalid ${component_name} path detected: $component_path"
        return 1
    fi
    
    if [ ! -d "$component_path" ]; then
        echo "❌ ${component_name} directory not found: $component_path"
        return 1
    fi
    
    # Use absolute path resolution for safety
    local safe_path=$(realpath "$component_path" 2>/dev/null)
    if [ -z "$safe_path" ] || [ ! -d "$safe_path" ]; then
        echo "❌ Cannot resolve ${component_name} directory path"
        return 1
    fi
    
    cd "$safe_path" || {
        echo "❌ Cannot access ${component_name} directory"
        return 1
    }
    
    local found_coverage=false
    
    # Check for HTML coverage report
    if [ -f "$html_path" ]; then
        echo "✅ ${component_name} HTML Coverage Report Available:"
        echo "   Location: $component_path/$html_path"
        found_coverage=true
        
        # Try to extract coverage data if available
        if [ -n "$data_file" ] && [ -f "$data_file" ]; then
            echo "📈 ${component_name} Coverage Summary:"
            case "$component_name" in
                "Backend")
                    if command -v uv >/dev/null 2>&1; then
                        uv run python -m coverage report --show-missing 2>/dev/null || echo "   Coverage summary not available"
                    else
                        echo "   UV not available - cannot generate coverage summary"
                    fi
                    ;;
                "Frontend") 
                    if [ -f "coverage/coverage-final.json" ]; then
                        echo "   JSON coverage data found"
                        # Try to extract basic stats if node is available
                        if command -v node >/dev/null 2>&1; then
                            echo "   Coverage data available for analysis"
                        fi
                    fi
                    ;;
            esac
        fi
    elif [ -d "coverage" ] && [ "$component_name" = "Frontend" ]; then
        echo "✅ ${component_name} Coverage Directory Found:"
        echo "   Location: $component_path/coverage/"
        
        if [ -f "coverage/index.html" ]; then
            echo "   HTML Report: $component_path/coverage/index.html"
            found_coverage=true
        fi
        
        if [ -f "coverage/coverage-final.json" ]; then
            echo "   JSON Report: $component_path/coverage/coverage-final.json"
            found_coverage=true
        fi
        
        # Check for clean test summary
        if [ -f "test-summary-clean.json" ]; then
            echo "   Clean Summary: $component_path/test-summary-clean.json"
            echo "   ✅ Lightweight test results available (90%+ size reduction)"
        fi
        
        # Check for partial coverage in .tmp directory
        if [ -d "coverage/.tmp" ] && [ "$found_coverage" = false ]; then
            local tmp_files=$(ls coverage/.tmp/*.json 2>/dev/null | wc -l)
            if [ "$tmp_files" -gt 0 ]; then
                echo "⚠️ Partial Coverage Data Found:"
                echo "   Temp Files: $tmp_files coverage files in .tmp/"
                echo "   Status: Coverage generated but not consolidated"
                echo "   💡 Run with 'coverage' profile to generate HTML report"
                found_coverage="partial"
            fi
        fi
        
        # Check for test summary as alternative coverage indicator
        if [ -f "test-summary-clean.json" ] && [ "$found_coverage" = false ]; then
            echo "📋 Test Summary Found (alternative coverage data):"
            echo "   Clean Summary: $component_path/test-summary-clean.json"
            echo "   ✅ Lightweight test results available (90%+ size reduction)"
            found_coverage="summary"
        fi
        
        # List coverage files safely
        if [ -d "coverage" ] && [ -r "coverage" ]; then
            echo "📈 ${component_name} Coverage Files:"
            ls -la coverage/ 2>/dev/null | head -10 || echo "   Cannot list coverage files"
        fi
    fi
    
    if [ "$found_coverage" = false ]; then
        echo "❌ ${component_name} Coverage Not Found"
        echo "   Run ${component_name,,} tests with coverage first"
        echo "   💡 Try: ./scripts/run-frontend-tests.sh coverage"
        return 1
    elif [ "$found_coverage" = "partial" ] || [ "$found_coverage" = "summary" ]; then
        echo "⚠️ ${component_name} Coverage Incomplete"
        echo "   Status: Partial data available, full HTML report missing"
        echo "   💡 Run: npm run test:coverage (to generate HTML report)"
        return 2  # New return code for partial coverage
    fi
    
    return 0
}

# Backend Coverage Analysis (skipped for frontend profile)
if [[ "${SKIP_BACKEND}" != "true" ]]; then
    analyze_coverage "Backend" "${PROJECT_ROOT}/apps/api" "htmlcov/index.html" ".coverage"
    BACKEND_STATUS=$?
else
    echo "⏭️ Skipping backend coverage analysis (profile: ${ANALYSIS_PROFILE})"
    BACKEND_STATUS=1
fi

# Frontend Coverage Analysis (skipped for backend profile)
if [[ "${SKIP_FRONTEND}" != "true" ]]; then
    analyze_coverage "Frontend" "${PROJECT_ROOT}/apps/web" "coverage/index.html" "coverage/coverage-final.json"
    FRONTEND_STATUS=$?
else
    echo "⏭️ Skipping frontend coverage analysis (profile: ${ANALYSIS_PROFILE})"
    FRONTEND_STATUS=1
fi

# Generate comprehensive coverage analysis report
echo "📋 Generating Coverage Analysis Report..."

COVERAGE_REPORT="${RESULTS_DIR}/coverage-analysis_${TIMESTAMP}.log"

{
    echo "=================================="
    echo "COVERAGE ANALYSIS REPORT"
    echo "Timestamp: $(date)"
    echo "=================================="
    echo ""
    
    echo "📊 Coverage Analysis Results:"
    if [ $BACKEND_STATUS -eq 0 ]; then
        echo "   ✅ Backend Coverage Available"
    elif [ $BACKEND_STATUS -eq 2 ]; then
        echo "   ⚠️ Backend Coverage Partial"
    else
        echo "   ❌ Backend Coverage Not Available"
    fi
    
    if [ $FRONTEND_STATUS -eq 0 ]; then
        echo "   ✅ Frontend Coverage Available"
    elif [ $FRONTEND_STATUS -eq 2 ]; then
        echo "   ⚠️ Frontend Coverage Partial"
    else
        echo "   ❌ Frontend Coverage Not Available"
    fi
    
    echo ""
    echo "🎯 Coverage Report Locations:"
    echo "   Backend HTML: ${PROJECT_ROOT}/apps/api/htmlcov/index.html"
    echo "   Frontend HTML: ${PROJECT_ROOT}/apps/web/coverage/index.html"
    echo ""
    
    echo "🔄 To regenerate coverage reports:"
    echo "   Backend: ./scripts/run-backend-tests.sh coverage"
    echo "   Frontend: ./scripts/run-frontend-tests.sh coverage"
    echo "   Frontend Profiles: complete | fast | coverage | debug | single"
    echo "   Or run both: ./scripts/run-backend-tests.sh coverage && ./scripts/run-frontend-tests.sh coverage"
    echo ""
    
    echo "📊 Clean Test Summaries:"
    echo "   Frontend: ./apps/web/test-summary-clean.json (90%+ size reduction)"
    echo "   Purpose: Lightweight test results without bulky coverage maps"
    echo "   Generated: Automatically after Vitest runs"
    echo ""
    
    echo "💡 Coverage Best Practices:"
    echo "   □ Maintain >80% line coverage for critical paths"
    echo "   □ Focus on branch coverage, not just line coverage"
    echo "   □ Review uncovered code for missing test scenarios"
    echo "   □ Use coverage to identify dead code"
    echo "   □ Don't chase 100% - focus on meaningful coverage"
    echo "   □ Use 'coverage' profile for detailed analysis"
    echo "   □ Use 'fast' profile for quick coverage checks during development"
    echo ""
    
    echo "🧪 Vitest Configuration Optimizations:"
    echo "   - Fork pool strategy improves React component test stability"
    echo "   - 30s timeout prevents hanging tests while allowing complex components"
    echo "   - Clean test summaries reduce log file sizes by 90%+"
    echo "   - Profile-based execution allows optimal testing strategy selection"
    echo ""
    
    echo "⚠️ Coverage Limitations to Remember:"
    echo "   - High coverage doesn't guarantee bug-free code"
    echo "   - Focus on testing behavior, not implementation"
    echo "   - Integration tests may not show in unit coverage"
    echo "   - Coverage tools may miss some edge cases"
    echo ""
    
    # Overall status with enhanced partial coverage detection
    if [ $BACKEND_STATUS -eq 0 ] && [ $FRONTEND_STATUS -eq 0 ]; then
        echo "🎉 Overall Status: Both backend and frontend coverage available"
    elif [ $BACKEND_STATUS -eq 0 ] && [ $FRONTEND_STATUS -eq 2 ]; then
        echo "⚠️ Overall Status: Backend coverage complete, frontend coverage partial"
    elif [ $BACKEND_STATUS -eq 2 ] && [ $FRONTEND_STATUS -eq 0 ]; then
        echo "⚠️ Overall Status: Frontend coverage complete, backend coverage partial"
    elif [ $BACKEND_STATUS -eq 0 ] || [ $FRONTEND_STATUS -eq 0 ] || [ $BACKEND_STATUS -eq 2 ] || [ $FRONTEND_STATUS -eq 2 ]; then
        echo "⚠️ Overall Status: Some coverage data available (complete or partial)"
    else
        echo "❌ Overall Status: No coverage reports found"
    fi
    
} > "${COVERAGE_REPORT}"

# Display the report
cat "${COVERAGE_REPORT}"

echo ""
echo "📊 Coverage Analysis Summary - ${TIMESTAMP}"
TOTAL_ANALYSIS_TIME=$(($(date +%s) - ANALYSIS_START_TIME))
echo "🕰️ Analysis completed in ${TOTAL_ANALYSIS_TIME}s ($((TOTAL_ANALYSIS_TIME / 60))m $((TOTAL_ANALYSIS_TIME % 60))s)"
echo "Report saved to: ${COVERAGE_REPORT}"

# Exit with appropriate status (enhanced for partial coverage detection)
if [ $BACKEND_STATUS -eq 0 ] && [ $FRONTEND_STATUS -eq 0 ]; then
    echo "✅ Coverage Analysis completed successfully"
    exit 0
elif [ $BACKEND_STATUS -eq 0 ] || [ $FRONTEND_STATUS -eq 0 ] || [ $BACKEND_STATUS -eq 2 ] || [ $FRONTEND_STATUS -eq 2 ]; then
    if [ $BACKEND_STATUS -eq 2 ] || [ $FRONTEND_STATUS -eq 2 ]; then
        echo "⚠️ Coverage Analysis completed with partial coverage detected"
    else
        echo "⚠️ Coverage Analysis completed with warnings"
    fi
    exit 1
else
    echo "❌ Coverage Analysis found no coverage reports"
    exit 2
fi