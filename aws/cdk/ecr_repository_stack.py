"""ECR Repository Stack - Container Image Storage Infrastructure

This stack creates and manages an Amazon Elastic Container Registry (ECR) repository
for storing Docker container images used by the MVP Backlog Generator CLI application.

Purpose:
- Provides a secure, managed container registry for Docker images
- Stores the CLI application container that will be executed by AWS Batch
- Implements lifecycle policies to manage storage costs by limiting image retention
- Enables vulnerability scanning for security compliance

Relationship to other stacks:
- Independent stack with no dependencies on other stacks
- The MVPBacklogBatchStack depends on this stack's repository to pull container images
- Images must be pushed to this repository before Batch jobs can run successfully

Key Components:
- ECR Repository: Stores versioned container images
- Lifecycle Rules: Automatically removes old images to control costs
- Image Scanning: Scans images for vulnerabilities on push
- Tags: Enables resource tracking and cost allocation

Deployment Notes:
- This stack should be deployed before MVPBacklogBatchStack
- After deployment, build and push Docker images to the created repository
- Repository URI will be: {account-id}.dkr.ecr.{region}.amazonaws.com/mvp-backlog-cli
"""

from aws_cdk import (
    Stack,
    RemovalPolicy,
    Tags,
    aws_ecr as ecr,
)
from constructs import Construct


class ECRRepositoryStack(Stack):
    """
    CDK Stack for ECR Repository to store the CLI container image
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ====== ECR Repository ======
        # Create the main ECR repository for storing CLI container images
        # This repository will be used by AWS Batch to pull images for job execution
        self.repository = ecr.Repository(
            self,
            'MVPBacklogRepository',
            repository_name='mvp-backlog-cli',  # Fixed name for easy reference
            image_scan_on_push=True,  # Enable automatic vulnerability scanning
            lifecycle_rules=[
                # Lifecycle rule to manage storage costs by limiting retained images
                # Only the 10 most recent images are kept, older ones are automatically deleted
                ecr.LifecycleRule(
                    description='Keep only 10 most recent images',
                    max_image_count=10
                )
            ],
            # DESTROY policy allows CloudFormation to delete the repository when stack is deleted
            # Be careful: this will delete all images! Use RETAIN in production
            removal_policy=RemovalPolicy.DESTROY
        )

        # ====== Tagging ======
        # Apply consistent tags for resource organization and cost tracking
        # These tags help identify resources in AWS console and cost reports
        Tags.of(self).add('project', 'mvp-backlog')    # Project identifier
        Tags.of(self).add('env', 'dev')                # Environment (dev/staging/prod)
        Tags.of(self).add('component', 'ecr')          # Component type for filtering