# AWS Batch Backlog Processing System

This directory contains the AWS CDK infrastructure code for deploying the GitHub Backlog Generator CLI tool to AWS Batch.

## Real Talk: What This Actually Is

**There's only ONE CLI** - the `github-backlog-generator` that lives in the parent directory. This AWS setup is just a way to run that same CLI in the cloud instead of on your laptop.

Think of it like this:
- **Local**: You type `github-backlog-generator init myorg/myrepo` in your terminal
- **AWS Batch**: A container runs the exact same command for you in the cloud

The Dockerfile literally just:
1. Copies the CLI source code from `../github-backlog-generator/`
2. Installs it with `pip install`
3. Runs the same commands you would run locally

No duplicate code. No separate "cloud version". Just the same CLI running in a different place.

## Overview

This system processes GitHub repository backlogs using AWS Batch with Fargate compute. It analyzes issues, pull requests, and generates comprehensive backlog reports that can be stored in various outputs.

## Architecture

The infrastructure consists of three main CDK stacks:

1. **ECRRepositoryStack** - Creates the ECR repository for storing the Docker container image
2. **MVPBacklogBatchStack** - The main stack containing:
   - AWS Batch compute environment (Fargate)
   - Job queue and job definition
   - VPC and networking configuration
   - IAM roles and permissions
   - Secrets Manager integration for GitHub tokens

## Prerequisites

- AWS CLI configured with appropriate credentials
- Python 3.8+
- Docker (for building container images)
- AWS CDK installed (`npm install -g aws-cdk`)
- GitHub Personal Access Token stored in AWS Secrets Manager

## Quick Start

1. Set up Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Configure AWS profile:
   ```bash
   ./setup-mvp-profile.sh
   ```

3. Set up secrets:
   ```bash
   ./setup-secrets.sh
   ```

4. Deploy the infrastructure:
   ```bash
   ./deploy.sh
   ```

## Testing

Run integration tests to verify the deployment:
```bash
python integration-test.py
```

For quick smoke testing:
```bash
python smoke-test.py
```

## Deployment Scripts

- `deploy.sh` - Main deployment script that handles the complete deployment process
- `deploy-with-credentials.sh` - Alternative deployment with explicit credential handling
- `setup-mvp-profile.sh` - Configures the AWS CLI profile for the MVP account
- `setup-secrets.sh` - Sets up required secrets in AWS Secrets Manager
- `check-deployment.sh` - Verifies the deployment status

## Documentation

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Complete deployment guide with prerequisites, step-by-step instructions, troubleshooting, and current status

## Project Structure

```
aws/
├── cdk/                      # CDK stack definitions
│   ├── __init__.py
│   ├── cdk_stack.py         # (Original template - archived)
│   ├── ecr_repository_stack.py
│   └── mvp_backlog_batch_stack.py
├── app.py                    # CDK app entry point
├── Dockerfile               # Container definition for batch job
├── requirements.txt         # Python dependencies
├── cdk.json                # CDK configuration
└── scripts/                 # Deployment and utility scripts
```

## Key Components

### Batch Job Configuration
- **Job Definition**: `mvp-backlog-job-def`
- **Compute Environment**: Fargate with 4 vCPU and 8GB memory
- **Container**: Runs the backlog generator CLI tool
- **Timeout**: 2 hours maximum job duration

### Container Override Pattern

This stack uses AWS Batch container overrides to provide maximum flexibility. Instead of using job parameters, we override environment variables at job submission time, allowing the same container to behave differently based on runtime configuration.

**Real talk about how this works:**
- The Batch job runs a bash script that constructs CLI commands using environment variables
- When you set `REPO=myorg/myrepo`, the script runs: `github-backlog-generator init myorg/myrepo`
- It's literally just string substitution - nothing fancy
- You could SSH into the container and type the same commands manually

#### How It Works

1. **Base Configuration**: The job definition includes default environment variables:
   - `REPO`: mvp-builder-app/default-repo
   - `PHASES`: 1
   - `EPICS`: 1
   - `ISSUES`: 3

