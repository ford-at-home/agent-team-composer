#!/usr/bin/env python3
"""
Smoke Test for MVP Backlog Batch Stack
Quick validation test that creates a minimal test repo and runs basic CLI workflow
Used for rapid development cycles and basic functionality verification
"""

import time
import json
import subprocess
import random
import string
import requests
import os
from datetime import datetime

def run_command(cmd, profile="mvp"):
    """Run AWS CLI command with error handling"""
    try:
        if isinstance(cmd, list):
            if '--profile' not in cmd:
                cmd.extend(['--profile', profile])
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        else:
            if '--profile' not in cmd:
                cmd += f' --profile {profile}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e.cmd}")
        print(f"Error: {e.stderr}")
        raise

def get_github_token():
    """Get GitHub token from AWS Secrets Manager"""
    try:
        cmd = [
            'aws', 'secretsmanager', 'get-secret-value',
            '--secret-id', 'github_token',
            '--query', 'SecretString',
            '--output', 'text'
        ]
        secret_string = run_command(cmd)
        try:
            secret_data = json.loads(secret_string)
            return secret_data.get('github_token', secret_string)
        except json.JSONDecodeError:
            return secret_string
    except Exception as e:
        print(f"Failed to get GitHub token: {e}")
        raise

def create_github_repo(org, repo_name, github_token):
    """Create a minimal GitHub repository"""
    url = f"https://api.github.com/orgs/{org}/repos"
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    
    data = {
        'name': repo_name,
        'description': 'Focused test repo for Fargate CLI testing',
        'private': False,
        'auto_init': True,
        'has_issues': True,
        'has_projects': True,
        'has_wiki': False
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        return response.json()
    else:
        print(f"Failed to create repo: {response.status_code}")
        print(f"Response: {response.text}")
        raise Exception(f"GitHub repo creation failed: {response.status_code}")

def update_readme(org, repo_name, github_token):
    """Update README with minimal test content"""
    url = f"https://api.github.com/repos/{org}/{repo_name}/contents/README.md"
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Get current README
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        readme_data = response.json()
        sha = readme_data['sha']
    else:
        sha = None
    
    # Minimal test content
    content = """# Test MVP - Digital Minimalism App

## The Vision
A simple app to help users track and reduce their digital screen time through mindful usage patterns.

## Core Features  
- Screen time tracking
- Usage goal setting
- Daily mindfulness reminders
- Progress visualization

## MVP Scope
1. Basic time tracking functionality
2. Simple goal setting interface  
3. Daily progress dashboard
4. Reminder notification system

This is a focused test repository for validating the CLI workflow.
"""
    
    import base64
    encoded_content = base64.b64encode(content.encode()).decode()
    
    data = {
        'message': 'Add minimal test MVP content',
        'content': encoded_content,
        'sha': sha
    }
    
    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code not in [200, 201]:
        print(f"Failed to update README: {response.status_code}")
        print(f"Response: {response.text}")
        raise Exception(f"README update failed: {response.status_code}")

def main():
    print("🚬 Smoke Test - Quick Validation of AWS Batch Stack")
    print(f"Timestamp: {datetime.now()}")
    
    # Generate unique test repo name
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    repo_name = f"smoke-test-{suffix}"
    org = "mvp-builder-app"
    
    github_token = None
    created_repo = False
    
    try:
        # Step 1: Create minimal test repository
        print(f"\n🔑 Getting GitHub token...")
        github_token = get_github_token()
        
        print(f"\n📦 Creating smoke test repository: {org}/{repo_name}")
        repo_data = create_github_repo(org, repo_name, github_token)
        created_repo = True
        print(f"✅ Repository created: {repo_data['html_url']}")
        
        print(f"\n📝 Adding minimal test content...")
        update_readme(org, repo_name, github_token)
        print("✅ README updated with test content")
        
        # Step 2: Submit targeted Batch job with command override
        print("\n🚀 Submitting smoke test job...")
        
        job_name = f"focused-test-{int(time.time())}"
        repo_full_name = f"{org}/{repo_name}"
        
        # Create job definition with targeted command for this specific test
        print(f"   Target repo: {repo_full_name}")
        print(f"   Target workflow: generate-phases -> create-epics -> create-issues (limited)")
        
        # Submit job with container overrides for environment variables
        container_overrides = {
            "environment": [
                {"name": "REPO", "value": repo_full_name},
                {"name": "PHASES", "value": "1"},
                {"name": "EPICS", "value": "1"},
                {"name": "ISSUES", "value": "2"}
            ]
        }
        
        submit_cmd = [
            'aws', 'batch', 'submit-job',
            '--job-name', job_name,
            '--job-queue', 'MVPBacklogQueue', 
            '--job-definition', 'MVPBacklogJob',
            '--container-overrides', json.dumps(container_overrides),
            '--query', 'jobId',
            '--output', 'text'
        ]
        
        job_id = run_command(submit_cmd)
        print(f"✅ Smoke test job submitted: {job_id}")
        
        # Step 3: Monitor execution
        print("\n👀 Monitoring smoke test job execution...")
        
        max_wait_time = 180  # 3 minutes for focused test
        start_time = time.time()
        status = 'PENDING'
        
        while time.time() - start_time < max_wait_time:
            status_cmd = [
                'aws', 'batch', 'describe-jobs',
                '--jobs', job_id,
                '--query', 'jobs[0].status',
                '--output', 'text'
            ]
            
            status = run_command(status_cmd)
            elapsed = int(time.time() - start_time)
            print(f"[{elapsed}s] Job status: {status}")
            
            if status in ['SUCCEEDED', 'FAILED']:
                break
                
            time.sleep(15)
        
        # Step 4: Get results
        print(f"\n📋 Final status: {status}")
        
        # Get logs regardless of status
        print("\n📄 Retrieving execution logs...")
        try:
            log_streams_cmd = [
                'aws', 'logs', 'describe-log-streams',
                '--log-group-name', '/mvp-backlog',
                '--order-by', 'LastEventTime',
                '--descending',
                '--max-items', '1',
                '--query', 'logStreams[0].logStreamName',
                '--output', 'text'
            ]
            
            log_stream = run_command(log_streams_cmd)
            
            if log_stream and log_stream != 'None':
                logs_cmd = [
                    'aws', 'logs', 'get-log-events',
                    '--log-group-name', '/mvp-backlog',
                    '--log-stream-name', log_stream,
                    '--query', 'events[*].message',
                    '--output', 'text'
                ]
                
                logs = run_command(logs_cmd)
                print("📝 Execution logs:")
                print("-" * 60)
                print(logs)
                print("-" * 60)
            else:
                print("⚠️  No recent log streams found")
                
        except Exception as e:
            print(f"⚠️  Could not retrieve logs: {e}")
        
        # Step 5: Quick validation
        if status == 'SUCCEEDED':
            print("\n🔍 Quick validation...")
            time.sleep(3)
            
            # Check for issues created
            headers = {
                'Authorization': f'token {github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            issues_url = f"https://api.github.com/repos/{org}/{repo_name}/issues"
            response = requests.get(issues_url, headers=headers)
            
            if response.status_code == 200:
                issues = response.json()
                print(f"✅ Found {len(issues)} issues created")
                
                if issues:
                    print("   Issue titles:")
                    for issue in issues[:3]:  # Show first 3
                        print(f"   - {issue['title']}")
            else:
                print("⚠️  Could not check issues")
        
        return status == 'SUCCEEDED'
        
    except Exception as e:
        print(f"\n❌ Smoke test failed: {e}")
        return False
    
    finally:
        # Cleanup
        if created_repo and github_token:
            print("\n🧹 Cleanup phase...")
            try:
                headers = {
                    'Authorization': f'token {github_token}',
                    'Accept': 'application/vnd.github+json'
                }
                response = requests.delete(f'https://api.github.com/repos/{org}/{repo_name}', headers=headers)
                if response.status_code == 204:
                    print(f"✅ Test repository deleted: {org}/{repo_name}")
                else:
                    print(f"⚠️  Failed to delete repository: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"⚠️  Failed to delete repository: {e}")

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)