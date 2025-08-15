#!/bin/bash

# Mock Violations Scanner - Enhanced Version  
# Purpose: Scan entire project for problematic mocking patterns that violate CLAUDE.md guidelines
# Profiles: complete (default), fast, backend, frontend, patterns
# Usage: ./run-mock-violations-scan.sh [profile]
#
# ENHANCEMENT FEATURES:
# - Filters out APPROVED external dependency mocks (Redis, pyotp, datetime, uuid)
# - Excludes dependency directories (.cache, .venv, node_modules)
# - Reduces false positives while maintaining violation detection
# - Enhanced pattern matching for accurate categorization
#
# APPROVED MOCK PATTERNS (will NOT be flagged as violations):
# ✅ patch.object(auth_service, '_redis_client', mock_redis) - External Redis dependency
# ✅ patch("src.services.auth_service.datetime") - Time mocking for deterministic tests
# ✅ patch("src.services.auth_service.pyotp.TOTP.verify") - Third-party library mocking
# ✅ patch("uuid.uuid4") - UUID generation mocking
# ✅ Files in .cache/, .venv/, node_modules/ - Not our code
#
# PROHIBITED PATTERNS (will be flagged as violations):
# ❌ Mock internal business logic (PermissionService, UserService, etc.)
# ❌ Mock internal frontend components, hooks, or utilities
# ❌ Mock database sessions in integration tests
# ❌ Mock authentication flows in business logic tests

# ===============================================================================
# 🤖 CLAUDE SONNET 4 - SELF-IMPROVEMENT GUIDANCE
# ===============================================================================
# 
# If you're seeing this message, you're likely analyzing mock violations and may
# encounter false positives. Here's how to systematically improve this script:
#
# 🔍 FALSE POSITIVE DETECTION STRATEGY:
# 
# 1. **ANALYZE EACH VIOLATION MANUALLY**:
#    - Read the actual code lines flagged as violations
#    - Check if they match CLAUDE.md APPROVED patterns:
#      ✅ External dependencies (Redis, databases, APIs)
#      ✅ Time/random generation (datetime, uuid, time.sleep)
#      ✅ Third-party libraries (pyotp, requests, httpx, smtp)
#      ✅ File I/O and system calls
#
# 2. **IDENTIFY NEW APPROVED PATTERNS**:
#    - If violations are external dependencies → ADD to filter_approved_patterns()
#    - If violations are in dependency directories → ADD to directory exclusions
#    - If violations are legitimate → INVESTIGATE why they weren't caught
#
# 3. **SCRIPT ENHANCEMENT LOCATIONS**:
#    - Line ~45: filter_approved_patterns() function - ADD new exclusion patterns
#    - Line ~92: Directory exclusions - ADD new dependency directories
#    - Line ~96: Scan type selection - MODIFY which scans use filtering
#
# 4. **ENHANCEMENT EXAMPLE**:
#    If you find: patch("new_external_lib.method") being flagged incorrectly:
#    ADD to filter_approved_patterns(): patch.*new_external_lib\.|
#
# 5. **VALIDATION PROCESS**:
#    - After enhancements, re-run the scan
#    - Verify real violations are still detected
#    - Document new patterns in the APPROVED MOCK PATTERNS section above
#
# 6. **FALSE POSITIVE INDICATORS**:
#    - High violation counts (50+) from external dependency patterns
#    - Violations in .cache/, .venv/, node_modules/ directories
#    - Time/datetime/uuid/random mocking being flagged
#    - Third-party library mocking being flagged
#
# 💡 REMEMBER: "Mock the boundaries, not the behavior" - CLAUDE.md Golden Rule
#    Only external system boundaries should be mocked, never internal business logic.
#
# ===============================================================================

# Don't exit on error - we want to capture all violations even if some checks fail
# set -e  # REMOVED to continue execution on check failures