2. **Runtime Overrides**: When submitting jobs, use `--container-overrides` to change behavior:
   ```bash
   aws batch submit-job \
     --job-name my-job \
     --job-queue MVPBacklogQueue \
     --job-definition MVPBacklogJob \
     --container-overrides '{"environment":[{"name":"REPO","value":"myorg/myrepo"}]}'
   ```

#### Available Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `REPO` | GitHub repository (org/repo) | mvp-builder-app/default-repo | myorg/awesome-project |
| `PHASES` | Number of phases to generate | 1 | 5 |
| `EPICS` | Number of epics per phase | 1 | 3 |
| `ISSUES` | Number of issues per epic | 3 | 10 |
| `GITHUB_TOKEN` | GitHub PAT (from Secrets Manager) | (from secrets) | ghp_xxxxx |
| `ANTHROPIC_API_KEY` | Anthropic API key (from Secrets Manager) | (from secrets) | sk-ant-xxxxx |
| `OUTPUT_FORMAT` | Output format | json | markdown |
| `S3_BUCKET` | S3 bucket for outputs | (optional) | my-outputs-bucket |
| `S3_KEY` | S3 object key | (optional) | backlogs/project1.json |

#### Example Override Scenarios

**1. Full Production Backlog**
```json
{
  "environment": [
    {"name": "REPO", "value": "mycompany/production-app"},
    {"name": "PHASES", "value": "6"},
    {"name": "EPICS", "value": "5"},
    {"name": "ISSUES", "value": "15"}
  ]
}
```

**2. Quick Smoke Test**
```json
{
  "environment": [
    {"name": "REPO", "value": "test-org/smoke-test"},
    {"name": "PHASES", "value": "1"},
    {"name": "EPICS", "value": "1"},
    {"name": "ISSUES", "value": "2"}
  ]
}
```

**3. Custom Workflow**
```json
{
  "environment": [
    {"name": "REPO", "value": "myorg/myrepo"},
    {"name": "WORKFLOW", "value": "phases-only"},
    {"name": "OUTPUT_FORMAT", "value": "markdown"},
    {"name": "S3_BUCKET", "value": "my-backlogs"},
    {"name": "S3_KEY", "value": "2024/q1-backlog.md"}
  ]
}
```

**4. Different API Keys (for testing)**
```json
{
  "environment": [
    {"name": "REPO", "value": "myorg/test-repo"},
    {"name": "GITHUB_TOKEN", "value": "ghp_different_token"},
    {"name": "ANTHROPIC_API_KEY", "value": "sk-ant-different_key"}
  ]
}
```

#### Python Example
```python
import boto3
import json

batch = boto3.client('batch')

response = batch.submit_job(
    jobName='my-backlog-job',
    jobQueue='MVPBacklogQueue',
    jobDefinition='MVPBacklogJob',
    containerOverrides={
        'environment': [
            {'name': 'REPO', 'value': 'myorg/myrepo'},
            {'name': 'PHASES', 'value': '3'},
            {'name': 'EPICS', 'value': '4'},
            {'name': 'ISSUES', 'value': '8'}
        ]
    }
)
```

### Security
- GitHub tokens stored in AWS Secrets Manager
- IAM roles with least-privilege access
- VPC with private subnets for compute resources

## Monitoring

Jobs can be monitored through:
- AWS Batch console
- CloudWatch logs (log group: `/aws/batch/mvp-backlog`)
- Integration test outputs

## Troubleshooting

If deployment fails:
1. Check AWS credentials: `aws sts get-caller-identity`
2. Verify secrets are configured: `aws secretsmanager get-secret-value --secret-id github-token-mvp`
3. Review CloudFormation stack events in AWS console
4. Check deployment logs from the scripts

## Cost Considerations

- Fargate pricing based on vCPU and memory usage
- Secrets Manager charges for secret storage
- CloudWatch logs retention (set to 7 days)
- ECR storage for container images

## Future Improvements

- Add CloudWatch alarms for job failures
- Implement job scheduling with EventBridge
- Add S3 integration for output storage
- Create Lambda functions for job triggering