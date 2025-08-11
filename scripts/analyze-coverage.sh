#!/bin/bash

# Coverage Analysis Script
# Generated: $(date)
# Purpose: Analyze coverage reports and generate summary

# Don't exit on error - we want to capture all coverage information available
# set -e  # REMOVED to allow checking multiple coverage sources

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/test-results"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Create results directory
mkdir -p "${RESULTS_DIR}"

echo "📊 Starting Coverage Analysis - ${TIMESTAMP}"

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
        
        # List coverage files safely
        if [ -d "coverage" ] && [ -r "coverage" ]; then
            echo "📈 ${component_name} Coverage Files:"
            ls -la coverage/ 2>/dev/null | head -10 || echo "   Cannot list coverage files"
        fi
    fi
    
    if [ "$found_coverage" = false ]; then
        echo "❌ ${component_name} Coverage Not Found"
        echo "   Run ${component_name,,} tests with coverage first"
        return 1
    fi
    
    return 0
}

# Backend Coverage Analysis
analyze_coverage "Backend" "${PROJECT_ROOT}/apps/api" "htmlcov/index.html" ".coverage"
BACKEND_STATUS=$?

# Frontend Coverage Analysis  
analyze_coverage "Frontend" "${PROJECT_ROOT}/apps/web" "coverage/index.html" "coverage/coverage-final.json"
FRONTEND_STATUS=$?

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
    else
        echo "   ❌ Backend Coverage Not Available"
    fi
    
    if [ $FRONTEND_STATUS -eq 0 ]; then
        echo "   ✅ Frontend Coverage Available"
    else
        echo "   ❌ Frontend Coverage Not Available"
    fi
    
    echo ""
    echo "🎯 Coverage Report Locations:"
    echo "   Backend HTML: ${PROJECT_ROOT}/apps/api/htmlcov/index.html"
    echo "   Frontend HTML: ${PROJECT_ROOT}/apps/web/coverage/index.html"
    echo ""
    
    echo "🔄 To regenerate coverage reports:"
    echo "   Backend: ./scripts/run-backend-tests.sh"
    echo "   Frontend: ./scripts/run-frontend-tests.sh"
    echo "   Or run both: npm run test:coverage"
    echo ""
    
    echo "💡 Coverage Best Practices:"
    echo "   □ Maintain >80% line coverage for critical paths"
    echo "   □ Focus on branch coverage, not just line coverage"
    echo "   □ Review uncovered code for missing test scenarios"
    echo "   □ Use coverage to identify dead code"
    echo "   □ Don't chase 100% - focus on meaningful coverage"
    echo ""
    
    echo "⚠️ Coverage Limitations to Remember:"
    echo "   - High coverage doesn't guarantee bug-free code"
    echo "   - Focus on testing behavior, not implementation"
    echo "   - Integration tests may not show in unit coverage"
    echo "   - Coverage tools may miss some edge cases"
    echo ""
    
    # Overall status
    if [ $BACKEND_STATUS -eq 0 ] && [ $FRONTEND_STATUS -eq 0 ]; then
        echo "🎉 Overall Status: Both backend and frontend coverage available"
    elif [ $BACKEND_STATUS -eq 0 ] || [ $FRONTEND_STATUS -eq 0 ]; then
        echo "⚠️ Overall Status: Partial coverage available"
    else
        echo "❌ Overall Status: No coverage reports found"
    fi
    
} > "${COVERAGE_REPORT}"

# Display the report
cat "${COVERAGE_REPORT}"

echo ""
echo "📊 Coverage Analysis Summary - ${TIMESTAMP}"
echo "Report saved to: ${COVERAGE_REPORT}"

# Exit with appropriate status
if [ $BACKEND_STATUS -eq 0 ] && [ $FRONTEND_STATUS -eq 0 ]; then
    echo "✅ Coverage Analysis completed successfully"
    exit 0
elif [ $BACKEND_STATUS -eq 0 ] || [ $FRONTEND_STATUS -eq 0 ]; then
    echo "⚠️ Coverage Analysis completed with warnings"
    exit 1
else
    echo "❌ Coverage Analysis found no coverage reports"
    exit 2
fi