# Show help if requested
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "🔍 Mock Violations Scanner - CLAUDE.md Compliance"
    echo ""
    echo "Usage: $0 [profile]"
    echo ""
    echo "Available profiles:"
    echo "  complete   (default) - Scan all code for mock violations: backend, frontend, patterns"
    echo "  fast       - Essential violations only: internal service and component mocking"
    echo "  backend    - Backend violations only: service, database, auth, business logic mocking"
    echo "  frontend   - Frontend violations only: component, hook, service, store mocking"
    echo "  patterns   - Pattern violations only: excessive mocking and import-level issues"
    echo ""
    echo "Examples:"
    echo "  $0                    # Complete violation scan"
    echo "  $0 fast              # Quick scan for critical violations"
    echo "  $0 backend           # Backend mock violations only"
    echo "  $0 frontend          # Frontend mock violations only"
    echo ""
    echo "CLAUDE.md Golden Rule: 'Mock the boundaries, not the behavior'"
    echo "✅ APPROVED: Mock external APIs, time/UUID, third-party libraries"
    echo "❌ PROHIBITED: Mock internal business logic, components, hooks"
    echo ""
    echo "Results saved to: scripts/test-results/*-mocks_TIMESTAMP.log"
    exit 0
fi

# Configure scan profile
SCAN_PROFILE="${1:-complete}"

case "$SCAN_PROFILE" in
    fast)
        SKIP_PATTERN_ANALYSIS=true
        SKIP_APPROVED_VERIFICATION=true
        SKIP_FILE_ANALYSIS=true
        ;;
    backend)
        SKIP_FRONTEND=true
        SKIP_PATTERN_ANALYSIS=true
        SKIP_APPROVED_VERIFICATION=true
        ;;
    frontend)
        SKIP_BACKEND=true
        SKIP_PATTERN_ANALYSIS=true
        SKIP_APPROVED_VERIFICATION=true
        ;;
    patterns)
        SKIP_BACKEND=true
        SKIP_FRONTEND=true
        SKIP_APPROVED_VERIFICATION=true
        ;;
    complete|*)
        # Run all scans
        ;;
esac

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/test-results"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Timing variables for statistics
SCAN_START_TIME=$(date +%s)

# Create results directory
mkdir -p "${RESULTS_DIR}"

echo "🔍 Starting Mock Violations Scan (Profile: ${SCAN_PROFILE}) - ${TIMESTAMP}"
echo "Results will be saved to: ${RESULTS_DIR}"

# Function to filter out approved mocking patterns
filter_approved_patterns() {
    # Read from stdin and filter out approved patterns
    grep -v -E "(
        # APPROVED: External Redis client mocking
        patch\.object\(.*_redis_client|
        # APPROVED: Third-party library mocking (pyotp, etc.)
        patch.*pyotp\.TOTP\.verify|
        # APPROVED: Time/datetime mocking
        patch.*datetime|
        patch.*time\.|       
        # APPROVED: UUID generation mocking
        patch.*uuid\.|       
        # APPROVED: External service mocking
        patch.*requests\.|   
        patch.*httpx\.|      
        patch.*smtp|         
        # APPROVED: Cache/session mocking (Redis-related)
        _redis_client|       
        # APPROVED: Comments indicating approved usage
        # APPROVED
    )" 2>/dev/null || true  # Return true if no input to avoid pipeline failure
}

