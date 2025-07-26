#!/bin/bash

# GitHub Backlog Orchestrator
# A shell script that generates phases for a repo and populates epics and issues 
# with native CLI cost and timing tracking.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Global variables
REPO_URL=""
DRY_RUN=false
VERBOSE=false
ENABLE_COST_TRACKING=false
ENABLE_TIME_TRACKING=false
TOTAL_START_TIME=""

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to build CLI command with tracking flags
build_cli_command() {
    local base_cmd="$1"
    local cmd="$base_cmd"
    
    # Add cost tracking flag if enabled
    if [[ "$ENABLE_COST_TRACKING" == true ]]; then
        cmd="github-backlog --cost $cmd"
    elif [[ "$ENABLE_TIME_TRACKING" == true ]]; then
        cmd="github-backlog --time $cmd"
    else
        cmd="github-backlog $cmd"
    fi
    
    echo "$cmd"
}

# Function to log simple timing for orchestrator-level operations
log_timing() {
    local step_name="$1"
    local start_time="$2"
    local end_time="$3"
    local duration=$((end_time - start_time))
    local formatted_duration=$(format_duration $duration)
    
    if [[ "$VERBOSE" == true ]]; then
        print_color $CYAN "⏱️  $step_name completed in $formatted_duration"
    fi
}

# Function to format duration in human-readable format
format_duration() {
    local duration=$1
    local hours=$((duration / 3600))
    local minutes=$(((duration % 3600) / 60))
    local seconds=$((duration % 60))
    
    if [[ $hours -gt 0 ]]; then
        echo "${hours}h ${minutes}m ${seconds}s"
    elif [[ $minutes -gt 0 ]]; then
        echo "${minutes}m ${seconds}s"
    else
        echo "${seconds}s"
    fi
}

