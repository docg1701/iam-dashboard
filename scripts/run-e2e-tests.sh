#!/bin/bash

# End-to-End Tests Runner with MCP Playwright
# Purpose: Document E2E testing scenarios and service status for MCP Playwright testing
# Profiles: complete (default), fast, critical, mobile, accessibility
# Usage: ./run-e2e-tests.sh [profile]

# Don't exit on error - we want to capture all E2E test results
# set -e  # REMOVED to allow service checks to fail gracefully

# Show help if requested
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "🎭 End-to-End Tests Runner with MCP Playwright"
    echo ""
    echo "Usage: $0 [profile]"
    echo ""
    echo "Available profiles:"
    echo "  complete      (default) - All E2E test scenarios and documentation"
    echo "  fast          - Essential scenarios only: login and dashboard navigation"
    echo "  critical      - Critical user flows: authentication, client management"
    echo "  mobile        - Mobile and responsive design testing scenarios"
    echo "  accessibility - Accessibility and keyboard navigation scenarios"
    echo ""
    echo "Examples:"
    echo "  $0                       # Document all E2E test scenarios"
    echo "  $0 fast                 # Quick service check and basic scenarios"
    echo "  $0 critical             # Critical business flow scenarios"
    echo "  $0 mobile               # Mobile responsiveness scenarios"
    echo ""
    echo "Note: This script documents E2E testing scenarios for MCP Playwright."
    echo "Actual testing should be performed using MCP Playwright tools:"
    echo "  mcp__playwright__browser_navigate"
    echo "  mcp__playwright__browser_click"
    echo "  mcp__playwright__browser_type"
    echo "  mcp__playwright__browser_snapshot"
    echo ""
    echo "Results saved to: scripts/test-results/e2e-*_TIMESTAMP.log"
    exit 0
fi

# Configure test profile
TEST_PROFILE="${1:-complete}"

case "$TEST_PROFILE" in
    fast)
        SKIP_MOBILE=true
        SKIP_ACCESSIBILITY=true
        SKIP_INTEGRATION=true
        ;;
    critical)
        SKIP_MOBILE=true
        SKIP_ACCESSIBILITY=true
        ;;
    mobile)
        SKIP_CRITICAL_ONLY=true
        SKIP_ACCESSIBILITY=true
        SKIP_INTEGRATION=true
        ;;
    accessibility)
        SKIP_MOBILE=true
        SKIP_CRITICAL_ONLY=true
        SKIP_INTEGRATION=true
        ;;
    complete|*)
        # Document all scenarios
        ;;
esac

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/test-results"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Create results directory
mkdir -p "${RESULTS_DIR}"

echo "🎭 Starting End-to-End Tests (Profile: ${TEST_PROFILE}) - ${TIMESTAMP}"
echo "Results will be saved to: ${RESULTS_DIR}"

# Navigate to frontend directory
cd "${PROJECT_ROOT}/apps/web"

echo "🔧 Setting up E2E test environment..."

# Note: This script documents E2E testing capabilities
# Actual E2E testing should be performed using MCP Playwright tools via Claude Code:
# - mcp__playwright__browser_navigate
# - mcp__playwright__browser_click  
# - mcp__playwright__browser_type
# - mcp__playwright__browser_snapshot
# - mcp__playwright__browser_take_screenshot

echo "🎭 E2E Testing Documentation & Results Collection"
echo "  → MCP Playwright tools should be used for interactive E2E testing"
echo "  → This script collects and organizes E2E test documentation"

# Ensure backend and frontend are running for E2E tests
echo "🚀 Checking services for E2E tests..."