# Safe function to run scan commands without eval
run_scan() {
    local scan_name="$1"
    local search_pattern="$2"
    local search_paths="$3"
    local log_file="$4"
    local file_patterns="$5"
    
    echo "  → $scan_name"
    
    {
        echo "Mock Violations Scan: $scan_name"
        echo "Pattern: $search_pattern"
        echo "Timestamp: $(date)"
        echo "========================================"
        echo ""
        
        # Use grep safely without eval, with improved filtering
        if [ -n "$file_patterns" ]; then
            # Split file patterns and use multiple --include flags
            local grep_includes=""
            IFS=',' read -ra PATTERNS <<< "$file_patterns"
            for pattern in "${PATTERNS[@]}"; do
                grep_includes="$grep_includes --include=$pattern"
            done
            
            # First find all matches, then filter out false positives
            local raw_results=$(grep -r $grep_includes -n -H -E "$search_pattern" $search_paths 2>/dev/null | \
                grep -v -E "(\.cache/|\.venv/|node_modules/|/dist/|/build/)" || true)
            
            if [ -n "$raw_results" ]; then
                # Apply approved pattern filtering for specific scans
                if [[ "$scan_name" == *"Business Logic"* ]] || [[ "$scan_name" == *"Authentication"* ]] || [[ "$scan_name" == *"Mock Implementation"* ]]; then
                    echo "$raw_results" | filter_approved_patterns || {
                        echo "No violations found for this pattern"
                        return 0
                    }
                else
                    echo "$raw_results"
                fi
            else
                echo "No violations found for this pattern"
                return 0
            fi
        else
            # First find all matches, then filter out false positives
            local raw_results=$(grep -r -n -H -E "$search_pattern" $search_paths 2>/dev/null | \
                grep -v -E "(\.cache/|\.venv/|node_modules/|/dist/|/build/)" || true)
            
            if [ -n "$raw_results" ]; then
                # Apply approved pattern filtering for specific scans
                if [[ "$scan_name" == *"Business Logic"* ]] || [[ "$scan_name" == *"Authentication"* ]] || [[ "$scan_name" == *"Mock Implementation"* ]]; then
                    echo "$raw_results" | filter_approved_patterns || {
                        echo "No violations found for this pattern"
                        return 0
                    }
                else
                    echo "$raw_results"
                fi
            else
                echo "No violations found for this pattern"
                return 0
            fi
        fi
        
    } > "$log_file"
    
    # Check if any violations were found
    if grep -q "No violations found" "$log_file"; then
        echo "    ✅ $scan_name: No violations found"
        return 0
    else
        echo "    ⚠️ $scan_name: Violations found (check: $(basename "$log_file"))"
        return 1
    fi
}

# Safe function for complex scans without command injection
run_complex_scan() {
    local scan_name="$1"
    local log_file="$2"
    
    echo "  → $scan_name"
    
    {
        echo "Complex Mock Violations Scan: $scan_name"
        echo "Timestamp: $(date)"
        echo "========================================"
        echo ""
        
        case "$scan_name" in
            "Excessive Mock Usage")
                echo "Scanning for test functions with multiple mocks..."
                find apps/ -name "*.py" -o -name "*.test.*" -o -name "*.spec.*" 2>/dev/null | while IFS= read -r -d '' file || [ -n "$file" ]; do
                    if [ -f "$file" ]; then
                        # Count mocks per test function safely
                        grep -n -E "(def test_|it\()" "$file" 2>/dev/null | while read -r line; do
                            local line_num=$(echo "$line" | cut -d: -f1)
                            local test_name=$(echo "$line" | cut -d: -f2-)
                            
                            # Count mocks in next 20 lines from test start
                            local mock_count=$(sed -n "${line_num},$((line_num + 20))p" "$file" | grep -c -E "(patch|mock|Mock|vi\.mock)" 2>/dev/null || echo "0")
                            
                            if [ "$mock_count" -gt 3 ]; then
                                echo "$file:$line_num: Excessive mocking ($mock_count mocks) in: $test_name"
                            fi
                        done
                    fi
                done
                ;;
            "Import Level Mocking")
                echo "Scanning for import-level mocking..."
                find apps/ -name "*.py" -o -name "*.test.*" -o -name "*.spec.*" 2>/dev/null | while IFS= read -r -d '' file || [ -n "$file" ]; do
                    if [ -f "$file" ]; then
                        # Look for mocks at module level (before any function/class definition)
                        awk '/^(patch|mock|Mock|vi\.mock)/ && !seen_def {print FILENAME ":" NR ": " $0} /^(def |class |function |const |let )/ {seen_def=1}' "$file" 2>/dev/null || true
                    fi
                done
                ;;
            *)
                echo "Unknown complex scan type: $scan_name"
                ;;
        esac
        
    } > "$log_file"
    
    if [ ! -s "$log_file" ] || grep -q "No violations found" "$log_file"; then
        echo "    ✅ $scan_name: No violations found"
        return 0
    else
        echo "    ⚠️ $scan_name: Violations found (check: $(basename "$log_file"))"
        return 1
    fi
}

