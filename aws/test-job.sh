#!/bin/bash

# Test script for MVP Backlog Batch Stack
# Usage: ./test-job.sh --profile personal

set -e

AWS_PROFILE="mvp"
REGION="us-east-1"
JOB_NAME="test-mvp-$(date +%s)"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --profile)
            AWS_PROFILE="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --job-name)
            JOB_NAME="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "🧪 Testing MVP Backlog Batch Stack"
echo "Profile: $AWS_PROFILE"
echo "Region: $REGION"
echo "Job Name: $JOB_NAME"

# Check if required resources exist
echo "🔍 Checking AWS Batch resources..."

# Get job queue
JOB_QUEUE=$(aws batch describe-job-queues --query 'jobQueues[?jobQueueName==`MVPBacklogQueue`].jobQueueArn' --output text --profile "$AWS_PROFILE" --region "$REGION")
if [ -z "$JOB_QUEUE" ]; then
    echo "❌ Job queue 'MVPBacklogQueue' not found. Make sure the stack is deployed."
    exit 1
fi
echo "✅ Found job queue: $JOB_QUEUE"

# Get job definition
JOB_DEF=$(aws batch describe-job-definitions --job-definition-name MVPBacklogJob --status ACTIVE --query 'jobDefinitions[0].jobDefinitionArn' --output text --profile "$AWS_PROFILE" --region "$REGION")
if [ -z "$JOB_DEF" ]; then
    echo "❌ Job definition 'MVPBacklogJob' not found. Make sure the stack is deployed."
    exit 1
fi
echo "✅ Found job definition: $JOB_DEF"

# Secrets are pre-configured in the MVP account
echo "✅ Using existing secrets in MVP account"

# Submit test job
echo "🚀 Submitting test job..."
JOB_ID=$(aws batch submit-job \
    --job-name "$JOB_NAME" \
    --job-queue "MVPBacklogQueue" \
    --job-definition "MVPBacklogJob" \
    --parameters phases=test-phases.json,repo=test/repo \
    --query 'jobId' \
    --output text \
    --profile "$AWS_PROFILE" \
    --region "$REGION")

echo "✅ Job submitted successfully!"
echo "Job ID: $JOB_ID"
echo "Job Name: $JOB_NAME"

# Monitor job status
echo "👀 Monitoring job status..."
while true; do
    JOB_STATUS=$(aws batch describe-jobs --jobs "$JOB_ID" --query 'jobs[0].status' --output text --profile "$AWS_PROFILE" --region "$REGION")
    echo "Status: $JOB_STATUS"
    
    case $JOB_STATUS in
        SUCCEEDED)
            echo "🎉 Job completed successfully!"
            break
            ;;
        FAILED)
            echo "❌ Job failed!"
            # Get failure reason
            REASON=$(aws batch describe-jobs --jobs "$JOB_ID" --query 'jobs[0].statusReason' --output text --profile "$AWS_PROFILE" --region "$REGION")
            echo "Failure reason: $REASON"
            break
            ;;
        SUBMITTED|PENDING|RUNNABLE|STARTING|RUNNING)
            echo "⏳ Job is still running... waiting 30 seconds"
            sleep 30
            ;;
        *)
            echo "❓ Unknown status: $JOB_STATUS"
            break
            ;;
    esac
done

# Show logs
echo "📋 Fetching job logs..."
LOG_STREAM=$(aws batch describe-jobs --jobs "$JOB_ID" --query 'jobs[0].attempts[0].taskProperties.containers[0].logStreamName' --output text --profile "$AWS_PROFILE" --region "$REGION")

if [ "$LOG_STREAM" != "None" ] && [ -n "$LOG_STREAM" ]; then
    echo "Log stream: $LOG_STREAM"
    echo "Recent logs:"
    aws logs get-log-events \
        --log-group-name "/mvp-backlog" \
        --log-stream-name "$LOG_STREAM" \
        --query 'events[*].message' \
        --output text \
        --profile "$AWS_PROFILE" \
        --region "$REGION" | tail -20
else
    echo "⚠️  No log stream found or job hasn't started yet"
    echo "You can check logs manually at: /mvp-backlog log group"
fi

echo ""
echo "🔍 Job Details:"
aws batch describe-jobs --jobs "$JOB_ID" --profile "$AWS_PROFILE" --region "$REGION"

echo ""
echo "✅ Test completed!"
echo "Check the AWS Batch console for more details: https://console.aws.amazon.com/batch/v2/home?region=$REGION"