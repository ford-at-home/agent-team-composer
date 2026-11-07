"""MVP Backlog Batch Stack - Serverless Job Execution Infrastructure

This stack creates a complete AWS Batch environment for running the MVP Backlog Generator
CLI application in a serverless, scalable manner using AWS Fargate.

Purpose:
- Provides serverless compute infrastructure for running containerized CLI jobs
- Manages secrets securely for API access (GitHub, Anthropic, OpenAI)
- Implements logging and monitoring for job execution
- Stores job outputs in S3 for later retrieval
- Scales automatically based on job queue demand

Relationship to other stacks:
- Depends on ECRRepositoryStack: Pulls container images from the ECR repository
- Independent of CdkStack: No direct relationship
- Container images must be pushed to ECR before this stack can run jobs

Key Components:
1. Networking: Custom VPC with public/private subnets for secure job execution
2. Secrets Management: Integration with AWS Secrets Manager for API keys
3. Compute Environment: AWS Batch with Fargate for serverless container execution
4. Job Queue & Definition: Manages job scheduling and container configuration
5. IAM Roles: Secure access to AWS services (S3, ECR, CloudWatch, Secrets)
6. Logging: CloudWatch Logs for debugging and monitoring
7. Storage: S3 bucket for job outputs and results

Configuration Choices:
- Fargate: Chosen for serverless operation (no EC2 management)
- Custom VPC: Provides network isolation and control
- 2-week log retention: Balances debugging needs with cost
- 30-day S3 lifecycle: Automatically cleans up old job outputs
- Auto-scaling: Batch automatically scales compute based on queue depth

Deployment Notes:
- Deploy ECRRepositoryStack first and push container images
- Ensure secrets exist in Secrets Manager before deployment
- Update container image URI in job definition after pushing new versions
- Monitor CloudWatch Logs for job execution details
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    Tags,
    aws_batch as batch,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_logs as logs,
    aws_s3 as s3,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct


class MVPBacklogBatchStack(Stack):
    """
    CDK Stack: MVPBacklogBatchStack
    Purpose: Run CLI app in cloud using AWS Batch with minimal setup and default networking
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ====== Secrets ======
        # Reference existing secrets by ARN in us-east-1 (never delete these)
        # These secrets must be created manually in AWS Secrets Manager before deploying this stack
        # The CLI application will access these at runtime for API authentication
        
        # GitHub Personal Access Token for repository operations
        github_token_secret = secretsmanager.Secret.from_secret_complete_arn(
            self, 'GithubToken', 
            'arn:aws:secretsmanager:us-east-1:984906149037:secret:github_token-sIuriy'
        )
        
        # Anthropic API key for Claude AI model access
        anthropic_key_secret = secretsmanager.Secret.from_secret_complete_arn(
            self, 'AnthropicKey',
            'arn:aws:secretsmanager:us-east-1:984906149037:secret:anthropic_key-47iAE6'
        )
        
        # Optional: OpenAI key available if needed for GPT models
        openai_key_secret = secretsmanager.Secret.from_secret_complete_arn(
            self, 'OpenAIKey',
            'arn:aws:secretsmanager:us-east-1:984906149037:secret:openai_key-PkoBXY'
        )

        # ====== Networking ======
        # Create a custom VPC for network isolation and control
        # This provides better security than using the default VPC
        # In production, you might want to use vpc.from_lookup to share an existing VPC
        
        vpc = ec2.Vpc(
            self,
            'MVPVPC',
            max_azs=2,          # Use 2 availability zones for high availability
            nat_gateways=1,     # Single NAT gateway to reduce costs (use 2+ for production)
            subnet_configuration=[
                # Public subnets for NAT gateways and load balancers
                ec2.SubnetConfiguration(
                    name="PublicSubnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24    # /24 provides 256 IP addresses per subnet
                ),
                # Private subnets for Batch compute resources
                # PRIVATE_WITH_EGRESS allows outbound internet via NAT gateway
                ec2.SubnetConfiguration(
                    name="PrivateSubnet", 
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ]
        )
        
        # Create security group for Batch jobs
        # This controls network traffic for containers running in Batch
        default_sg = ec2.SecurityGroup(
            self,
            'BatchJobSecurityGroup',
            vpc=vpc,
            description='Security group for MVP Batch jobs',
            allow_all_outbound=True  # Allows jobs to access internet APIs
        )

        # ====== Logging ======
        # CloudWatch Logs group for capturing job output and debugging
        # All Batch job logs will be streamed here for monitoring and troubleshooting
        log_group = logs.LogGroup(
            self,
            'MVPLogGroup',
            log_group_name='/mvp-backlog',  # Organized under /mvp-backlog namespace
            retention=logs.RetentionDays.TWO_WEEKS,  # Balance cost vs debugging needs
            removal_policy=RemovalPolicy.DESTROY  # Allows deletion with stack (careful in prod!)
        )

        # ====== S3 Bucket ======
        # S3 bucket for storing job outputs and results
        # Jobs can write their outputs here for later retrieval
        result_bucket = s3.Bucket(
            self,
            'MVPResultsBucket',
            # Auto-generate unique name to avoid conflicts
            versioned=True,  # Enable versioning for data protection
            lifecycle_rules=[
                # Automatically delete old objects to control storage costs
                s3.LifecycleRule(expiration=Duration.days(30))
            ],
            # Dev environment settings - use RETAIN in production!
            removal_policy=RemovalPolicy.DESTROY,  # Allows bucket deletion with stack
            auto_delete_objects=True  # Empties bucket before deletion
        )

        # ====== IAM Role ======
        # Main execution role for Batch jobs
        # This role defines what AWS services the running containers can access
        job_execution_role = iam.Role(
            self,
            'JobExecutionRole',
            role_name='MVPBacklogBatchRole',
            # Allow both ECS (Fargate runtime) and Batch to assume this role
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
                iam.ServicePrincipal('batch.amazonaws.com')
            )
        )

        # Add S3 permissions
        # Allow jobs to write outputs to the results bucket
        job_execution_role.add_to_policy(
            iam.PolicyStatement(
                actions=['s3:PutObject'],
                resources=[result_bucket.arn_for_objects('*')]  # All objects in bucket
            )
        )

        # Add CloudWatch Logs permissions
        # Required for streaming container logs to CloudWatch
        job_execution_role.add_to_policy(
            iam.PolicyStatement(
                actions=['logs:CreateLogStream', 'logs:PutLogEvents'],
                resources=['*']  # Could be restricted to specific log group in production
            )
        )

        # Add Secrets Manager permissions
        # Allow jobs to retrieve API keys at runtime
        job_execution_role.add_to_policy(
            iam.PolicyStatement(
                actions=['secretsmanager:GetSecretValue'],
                resources=[
                    github_token_secret.secret_arn,
                    anthropic_key_secret.secret_arn,
                    openai_key_secret.secret_arn
                ]
            )
        )

        # Add ECR permissions for pulling images
        # Required for Fargate to pull container images from ECR
        job_execution_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    'ecr:GetAuthorizationToken',       # Authenticate to ECR
                    'ecr:BatchCheckLayerAvailability',  # Check image layers
                    'ecr:GetDownloadUrlForLayer',       # Download image layers
                    'ecr:BatchGetImage'                 # Get image manifest
                ],
                resources=['*']  # ECR operations require * resource
            )
        )

        # ====== Batch Service Role ======
        # Service role for AWS Batch to manage compute resources
        # This is different from job execution role - it's for Batch service itself
        batch_service_role = iam.Role(
            self,
            'BatchServiceRole',
            assumed_by=iam.ServicePrincipal('batch.amazonaws.com'),
            managed_policies=[
                # AWS managed policy provides necessary permissions for Batch operations
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    'service-role/AWSBatchServiceRole'
                )
            ]
        )

        # ====== Compute Environment ======
        # Defines the compute resources available for running Batch jobs
        # Using Fargate for serverless container execution (no EC2 management)
        compute_env = batch.CfnComputeEnvironment(
            self,
            'MVPFargateEnv',
            type='MANAGED',  # AWS manages the compute resources
            compute_environment_name='MVPFargateEnv',
            compute_resources=batch.CfnComputeEnvironment.ComputeResourcesProperty(
                type='FARGATE',  # Serverless compute - no EC2 instances to manage
                maxv_cpus=16,    # Maximum vCPUs available (auto-scales up to this limit)
                # Deploy in private subnets for security (internet access via NAT)
                subnets=[subnet.subnet_id for subnet in vpc.private_subnets],
                security_group_ids=[default_sg.security_group_id]
            ),
            service_role=batch_service_role.role_arn
        )

        # ====== Job Queue ======
        # Queue where jobs wait to be executed
        # Jobs are processed in FIFO order within their priority level
        job_queue = batch.CfnJobQueue(
            self,
            'MVPJobQueue',
            job_queue_name='MVPBacklogQueue',
            priority=1,  # Higher numbers = higher priority queues
            compute_environment_order=[
                # Can specify multiple compute environments with different priorities
                # Jobs will prefer environments with lower order numbers
                batch.CfnJobQueue.ComputeEnvironmentOrderProperty(
                    order=1,
                    compute_environment=compute_env.ref
                )
            ]
        )

        # ====== Job Definition ======
        # Defines how to run the CLI container as a Batch job
        # This is like a template for creating actual job instances
        job_def = batch.CfnJobDefinition(
            self,
            'MVPJobDef',
            type='container',  # Single container job (vs multi-node)
            job_definition_name='MVPBacklogJob',
            platform_capabilities=['FARGATE'],  # Must match compute environment type
            container_properties=batch.CfnJobDefinition.ContainerPropertiesProperty(
                # Container image from ECR repository (created by ECRRepositoryStack)
                # Update this when deploying new versions
                image='984906149037.dkr.ecr.us-east-1.amazonaws.com/mvp-backlog-cli:latest',
                execution_role_arn=job_execution_role.role_arn,  # For Fargate platform
                job_role_arn=job_execution_role.role_arn,        # For container permissions
                # Resource allocation for each job
                resource_requirements=[
                    batch.CfnJobDefinition.ResourceRequirementProperty(
                        type='VCPU',
                        value='1'     # 1 vCPU per job
                    ),
                    batch.CfnJobDefinition.ResourceRequirementProperty(
                        type='MEMORY',
                        value='2048'  # 2GB RAM per job
                    )
                ],
                # Container entrypoint command
                # This bash script orchestrates the complete backlog generation workflow
                command=[
                    'bash', '-c', 
                    '''
                    echo "=== GitHub Backlog Generator Starting ==="
                    echo "Environment REPO: $REPO"
                    
                    
                    # Fix GitHub token format if it's JSON
                    # Secrets Manager sometimes returns JSON format, we need the raw value
                    if [[ $GITHUB_TOKEN == "{"* ]]; then
                        echo "Parsing JSON GitHub token format..."
                        export GITHUB_TOKEN=$(echo "$GITHUB_TOKEN" | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('github_token', ''))" 2>/dev/null || echo "$GITHUB_TOKEN")
                    fi
                    echo "GitHub token configured: ${GITHUB_TOKEN:0:15}..."
                    
                    # Fix Anthropic API key format if it's JSON
                    if [[ $ANTHROPIC_API_KEY == "{"* ]]; then
                        echo "Parsing JSON Anthropic key format..."
                        export ANTHROPIC_API_KEY=$(echo "$ANTHROPIC_API_KEY" | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('anthropic_key', ''))" 2>/dev/null || echo "$ANTHROPIC_API_KEY")
                    fi
                    echo "Anthropic API key configured: ${ANTHROPIC_API_KEY:0:15}..."
                    
                    echo "Final REPO: $REPO"
                    echo "=== Starting Complete Workflow ==="
                    
                    # Execute the 4-step workflow to create a minimal backlog
                    echo "Step 1: Initialize project and generate phases..."
                    github-backlog-generator init "$REPO"
                    
                    echo "Step 2: Create GitHub milestones from phases..."
                    github-backlog-generator create-milestones --repo "$REPO"
                    
                    echo "Step 3: Create epics for phase 1..."
                    github-backlog-generator create-epics --repo "$REPO" -p 1
                    
                    echo "Step 4: Create issues for first epic of first phase..."
                    github-backlog-generator create-issues --repo "$REPO" -p 1 -e 1
                    
                    echo "=== Workflow Complete ==="
                    echo "Summary: Generated phases, epics for phase 1, and issues for epic 1"
                    '''
                ],
                # Default environment variables
                # These can be overridden when submitting jobs
                environment=[
                    {
                        'name': 'REPO',
                        'value': 'mvp-builder-app/default-repo'  # Default value, will be overridden by parameter
                    },
                    {
                        'name': 'PHASES', 
                        'value': '1'      # Number of project phases to generate
                    },
                    {
                        'name': 'EPICS',
                        'value': '1'      # Number of epics per phase
                    },
                    {
                        'name': 'ISSUES',
                        'value': '3'      # Number of issues per epic
                    }
                ],
                # Secrets injected as environment variables at runtime
                # Values are fetched from AWS Secrets Manager
                secrets=[
                    batch.CfnJobDefinition.SecretProperty(
                        name='GITHUB_TOKEN',      # GitHub API access
                        value_from=github_token_secret.secret_arn
                    ),
                    batch.CfnJobDefinition.SecretProperty(
                        name='ANTHROPIC_API_KEY', # Claude AI access
                        value_from=anthropic_key_secret.secret_arn
                    ),
                    batch.CfnJobDefinition.SecretProperty(
                        name='OPENAI_API_KEY',    # Optional GPT access
                        value_from=openai_key_secret.secret_arn
                    )
                ],
                # CloudWatch Logs configuration for job output
                log_configuration=batch.CfnJobDefinition.LogConfigurationProperty(
                    log_driver='awslogs',  # Stream logs to CloudWatch
                    options={
                        'awslogs-group': log_group.log_group_name,
                        'awslogs-region': self.region,
                        'awslogs-stream-prefix': 'mvp'  # Log streams: mvp/container/job-id
                    }
                )
            )
        )

        # ====== Tagging ======
        # Apply consistent tags to all resources in this stack
        Tags.of(self).add('project', 'mvp-backlog')
        Tags.of(self).add('env', 'dev')

        # Store references as instance variables for potential cross-stack references
        # These can be accessed from other stacks if needed
        self.job_queue = job_queue          # For submitting jobs
        self.job_definition = job_def       # For job configuration reference
        self.result_bucket = result_bucket  # For accessing job outputs
        self.log_group = log_group         # For monitoring and debugging