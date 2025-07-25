"""
Lambda function to check ECS task status for GitHub Backlog Generator.
"""
import json
import os
import boto3
from typing import Dict, Any, List, Optional


# Initialize AWS clients
ecs = boto3.client('ecs')


def lambda_handler(event: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get the status of an ECS task.
    
    Query parameters:
    - task_arn: The full ARN of the task (required)
    - task_id: Alternative to task_arn, the short task ID
    """
    try:
        # Get query parameters
        params = event.get('queryStringParameters', {}) or {}
        task_arn = params.get('task_arn')
        task_id = params.get('task_id')
        
        # Validate input
        if not task_arn and not task_id:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Either task_arn or task_id is required'})
            }
        
        # Get cluster name
        cluster_name = os.environ['ECS_CLUSTER_NAME']
        
        # If only task_id provided, list tasks to find the full ARN
        if task_id and not task_arn:
            list_response = ecs.list_tasks(
                cluster=cluster_name,
                desiredStatus='RUNNING'
            )
            
            # Check stopped tasks if not found in running
            if not any(task_id in arn for arn in list_response.get('taskArns', [])):
                list_response = ecs.list_tasks(
                    cluster=cluster_name,
                    desiredStatus='STOPPED'
                )
            
            # Find matching task ARN
            for arn in list_response.get('taskArns', []):
                if task_id in arn:
                    task_arn = arn
                    break
            
            if not task_arn:
                return {
                    'statusCode': 404,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': f'Task {task_id} not found'})
                }
        
        # Describe the task
        response = ecs.describe_tasks(
            cluster=cluster_name,
            tasks=[task_arn]
        )
        
        if not response.get('tasks'):
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Task not found'})
            }
        
        # Get task details
        task = response['tasks'][0]
        
        # Extract relevant information
        task_info = format_task_info(task)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(task_info)
        }
        
    except Exception as e:
        print(f"Error getting task status: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }


def format_task_info(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format ECS task information for the response.
    
    Args:
        task: Raw task data from ECS
        
    Returns:
        Formatted task information
    """
    # Extract basic info
    task_arn = task.get('taskArn', '')
    task_id = task_arn.split('/')[-1] if task_arn else ''
    
    # Get container status
    containers = task.get('containers', [])
    container_status = {}
    if containers:
        container = containers[0]  # We only have one container
        container_status = {
            'name': container.get('name'),
            'lastStatus': container.get('lastStatus'),
            'exitCode': container.get('exitCode'),
            'reason': container.get('reason'),
            'runtimeId': container.get('runtimeId')
        }
    
    # Get task timing
    created_at = task.get('createdAt')
    started_at = task.get('startedAt')
    stopped_at = task.get('stoppedAt')
    
    # Format timestamps
    def format_timestamp(ts):
        return ts.isoformat() if ts else None
    
    # Calculate duration if task has stopped
    duration = None
    if started_at and stopped_at:
        duration = int((stopped_at - started_at).total_seconds())
    elif started_at:
        # Still running
        from datetime import datetime
        duration = int((datetime.now(started_at.tzinfo) - started_at).total_seconds())
    
    # Get task tags
    tags = {}
    for tag in task.get('tags', []):
        tags[tag.get('key')] = tag.get('value')
    
    # Get stop reason if task stopped
    stop_reason = None
    if task.get('stoppedReason'):
        stop_reason = task.get('stoppedReason')
    elif task.get('stopCode'):
        stop_reason = f"Stop code: {task.get('stopCode')}"
    
    return {
        'taskArn': task_arn,
        'taskId': task_id,
        'lastStatus': task.get('lastStatus'),
        'desiredStatus': task.get('desiredStatus'),
        'createdAt': format_timestamp(created_at),
        'startedAt': format_timestamp(started_at),
        'stoppedAt': format_timestamp(stopped_at),
        'duration': duration,
        'launchType': task.get('launchType'),
        'platformVersion': task.get('platformVersion'),
        'cpu': task.get('cpu'),
        'memory': task.get('memory'),
        'containerStatus': container_status,
        'stopReason': stop_reason,
        'tags': tags,
        'isRunning': task.get('lastStatus') == 'RUNNING'
    }


def get_cors_headers() -> Dict[str, str]:
    """Return CORS headers for API responses."""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Content-Type': 'application/json'
    }