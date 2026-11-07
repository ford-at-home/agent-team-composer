"""
End-to-end integration tests for GitHub Backlog Generator v2.

Tests the complete workflow from API request to task completion.
"""

import requests
import time
import pytest
import os
from typing import Dict, Any, List
import json


class TestEndToEnd:
    """Test complete user workflows."""
    
    @pytest.fixture(scope="class")
    def api_config(self) -> Dict[str, str]:
        """Get API configuration from environment."""
        return {
            'base_url': os.environ.get('API_URL', 'https://api.example.com'),
            'api_key': os.environ.get('API_KEY', 'test-api-key')
        }
    
    @pytest.fixture
    def test_repo(self) -> str:
        """Get test repository URL."""
        return os.environ.get('TEST_REPO_URL', 'https://github.com/octocat/Hello-World')
    
    def wait_for_task_completion(
        self, 
        api_config: Dict[str, str], 
        task_id: str, 
        timeout: int = 300
    ) -> Dict[str, Any]:
        """Wait for task to complete with timeout."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = requests.get(
                f"{api_config['base_url']}/status",
                params={'task_id': task_id},
                headers={'x-api-key': api_config['api_key']}
            )
            
            if response.status_code == 200:
                status_data = response.json()
                if status_data['lastStatus'] not in ['RUNNING', 'PROVISIONING', 'PENDING']:
                    return status_data
            
            time.sleep(5)
        
        raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")
    
    def test_complete_workflow_planning_phase(self, api_config, test_repo):
        """Test complete workflow for planning phase."""
        # Step 1: Start task
        start_response = requests.post(
            f"{api_config['base_url']}/start",
            json={
                'repo_url': test_repo,
                'phase': 'planning'
            },
            headers={'x-api-key': api_config['api_key']}
        )
        
        assert start_response.status_code == 200
        start_data = start_response.json()
        
        assert 'taskId' in start_data
        assert 'taskArn' in start_data
        assert 'logStream' in start_data
        
        task_id = start_data['taskId']
        log_stream = start_data['logStream']
        
        print(f"Started task: {task_id}")
        
        # Step 2: Check initial status
        status_response = requests.get(
            f"{api_config['base_url']}/status",
            params={'task_id': task_id},
            headers={'x-api-key': api_config['api_key']}
        )
        
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data['taskId'] == task_id
        assert status_data['lastStatus'] in ['PROVISIONING', 'RUNNING']
        
        # Step 3: Retrieve logs while running
        logs_retrieved = False
        for _ in range(5):  # Try a few times
            logs_response = requests.get(
                f"{api_config['base_url']}/logs",
                params={'log_stream': log_stream},
                headers={'x-api-key': api_config['api_key']}
            )
            
            if logs_response.status_code == 200:
                logs_data = logs_response.json()
                if logs_data.get('events'):
                    logs_retrieved = True
                    print(f"Retrieved {len(logs_data['events'])} log entries")
                    
                    # Verify log structure
                    for event in logs_data['events'][:5]:  # Check first 5
                        assert 'timestamp' in event
                        assert 'message' in event
                        assert 'eventId' in event
                    break
            
            time.sleep(2)
        
        assert logs_retrieved, "Should retrieve some logs during execution"
        
        # Step 4: Wait for completion
        final_status = self.wait_for_task_completion(api_config, task_id)
        
        assert final_status['lastStatus'] == 'STOPPED'
        assert 'exitCode' in final_status
        assert final_status['exitCode'] == 0
        
        print(f"Task completed successfully in {final_status.get('duration', 'unknown')} seconds")
        
        # Step 5: Retrieve all logs
        all_logs = []
        next_token = None
        
        while True:
            params = {'log_stream': log_stream}
            if next_token:
                params['next_token'] = next_token
            
            logs_response = requests.get(
                f"{api_config['base_url']}/logs",
                params=params,
                headers={'x-api-key': api_config['api_key']}
            )
            
            assert logs_response.status_code == 200
            logs_data = logs_response.json()
            
            all_logs.extend(logs_data.get('events', []))
            
            if not logs_data.get('hasMore'):
                break
            
            next_token = logs_data.get('nextToken')
        
        print(f"Retrieved total of {len(all_logs)} log entries")
        
        # Verify expected log messages
        log_messages = [event['message'] for event in all_logs]
        expected_patterns = [
            'Starting GitHub Backlog Generator',
            'Repository:',
            'Phase: planning',
            'Fetching repository',
            'Task completed'
        ]
        
        for pattern in expected_patterns:
            assert any(pattern in msg for msg in log_messages), \
                f"Expected to find '{pattern}' in logs"
    
    def test_error_handling_invalid_repo(self, api_config):
        """Test error handling with invalid repository."""
        # Start task with invalid repo
        start_response = requests.post(
            f"{api_config['base_url']}/start",
            json={
                'repo_url': 'not-a-valid-url',
                'phase': 'planning'
            },
            headers={'x-api-key': api_config['api_key']}
        )
        
        # Should either reject immediately or task should fail
        if start_response.status_code == 200:
            # Task started, should fail during execution
            start_data = start_response.json()
            task_id = start_data['taskId']
            
            final_status = self.wait_for_task_completion(api_config, task_id)
            
            assert final_status['lastStatus'] == 'STOPPED'
            assert final_status.get('exitCode', 1) != 0
        else:
            # Rejected immediately
            assert start_response.status_code == 400
            error_data = start_response.json()
            assert 'error' in error_data
    
    def test_error_handling_missing_phase(self, api_config, test_repo):
        """Test error handling with missing phase."""
        start_response = requests.post(
            f"{api_config['base_url']}/start",
            json={
                'repo_url': test_repo
                # phase is missing
            },
            headers={'x-api-key': api_config['api_key']}
        )
        
        assert start_response.status_code == 400
        error_data = start_response.json()
        assert 'error' in error_data
        assert 'phase' in error_data['error'].lower()
    
    def test_concurrent_tasks(self, api_config, test_repo):
        """Test running multiple tasks concurrently."""
        phases = ['planning', 'design', 'implementation']
        tasks = []
        
        # Start multiple tasks
        for phase in phases:
            start_response = requests.post(
                f"{api_config['base_url']}/start",
                json={
                    'repo_url': test_repo,
                    'phase': phase
                },
                headers={'x-api-key': api_config['api_key']}
            )
            
            assert start_response.status_code == 200
            task_data = start_response.json()
            tasks.append({
                'phase': phase,
                'task_id': task_data['taskId'],
                'log_stream': task_data['logStream']
            })
            
            print(f"Started task for {phase}: {task_data['taskId']}")
        
        # Monitor all tasks
        completed_tasks = []
        start_time = time.time()
        
        while len(completed_tasks) < len(tasks) and time.time() - start_time < 600:
            for task in tasks:
                if task['task_id'] in [t['task_id'] for t in completed_tasks]:
                    continue
                
                status_response = requests.get(
                    f"{api_config['base_url']}/status",
                    params={'task_id': task['task_id']},
                    headers={'x-api-key': api_config['api_key']}
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if status_data['lastStatus'] not in ['RUNNING', 'PROVISIONING', 'PENDING']:
                        completed_tasks.append(task)
                        print(f"Task {task['phase']} completed with status: {status_data['lastStatus']}")
            
            time.sleep(5)
        
        # Verify all completed successfully
        assert len(completed_tasks) == len(tasks)
        
        for task in completed_tasks:
            # Get final status
            status_response = requests.get(
                f"{api_config['base_url']}/status",
                params={'task_id': task['task_id']},
                headers={'x-api-key': api_config['api_key']}
            )
            
            status_data = status_response.json()
            assert status_data['lastStatus'] == 'STOPPED'
            assert status_data.get('exitCode') == 0
    
    def test_api_authentication(self, api_config, test_repo):
        """Test API authentication and authorization."""
        # Test without API key
        response = requests.post(
            f"{api_config['base_url']}/start",
            json={
                'repo_url': test_repo,
                'phase': 'planning'
            }
            # No API key header
        )
        
        assert response.status_code in [401, 403]
        
        # Test with invalid API key
        response = requests.post(
            f"{api_config['base_url']}/start",
            json={
                'repo_url': test_repo,
                'phase': 'planning'
            },
            headers={'x-api-key': 'invalid-key-12345'}
        )
        
        assert response.status_code in [401, 403]
    
    def test_log_pagination(self, api_config, test_repo):
        """Test log pagination for large outputs."""
        # Start a task
        start_response = requests.post(
            f"{api_config['base_url']}/start",
            json={
                'repo_url': test_repo,
                'phase': 'planning'
            },
            headers={'x-api-key': api_config['api_key']}
        )
        
        assert start_response.status_code == 200
        task_data = start_response.json()
        task_id = task_data['taskId']
        log_stream = task_data['logStream']
        
        # Wait for some logs to accumulate
        time.sleep(10)
        
        # Test pagination
        first_page = requests.get(
            f"{api_config['base_url']}/logs",
            params={
                'log_stream': log_stream,
                'limit': 10  # Small limit to force pagination
            },
            headers={'x-api-key': api_config['api_key']}
        )
        
        assert first_page.status_code == 200
        first_data = first_page.json()
        
        if first_data.get('hasMore') and first_data.get('nextToken'):
            # Get second page
            second_page = requests.get(
                f"{api_config['base_url']}/logs",
                params={
                    'log_stream': log_stream,
                    'next_token': first_data['nextToken'],
                    'limit': 10
                },
                headers={'x-api-key': api_config['api_key']}
            )
            
            assert second_page.status_code == 200
            second_data = second_page.json()
            
            # Verify no duplicate events
            first_ids = {e['eventId'] for e in first_data.get('events', [])}
            second_ids = {e['eventId'] for e in second_data.get('events', [])}
            assert len(first_ids & second_ids) == 0, "No duplicate events between pages"
    
    def test_performance_metrics(self, api_config, test_repo):
        """Test performance metrics and SLAs."""
        metrics = {
            'api_response_times': [],
            'task_startup_time': None,
            'log_latency': []
        }
        
        # Measure API response time
        start_time = time.time()
        start_response = requests.post(
            f"{api_config['base_url']}/start",
            json={
                'repo_url': test_repo,
                'phase': 'planning'
            },
            headers={'x-api-key': api_config['api_key']}
        )
        api_time = time.time() - start_time
        metrics['api_response_times'].append(api_time)
        
        assert start_response.status_code == 200
        assert api_time < 1.0, f"API response too slow: {api_time}s"
        
        task_data = start_response.json()
        task_id = task_data['taskId']
        log_stream = task_data['logStream']
        
        # Measure task startup time
        startup_start = time.time()
        while True:
            status_response = requests.get(
                f"{api_config['base_url']}/status",
                params={'task_id': task_id},
                headers={'x-api-key': api_config['api_key']}
            )
            
            if status_response.status_code == 200:
                status = status_response.json()['lastStatus']
                if status == 'RUNNING':
                    metrics['task_startup_time'] = time.time() - startup_start
                    break
            
            time.sleep(2)
            
            if time.time() - startup_start > 120:
                pytest.fail("Task took too long to start")
        
        assert metrics['task_startup_time'] < 60, \
            f"Task startup too slow: {metrics['task_startup_time']}s"
        
        # Measure log streaming latency
        for _ in range(3):
            log_start = time.time()
            logs_response = requests.get(
                f"{api_config['base_url']}/logs",
                params={'log_stream': log_stream},
                headers={'x-api-key': api_config['api_key']}
            )
            log_time = time.time() - log_start
            metrics['log_latency'].append(log_time)
            
            assert log_time < 5.0, f"Log retrieval too slow: {log_time}s"
            time.sleep(5)
        
        # Print performance summary
        print("\nPerformance Metrics:")
        print(f"- API Response Time: {metrics['api_response_times'][0]:.2f}s")
        print(f"- Task Startup Time: {metrics['task_startup_time']:.2f}s")
        print(f"- Avg Log Latency: {sum(metrics['log_latency'])/len(metrics['log_latency']):.2f}s")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])