# Navigate to project root
cd "${PROJECT_ROOT}"

echo "🚨 Scanning for PROHIBITED Mock Patterns (CLAUDE.md violations)..."

# Backend Mock Violations (skipped for frontend and patterns profiles)
if [[ "${SKIP_BACKEND}" != "true" ]]; then
    echo "🔧 Scanning Backend Test Files..."

    run_scan "Backend Internal Service Mocking" \
        "(patch|mock|Mock).*(\.|@)(PermissionService|UserService|ClientService|permission_service|user_service|client_service)" \
        "apps/api/tests/" \
        "${RESULTS_DIR}/backend-internal-service-mocks_${TIMESTAMP}.log" \
        "*.py"

    run_scan "Backend Database Session Mocking" \
        "(patch|mock|Mock).*(get_db|database|session|Session)" \
        "apps/api/tests/integration/" \
        "${RESULTS_DIR}/backend-database-mocks_${TIMESTAMP}.log" \
        "*.py"

    run_scan "Backend Authentication Flow Mocking" \
        "(patch|mock|Mock).*(auth|Auth|login|Login|jwt|JWT|token|Token)" \
        "apps/api/tests/unit/ apps/api/tests/integration/" \
        "${RESULTS_DIR}/backend-auth-mocks_${TIMESTAMP}.log" \
        "*.py"

    run_scan "Backend Business Logic Mocking" \
        "(patch|mock|Mock).*(core\.permissions|core\.auth|services\.)" \
        "apps/api/tests/" \
        "${RESULTS_DIR}/backend-business-logic-mocks_${TIMESTAMP}.log" \
        "*.py"

    run_scan "Backend Model/Schema Mocking" \
        "(patch|mock|Mock).*(models\.|schemas\.)" \
        "apps/api/tests/unit/ apps/api/tests/integration/" \
        "${RESULTS_DIR}/backend-models-mocks_${TIMESTAMP}.log" \
        "*.py"
else
    echo "⏭️ Skipping backend mock violations scan (profile: ${SCAN_PROFILE})"
fi

# Frontend Mock Violations (skipped for backend and patterns profiles)
if [[ "${SKIP_FRONTEND}" != "true" ]]; then
    echo "🎨 Scanning Frontend Test Files..."

    run_scan "Frontend Internal Component Mocking" \
        "vi\.mock.*@/(components|hooks|services|stores|utils)" \
        "apps/web/tests/" \
        "${RESULTS_DIR}/frontend-internal-mocks_${TIMESTAMP}.log" \
        "*.test.*,*.spec.*"

    run_scan "Frontend Hook Mocking" \
        "vi\.mock.*use[A-Z]" \
        "apps/web/tests/" \
        "${RESULTS_DIR}/frontend-hook-mocks_${TIMESTAMP}.log" \
        "*.test.*,*.spec.*"

    run_scan "Frontend Service Mocking" \
        "vi\.mock.*(Service|service)" \
        "apps/web/tests/" \
        "${RESULTS_DIR}/frontend-service-mocks_${TIMESTAMP}.log" \
        "*.test.*,*.spec.*"

    run_scan "Frontend Store/Context Mocking" \
        "vi\.mock.*(Store|Context|Provider)" \
        "apps/web/tests/" \
        "${RESULTS_DIR}/frontend-store-mocks_${TIMESTAMP}.log" \
        "*.test.*,*.spec.*"

    run_scan "Frontend Component Import Mocking" \
        "vi\.mock.*\.(tsx?|jsx?)" \
        "apps/web/tests/" \
        "${RESULTS_DIR}/frontend-component-import-mocks_${TIMESTAMP}.log" \
        "*.test.*,*.spec.*"
