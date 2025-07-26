#!/bin/bash

# Deploy MVP Backlog Batch Stack with manual credential input
# Usage: ./deploy-with-credentials.sh

set -e

echo "🚀 Deploying MVP Backlog Batch Stack"
echo "Target Account: 984906149037"
echo "Region: us-east-1"
echo ""

# Check if MVP profile exists
if aws configure list-profiles | grep -q "^mvp$"; then
    echo "✅ Using existing MVP profile"
    AWS_PROFILE="mvp"
else
    echo "❌ MVP profile not found"
    echo "Please configure MVP profile first:"
    echo "aws configure --profile mvp"
    echo ""
    echo "Or provide credentials via environment variables:"
    echo "export AWS_ACCESS_KEY_ID=your-key"
    echo "export AWS_SECRET_ACCESS_KEY=your-secret"
    echo "export AWS_DEFAULT_REGION=us-east-1"
    echo ""
    
    read -p "Do you want to continue with environment variables? (y/N): " use_env
    if [[ ! "$use_env" =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled. Please configure MVP profile and try again."
        exit 1
    fi
    
    if [[ -z "$AWS_ACCESS_KEY_ID" || -z "$AWS_SECRET_ACCESS_KEY" ]]; then
        echo "❌ AWS credentials not found in environment variables"
        exit 1
    fi
    
    AWS_PROFILE=""
    echo "✅ Using environment variables for AWS credentials"
fi

# Set environment variables
export CDK_DEFAULT_REGION=us-east-1
export CDK_DEFAULT_ACCOUNT=984906149037

echo "Account: $CDK_DEFAULT_ACCOUNT"
echo "Region: $CDK_DEFAULT_REGION"

# Verify access to target account
echo "🔍 Verifying AWS access..."
if [[ -n "$AWS_PROFILE" ]]; then
    ACCOUNT_ID=$(aws sts get-caller-identity --profile "$AWS_PROFILE" --query Account --output text)
else
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
fi

if [[ "$ACCOUNT_ID" != "984906149037" ]]; then
    echo "❌ Connected to account $ACCOUNT_ID, expected 984906149037"
    echo "Please verify your credentials are for the MVP account"
    exit 1
fi

echo "✅ Connected to MVP account ($ACCOUNT_ID)"

# Activate virtual environment
echo "📦 Activating Python virtual environment..."
source .venv/bin/activate

# Set profile flag for CDK commands
PROFILE_FLAG=""
if [[ -n "$AWS_PROFILE" ]]; then
    PROFILE_FLAG="--profile $AWS_PROFILE"
fi

# Step 1: Bootstrap CDK (if needed)
echo "📦 Bootstrapping CDK..."
cdk bootstrap $PROFILE_FLAG 2>/dev/null || echo "CDK already bootstrapped or bootstrap failed"

# Step 2: Deploy ECR Repository first
echo "📦 Deploying ECR Repository..."
cdk deploy ECRRepositoryStack $PROFILE_FLAG --require-approval never

# Step 3: Get ECR URI
echo "🔍 Getting ECR repository URI..."
if [[ -n "$AWS_PROFILE" ]]; then
    ECR_URI=$(aws ecr describe-repositories --repository-names mvp-backlog-cli --query 'repositories[0].repositoryUri' --output text --profile "$AWS_PROFILE" --region us-east-1)
else
    ECR_URI=$(aws ecr describe-repositories --repository-names mvp-backlog-cli --query 'repositories[0].repositoryUri' --output text --region us-east-1)
fi

echo "ECR URI: $ECR_URI"

# Step 4: Build and push Docker image
echo "🐳 Building and pushing Docker image..."
if [[ -n "$AWS_PROFILE" ]]; then
    aws ecr get-login-password --region us-east-1 --profile "$AWS_PROFILE" | docker login --username AWS --password-stdin "$ECR_URI"
else
    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin "$ECR_URI"
fi

docker build -t mvp-backlog-cli .
docker tag mvp-backlog-cli:latest "$ECR_URI:latest"
docker push "$ECR_URI:latest"

# Step 5: Update job definition with ECR URI
echo "🔧 Updating job definition with ECR URI..."
sed -i.bak "s|<ECR_URI>|$ECR_URI:latest|g" cdk/mvp_backlog_batch_stack.py

# Step 6: Deploy main Batch stack
echo "⚡ Deploying MVP Backlog Batch Stack..."
cdk deploy MVPBacklogBatchStack $PROFILE_FLAG --require-approval never

# Step 7: Restore original file
mv cdk/mvp_backlog_batch_stack.py.bak cdk/mvp_backlog_batch_stack.py

echo "✅ Deployment complete!"
echo ""
echo "📋 Stack Resources:"
echo "- Job Queue: MVPBacklogQueue"
echo "- Job Definition: MVPBacklogJob"
echo "- Log Group: /mvp-backlog"
echo "- ECR Repository: mvp-backlog-cli"
echo ""
echo "🧪 Test the deployment:"
echo "./test-job.sh $PROFILE_FLAG"
echo ""
echo "📊 Monitor in AWS Console:"
echo "- Batch: https://console.aws.amazon.com/batch/v2/home?region=us-east-1"
echo "- CloudWatch: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1"