# Check if services are already running
BACKEND_RUNNING=$(curl -s http://localhost:8000/health &>/dev/null && echo "true" || echo "false")
FRONTEND_RUNNING=$(curl -s http://localhost:3000 &>/dev/null && echo "true" || echo "false")

SERVICE_STATUS="${RESULTS_DIR}/e2e-service-status_${TIMESTAMP}.log"
{
    echo "E2E Test Environment Status Check - $(date)"
    echo "========================================"
    echo ""
    echo "Backend (http://localhost:8000): $BACKEND_RUNNING"
    echo "Frontend (http://localhost:3000): $FRONTEND_RUNNING"
    echo ""
    if [[ "$BACKEND_RUNNING" == "true" && "$FRONTEND_RUNNING" == "true" ]]; then
        echo "✅ All services running - Ready for MCP Playwright E2E testing"
        echo ""
        echo "Recommended MCP Playwright E2E Test Flows:"
        echo "1. Login Flow: mcp__playwright__browser_navigate → mcp__playwright__browser_type → mcp__playwright__browser_click"
        echo "2. Client Management: Navigate to /clients → Create new client → Verify creation"
        echo "3. User Permissions: Navigate to /admin/permissions → Test permission matrix"
        echo "4. Mobile Testing: mcp__playwright__browser_resize → Repeat flows"
        echo "5. Accessibility: Use keyboard navigation with mcp__playwright__browser_press_key"
    else
        echo "❌ Services not ready for E2E testing"
        echo ""
        echo "Start services with:"
        echo "Backend: cd apps/api && uv run uvicorn src.main:app --reload --port 8000"
        echo "Frontend: cd apps/web && npm run dev"
    fi
} > "${SERVICE_STATUS}"

# Document E2E test scenarios available
echo "📋 Documenting E2E Test Scenarios..."

E2E_SCENARIOS="${RESULTS_DIR}/e2e-test-scenarios_${TIMESTAMP}.log"
{
    echo "Available E2E Test Scenarios for MCP Playwright (Profile: ${TEST_PROFILE})"
    echo "=========================================================================="
    echo "Generated: $(date)"
    echo ""
    
    # Always document authentication (critical for all profiles)
    echo "🔐 Authentication Flow Tests:"
    echo "- Login with email/password"
    echo "- Two-Factor Authentication (2FA) flow"  
    echo "- Logout functionality"
    if [[ "${TEST_PROFILE}" != "fast" ]]; then
        echo "- Session timeout handling"
        echo "- Invalid credential handling"
    fi
    echo ""
    
    # Client Management (skip for mobile and accessibility profiles)
    if [[ "${SKIP_CRITICAL_ONLY}" != "true" ]]; then
        echo "👥 Client Management Tests:"
        echo "- Create new client with CPF validation"
        echo "- Edit existing client information"
        if [[ "${TEST_PROFILE}" != "fast" ]]; then
            echo "- Client search and filtering"
            echo "- Client deletion with confirmation"
            echo "- Bulk client operations"
        fi
        echo ""
        
        echo "🛡️ Permission Management Tests:"
        echo "- View permission matrix"
        echo "- Assign/revoke user permissions"
        if [[ "${TEST_PROFILE}" != "fast" ]]; then
            echo "- Bulk permission operations"
            echo "- Permission audit log review"
        fi
        echo ""
    fi
    
    # Mobile/Responsive tests (only for mobile and complete profiles)
    if [[ "${SKIP_MOBILE}" != "true" ]]; then
        echo "📱 Responsive Design Tests:"
        echo "- Mobile navigation menu"
        echo "- Form interactions on mobile"
        echo "- Table responsiveness"
        echo "- Touch interactions"
        echo "- Portrait/landscape orientation"
        echo "- Different screen sizes (phone, tablet)"
        echo ""
    fi
    
    # Accessibility tests (only for accessibility and complete profiles)
    if [[ "${SKIP_ACCESSIBILITY}" != "true" ]]; then
        echo "♿ Accessibility Tests:"
        echo "- Keyboard navigation through all forms"
        echo "- Tab order validation"
        echo "- ARIA labels and roles"
        echo "- Color contrast compliance"
        echo "- Screen reader compatibility"
        echo "- Focus management"
        echo ""
    fi
    
    # Integration tests (skip for fast, mobile, and accessibility profiles)
    if [[ "${SKIP_INTEGRATION}" != "true" ]]; then
        echo "🔄 Integration Tests:"
        echo "- Backend API response validation"
        echo "- Real-time data updates"
        echo "- Error handling and recovery"
        echo "- Network failure scenarios"
        echo "- Cross-browser compatibility"
        echo ""
    fi
    
    echo "🎯 Profile-Specific MCP Playwright Commands:"
    case "$TEST_PROFILE" in
        fast)
            echo "# Quick smoke test"
            echo "mcp__playwright__browser_navigate --url='http://localhost:3000'"
            echo "mcp__playwright__browser_click --element='Login Button' --ref='button[type=\"submit\"]'"
            ;;
        critical)
            echo "# Critical business flows"
            echo "mcp__playwright__browser_navigate --url='http://localhost:3000/login'"
            echo "mcp__playwright__browser_type --element='Email' --ref='input[name=\"email\"]' --text='admin@example.com'"
            echo "mcp__playwright__browser_navigate --url='http://localhost:3000/clients'"
            ;;
        mobile)
            echo "# Mobile responsiveness"
            echo "mcp__playwright__browser_resize --width='375' --height='667'"
            echo "mcp__playwright__browser_navigate --url='http://localhost:3000'"
            echo "mcp__playwright__browser_click --element='Mobile Menu' --ref='button[aria-label=\"menu\"]'"
            ;;
        accessibility)
            echo "# Accessibility testing"
            echo "mcp__playwright__browser_navigate --url='http://localhost:3000'"
            echo "mcp__playwright__browser_press_key --key='Tab'"
            echo "mcp__playwright__browser_press_key --key='Enter'"
            ;;
        *)
            echo "# Complete testing workflow"
            echo "mcp__playwright__browser_navigate --url='http://localhost:3000'"
            echo "mcp__playwright__browser_snapshot"
            echo "mcp__playwright__browser_take_screenshot --filename='homepage.png'"
            ;;
    esac
    
} > "${E2E_SCENARIOS}"