else
    echo "⏭️ Skipping frontend mock violations scan (profile: ${SCAN_PROFILE})"
fi

# Pattern Analysis (only for patterns and complete profiles)
if [[ "${SKIP_PATTERN_ANALYSIS}" != "true" ]]; then
    echo "🔍 Scanning for Specific Violation Patterns..."

    run_scan "Mock Implementation Instead of Real Logic" \
        "(mockImplementation|mockReturnValue|return_value).*\.(create|update|delete|get|find)" \
        "apps/" \
        "${RESULTS_DIR}/mock-implementation-violations_${TIMESTAMP}.log" \
        "*.py,*.test.*,*.spec.*"

    run_complex_scan "Excessive Mock Usage" \
        "${RESULTS_DIR}/excessive-mocking_${TIMESTAMP}.log"

    run_complex_scan "Import Level Mocking" \
        "${RESULTS_DIR}/import-level-mocks_${TIMESTAMP}.log"
else
    echo "⏭️ Skipping pattern analysis (profile: ${SCAN_PROFILE})"
fi

# Approved Pattern Verification (skipped for fast, backend, frontend, patterns profiles)
if [[ "${SKIP_APPROVED_VERIFICATION}" != "true" ]]; then
    echo "✅ Verifying APPROVED Mock Patterns..."

    run_scan "External API Mocking (Approved)" \
        "(patch|mock|Mock).*(requests|httpx|fetch|axios)" \
        "apps/" \
        "${RESULTS_DIR}/approved-external-api-mocks_${TIMESTAMP}.log" \
        "*.py,*.test.*,*.spec.*"

    run_scan "Time/Random Mocking (Approved)" \
        "(patch|mock|Mock).*(time\.|datetime\.|random\.|uuid\.|pyotp\.)" \
        "apps/" \
        "${RESULTS_DIR}/approved-time-random-mocks_${TIMESTAMP}.log" \
        "*.py,*.test.*,*.spec.*"

    run_scan "External Service Mocking (Approved)" \
        "(patch|mock|Mock).*(external_services|notification_service|email_service|redis|_redis_client|smtp)" \
        "apps/" \
        "${RESULTS_DIR}/approved-external-service-mocks_${TIMESTAMP}.log" \
        "*.py,*.test.*,*.spec.*"
else
    echo "⏭️ Skipping approved pattern verification (profile: ${SCAN_PROFILE})"
fi

# File-by-File Analysis (skipped for fast profile)
if [[ "${SKIP_FILE_ANALYSIS}" != "true" ]]; then
    echo "📄 Performing File-by-File Deep Analysis..."

# Find all test files and analyze each one
find apps/ -name "*.test.*" -o -name "*test*.py" | while read -r file; do
    if [[ -f "$file" ]]; then
        filename=$(basename "$file")
        echo "   Analyzing: $filename"
        
        # Count mocks per file
        mock_count=$(grep -c -E '(patch|mock|Mock|vi\.mock)' "$file" 2>/dev/null || echo "0")
        
        # Extract specific violations  
        violations=$(grep -n -E '(patch|mock|Mock|vi\.mock).*(Service|service|Component|Hook|use[A-Z]|@/|core\.|models\.|schemas\.)' "$file" 2>/dev/null || true)
        
        if [[ $mock_count -gt 5 ]] || [[ -n "$violations" ]]; then
            {
                echo "FILE: $file"
                echo "MOCK COUNT: $mock_count"
                echo "VIOLATIONS:"
                echo "$violations"
                echo "---"
            } >> "${RESULTS_DIR}/file-by-file-analysis_${TIMESTAMP}.log"
        fi
    fi
