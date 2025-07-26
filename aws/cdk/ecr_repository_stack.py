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
        self.repository = ecr.Repository(
            self,
            'MVPBacklogRepository',
            repository_name='mvp-backlog-cli',
            image_scan_on_push=True,
            lifecycle_rules=[
                ecr.LifecycleRule(
                    description='Keep only 10 most recent images',
                    max_image_count=10
                )
            ],
            removal_policy=RemovalPolicy.DESTROY
        )

        # ====== Tagging ======
        Tags.of(self).add('project', 'mvp-backlog')
        Tags.of(self).add('env', 'dev')
        Tags.of(self).add('component', 'ecr')