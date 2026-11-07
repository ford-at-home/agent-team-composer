#!/bin/bash

# Script to rebuild and push Docker image only
# This is useful after code changes without full redeploy

set -e

# Change to parent directory for correct Docker build context
cd "$(dirname "$0")/../.."

# Default values
AWS_PROFILE="mvp"
REGION="us-east-1"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --profile)
            AWS_PROFILE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "🐳 Rebuilding and pushing Docker image..."

# Get ECR URI
ECR_URI=$(aws ecr describe-repositories --repository-names mvp-backlog-cli --query 'repositories[0].repositoryUri' --output text --profile $AWS_PROFILE --region $REGION)
echo "ECR URI: $ECR_URI"

# Login to ECR
aws ecr get-login-password --region $REGION --profile $AWS_PROFILE | docker login --username AWS --password-stdin $ECR_URI

# Build and push
docker build -f aws/Dockerfile -t mvp-backlog-cli .
docker tag mvp-backlog-cli:latest $ECR_URI:latest
docker push $ECR_URI:latest

echo "✅ Docker image rebuilt and pushed successfully!"
echo "   Image: $ECR_URI:latest"
echo ""
echo "Note: AWS Batch will use the new image for future jobs."