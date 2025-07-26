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
        github_token_secret = secretsmanager.Secret.from_secret_complete_arn(
            self, 'GithubToken', 
            'arn:aws:secretsmanager:us-east-1:984906149037:secret:github_token-sIuriy'
        )
        anthropic_key_secret = secretsmanager.Secret.from_secret_complete_arn(
            self, 'AnthropicKey',
            'arn:aws:secretsmanager:us-east-1:984906149037:secret:anthropic_key-47iAE6'
        )
        # Optional: OpenAI key available if needed
        openai_key_secret = secretsmanager.Secret.from_secret_complete_arn(
            self, 'OpenAIKey',
            'arn:aws:secretsmanager:us-east-1:984906149037:secret:openai_key-PkoBXY'
        )

        # ====== Networking ======
        # For validation, we'll create a new VPC instead of looking up default
        # In production, you can switch back to vpc.from_lookup for existing VPC
        vpc = ec2.Vpc(
            self,
            'MVPVPC',
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="PublicSubnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="PrivateSubnet", 
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ]
        )
        
        # Create security group for Batch jobs
        default_sg = ec2.SecurityGroup(
            self,
            'BatchJobSecurityGroup',
            vpc=vpc,
            description='Security group for MVP Batch jobs',
            allow_all_outbound=True
        )

        # ====== Logging ======
        log_group = logs.LogGroup(
            self,
            'MVPLogGroup',
            log_group_name='/mvp-backlog',
            retention=logs.RetentionDays.TWO_WEEKS,
            removal_policy=RemovalPolicy.DESTROY
        )

        # ====== S3 Bucket ======
        result_bucket = s3.Bucket(
            self,
            'MVPResultsBucket',
            # Remove bucket_name to auto-generate unique name
            versioned=True,
            lifecycle_rules=[
                s3.LifecycleRule(expiration=Duration.days(30))
            ],
            removal_policy=RemovalPolicy.DESTROY,  # Changed for dev environment
            auto_delete_objects=True  # Changed for dev environment
        )

        # ====== IAM Role ======
        job_execution_role = iam.Role(
            self,
            'JobExecutionRole',
            role_name='MVPBacklogBatchRole',
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
                iam.ServicePrincipal('batch.amazonaws.com')
            )
        )

        # Add S3 permissions
        job_execution_role.add_to_policy(
            iam.PolicyStatement(
                actions=['s3:PutObject'],
                resources=[result_bucket.arn_for_objects('*')]
            )
        )

        # Add CloudWatch Logs permissions
        job_execution_role.add_to_policy(
            iam.PolicyStatement(
                actions=['logs:CreateLogStream', 'logs:PutLogEvents'],
                resources=['*']
            )
        )

        # Add Secrets Manager permissions
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
        job_execution_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    'ecr:GetAuthorizationToken',
                    'ecr:BatchCheckLayerAvailability',
                    'ecr:GetDownloadUrlForLayer',
                    'ecr:BatchGetImage'
                ],
                resources=['*']
            )
        )

        # ====== Batch Service Role ======
        batch_service_role = iam.Role(
            self,
            'BatchServiceRole',
            assumed_by=iam.ServicePrincipal('batch.amazonaws.com'),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    'service-role/AWSBatchServiceRole'
                )
            ]
        )

        # ====== Compute Environment ======
        compute_env = batch.CfnComputeEnvironment(
            self,
            'MVPFargateEnv',
            type='MANAGED',
            compute_environment_name='MVPFargateEnv',
            compute_resources=batch.CfnComputeEnvironment.ComputeResourcesProperty(
                type='FARGATE',
                maxv_cpus=16,
                subnets=[subnet.subnet_id for subnet in vpc.private_subnets],
                security_group_ids=[default_sg.security_group_id]
            ),
            service_role=batch_service_role.role_arn
        )

        # ====== Job Queue ======
        job_queue = batch.CfnJobQueue(
            self,
            'MVPJobQueue',
            job_queue_name='MVPBacklogQueue',
            priority=1,
            compute_environment_order=[
                batch.CfnJobQueue.ComputeEnvironmentOrderProperty(
                    order=1,
                    compute_environment=compute_env.ref
                )
            ]
        )

        # ====== Job Definition ======
        job_def = batch.CfnJobDefinition(
            self,
            'MVPJobDef',
            type='container',
            job_definition_name='MVPBacklogJob',
            platform_capabilities=['FARGATE'],
            container_properties=batch.CfnJobDefinition.ContainerPropertiesProperty(
                image='984906149037.dkr.ecr.us-east-1.amazonaws.com/mvp-backlog-cli:latest',
                execution_role_arn=job_execution_role.role_arn,
                job_role_arn=job_execution_role.role_arn,
                resource_requirements=[
                    batch.CfnJobDefinition.ResourceRequirementProperty(
                        type='VCPU',
                        value='1'
                    ),
                    batch.CfnJobDefinition.ResourceRequirementProperty(
                        type='MEMORY',
                        value='2048'
                    )
                ],
                command=[
                    'bash', '-c', 
                    '''
                    echo "=== GitHub Backlog Generator Starting ==="
                    echo "Environment REPO: $REPO"
                    
                    # Fix GitHub token format if it's JSON
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
                    
                    # Parse job parameters if they exist
                    if [ ! -z "$AWS_BATCH_JOB_PARAMETERS" ]; then
                        REPO_PARAM=$(echo "$AWS_BATCH_JOB_PARAMETERS" | python3 -c "import sys,json; params=json.loads(sys.stdin.read()); print(params.get('REPO', ''))" 2>/dev/null || echo "")
                        if [ ! -z "$REPO_PARAM" ]; then
                            export REPO="$REPO_PARAM"
                            echo "Using parameter REPO: $REPO"
                        fi
                    fi
                    
                    echo "Final REPO: $REPO"
                    echo "=== Starting Complete Workflow ==="
                    
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
                environment=[
                    {
                        'name': 'REPO',
                        'value': 'mvp-builder-app/default-repo'
                    },
                    {
                        'name': 'PHASES', 
                        'value': '1'
                    },
                    {
                        'name': 'EPICS',
                        'value': '1'
                    },
                    {
                        'name': 'ISSUES',
                        'value': '3'
                    }
                ],
                secrets=[
                    batch.CfnJobDefinition.SecretProperty(
                        name='GITHUB_TOKEN',
                        value_from=github_token_secret.secret_arn
                    ),
                    batch.CfnJobDefinition.SecretProperty(
                        name='ANTHROPIC_API_KEY',
                        value_from=anthropic_key_secret.secret_arn
                    ),
                    batch.CfnJobDefinition.SecretProperty(
                        name='OPENAI_API_KEY',
                        value_from=openai_key_secret.secret_arn
                    )
                ],
                log_configuration=batch.CfnJobDefinition.LogConfigurationProperty(
                    log_driver='awslogs',
                    options={
                        'awslogs-group': log_group.log_group_name,
                        'awslogs-region': self.region,
                        'awslogs-stream-prefix': 'mvp'
                    }
                )
            )
        )

        # ====== Tagging ======
        Tags.of(self).add('project', 'mvp-backlog')
        Tags.of(self).add('env', 'dev')

        # Store references as instance variables for potential future use
        self.job_queue = job_queue
        self.job_definition = job_def
        self.result_bucket = result_bucket
        self.log_group = log_group