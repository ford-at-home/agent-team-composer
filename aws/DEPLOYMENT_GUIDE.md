# MVP Backlog Batch Stack - Complete Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the AWS Batch infrastructure for running CLI applications in the cloud. The stack is configured for the MVP account (`984906149037`) in the `us-east-1` region.

## Current Deployment Status

✅ **Ready for Deployment** - All CDK code has been created and validated.

### Status Checklist:
- **CDK Stack**: ✅ Complete and validated
- **Secret Integration**: ✅ Configured for existing secrets in us-east-1
- **Environment**: ✅ Set to MVP account (984906149037) and us-east-1
- **Scripts**: ✅ All deployment and test scripts ready
- **AWS Profile**: ⚠️ Needs configuration (see Prerequisites)

## Architecture

The stack includes:
- **VPC**: New VPC with public/private subnets for isolation
- **AWS Batch**: Fargate-based compute environment for containerized jobs (max 16 vCPUs)
- **ECR Repository**: Container registry for the CLI application image
- **S3 Bucket**: Storage for job results and artifacts
- **CloudWatch Logs**: Centralized logging for job execution
- **Secrets Manager**: Secure storage for GitHub token and Anthropic API key
- **IAM Roles**: Proper permissions for job execution

### Stack Components:

1. **ECRRepositoryStack**:
   - Repository: `mvp-backlog-cli`
   - Lifecycle policy: Keep 10 most recent images

2. **MVPBacklogBatchStack**:
   - Job queue: `MVPBacklogQueue`
   - Job definition: `MVPBacklogJob`
   - CloudWatch logging: `/mvp-backlog`
   - S3 bucket for results

## Prerequisites

### 1. AWS CLI Configuration
Configure your AWS CLI with the mvp profile:
```bash
# Run the setup script
./setup-mvp-profile.sh
```

Or configure manually:
```bash
aws configure --profile mvp
# Enter:
# Access Key ID: [your-mvp-access-key]
# Secret Access Key: [your-mvp-secret-key]
# Default region: us-east-1
# Default output format: json
```

### 2. Verify Profile Configuration
```bash
aws sts get-caller-identity --profile mvp
# Should return Account: "984906149037"
```

### 3. Install Required Tools
- **Node.js and AWS CDK CLI:**
  ```bash
  npm install -g aws-cdk
  ```
- **Docker** (for building container images)
- **Python 3.11+** with virtual environment

### 4. Pre-configured Secrets
The following secrets already exist in your MVP account:
- `github_token` - GitHub personal access token
  - ARN: `arn:aws:secretsmanager:us-east-1:984906149037:secret:github_token-sIuriy`
- `anthropic_key` - Anthropic API key
  - ARN: `arn:aws:secretsmanager:us-east-1:984906149037:secret:anthropic_key-47iAE6`
- `openai_key` - OpenAI API key
  - ARN: `arn:aws:secretsmanager:us-east-1:984906149037:secret:openai_key-PkoBXY`

These are referenced by ARN and will never be deleted by the CDK stack.

## Step-by-Step Deployment Process

### Option 1: Quick Deployment (Recommended)

Use the automated deployment script:
```bash
./deploy.sh --profile mvp
```

This script will:
1. Bootstrap CDK if needed
2. Deploy ECR repository
3. Build and push Docker image
4. Deploy the main Batch stack
5. Display deployment results

### Option 2: Manual Deployment

#### 1. Setup Environment
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Configure AWS Environment
```bash
export AWS_PROFILE=mvp
export CDK_DEFAULT_REGION=us-east-1
export CDK_DEFAULT_ACCOUNT=984906149037
```

#### 3. Bootstrap CDK (First time only)
```bash
cdk bootstrap --profile mvp
```

#### 4. Deploy Infrastructure
```bash
# Deploy ECR repository first
cdk deploy ECRRepositoryStack --profile mvp --require-approval never

# Deploy main Batch stack
cdk deploy MVPBacklogBatchStack --profile mvp --require-approval never
```

#### 5. Build and Push Container Image
```bash
# Get ECR repository URI
ECR_URI=$(aws ecr describe-repositories --repository-names mvp-backlog-cli --query 'repositories[0].repositoryUri' --output text --profile mvp --region us-east-1)

# Login to ECR
aws ecr get-login-password --region us-east-1 --profile mvp | docker login --username AWS --password-stdin $ECR_URI

# Build and push image
docker build -t mvp-backlog-cli .
docker tag mvp-backlog-cli:latest $ECR_URI:latest
docker push $ECR_URI:latest

# Display ECR URI for reference
echo "ECR URI: $ECR_URI:latest"
```

## Post-Deployment Verification

### 1. Test the Deployment
Run the automated test script:
```bash
./test-job.sh --profile mvp
```

