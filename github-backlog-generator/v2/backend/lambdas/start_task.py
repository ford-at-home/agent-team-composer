"""
Lambda function to start ECS tasks for GitHub Backlog Generator.
"""
import json
import os
import uuid
import boto3
from datetime import datetime
from typing import Dict, Any


# Initialize AWS clients
ecs = boto3.client('ecs')


def lambda_handler(event: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Start an ECS task for the GitHub Backlog Generator.
    
    Expected event body:
    {
        "repo_url": "https://github.com/owner/repo",
        "phase": 1
    }
    """
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        # Validate input
        repo_url = body.get('repo_url')
        phase = body.get('phase', 1)
        
        if not repo_url:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'repo_url is required'})
            }
        
        # Validate phase number
        if not isinstance(phase, int) or phase < 1 or phase > 10:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'phase must be an integer between 1 and 10'})
            }
        
        # Generate unique task ID
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        
        # Get environment variables
        cluster_name = os.environ['ECS_CLUSTER_NAME']
        task_definition_arn = os.environ['TASK_DEFINITION_ARN']
        subnet_ids = os.environ['SUBNET_IDS'].split(',')
        security_group_id = os.environ['SECURITY_GROUP_ID']
        
        # Start ECS task
        response = ecs.run_task(
            cluster=cluster_name,
            taskDefinition=task_definition_arn,
            launchType='FARGATE',
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': subnet_ids,
                    'securityGroups': [security_group_id],
                    'assignPublicIp': 'DISABLED'  # Tasks in private subnet
                }
            },
            overrides={
                'containerOverrides': [{
                    'name': 'github-backlog-generator',
                    'environment': [
                        {'name': 'REPO_URL', 'value': repo_url},
                        {'name': 'PHASE', 'value': str(phase)},
                        {'name': 'TASK_ID', 'value': task_id}
                    ]
                }]
            },
            tags=[
                {'key': 'TaskId', 'value': task_id},
                {'key': 'Repository', 'value': repo_url},
                {'key': 'Phase', 'value': str(phase)},
                {'key': 'StartTime', 'value': datetime.utcnow().isoformat()}
            ],
            propagateTags='TASK_DEFINITION'
        )
        
        # Check if task started successfully
        if not response.get('tasks'):
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Failed to start ECS task'})
            }
        
        # Get task details
        task = response['tasks'][0]
        task_arn = task['taskArn']
        task_id_from_arn = task_arn.split('/')[-1]
        
        # Construct log stream name
        # Format: ecs/{container-name}/{task-id}
        log_stream = f"ecs/github-backlog-generator/{task_id_from_arn}"
        
        # Return task information
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'task_id': task_id,
                'task_arn': task_arn,
                'ecs_task_id': task_id_from_arn,
                'log_group': os.environ.get('LOG_GROUP_NAME', '/ecs/github-backlog-generator'),
                'log_stream': log_stream,
                'status': 'PROVISIONING',
                'repo_url': repo_url,
                'phase': phase,
                'started_at': datetime.utcnow().isoformat()
            })
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Invalid JSON in request body'})
        }
    except Exception as e:
        print(f"Error starting task: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }


def get_cors_headers() -> Dict[str, str]:
    """Return CORS headers for API responses."""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Content-Type': 'application/json'
    }