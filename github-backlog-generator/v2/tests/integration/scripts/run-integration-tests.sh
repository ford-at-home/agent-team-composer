#!/bin/bash
set -e

# GitHub Backlog Generator v2 Integration Test Runner
# Runs integration tests with proper setup and reporting

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$(dirname "$SCRIPT_DIR")"
RESULTS_DIR="${TEST_DIR}/test-results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Parse arguments
PHASE=""
VERBOSE=false
SPECIFIC_TEST=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --phase)
            PHASE="$2"
            shift 2
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --test)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --phase NUM     Run specific test phase (1-5)"
            echo "  --test NAME     Run specific test file or test name"
            echo "  --verbose, -v   Enable verbose output"
            echo "  --help, -h      Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

check_requirements() {
    log "Checking requirements..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        error "AWS CLI is required but not installed"
        exit 1
    fi
    
    # Check pytest
    if ! python3 -m pytest --version &> /dev/null; then
        warning "pytest not found, installing..."
        pip3 install pytest pytest-html pytest-json-report boto3 requests
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured or invalid"
        exit 1
    fi
    
    # Check environment variables
    if [ -z "$API_URL" ]; then
        warning "API_URL not set, using default"
        export API_URL="https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/prod"
    fi
    
    if [ -z "$API_KEY" ]; then
        error "API_KEY environment variable is required"
        exit 1
    fi
}

setup_test_environment() {
    log "Setting up test environment..."
    
    # Create results directory
    mkdir -p "$RESULTS_DIR/logs"
    mkdir -p "$RESULTS_DIR/reports"
    
    # Export test configuration
    export PYTHONPATH="${TEST_DIR}:${PYTHONPATH}"
    export TEST_RUN_ID="${TIMESTAMP}"
    export TEST_RESULTS_DIR="${RESULTS_DIR}"
    
    # Set test repository if not provided
    if [ -z "$TEST_REPO_URL" ]; then
        export TEST_REPO_URL="https://github.com/octocat/Hello-World"
    fi
    
    log "Test configuration:"
    log "  API_URL: $API_URL"
    log "  TEST_REPO_URL: $TEST_REPO_URL"
    log "  Results directory: $RESULTS_DIR"
}

run_phase_1_tests() {
    log "Running Phase 1: Infrastructure Tests"
    
    pytest "${TEST_DIR}/test_infrastructure.py" \
        --verbose \
        --junit-xml="${RESULTS_DIR}/reports/phase1_junit_${TIMESTAMP}.xml" \
        --html="${RESULTS_DIR}/reports/phase1_report_${TIMESTAMP}.html" \
        --self-contained-html \
        ${VERBOSE:+"-s"} \
        ${SPECIFIC_TEST:+"-k $SPECIFIC_TEST"} \
        2>&1 | tee "${RESULTS_DIR}/logs/phase1_${TIMESTAMP}.log"
    
    return ${PIPESTATUS[0]}
}

run_phase_2_tests() {
    log "Running Phase 2: Component Integration Tests"
    
    # Test Lambda functions
    log "Testing Lambda functions..."
    python3 "${SCRIPT_DIR}/test_lambda_functions.py" \
        2>&1 | tee "${RESULTS_DIR}/logs/phase2_lambda_${TIMESTAMP}.log"
    
    # Test ECS tasks
    log "Testing ECS task execution..."
    python3 "${SCRIPT_DIR}/test_ecs_tasks.py" \
        2>&1 | tee "${RESULTS_DIR}/logs/phase2_ecs_${TIMESTAMP}.log"
    
    return 0
}

run_phase_3_tests() {
    log "Running Phase 3: End-to-End Tests"
    
    pytest "${TEST_DIR}/test_end_to_end.py" \
        --verbose \
        --junit-xml="${RESULTS_DIR}/reports/phase3_junit_${TIMESTAMP}.xml" \
        --html="${RESULTS_DIR}/reports/phase3_report_${TIMESTAMP}.html" \
        --self-contained-html \
        ${VERBOSE:+"-s"} \
        ${SPECIFIC_TEST:+"-k $SPECIFIC_TEST"} \
        2>&1 | tee "${RESULTS_DIR}/logs/phase3_${TIMESTAMP}.log"
    
    return ${PIPESTATUS[0]}
}

