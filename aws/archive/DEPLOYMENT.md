# MVP Backlog Batch Stack

This CDK project creates an AWS Batch infrastructure for running CLI applications in the cloud.

## Architecture

The stack includes:
- **VPC**: New VPC with public/private subnets for isolation
- **AWS Batch**: Fargate-based compute environment for containerized jobs
- **ECR Repository**: Container registry for the CLI application image
- **S3 Bucket**: Storage for job results and artifacts
- **CloudWatch Logs**: Centralized logging for job execution
- **Secrets Manager**: Secure storage for GitHub token and Anthropic API key
- **IAM Roles**: Proper permissions for job execution

## Prerequisites

1. **AWS CLI configured with your mvp profile:**
   ```bash
   aws configure --profile mvp
   ```

2. **Node.js and AWS CDK CLI installed:**
   ```bash
   npm install -g aws-cdk
   ```

3. **Docker installed** (for building container images)

4. **Python 3.11+ with virtual environment**

## Deployment Steps

### 1. Setup Environment
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure AWS Environment
```bash
export AWS_PROFILE=mvp
export CDK_DEFAULT_REGION=us-east-1
export CDK_DEFAULT_ACCOUNT=984906149037
```

### 3. Secrets (Pre-configured)
The following secrets already exist in your MVP account:
- `github_token` - GitHub personal access token
- `anthropic_key` - Anthropic API key  
- `openai_key` - OpenAI API key

These are referenced by ARN and will never be deleted by the CDK stack.

### 4. Bootstrap CDK (First time only)
```bash
cdk bootstrap --profile mvp
```

### 5. Deploy Infrastructure
```bash
# Deploy ECR repository first
cdk deploy ECRRepositoryStack --profile mvp --require-approval never

# Deploy main Batch stack
cdk deploy MVPBacklogBatchStack --profile mvp --require-approval never
```

### 6. Build and Push Container Image
```bash
# Get ECR repository URI
ECR_URI=$(aws ecr describe-repositories --repository-names mvp-backlog-cli --query 'repositories[0].repositoryUri' --output text --profile mvp --region us-east-1)

# Login to ECR
aws ecr get-login-password --region us-east-1 --profile mvp | docker login --username AWS --password-stdin $ECR_URI

# Build and push image
docker build -t mvp-backlog-cli .
docker tag mvp-backlog-cli:latest $ECR_URI:latest
docker push $ECR_URI:latest

# Update job definition with image URI (if needed)
echo "ECR URI: $ECR_URI:latest"
```

## Quick Deployment Script

For automated deployment, use the provided script:

```bash
./deploy.sh --profile mvp
```

This script will:
1. Bootstrap CDK if needed
2. Deploy ECR repository
3. Build and push Docker image
4. Deploy the main Batch stack
5. Display next steps

## Testing the Stack

### Submit a Test Job
```bash
# Get job queue and definition names
QUEUE_NAME="MVPBacklogQueue"
JOB_DEF_NAME="MVPBacklogJob"

# Submit a test job
aws batch submit-job \
    --job-name "test-mvp-job" \
    --job-queue "$QUEUE_NAME" \
    --job-definition "$JOB_DEF_NAME" \
    --profile personal
```

### Monitor Job Execution
```bash
# Check job status
aws batch list-jobs --job-queue "$QUEUE_NAME" --profile personal

# View logs in CloudWatch
aws logs tail /mvp-backlog --follow --profile personal
```

## Stack Outputs

After deployment, the stack provides:
- **Job Queue ARN**: For submitting jobs
- **Job Definition ARN**: For job configuration
- **S3 Bucket Name**: For result storage
- **Log Group Name**: For monitoring

## Cleanup

To remove all resources:
```bash
# Delete stacks
cdk destroy MVPBacklogBatchStack --profile personal
cdk destroy ECRRepositoryStack --profile personal

# Remove secrets (optional)
aws secretsmanager delete-secret --secret-id github-token --profile personal
aws secretsmanager delete-secret --secret-id anthropic_api_key --profile personal
```

## Troubleshooting

### Common Issues:

1. **Invalid credentials**: Ensure AWS CLI is configured with `aws configure --profile personal`

2. **Node.js version warning**: The stack works despite Node.js version warnings

3. **ECR image not found**: Make sure to build and push the Docker image before running jobs

4. **Secrets not found**: Ensure secrets are created in the same region as the stack

5. **VPC limits**: If you hit VPC limits, modify the stack to use existing VPC instead of creating new one

### Monitoring:
- **CloudWatch Logs**: `/mvp-backlog` log group
- **AWS Batch Console**: Monitor job status and compute environments
- **S3 Console**: Check for job results and artifacts

## Development

To modify the CLI application:
1. Update the `Dockerfile` with your application code
2. Rebuild and push the image to ECR
3. Submit new jobs to test changes

The current CLI is a placeholder that demonstrates:
- Environment variable access
- JSON output formatting
- Basic logging
- Exit code handling