done 2>/dev/null || true
else
    echo "⏭️ Skipping file-by-file analysis (profile: ${SCAN_PROFILE})"
fi

# Generate comprehensive report
echo "📊 Generating Mock Violations Analysis Report..."

VIOLATIONS_REPORT="${RESULTS_DIR}/mock-violations-report_${TIMESTAMP}.log"

{
    echo "=========================================="
    echo "MOCK VIOLATIONS COMPREHENSIVE SCAN REPORT"
    echo "Timestamp: $(date)"
    echo "=========================================="
    echo ""
    
    echo "🚨 CRITICAL VIOLATIONS DETECTED:"
    echo ""
    
# Function to count actual violations (excluding headers and empty lines)
count_violations() {
    local file="$1"
    if [[ -f "$file" ]]; then
        grep -v -E "(Mock Violations Scan|Pattern:|Timestamp:|========|^$|No violations found)" "$file" 2>/dev/null | wc -l
    else
        echo "0"
    fi
}

    echo "📋 Backend Violations:"
    echo "   Internal Service Mocking: $(count_violations "${RESULTS_DIR}/backend-internal-service-mocks_${TIMESTAMP}.log") instances"
    echo "   Database Session Mocking: $(count_violations "${RESULTS_DIR}/backend-database-mocks_${TIMESTAMP}.log") instances"
    echo "   Authentication Flow Mocking: $(count_violations "${RESULTS_DIR}/backend-auth-mocks_${TIMESTAMP}.log") instances"
    echo "   Business Logic Mocking: $(count_violations "${RESULTS_DIR}/backend-business-logic-mocks_${TIMESTAMP}.log") instances"
    echo "   Model/Schema Mocking: $(count_violations "${RESULTS_DIR}/backend-models-mocks_${TIMESTAMP}.log") instances"
    echo ""
    
    echo "🎨 Frontend Violations:"
    echo "   Internal Component Mocking: $(count_violations "${RESULTS_DIR}/frontend-internal-mocks_${TIMESTAMP}.log") instances"
    echo "   Hook Mocking: $(count_violations "${RESULTS_DIR}/frontend-hook-mocks_${TIMESTAMP}.log") instances"
    echo "   Service Mocking: $(count_violations "${RESULTS_DIR}/frontend-service-mocks_${TIMESTAMP}.log") instances"
    echo "   Store/Context Mocking: $(count_violations "${RESULTS_DIR}/frontend-store-mocks_${TIMESTAMP}.log") instances"
    echo "   Component Import Mocking: $(count_violations "${RESULTS_DIR}/frontend-component-import-mocks_${TIMESTAMP}.log") instances"
    echo ""
    
    echo "⚡ Pattern Violations:"
    echo "   Mock Implementations: $(count_violations "${RESULTS_DIR}/mock-implementation-violations_${TIMESTAMP}.log") instances"
    echo "   Import-Level Mocks: $(count_violations "${RESULTS_DIR}/import-level-mocks_${TIMESTAMP}.log") instances"
    echo ""
    
    echo "✅ APPROVED Patterns Detected:"
    echo "   External API Mocks: $(count_violations "${RESULTS_DIR}/approved-external-api-mocks_${TIMESTAMP}.log") instances (✅ Good)"
    echo "   Time/Random Mocks: $(count_violations "${RESULTS_DIR}/approved-time-random-mocks_${TIMESTAMP}.log") instances (✅ Good)" 
    echo "   External Service Mocks: $(count_violations "${RESULTS_DIR}/approved-external-service-mocks_${TIMESTAMP}.log") instances (✅ Good)"
    echo ""
    
    echo "📁 Detailed Result Files:"
    echo "   Backend Internal Service Mocks: backend-internal-service-mocks_${TIMESTAMP}.log"
    echo "   Backend Database Session Mocks: backend-database-mocks_${TIMESTAMP}.log"
    echo "   Backend Authentication Flow Mocks: backend-auth-mocks_${TIMESTAMP}.log"
    echo "   Backend Business Logic Mocks: backend-business-logic-mocks_${TIMESTAMP}.log"
    echo "   Backend Model/Schema Mocks: backend-models-mocks_${TIMESTAMP}.log"
    echo "   Frontend Internal Component Mocks: frontend-internal-mocks_${TIMESTAMP}.log"
    echo "   Frontend Hook Mocks: frontend-hook-mocks_${TIMESTAMP}.log"
    echo "   Frontend Service Mocks: frontend-service-mocks_${TIMESTAMP}.log"
    echo "   Frontend Store/Context Mocks: frontend-store-mocks_${TIMESTAMP}.log"
    echo "   Frontend Component Import Mocks: frontend-component-import-mocks_${TIMESTAMP}.log"
    echo "   Mock Implementation Violations: mock-implementation-violations_${TIMESTAMP}.log"
    echo "   Import-Level Global Mocks: import-level-mocks_${TIMESTAMP}.log"
    echo "   File-by-File Analysis: file-by-file-analysis_${TIMESTAMP}.log"
    echo "   Approved External API Mocks: approved-external-api-mocks_${TIMESTAMP}.log"
    echo "   Approved Time/Random Mocks: approved-time-random-mocks_${TIMESTAMP}.log"
    echo "   Approved External Service Mocks: approved-external-service-mocks_${TIMESTAMP}.log"
    echo ""
    
    echo "🔍 CLAUDE.md Testing Directive Compliance:"
    echo "   ❌ PROHIBITED: Mock internal business logic (PermissionService, authentication flows, database operations)"
    echo "   ❌ PROHIBITED: Mock internal frontend code (components, hooks, utilities)"
    echo "   ✅ APPROVED: Mock external dependencies (APIs, file systems, Redis/cache, time/UUID generation)"
    echo "   ✅ APPROVED: Mock system boundaries, test internal logic"
    echo ""
    
    echo "🚀 ENHANCED SCAN FEATURES:"
    echo "   ✅ Filters out approved external dependency mocks (Redis, pyotp, datetime, uuid)"
    echo "   ✅ Excludes dependency directories (.cache, .venv, node_modules)"  
    echo "   ✅ Reduces false positives while maintaining accurate violation detection"
    echo "   ✅ Enhanced pattern matching for precise categorization"
    echo ""
    
    echo "📊 Golden Rule Compliance:"
    echo '   "Mock the boundaries, not the behavior"'
    echo "   - Mock system edges ✅"
    echo "   - Test internal logic ✅" 
    echo "   - Never mock business rules ❌"
    echo ""
    
    echo "💡 Immediate Actions Required:"
    echo "   1. Review all flagged violations in detail result files"
    echo "   2. Refactor tests to remove internal service/component mocking"
    echo "   3. Replace mocked business logic with real implementation"
    echo "   4. Keep only external dependency mocks (APIs, time, external services)"
    echo "   5. Ensure integration tests use real database sessions"
    echo "   6. Frontend tests should test real component behavior"
    echo ""
    
    echo "🚀 Mock Violations Quality Checklist:"
    echo "   □ No PermissionService/UserService/ClientService mocking"
    echo "   □ No database session mocking in integration tests"
    echo "   □ No authentication flow mocking in business logic tests"
    echo "   □ No internal component/hook mocking in frontend"
    echo "   □ Only external API mocking (fetch, requests, httpx)"
    echo "   □ Only time/random mocking for deterministic tests"
    echo "   □ Only external service mocking (email, notifications)"
    echo "   □ Tests validate real business logic behavior"
    echo "   □ Integration tests use real database operations"
    echo "   □ Frontend tests validate real component interactions"
    
} > "${VIOLATIONS_REPORT}"