run_phase_4_tests() {
    log "Running Phase 4: Frontend Integration Tests"
    
    # Check if frontend tests exist
    if [ -d "${TEST_DIR}/../../frontend/src" ]; then
        cd "${TEST_DIR}/../../frontend"
        
        # Run Jest tests
        npm test -- --ci --coverage --json --outputFile="${RESULTS_DIR}/reports/phase4_jest_${TIMESTAMP}.json" \
            2>&1 | tee "${RESULTS_DIR}/logs/phase4_${TIMESTAMP}.log"
        
        cd - > /dev/null
    else
        warning "Frontend tests not found, skipping Phase 4"
    fi
    
    return 0
}

run_phase_5_tests() {
    log "Running Phase 5: Security Tests"
    
    # Run security validation tests
    python3 "${SCRIPT_DIR}/test_security.py" \
        2>&1 | tee "${RESULTS_DIR}/logs/phase5_${TIMESTAMP}.log"
    
    return $?
}

run_all_tests() {
    local failed_phases=()
    
    # Run all phases
    for phase in 1 2 3 4 5; do
        log "Starting Phase $phase..."
        
        if run_phase_${phase}_tests; then
            log "Phase $phase completed successfully"
        else
            error "Phase $phase failed"
            failed_phases+=($phase)
        fi
        
        # Add delay between phases
        sleep 2
    done
    
    # Summary
    if [ ${#failed_phases[@]} -eq 0 ]; then
        log "All test phases completed successfully!"
        return 0
    else
        error "Failed phases: ${failed_phases[*]}"
        return 1
    fi
}

generate_summary_report() {
    log "Generating summary report..."
    
    local report_file="${RESULTS_DIR}/summary_${TIMESTAMP}.txt"
    
    cat > "$report_file" << EOF
GitHub Backlog Generator v2 Integration Test Summary
====================================================
Run ID: ${TEST_RUN_ID}
Date: $(date)
API URL: ${API_URL}
Test Repository: ${TEST_REPO_URL}

Test Results:
-------------
EOF
    
    # Parse test results
    for phase in 1 2 3 4 5; do
        local log_file="${RESULTS_DIR}/logs/phase${phase}_${TIMESTAMP}.log"
        if [ -f "$log_file" ]; then
            local passed=$(grep -c "PASSED" "$log_file" || echo "0")
            local failed=$(grep -c "FAILED" "$log_file" || echo "0")
            echo "Phase $phase: $passed passed, $failed failed" >> "$report_file"
        fi
    done
    
    echo "" >> "$report_file"
    echo "Log files available in: ${RESULTS_DIR}/logs/" >> "$report_file"
    echo "HTML reports available in: ${RESULTS_DIR}/reports/" >> "$report_file"
    
    cat "$report_file"
}

cleanup() {
    log "Cleaning up..."
    
    # Archive old results (keep last 10 runs)
    local old_results=$(ls -t "${RESULTS_DIR}"/summary_*.txt 2>/dev/null | tail -n +11)
    if [ -n "$old_results" ]; then
        log "Archiving old test results..."
        mkdir -p "${RESULTS_DIR}/archive"
        echo "$old_results" | while read -r file; do
            local basename=$(basename "$file" .txt)
            mv "${RESULTS_DIR}/logs/${basename}"* "${RESULTS_DIR}/archive/" 2>/dev/null || true
            mv "${RESULTS_DIR}/reports/${basename}"* "${RESULTS_DIR}/archive/" 2>/dev/null || true
            mv "$file" "${RESULTS_DIR}/archive/" 2>/dev/null || true
        done
    fi
}

# Main execution
main() {
    log "GitHub Backlog Generator v2 Integration Test Runner"
    log "=================================================="
    
    # Check requirements
    check_requirements
    
    # Setup environment
    setup_test_environment
    
    # Run tests
    local exit_code=0
    
    if [ -n "$PHASE" ]; then
        # Run specific phase
        log "Running only Phase $PHASE"
        if run_phase_${PHASE}_tests; then
            log "Phase $PHASE completed successfully"
        else
            error "Phase $PHASE failed"
            exit_code=1
        fi
    else
        # Run all tests
        if run_all_tests; then
            log "All tests completed successfully"
        else
            error "Some tests failed"
            exit_code=1
        fi
    fi
    
    # Generate summary
    generate_summary_report
    
    # Cleanup
    cleanup
    
    log "Test run complete. Exit code: $exit_code"
    exit $exit_code
}

# Run main function
main