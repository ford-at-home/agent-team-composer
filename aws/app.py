#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk.cdk_stack import CdkStack
from cdk.mvp_backlog_batch_stack import MVPBacklogBatchStack
from cdk.ecr_repository_stack import ECRRepositoryStack


app = cdk.App()

# Environment configuration for MVP account in us-east-1
env = cdk.Environment(
    account='984906149037',  # MVP account
    region='us-east-1'       # Region where secrets exist
)

# Original stack
CdkStack(app, "CdkStack", env=env)

# ECR Repository Stack (deploy first to get image URI)
ecr_stack = ECRRepositoryStack(app, "ECRRepositoryStack", env=env)

# MVP Backlog Batch Stack
MVPBacklogBatchStack(app, "MVPBacklogBatchStack", env=env)

app.synth()