### 2. Submit a Manual Test Job
```bash
# Get job queue and definition names
QUEUE_NAME="MVPBacklogQueue"
JOB_DEF_NAME="MVPBacklogJob"

# Submit a test job
aws batch submit-job \
    --job-name "test-mvp-job" \
    --job-queue "$QUEUE_NAME" \
    --job-definition "$JOB_DEF_NAME" \
    --profile mvp
```

### 3. Monitor Job Execution
```bash
# Check job status
aws batch list-jobs --job-queue "$QUEUE_NAME" --profile mvp

# View logs in CloudWatch
aws logs tail /mvp-backlog --follow --profile mvp
```

### 4. Verify Stack Outputs
After deployment, verify these resources are created:
- **Job Queue ARN**: For submitting jobs
- **Job Definition ARN**: For job configuration
- **S3 Bucket Name**: For result storage
- **Log Group Name**: For monitoring

## Container Application

The stack includes a placeholder CLI application that:
- Reads environment variables (GitHub token, API keys)
- Demonstrates cloud job execution
- Outputs structured JSON results
- Implements proper exit code handling

To customize for your use case, modify:
- `Dockerfile` - Container configuration
- `cli.py` - Application logic

## Monitoring and Logging

Once deployed, monitor your jobs through:
- **AWS Batch Console**: Job status and compute environments
- **CloudWatch Logs**: `/mvp-backlog` log group
- **S3 Console**: Job results and artifacts
- **ECR Console**: Container images

## Troubleshooting

### Common Issues and Solutions:

1. **Invalid credentials**
   - Ensure AWS CLI is configured: `aws configure --profile mvp`
   - Verify profile: `aws sts get-caller-identity --profile mvp`

2. **Node.js version warning**
   - The stack works despite Node.js version warnings
   - Ensure CDK is installed: `npm install -g aws-cdk`

3. **ECR image not found**
   - Build and push the Docker image before running jobs
   - Verify image exists: `aws ecr list-images --repository-name mvp-backlog-cli --profile mvp`

4. **Secrets not found**
   - Ensure secrets exist in the same region (us-east-1)
   - Check secret: `aws secretsmanager describe-secret --secret-id github_token --profile mvp`

5. **VPC limits**
   - If you hit VPC limits, modify the stack to use existing VPC
   - Check VPC quota in Service Quotas console

6. **Job failures**
   - Check CloudWatch logs: `/mvp-backlog`
   - Review job details in Batch console
   - Verify IAM permissions are correct

### Debug Commands:
```bash
# Check CDK stack status
cdk list --profile mvp

# View stack events
aws cloudformation describe-stack-events --stack-name MVPBacklogBatchStack --profile mvp

# Check Batch compute environment
aws batch describe-compute-environments --profile mvp

# View job definitions
aws batch describe-job-definitions --status ACTIVE --profile mvp
```

## Cleanup

To remove all resources:
```bash
# Delete stacks (in reverse order)
cdk destroy MVPBacklogBatchStack --profile mvp
cdk destroy ECRRepositoryStack --profile mvp

# Note: Secrets are not deleted by CDK and must be removed manually if needed
# aws secretsmanager delete-secret --secret-id github_token --profile mvp --force-delete-without-recovery
# aws secretsmanager delete-secret --secret-id anthropic_key --profile mvp --force-delete-without-recovery
# aws secretsmanager delete-secret --secret-id openai_key --profile mvp --force-delete-without-recovery
```

## Development Workflow

To modify and test the CLI application:

1. **Update Application Code**
   - Modify `Dockerfile` with your application code
   - Update `cli.py` with new functionality

2. **Rebuild and Deploy**
   ```bash
   # Rebuild and push image
   ./deploy.sh --profile mvp --image-only
   ```

3. **Test Changes**
   ```bash
   # Submit test job
   ./test-job.sh --profile mvp
   ```

## Security Best Practices

- Secrets are stored in AWS Secrets Manager and never in code
- IAM roles follow least-privilege principle
- VPC uses private subnets for compute resources
- Container images are scanned for vulnerabilities in ECR
- CloudWatch logs are encrypted at rest

## Cost Optimization

- **Fargate pricing**: Based on vCPU and memory usage per second
- **Secrets Manager**: ~$0.40/month per secret
- **CloudWatch logs**: Set to 7-day retention to minimize costs
- **ECR storage**: Lifecycle policy keeps only 10 most recent images
- **Batch compute**: Scales to zero when no jobs are running

## Support and Resources

- AWS Batch Documentation: https://docs.aws.amazon.com/batch/
- CDK Documentation: https://docs.aws.amazon.com/cdk/
- CloudFormation Console: Check stack events for deployment issues
- AWS Support: For account-specific issues