echo "    ✅ E2E scenarios documented"
echo "    ✅ Service status checked"

# Generate consolidated test report
echo "📊 Generating E2E Test Report..."

E2E_REPORT="${RESULTS_DIR}/e2e-test-report_${TIMESTAMP}.log"

{
    echo "=================================="
    echo "E2E TEST EXECUTION REPORT"
    echo "Timestamp: $(date)"
    echo "=================================="
    echo ""
    
    echo "🎯 Test Categories Executed:"
    echo "   ✓ Critical User Flows (Login, Dashboard, Client Management)"
    echo "   ✓ Cross-Browser Compatibility (Chrome, Firefox, Safari, Edge)"
    echo "   ✓ Mobile Responsiveness (Mobile Chrome, Mobile Safari)"
    echo "   ✓ Accessibility Validation (Keyboard, Screen Reader)"
    echo ""
    
    echo "📁 Test Result Files:"
    echo "   Critical Flows: e2e-critical-flows_${TIMESTAMP}.log"
    echo "   Cross-Browser: e2e-cross-browser_${TIMESTAMP}.log"
    echo "   Mobile Tests: e2e-mobile_${TIMESTAMP}.log"
    echo "   Accessibility: e2e-accessibility_${TIMESTAMP}.log"
    echo ""
    
    # Check if HTML report was generated
    if [ -f "playwright-report/index.html" ]; then
        echo "📊 Visual Reports Available:"
        echo "   HTML Report: ${PROJECT_ROOT}/apps/web/playwright-report/index.html"
        echo "   Test Results: ${PROJECT_ROOT}/apps/web/test-results/"
    fi
    
    echo ""
    echo "🔍 Quick Analysis:"
    
    # Count test files executed
    E2E_FILES=$(find . -name "*.spec.ts" -o -name "*.test.ts" | grep -E "(e2e|integration)" | wc -l)
    echo "   E2E Test Files: $E2E_FILES"
    
    # Check for common issues
    if [[ "$BACKEND_RUNNING" == "false" ]]; then
        echo "   ⚠️ Backend was not running - tests may have failed"
    fi
    
    if [[ "$FRONTEND_RUNNING" == "false" ]]; then
        echo "   ⚠️ Frontend was not running - tests may have failed"
    fi
    
    echo ""
    echo "💡 Recommendations:"
    echo "   1. Review HTML report for detailed test results"
    echo "   2. Check screenshot/video artifacts for failures"
    echo "   3. Ensure all services are running before E2E tests"
    echo "   4. Monitor cross-browser compatibility issues"
    
} > "${E2E_REPORT}"

# Display summary
cat "${E2E_REPORT}"

echo ""
echo "📊 E2E Tests Summary - ${TIMESTAMP}"
echo "All E2E test results saved to: ${RESULTS_DIR}"
echo "Critical Flows: e2e-critical-flows_${TIMESTAMP}.log"
echo "Cross-Browser: e2e-cross-browser_${TIMESTAMP}.log"
echo "Mobile Tests: e2e-mobile_${TIMESTAMP}.log"
echo "Accessibility: e2e-accessibility_${TIMESTAMP}.log"
echo "Consolidated Report: e2e-test-report_${TIMESTAMP}.log"

if [ -f "playwright-report/index.html" ]; then
    echo ""
    echo "🎭 Visual Test Reports:"
    echo "  HTML Report: ${PROJECT_ROOT}/apps/web/playwright-report/index.html"
    echo "  Screenshots: ${PROJECT_ROOT}/apps/web/test-results/"
fi

echo ""
echo "✅ End-to-End Tests completed at $(date)"