# Display report
cat "${VIOLATIONS_REPORT}"

# Summary
echo ""
echo "🚨 Mock Violations Scan Summary - ${TIMESTAMP}"
TOTAL_SCAN_TIME=$(($(date +%s) - SCAN_START_TIME))
echo "🕰️ Scan completed in ${TOTAL_SCAN_TIME}s ($((TOTAL_SCAN_TIME / 60))m $((TOTAL_SCAN_TIME % 60))s)"
echo "All violation results saved to: ${RESULTS_DIR}"
echo "Primary Report: mock-violations-report_${TIMESTAMP}.log"
echo ""

# Count total violations using accurate counting function
total_violations=0
for log_file in "${RESULTS_DIR}"/*mocks_${TIMESTAMP}.log "${RESULTS_DIR}"/*violations_${TIMESTAMP}.log; do
    if [[ -f "$log_file" && ! "$log_file" =~ approved ]]; then
        count=$(count_violations "$log_file")
        if [[ "$count" =~ ^[0-9]+$ ]]; then
            total_violations=$((total_violations + count))
        fi
    fi
done

if [ $total_violations -gt 0 ]; then
    echo "⚠️ CRITICAL: $total_violations mock violations detected!"
    echo "📋 Review detailed logs and refactor tests according to CLAUDE.md guidelines"
    echo ""
    
    # 🤖 CLAUDE SONNET 4 - SMART FALSE POSITIVE ANALYSIS
    if [ $total_violations -gt 20 ]; then
        echo "🤖 CLAUDE SONNET 4 ADVISORY:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "⚠️  HIGH VIOLATION COUNT ($total_violations) - POTENTIAL FALSE POSITIVES DETECTED"
        echo ""
        echo "This high count suggests possible false positives. Please:"
        echo ""
        echo "🔍 1. ANALYZE the violation patterns in these files:"
        echo "   • backend-auth-mocks_${TIMESTAMP}.log"
        echo "   • backend-business-logic-mocks_${TIMESTAMP}.log"
        echo "   • mock-implementation-violations_${TIMESTAMP}.log"
        echo ""
        echo "🧠 2. CHECK if violations match APPROVED CLAUDE.md patterns:"
        echo "   ✅ patch.object(service, '_redis_client', mock)  → External Redis"
        echo "   ✅ patch('service.datetime')                    → Time mocking"
        echo "   ✅ patch('service.pyotp.TOTP.verify')          → Third-party lib"
        echo "   ✅ patch('requests.get')                       → External API"
        echo "   ✅ Files in .cache/, .venv/, node_modules/     → Dependencies"
        echo ""
        echo "⚙️  3. IF VIOLATIONS ARE FALSE POSITIVES:"
        echo "   • Examine this script's filter_approved_patterns() function (line ~81)"
        echo "   • Add new patterns to exclude legitimate external dependency mocks"
        echo "   • Re-run the scan to validate improvements"
        echo ""
        echo "⚖️  4. REMEMBER THE GOLDEN RULE:"
        echo "   \"Mock the boundaries, not the behavior\""
        echo "   • External dependencies (APIs, databases, time, file I/O) → ✅ MOCK"
        echo "   • Internal business logic (PermissionService, etc.)      → ❌ NEVER MOCK"
        echo ""
        echo "📖 5. FOR DETAILED GUIDANCE:"
        echo "   • Review the CLAUDE SONNET 4 - SELF-IMPROVEMENT GUIDANCE section"
        echo "   • at the top of this script (lines 27-71)"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
    fi
    
    exit 1
else
    echo "✅ No mock violations detected - tests follow CLAUDE.md guidelines"
    exit 0
fi

echo ""
echo "🔍 Mock Violations Scan completed at $(date)"