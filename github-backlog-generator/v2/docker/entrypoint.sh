#!/bin/bash
set -e

# Function to log with timestamp
log() {
    if [ "$LOG_FORMAT" = "json" ]; then
        echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)\",\"level\":\"INFO\",\"message\":\"$1\"}"
    else
        echo "[$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)] $1"
    fi
}

# Log startup information
log "Starting GitHub Backlog Generator v2"
log "Task ID: ${TASK_ID:-unknown}"
log "Repository: ${REPO_URL:-not set}"
log "Phase: ${PHASE:-not set}"
log "Log Format: ${LOG_FORMAT:-text}"

# Validate required environment variables
if [ -z "$REPO_URL" ]; then
    log "ERROR: REPO_URL environment variable is required"
    exit 1
fi

if [ -z "$PHASE" ]; then
    log "ERROR: PHASE environment variable is required"
    exit 1
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    log "ERROR: ANTHROPIC_API_KEY is not set"
    exit 1
fi

if [ -z "$GITHUB_TOKEN" ]; then
    log "ERROR: GITHUB_TOKEN is not set"
    exit 1
fi

# Log configuration
log "Configuration validated successfully"
log "=========================================="

# Run the GitHub Backlog Generator
# The tool expects the phase as a CLI argument
log "Executing: github-backlog generate \"$REPO_URL\" --phase $PHASE"

# Execute the command and capture output
if [ "$LOG_FORMAT" = "json" ]; then
    # For JSON logging, we need to capture and format the output
    github-backlog generate "$REPO_URL" --phase "$PHASE" 2>&1 | while IFS= read -r line; do
        # Escape quotes in the message
        escaped_line=$(echo "$line" | sed 's/"/\\"/g')
        echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)\",\"level\":\"INFO\",\"source\":\"github-backlog\",\"message\":\"$escaped_line\"}"
    done
else
    # For text logging, just pass through
    github-backlog generate "$REPO_URL" --phase "$PHASE"
fi

# Capture exit code
EXIT_CODE=$?

# Log completion
if [ $EXIT_CODE -eq 0 ]; then
    log "=========================================="
    log "Task completed successfully"
    log "Exit code: $EXIT_CODE"
else
    log "=========================================="
    log "Task failed with exit code: $EXIT_CODE"
fi

exit $EXIT_CODE