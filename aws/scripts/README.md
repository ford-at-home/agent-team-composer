# AWS Deployment Scripts

This directory contains all deployment and utility scripts for the AWS Batch Backlog Processing system.

## Deployment Scripts

### deploy.sh
Main deployment script that orchestrates the complete deployment process:
- Builds and pushes Docker image to ECR
- Synthesizes CDK stacks
- Deploys infrastructure in correct order
- Handles AWS credentials and profile setup

### deploy-with-credentials.sh
Alternative deployment script with explicit credential handling:
- Useful for CI/CD environments
- Allows passing AWS credentials as parameters
- Performs same deployment steps as deploy.sh

### setup-mvp-profile.sh
Configures AWS CLI profile for the MVP account:
- Sets up named profile for multi-account environments
- Configures default region (us-east-1)
- Validates credentials

### setup-secrets.sh
Creates and manages secrets in AWS Secrets Manager:
- Prompts for GitHub Personal Access Token
- Stores token securely in Secrets Manager
- Used by Batch jobs to access GitHub API

### check-deployment.sh
Verifies deployment status and health:
- Checks if stacks are deployed
- Validates Batch environment is active
- Verifies job definitions are created

## Testing Scripts

### integration-test.py
Comprehensive integration test suite:
- Creates test GitHub repository
- Submits test job to AWS Batch
- Monitors job execution
- Validates output and cleans up resources
- Tests end-to-end functionality

### smoke-test.py
Quick validation test for basic functionality:
- Minimal test workflow with reduced parameters
- Rapid feedback for development cycles
- Tests core AWS Batch operations
- 3-minute timeout for fast results


## Usage Examples

### Full Deployment
```bash
./setup-mvp-profile.sh
./setup-secrets.sh
./deploy.sh
```

### Run Tests
```bash
python integration-test.py
```

### Check Deployment Status
```bash
./check-deployment.sh
```

## Script Dependencies

- AWS CLI must be installed and configured
- Python 3.8+ for test scripts
- Docker for building container images
- jq for JSON parsing in some scripts

## Notes

- All scripts assume execution from the aws/ directory
- Scripts use the AWS profile "mvp-backlog" by default
- Error handling included with descriptive messages
- Scripts are idempotent where possible