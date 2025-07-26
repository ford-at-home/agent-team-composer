#!/bin/bash

# MVP Backlog Batch Stack Deployment Script
# Usage: ./deploy.sh [--profile personal]

set -e

# Default values for MVP account
AWS_PROFILE="mvp"
REGION="us-east-1"

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
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "🚀 Deploying MVP Backlog Batch Stack"
echo "Profile: $AWS_PROFILE"
echo "Region: $REGION"

# Set environment variables
export AWS_PROFILE=$AWS_PROFILE
export CDK_DEFAULT_REGION=$REGION
export CDK_DEFAULT_ACCOUNT=984906149037  # Fixed MVP account ID

echo "Account: $CDK_DEFAULT_ACCOUNT"

# Step 1: Bootstrap CDK (if needed)
echo "📦 Bootstrapping CDK..."
cdk bootstrap --profile $AWS_PROFILE

# Step 2: Deploy ECR Repository first
echo "📦 Deploying ECR Repository..."
cdk deploy ECRRepositoryStack --profile $AWS_PROFILE --require-approval never

# Step 3: Get ECR URI
ECR_URI=$(aws ecr describe-repositories --repository-names mvp-backlog-cli --query 'repositories[0].repositoryUri' --output text --profile $AWS_PROFILE --region $REGION)
echo "ECR URI: $ECR_URI"

# Step 4: Build and push Docker image
echo "🐳 Building and pushing Docker image..."
aws ecr get-login-password --region $REGION --profile $AWS_PROFILE | docker login --username AWS --password-stdin $ECR_URI

docker build -t mvp-backlog-cli .
docker tag mvp-backlog-cli:latest $ECR_URI:latest
docker push $ECR_URI:latest

# Step 5: Update job definition with ECR URI
echo "🔧 Updating job definition with ECR URI..."
sed -i.bak "s|<ECR_URI>|$ECR_URI:latest|g" cdk/mvp_backlog_batch_stack.py

# Step 6: Deploy main Batch stack
echo "⚡ Deploying MVP Backlog Batch Stack..."
cdk deploy MVPBacklogBatchStack --profile $AWS_PROFILE --require-approval never

# Step 7: Restore original file
mv cdk/mvp_backlog_batch_stack.py.bak cdk/mvp_backlog_batch_stack.py

echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Ensure secrets 'github-token' and 'anthropic_api_key' exist in AWS Secrets Manager"
echo "2. Test job submission using AWS CLI or console"
echo "3. Monitor logs in CloudWatch log group '/mvp-backlog'"