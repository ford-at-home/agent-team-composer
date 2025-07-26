#!/bin/bash

# GitHub Backlog Orchestrator with LLM Cost Tracking
# A shell script that generates phases for a repo and populates epics and issues 
# with timing and LLM cost tracking for each step.

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
TIMING_LOG=""
COST_LOG=""
TOTAL_START_TIME=""
TOTAL_COST=0

# Anthropic Claude API Pricing (as of 2024)
# Prices per 1,000 tokens
declare -A MODEL_PRICING
MODEL_PRICING["claude-3-5-sonnet-20241022_input"]=0.003
MODEL_PRICING["claude-3-5-sonnet-20241022_output"]=0.015
MODEL_PRICING["claude-3-5-haiku-20241022_input"]=0.0008
MODEL_PRICING["claude-3-5-haiku-20241022_output"]=0.004
MODEL_PRICING["claude-sonnet-4-20250514_input"]=0.003
MODEL_PRICING["claude-sonnet-4-20250514_output"]=0.015

# Default model (can be overridden by GITHUB_BACKLOG_MODEL env var)
DEFAULT_MODEL="claude-3-5-sonnet-20241022"

# Token estimation patterns for different operations
declare -A ESTIMATED_TOKENS
ESTIMATED_TOKENS["readme_analysis"]=2500
ESTIMATED_TOKENS["phase_generation"]=8000
ESTIMATED_TOKENS["epic_generation"]=6000
ESTIMATED_TOKENS["task_generation"]=4000
ESTIMATED_TOKENS["task_description"]=3000

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to get current model from environment or default
get_current_model() {
    echo "${GITHUB_BACKLOG_MODEL:-$DEFAULT_MODEL}"
}

# Function to estimate cost for a given operation
estimate_cost() {
    local operation_type="$1"
    local model=$(get_current_model)
    
    # Get estimated token usage for this operation
    local estimated_tokens=${ESTIMATED_TOKENS[$operation_type]:-1000}
    
    # Estimate 70% input tokens, 30% output tokens (typical for generation tasks)
    local input_tokens=$((estimated_tokens * 70 / 100))
    local output_tokens=$((estimated_tokens * 30 / 100))
    
    # Calculate costs (convert to cost per 1000 tokens)
    local input_cost_per_1k=${MODEL_PRICING[${model}_input]:-0.003}
    local output_cost_per_1k=${MODEL_PRICING[${model}_output]:-0.015}
    
    local input_cost=$(echo "scale=6; $input_tokens * $input_cost_per_1k / 1000" | bc -l)
    local output_cost=$(echo "scale=6; $output_tokens * $output_cost_per_1k / 1000" | bc -l)
    local total_cost=$(echo "scale=6; $input_cost + $output_cost" | bc -l)
    
    echo "$total_cost"
}

# Function to log cost information
log_cost() {
    local step_name="$1"
    local operation_type="$2"
    local estimated_cost=$(estimate_cost "$operation_type")
    
    # Add to total cost
    TOTAL_COST=$(echo "scale=6; $TOTAL_COST + $estimated_cost" | bc -l)
    
    # Log to cost file
    echo "[$step_name] Estimated Cost: \$$estimated_cost (Operation: $operation_type)" >> "$COST_LOG"
    
    if [[ "$VERBOSE" == true ]]; then
        print_color $YELLOW "💰 $step_name estimated cost: \$$estimated_cost"
    fi
}

