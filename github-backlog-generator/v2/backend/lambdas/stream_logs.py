"""
Lambda function to stream CloudWatch logs for GitHub Backlog Generator tasks.
"""
import json
import os
import boto3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


# Initialize AWS clients
logs = boto3.client('logs')


def lambda_handler(event: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stream logs from CloudWatch for a specific task.
    
    Query parameters:
    - log_stream: The log stream name (required)
    - next_token: Token for pagination (optional)
    - start_time: ISO timestamp to start from (optional)
    """
    try:
        # Get query parameters
        params = event.get('queryStringParameters', {}) or {}
        log_stream = params.get('log_stream')
        next_token = params.get('next_token')
        start_time = params.get('start_time')
        
        # Validate required parameters
        if not log_stream:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'log_stream parameter is required'})
            }
        
        # Get log group from environment
        log_group = os.environ.get('LOG_GROUP_NAME', '/ecs/github-backlog-generator')
        
        # Build request parameters
        request_params = {
            'logGroupName': log_group,
            'logStreamName': log_stream,
            'startFromHead': True
        }
        
        # Add pagination token if provided
        if next_token:
            request_params['nextToken'] = next_token
        
        # Add start time if provided
        if start_time:
            try:
                # Parse ISO timestamp and convert to milliseconds
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                request_params['startTime'] = int(start_dt.timestamp() * 1000)
            except ValueError:
                return {
                    'statusCode': 400,
                    'headers': get_cors_headers(),
                    'body': json.dumps({'error': 'Invalid start_time format. Use ISO 8601.'})
                }
        
        # Fetch logs from CloudWatch
        try:
            response = logs.get_log_events(**request_params)
        except logs.exceptions.ResourceNotFoundException:
            # Log stream might not exist yet if task just started
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'events': [],
                    'nextToken': None,
                    'nextBackwardToken': None,
                    'message': 'Log stream not found. Task may still be starting.'
                })
            }
        
        # Format log events
        events = format_log_events(response.get('events', []))
        
        # Check if we have more data
        has_more = len(events) > 0 or response.get('nextForwardToken') != next_token
        
        # Return formatted response
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'events': events,
                'nextToken': response.get('nextForwardToken'),
                'nextBackwardToken': response.get('nextBackwardToken'),
                'hasMore': has_more,
                'logStream': log_stream,
                'logGroup': log_group
            })
        }
        
    except Exception as e:
        print(f"Error streaming logs: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }


def format_log_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format CloudWatch log events for the UI.
    
    Args:
        events: Raw events from CloudWatch
        
    Returns:
        Formatted events with timestamp and message
    """
    formatted = []
    
    for event in events:
        # Convert timestamp from milliseconds to ISO format
        timestamp_ms = event.get('timestamp', 0)
        timestamp = datetime.fromtimestamp(timestamp_ms / 1000).isoformat()
        
        # Get the message and clean it up
        message = event.get('message', '').rstrip()
        
        # Parse JSON logs if applicable
        parsed_message = message
        try:
            # Check if the message is JSON
            if message.startswith('{') and message.endswith('}'):
                log_data = json.loads(message)
                # Extract relevant fields for structured logs
                if 'level' in log_data and 'msg' in log_data:
                    parsed_message = f"[{log_data.get('level', 'INFO')}] {log_data.get('msg', message)}"
                elif 'message' in log_data:
                    parsed_message = log_data.get('message', message)
        except json.JSONDecodeError:
            # Not JSON, use as-is
            pass
        
        formatted.append({
            'timestamp': timestamp,
            'message': parsed_message,
            'ingestionTime': event.get('ingestionTime'),
            'eventId': event.get('eventId')
        })
    
    return formatted


def get_cors_headers() -> Dict[str, str]:
    """Return CORS headers for API responses."""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Content-Type': 'application/json'
    }