# Function to display usage information
usage() {
    cat << EOF
GitHub Backlog Orchestrator v1.0

USAGE:
    $0 [OPTIONS] REPO_URL

DESCRIPTION:
    Generates phases for a GitHub repository and populates epics and issues 
    for those phases using the enhanced CLI with native cost and timing tracking.

ARGUMENTS:
    REPO_URL    GitHub repository URL (e.g., https://github.com/owner/repo)

OPTIONS:
    -d, --dry-run           Generate without creating GitHub items
    -v, --verbose           Enable verbose output with operation details
    -c, --cost             Enable cost tracking via CLI --cost flag
    -t, --time             Enable timing tracking via CLI --time flag
    -h, --help             Show this help message
    --phases RANGE         Specify phase range (e.g., 1-3 or 1,3,5)
    --epics-only           Only generate epics, skip issues

EXAMPLES:
    # Basic usage - generate everything
    $0 https://github.com/owner/repo

    # With cost tracking
    $0 --cost https://github.com/owner/repo

    # With timing tracking and verbose output
    $0 --time --verbose https://github.com/owner/repo

    # Generate only phases 1-3 with cost tracking
    $0 --cost --phases 1-3 https://github.com/owner/repo

    # Generate epics only with timing
    $0 --time --epics-only https://github.com/owner/repo

WORKFLOW:
    1. Initialize project and analyze README (with optional cost/time tracking)
    2. Create GitHub milestones for all phases
    3. Generate epics for each phase (with CLI tracking)
    4. Generate issues for all epics (with CLI tracking)
    5. Display final status (with historical cost/timing data)

REQUIREMENTS:
    - github-backlog CLI tool installed
    - ANTHROPIC_API_KEY environment variable set
    - GITHUB_TOKEN environment variable set
    - Internet connection for API calls

EOF
}

# Function to validate prerequisites
validate_prerequisites() {
    local step_start=$(date +%s)
    print_color $BLUE "🔍 Validating prerequisites..."
    
    # Check if github-backlog command exists
    if ! command -v github-backlog &> /dev/null; then
        print_color $RED "❌ Error: github-backlog command not found!"
        print_color $YELLOW "Please install the github-backlog-generator package first."
        exit 1
    fi
    
    # Check for required environment variables
    if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
        print_color $RED "❌ Error: ANTHROPIC_API_KEY environment variable not set!"
        print_color $YELLOW "Please set your Anthropic API key: export ANTHROPIC_API_KEY=your_key"
        exit 1
    fi
    
    if [[ -z "${GITHUB_TOKEN:-}" ]]; then
        print_color $RED "❌ Error: GITHUB_TOKEN environment variable not set!"
        print_color $YELLOW "Please set your GitHub token: export GITHUB_TOKEN=your_token"
        exit 1
    fi
    
    print_color $GREEN "✅ Prerequisites validated"
    local step_end=$(date +%s)
    log_timing "Prerequisites Validation" $step_start $step_end
}

# Function to initialize project
initialize_project() {
    local step_start=$(date +%s)
    print_color $BLUE "🚀 Initializing project and analyzing README..."
    
    local base_cmd="init"
    if [[ "$DRY_RUN" == true ]]; then
        base_cmd="$base_cmd --dry-run"
    fi
    base_cmd="$base_cmd $REPO_URL"
    
    local cmd=$(build_cli_command "$base_cmd")
    
    if [[ "$VERBOSE" == true ]]; then
        print_color $CYAN "Executing: $cmd"
    fi
    
    if eval "$cmd"; then
        print_color $GREEN "✅ Project initialized successfully"
    else
        print_color $RED "❌ Project initialization failed"
        exit 1
    fi
    
    local step_end=$(date +%s)
    log_timing "Project Initialization" $step_start $step_end
}

# Function to create milestones
create_milestones() {
    local step_start=$(date +%s)
    print_color $BLUE "🎯 Creating GitHub milestones for all phases..."
    
    local base_cmd="milestones"
    if [[ "$DRY_RUN" == true ]]; then
        base_cmd="$base_cmd --dry-run"
    fi
    base_cmd="$base_cmd $REPO_URL"
    
    local cmd=$(build_cli_command "$base_cmd")
    
    if [[ "$VERBOSE" == true ]]; then
        print_color $CYAN "Executing: $cmd"
    fi
    
    if eval "$cmd"; then
        print_color $GREEN "✅ Milestones created successfully"
    else
        print_color $RED "❌ Milestone creation failed"
        exit 1
    fi
    
    local step_end=$(date +%s)
    log_timing "Milestone Creation" $step_start $step_end
}

# Function to get phase count
get_phase_count() {
    # Try to determine phase count from status command
    local status_output=$(github-backlog status "$REPO_URL" 2>/dev/null | grep -E "Phase [0-9]+" | wc -l)
    if [[ $status_output -gt 0 ]]; then
        echo $status_output
    else
        # Default to 8 phases if we can't determine
        echo 8
    fi
}

# Function to parse phase range specification
parse_phase_range() {
    local range_spec="$1"
    local phase_count="$2"
    local phases=()
    
    if [[ "$range_spec" == *"-"* ]]; then
        # Range format (e.g., 1-3)
        local start=$(echo "$range_spec" | cut -d'-' -f1)
        local end=$(echo "$range_spec" | cut -d'-' -f2)
        for ((i=start; i<=end && i<=phase_count; i++)); do
            phases+=($i)
        done
    elif [[ "$range_spec" == *","* ]]; then
        # Comma-separated format (e.g., 1,3,5)
        IFS=',' read -ra PHASE_ARRAY <<< "$range_spec"
        for phase in "${PHASE_ARRAY[@]}"; do
            if [[ $phase -le $phase_count ]]; then
                phases+=($phase)
            fi
        done
    elif [[ "$range_spec" =~ ^[0-9]+$ ]]; then
        # Single phase
        if [[ $range_spec -le $phase_count ]]; then
            phases+=($range_spec)
        fi
    else
        print_color $RED "❌ Invalid phase range format: $range_spec"
        exit 1
    fi
    
    echo "${phases[@]}"
}

# Function to generate epics for a phase
generate_epics_for_phase() {
    local phase_num=$1
    local step_start=$(date +%s)
    print_color $BLUE "📋 Generating epics for Phase $phase_num..."
    
    local base_cmd="generate"
    if [[ "$DRY_RUN" == true ]]; then
        base_cmd="$base_cmd --dry-run"
    fi
    base_cmd="$base_cmd $REPO_URL --phase $phase_num"
    
    local cmd=$(build_cli_command "$base_cmd")
    
    if [[ "$VERBOSE" == true ]]; then
        print_color $CYAN "Executing: $cmd"
    fi
    
    if eval "$cmd"; then
        print_color $GREEN "✅ Epics generated for Phase $phase_num"
    else
        print_color $RED "❌ Epic generation failed for Phase $phase_num"
        return 1
    fi
    
    local step_end=$(date +%s)
    log_timing "Phase $phase_num Epic Generation" $step_start $step_end
}

# Function to generate issues for all epics in a phase
generate_issues_for_phase() {
    local phase_num=$1
    local step_start=$(date +%s)
    print_color $BLUE "📝 Generating issues for all epics in Phase $phase_num..."
    
    local base_cmd="generate"
    if [[ "$DRY_RUN" == true ]]; then
        base_cmd="$base_cmd --dry-run"
    fi
    base_cmd="$base_cmd $REPO_URL --phase $phase_num --all-epics"
    
    local cmd=$(build_cli_command "$base_cmd")
    
    if [[ "$VERBOSE" == true ]]; then
        print_color $CYAN "Executing: $cmd"
    fi
    
    if eval "$cmd"; then
        print_color $GREEN "✅ Issues generated for all epics in Phase $phase_num"
    else
        print_color $RED "❌ Issue generation failed for Phase $phase_num"
        return 1
    fi
    
    local step_end=$(date +%s)
    log_timing "Phase $phase_num Issue Generation" $step_start $step_end
}

# Function to display final status
display_final_status() {
    local step_start=$(date +%s)
    print_color $BLUE "📊 Displaying final project status..."
    
    local cmd=$(build_cli_command "status $REPO_URL")
    
    if [[ "$VERBOSE" == true ]]; then
        print_color $CYAN "Executing: $cmd"
    fi
    
    eval "$cmd"
    
    local step_end=$(date +%s)
    log_timing "Status Display" $step_start $step_end
}

# Function to generate orchestrator summary report
generate_summary_report() {
    local total_end_time=$(date +%s)
    local total_duration=$((total_end_time - TOTAL_START_TIME))
    local formatted_total_duration=$(format_duration $total_duration)
    
    print_color $PURPLE "\n🎼 ORCHESTRATOR SUMMARY"
    print_color $PURPLE "======================="
    
    echo -e "${PURPLE}TOTAL ORCHESTRATION TIME: $formatted_total_duration${NC}"
    
    if [[ "$ENABLE_COST_TRACKING" == true ]]; then
        print_color $YELLOW "💰 Detailed cost information available in CLI output above"
        print_color $YELLOW "Cost data saved to: .backlog-*/cost_tracking.json"
    fi
    
    if [[ "$ENABLE_TIME_TRACKING" == true ]]; then
        print_color $CYAN "⏱️  Detailed timing information available in CLI output above"
    fi
    
    print_color $PURPLE "Orchestration completed at: $(date)"
}

# Function to cleanup on exit
cleanup() {
    if [[ $? -ne 0 ]]; then
        print_color $RED "\n❌ Orchestrator execution failed"
        if [[ "$ENABLE_COST_TRACKING" == true ]] || [[ "$ENABLE_TIME_TRACKING" == true ]]; then
            print_color $YELLOW "Partial cost/timing data may be available in .backlog-*/ directory"
        fi
    fi
}

# Main execution function
main() {
    TOTAL_START_TIME=$(date +%s)
    
    print_color $PURPLE "🎼 GitHub Backlog Orchestrator v2.0"
    print_color $PURPLE "Generating comprehensive project backlog with native CLI tracking..."
    print_color $CYAN "Repository: $REPO_URL"
    print_color $CYAN "Dry Run: $DRY_RUN"
    print_color $CYAN "Cost Tracking: $ENABLE_COST_TRACKING"
    print_color $CYAN "Time Tracking: $ENABLE_TIME_TRACKING"
    echo ""
    
    # Execute workflow steps
    validate_prerequisites
    initialize_project
    
    if [[ "$DRY_RUN" == false ]]; then
        create_milestones
    else
        print_color $YELLOW "⏭️  Skipping milestone creation (dry run)"
    fi
    
    # Determine which phases to process
    local phase_count=$(get_phase_count)
    local phases_to_process=()
    
    if [[ -n "${PHASE_RANGE:-}" ]]; then
        IFS=' ' read -ra phases_to_process <<< "$(parse_phase_range "$PHASE_RANGE" $phase_count)"
        print_color $CYAN "Processing specified phases: ${phases_to_process[*]}"
    else
        for ((i=1; i<=phase_count; i++)); do
            phases_to_process+=($i)
        done
        print_color $CYAN "Processing all $phase_count phases"
    fi
    
    # Generate epics and issues for each phase
    for phase in "${phases_to_process[@]}"; do
        generate_epics_for_phase $phase
        
        if [[ "${EPICS_ONLY:-false}" != true ]]; then
            generate_issues_for_phase $phase
        else
            print_color $YELLOW "⏭️  Skipping issue generation for Phase $phase (epics-only mode)"
        fi
    done
    
    display_final_status
    generate_summary_report
    
    print_color $GREEN "\n🎉 GitHub Backlog Orchestration completed successfully!"
    print_color $CYAN "Total phases processed: ${#phases_to_process[@]}"
    
    if [[ "$ENABLE_COST_TRACKING" == true ]] || [[ "$ENABLE_TIME_TRACKING" == true ]]; then
        print_color $CYAN "Detailed tracking data available in .backlog-*/ directory"
    fi
}

# Parse command line arguments
PHASE_RANGE=""
EPICS_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -c|--cost)
            ENABLE_COST_TRACKING=true
            shift
            ;;
        -t|--time)
            ENABLE_TIME_TRACKING=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --phases)
            PHASE_RANGE="$2"
            shift 2
            ;;
        --epics-only)
            EPICS_ONLY=true
            shift
            ;;
        -*)
            print_color $RED "Unknown option: $1"
            usage
            exit 1
            ;;
        *)
            if [[ -z "$REPO_URL" ]]; then
                REPO_URL="$1"
            else
                print_color $RED "Multiple repository URLs specified"
                usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate required arguments
if [[ -z "$REPO_URL" ]]; then
    print_color $RED "Error: Repository URL is required"
    usage
    exit 1
fi

# Set up cleanup trap
trap cleanup EXIT

# Execute main function
main "$@"