# Function to log timing and cost information
log_timing_and_cost() {
    local step_name="$1"
    local start_time="$2"
    local end_time="$3"
    local operation_type="$4"
    local duration=$((end_time - start_time))
    local formatted_duration=$(format_duration $duration)
    
    # Log timing
    echo "[$step_name] Duration: $formatted_duration" >> "$TIMING_LOG"
    
    # Log cost
    log_cost "$step_name" "$operation_type"
    
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

# Function to format cost in human-readable format
format_cost() {
    local cost="$1"
    printf "%.4f" "$cost"
}

# Function to display usage information
usage() {
    cat << EOF
GitHub Backlog Orchestrator with LLM Cost Tracking v1.1

USAGE:
    $0 [OPTIONS] REPO_URL

DESCRIPTION:
    Generates phases for a GitHub repository and populates epics and issues 
    for those phases with comprehensive timing and LLM cost tracking.

ARGUMENTS:
    REPO_URL    GitHub repository URL (e.g., https://github.com/owner/repo)

OPTIONS:
    -d, --dry-run           Generate without creating GitHub items
    -v, --verbose           Enable verbose output with timing and cost details
    -h, --help             Show this help message
    --phases RANGE         Specify phase range (e.g., 1-3 or 1,3,5)
    --epics-only           Only generate epics, skip issues
    --timing-log FILE      Custom timing log file
    --cost-log FILE        Custom cost log file
    --show-pricing         Display current API pricing information

EXAMPLES:
    # Basic usage - generate everything with cost tracking
    $0 https://github.com/owner/repo

    # Dry run with verbose timing and cost output
    $0 --dry-run --verbose https://github.com/owner/repo

    # Generate only phases 1-3 with custom cost log
    $0 --phases 1-3 --cost-log my-costs.log https://github.com/owner/repo

    # Show current API pricing
    $0 --show-pricing

WORKFLOW:
    1. Initialize project and analyze README (~\$0.02)
    2. Create GitHub milestones for all phases (free)
    3. Generate epics for each phase (~\$0.04 per phase)
    4. Generate issues for all epics (~\$0.05 per epic)
    5. Display comprehensive timing and cost report

COST ESTIMATION:
    - Small Project (1-20 features): \$0.50 - \$2.00
    - Medium Project (21-50 features): \$2.00 - \$8.00
    - Large Project (50+ features): \$8.00 - \$20.00

REQUIREMENTS:
    - github-backlog CLI tool installed
    - ANTHROPIC_API_KEY environment variable set
    - GITHUB_TOKEN environment variable set
    - bc command for cost calculations
    - Internet connection for API calls

EOF
}

# Function to display pricing information
show_pricing() {
    local current_model=$(get_current_model)
    
    print_color $PURPLE "\n💰 ANTHROPIC CLAUDE API PRICING (2024)"
    print_color $PURPLE "========================================"
    
    echo -e "\n${CYAN}Current Model: $current_model${NC}\n"
    
    echo "Model                           Input (per 1K tokens)    Output (per 1K tokens)"
    echo "--------------------------------------------------------------------------"
    echo "claude-3-5-sonnet-20241022     \$0.003                   \$0.015"
    echo "claude-3-5-haiku-20241022      \$0.0008                  \$0.004"
    echo "claude-sonnet-4-20250514       \$0.003                   \$0.015"
    
    echo -e "\n${YELLOW}Token Estimation Guidelines:${NC}"
    echo "• 1 token ≈ 4 characters or 0.75 words in English"
    echo "• README Analysis: ~2,500 tokens"
    echo "• Phase Generation: ~8,000 tokens"
    echo "• Epic Generation: ~6,000 tokens per phase"
    echo "• Task Generation: ~4,000 tokens per epic"
    echo "• Task Description: ~3,000 tokens per task"
    
    echo -e "\n${GREEN}Cost-Saving Tips:${NC}"
    echo "• Use claude-3-5-haiku for simpler tasks (75% cheaper)"
    echo "• Consider batch processing for large projects"
    echo "• Use --dry-run to test without API costs"
    echo "• Enable prompt caching for up to 90% savings on repeated content"
    
    exit 0
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
    
    # Check for bc command (needed for cost calculations)
    if ! command -v bc &> /dev/null; then
        print_color $RED "❌ Error: bc command not found!"
        print_color $YELLOW "Please install bc: sudo apt-get install bc"
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
    log_timing_and_cost "Prerequisites Validation" $step_start $step_end "readme_analysis"
}

# Function to initialize project
initialize_project() {
    local step_start=$(date +%s)
    print_color $BLUE "🚀 Initializing project and analyzing README..."
    
    local cmd="github-backlog init"
    if [[ "$DRY_RUN" == true ]]; then
        cmd="$cmd --dry-run"
    fi
    cmd="$cmd $REPO_URL"
    
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
    log_timing_and_cost "Project Initialization" $step_start $step_end "readme_analysis"
}

# Function to create milestones
create_milestones() {
    local step_start=$(date +%s)
    print_color $BLUE "🎯 Creating GitHub milestones for all phases..."
    
    local cmd="github-backlog milestones"
    if [[ "$DRY_RUN" == true ]]; then
        cmd="$cmd --dry-run"
    fi
    cmd="$cmd $REPO_URL"
    
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
    # Milestone creation doesn't use LLM, so no cost
    echo "[$step_name] Duration: $(format_duration $((step_end - step_start)))" >> "$TIMING_LOG"
    echo "[Milestone Creation] Estimated Cost: \$0.000 (No LLM usage)" >> "$COST_LOG"
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
    
    local cmd="github-backlog generate"
    if [[ "$DRY_RUN" == true ]]; then
        cmd="$cmd --dry-run"
    fi
    cmd="$cmd $REPO_URL --phase $phase_num"
    
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
    log_timing_and_cost "Phase $phase_num Epic Generation" $step_start $step_end "epic_generation"
}

# Function to generate issues for all epics in a phase
generate_issues_for_phase() {
    local phase_num=$1
    local step_start=$(date +%s)
    print_color $BLUE "📝 Generating issues for all epics in Phase $phase_num..."
    
    local cmd="github-backlog generate"
    if [[ "$DRY_RUN" == true ]]; then
        cmd="$cmd --dry-run"
    fi
    cmd="$cmd $REPO_URL --phase $phase_num --all-epics"
    
    if [[ "$VERBOSE" == true ]]; then
        print_color $CYAN "Executing: $cmd"
    fi
    
    if eval "$cmd"; then
        print_color $GREEN "✅ Issues generated for all epics in Phase $phase_num"
        
        # Estimate number of epics and tasks for cost calculation
        # This is an approximation - in reality we'd parse the actual output
        local estimated_epics=6  # Average epics per phase
        local estimated_tasks_per_epic=5  # Average tasks per epic
        local total_task_operations=$((estimated_epics * estimated_tasks_per_epic))
        
        # Log additional cost for task descriptions
        for ((i=1; i<=total_task_operations; i++)); do
            log_cost "Phase $phase_num Task $i Description" "task_description"
        done
        
    else
        print_color $RED "❌ Issue generation failed for Phase $phase_num"
        return 1
    fi
    
    local step_end=$(date +%s)
    log_timing_and_cost "Phase $phase_num Issue Generation" $step_start $step_end "task_generation"
}

# Function to display final status
display_final_status() {
    local step_start=$(date +%s)
    print_color $BLUE "📊 Displaying final project status..."
    
    github-backlog status "$REPO_URL"
    
    local step_end=$(date +%s)
    # Status display doesn't use LLM
    echo "[Status Display] Duration: $(format_duration $((step_end - step_start)))" >> "$TIMING_LOG"
    echo "[Status Display] Estimated Cost: \$0.000 (No LLM usage)" >> "$COST_LOG"
}

# Function to generate comprehensive timing and cost report
generate_report() {
    local total_end_time=$(date +%s)
    local total_duration=$((total_end_time - TOTAL_START_TIME))
    local formatted_total_duration=$(format_duration $total_duration)
    local formatted_total_cost=$(format_cost $TOTAL_COST)
    
    print_color $PURPLE "\n🕒 TIMING & COST REPORT"
    print_color $PURPLE "======================="
    
    if [[ -f "$TIMING_LOG" ]] && [[ -f "$COST_LOG" ]]; then
        # Combine timing and cost information
        while IFS= read -r timing_line; do
            local step_name=$(echo "$timing_line" | sed 's/\[//g' | sed 's/\].*//g')
            local cost_line=$(grep "\\[$step_name\\]" "$COST_LOG" 2>/dev/null || echo "")
            
            echo "$timing_line"
            if [[ -n "$cost_line" ]]; then
                echo "$cost_line"
            fi
            echo ""
        done < "$TIMING_LOG"
    fi
    
    print_color $PURPLE "======================="
    echo -e "${PURPLE}TOTAL EXECUTION TIME: $formatted_total_duration${NC}"
    echo -e "${YELLOW}TOTAL ESTIMATED COST: \$$formatted_total_cost${NC}"
    print_color $PURPLE "Timing log saved to: $TIMING_LOG"
    print_color $PURPLE "Cost log saved to: $COST_LOG"
    
    # Add summary to logs
    echo "" >> "$TIMING_LOG"
    echo "======================" >> "$TIMING_LOG"
    echo "TOTAL EXECUTION TIME: $formatted_total_duration" >> "$TIMING_LOG"
    echo "Completed at: $(date)" >> "$TIMING_LOG"
    
    echo "" >> "$COST_LOG"
    echo "======================" >> "$COST_LOG"
    echo "TOTAL ESTIMATED COST: \$$formatted_total_cost" >> "$COST_LOG"
    echo "Model Used: $(get_current_model)" >> "$COST_LOG"
    echo "Completed at: $(date)" >> "$COST_LOG"
    
    # Cost breakdown by operation type
    print_color $YELLOW "\n💰 COST BREAKDOWN BY OPERATION"
    print_color $YELLOW "==============================="
    echo "README Analysis: ~\$0.01-0.02"
    echo "Phase Generation: ~\$0.02-0.05 per phase"
    echo "Epic Generation: ~\$0.03-0.06 per phase"
    echo "Task Generation: ~\$0.02-0.04 per epic"
    echo "Task Descriptions: ~\$0.01-0.02 per task"
    
    if [[ $(echo "$TOTAL_COST > 5.0" | bc -l) -eq 1 ]]; then
        print_color $YELLOW "\n💡 Cost Optimization Tips:"
        print_color $YELLOW "- Consider using claude-3-5-haiku for simpler operations"
        print_color $YELLOW "- Use --phases flag to generate incrementally"
        print_color $YELLOW "- Use --epics-only for initial planning phase"
    fi
}

# Function to cleanup on exit
cleanup() {
    if [[ $? -ne 0 ]]; then
        print_color $RED "\n❌ Script execution failed"
        if [[ -f "$TIMING_LOG" ]]; then
            print_color $YELLOW "Partial timing log available at: $TIMING_LOG"
        fi
        if [[ -f "$COST_LOG" ]]; then
            print_color $YELLOW "Partial cost log available at: $COST_LOG"
        fi
    fi
}

# Main execution function
main() {
    # Set up timing and cost logs
    local timestamp=$(date +"%Y%m%d-%H%M%S")
    TIMING_LOG="${TIMING_LOG:-timing-$timestamp.log}"
    COST_LOG="${COST_LOG:-costs-$timestamp.log}"
    TOTAL_START_TIME=$(date +%s)
    
    # Initialize logs
    echo "GitHub Backlog Orchestrator - Timing Log" > "$TIMING_LOG"
    echo "Started at: $(date)" >> "$TIMING_LOG"
    echo "Repository: $REPO_URL" >> "$TIMING_LOG"
    echo "Dry Run: $DRY_RUN" >> "$TIMING_LOG"
    echo "Model: $(get_current_model)" >> "$TIMING_LOG"
    echo "========================================" >> "$TIMING_LOG"
    
    echo "GitHub Backlog Orchestrator - Cost Log" > "$COST_LOG"
    echo "Started at: $(date)" >> "$COST_LOG"
    echo "Repository: $REPO_URL" >> "$COST_LOG"
    echo "Model: $(get_current_model)" >> "$COST_LOG"
    echo "Dry Run: $DRY_RUN" >> "$COST_LOG"
    echo "=======================================" >> "$COST_LOG"
    
    print_color $PURPLE "🎼 GitHub Backlog Orchestrator with Cost Tracking v1.1"
    print_color $PURPLE "Generating comprehensive project backlog with timing and cost analysis..."
    print_color $CYAN "Repository: $REPO_URL"
    print_color $CYAN "Model: $(get_current_model)"
    print_color $CYAN "Dry Run: $DRY_RUN"
    print_color $CYAN "Timing Log: $TIMING_LOG"
    print_color $CYAN "Cost Log: $COST_LOG"
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
    generate_report
    
    print_color $GREEN "\n🎉 GitHub Backlog Orchestration completed successfully!"
    print_color $CYAN "Total phases processed: ${#phases_to_process[@]}"
    print_color $YELLOW "Total estimated cost: \$$(format_cost $TOTAL_COST)"
    print_color $CYAN "Reports: $TIMING_LOG, $COST_LOG"
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
        -h|--help)
            usage
            exit 0
            ;;
        --show-pricing)
            show_pricing
            ;;
        --phases)
            PHASE_RANGE="$2"
            shift 2
            ;;
        --epics-only)
            EPICS_ONLY=true
            shift
            ;;
        --timing-log)
            TIMING_LOG="$2"
            shift 2
            ;;
        --cost-log)
            COST_LOG="$2"
            shift 2
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

# Handle --show-pricing without repo URL
if [[ "$1" == "--show-pricing" ]] 2>/dev/null; then
    show_pricing
fi

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