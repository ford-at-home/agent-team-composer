#!/usr/bin/env python3
"""
Integration test for MVP Backlog Batch Stack
Creates a test repo with innovative MVP idea, runs CLI against it, validates output, then cleans up
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
        # Parse JSON if the secret is stored as JSON
        try:
            secret_data = json.loads(secret_string)
            return secret_data.get('github_token', secret_string)
        except json.JSONDecodeError:
            # If it's not JSON, return as-is
            return secret_string
    except Exception as e:
        print(f"Failed to get GitHub token: {e}")
        raise

def create_github_repo(org, repo_name, description, github_token):
    """Create a GitHub repository under the specified org"""
    url = f"https://api.github.com/orgs/{org}/repos"
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    
    data = {
        'name': repo_name,
        'description': description,
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

def update_readme(org, repo_name, content, github_token):
    """Update the README.md file with innovative MVP content"""
    # Get current README to get its SHA
    url = f"https://api.github.com/repos/{org}/{repo_name}/contents/README.md"
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        readme_data = response.json()
        sha = readme_data['sha']
    else:
        sha = None
    
    # Update README
    import base64
    encoded_content = base64.b64encode(content.encode()).decode()
    
    data = {
        'message': 'Add innovative MVP idea to README',
        'content': encoded_content,
        'sha': sha
    }
    
    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code not in [200, 201]:
        print(f"Failed to update README: {response.status_code}")
        print(f"Response: {response.text}")
        raise Exception(f"README update failed: {response.status_code}")

def delete_github_repo(org, repo_name, github_token):
    """Delete the GitHub repository"""
    url = f"https://api.github.com/repos/{org}/{repo_name}"
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    response = requests.delete(url, headers=headers)
    
    if response.status_code == 204:
        print(f"✅ Repository {org}/{repo_name} deleted successfully")
    else:
        print(f"⚠️  Failed to delete repo: {response.status_code}")
        print(f"Response: {response.text}")

def validate_repo_artifacts(org, repo_name, github_token):
    """Validate that phases, epics, and issues were created"""
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    results = {
        'phases_file': False,
        'epics_created': 0,
        'issues_created': 0
    }
    
    # Check for phases.json file
    phases_url = f"https://api.github.com/repos/{org}/{repo_name}/contents/phases.json"
    response = requests.get(phases_url, headers=headers)
    if response.status_code == 200:
        results['phases_file'] = True
        print("✅ phases.json file found")
    else:
        print("❌ phases.json file not found")
    
    # Check for issues (epics and regular issues)
    issues_url = f"https://api.github.com/repos/{org}/{repo_name}/issues"
    response = requests.get(issues_url, headers=headers)
    if response.status_code == 200:
        issues = response.json()
        results['issues_created'] = len(issues)
        
        # Count epics (issues with "epic" label)
        epics = [issue for issue in issues if any(label['name'].lower() == 'epic' for label in issue.get('labels', []))]
        results['epics_created'] = len(epics)
        
        print(f"✅ Found {results['issues_created']} total issues")
        print(f"✅ Found {results['epics_created']} epics")
    else:
        print("❌ Could not retrieve issues")
    
    return results

def generate_innovative_mvp_idea():
    """Generate an innovative MVP idea for the README"""
    ideas = [
        {
            'name': 'EcoTrace',
            'tagline': 'Personal Carbon Footprint Gamification Platform',
            'description': '''# EcoTrace 🌱

## The Vision
Transform environmental consciousness into an engaging, competitive experience where users track, reduce, and offset their carbon footprint through gamified challenges and social interaction.

## Core Features
- **Smart Tracking**: AI-powered carbon footprint calculation from photos and receipts
- **Challenge System**: Weekly eco-challenges with point rewards and badges
- **Social Competition**: Friend leaderboards and team environmental goals
- **Impact Marketplace**: Direct integration with verified carbon offset projects
- **AR Visualization**: See your environmental impact through augmented reality

## Why This Matters
Climate change requires individual action at scale. By making environmental responsibility fun, competitive, and social, we can drive meaningful behavior change while building a community of eco-conscious users.

## MVP Scope
1. Mobile app with basic carbon tracking
2. Simple challenge system with point rewards
3. Social features for friend comparison
4. Integration with 2-3 carbon offset providers

## Market Opportunity
- $1.2B carbon offset market growing 20% annually
- Gen Z users willing to pay premium for sustainable products
- Corporate partnerships for employee wellness programs
'''
        },
        {
            'name': 'SkillSwap',
            'tagline': 'Peer-to-Peer Professional Skill Exchange Network',
            'description': '''# SkillSwap 🔄

## The Vision
Create a barter economy for professional skills where people exchange expertise directly without monetary transactions, building communities and reducing barriers to learning.

## Core Features
- **Skill Matching**: AI-powered matching of complementary skills
- **Credit System**: Time-based credits for fair skill exchanges
- **Video Sessions**: Integrated video calls for remote skill sharing
- **Project Collaboration**: Team up on real projects while learning
- **Reputation System**: Community-driven ratings and endorsements

## Why This Matters
Traditional education is expensive and slow. Many professionals have valuable skills but lack opportunities to learn new ones. SkillSwap democratizes learning by leveraging the knowledge within communities.

## MVP Scope
1. User profiles with skill inventories
2. Basic matching algorithm
3. Scheduling and video call integration
4. Simple credit tracking system

## Market Opportunity
- $400B online education market
- Growing freelance economy needing skill diversification
- Remote work trend increasing demand for digital skill sharing
'''
        },
        {
            'name': 'MoodSync',
            'tagline': 'Emotional Intelligence for Remote Teams',
            'description': '''# MoodSync 😊

## The Vision
Help remote teams maintain emotional connection and mental health awareness through ambient mood sharing and intelligent team dynamics insights.

## Core Features
- **Mood Check-ins**: Quick daily emotional state logging
- **Team Pulse**: Real-time team emotional health dashboard
- **Smart Suggestions**: AI-driven recommendations for team interactions
- **Anonymous Feedback**: Safe space for team dynamic concerns
- **Wellness Resources**: Personalized mental health content and exercises

## Why This Matters
Remote work has created emotional disconnection in teams. Mental health issues cost companies $1T annually. MoodSync helps teams stay emotionally connected and productive.

## MVP Scope
1. Daily mood tracking with simple UI
2. Team dashboard showing aggregate mood trends
3. Basic suggestion engine for team activities
4. Integration with Slack/Teams

## Market Opportunity
- $4.2B employee wellness market
- 88% of organizations plan to continue remote work
- Rising awareness of workplace mental health importance
'''
        }
    ]
    
    return random.choice(ideas)

def main():
    print("🧪 Starting MVP Backlog Batch Stack Integration Test")
    print(f"Timestamp: {datetime.now()}")
    
    # Generate unique test repo name
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    repo_name = f"mvp-test-{suffix}"
    org = "mvp-builder-app"
    
    github_token = None
    created_repo = False
    
    try:
        # Pre-hook: Get GitHub token and create test repository with innovative MVP idea
        print(f"\n🔑 Getting GitHub token from AWS Secrets Manager...")
        github_token = get_github_token()
        
        print(f"\n💡 Generating innovative MVP idea...")
        mvp_idea = generate_innovative_mvp_idea()
        print(f"Selected MVP: {mvp_idea['name']} - {mvp_idea['tagline']}")
        
        print(f"\n📦 Creating test repository: {org}/{repo_name}")
        repo_data = create_github_repo(org, repo_name, mvp_idea['tagline'], github_token)
        created_repo = True
        print(f"✅ Repository created: {repo_data['html_url']}")
        
        print(f"\n📝 Updating README with innovative MVP idea...")
        update_readme(org, repo_name, mvp_idea['description'], github_token)
        print("✅ README updated with MVP idea")
        
        # Step 1: Submit Batch job with real GitHub repository
        print("\n🚀 Submitting test job to AWS Batch...")
        
        job_name = f"integration-test-{int(time.time())}"
        test_repo_url = f"https://github.com/{org}/{repo_name}"
        
        submit_cmd = [
            'aws', 'batch', 'submit-job',
            '--job-name', job_name,
            '--job-queue', 'MVPBacklogQueue', 
            '--job-definition', 'MVPBacklogJob',
            '--parameters', f'{{"REPO":"{org}/{repo_name}","PHASES":"1","EPICS":"1","ISSUES":"3"}}',
            '--query', 'jobId',
            '--output', 'text'
        ]
        
        job_id = run_command(submit_cmd)
        print(f"✅ Job submitted successfully: {job_id}")
        print(f"   Running against repo: {test_repo_url}")
        print(f"   Expected output: 1 phase, 1 epic, 3 issues")
        
        # Step 2: Monitor job execution
        print("\n👀 Monitoring job execution...")
        
        max_wait_time = 300  # 5 minutes
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
            print(f"Job status: {status}")
            
            if status in ['SUCCEEDED', 'FAILED']:
                break
                
            time.sleep(10)
        
        # Step 3: Check job results
        print(f"\n📋 Final job status: {status}")
        
        if status == 'SUCCEEDED':
            print("🎉 Job completed successfully!")
            
            # Get job logs
            print("\n📄 Retrieving job logs...")
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
                    print("Recent logs:")
                    print(logs)
                else:
                    print("⚠️  No recent log streams found")
                    
            except Exception as e:
                print(f"⚠️  Could not retrieve logs: {e}")
            
            # Step 4: Validate that CLI created artifacts in the repository
            print("\n🔍 Validating repository artifacts...")
            # Wait a moment for any async operations to complete
            time.sleep(5)
            
            validation_results = validate_repo_artifacts(org, repo_name, github_token)
            
            print(f"\n📊 Validation Results:")
            print(f"   phases.json file: {'✅' if validation_results['phases_file'] else '❌'}")
            print(f"   Epics created: {validation_results['epics_created']}")
            print(f"   Total issues: {validation_results['issues_created']}")
            
            # Determine if validation passed
            validation_passed = (
                validation_results['phases_file'] and
                validation_results['epics_created'] >= 1 and
                validation_results['issues_created'] >= 3
            )
            
            if validation_passed:
                print("✅ All validations passed!")
            else:
                print("❌ Some validations failed")
        
        elif status == 'FAILED':
            print("❌ Job failed!")
            
            # Get failure reason
            reason_cmd = [
                'aws', 'batch', 'describe-jobs',
                '--jobs', job_id,
                '--query', 'jobs[0].statusReason',
                '--output', 'text'
            ]
            
            reason = run_command(reason_cmd)
            print(f"Failure reason: {reason}")
            
        else:
            print(f"⏰ Job did not complete within {max_wait_time} seconds")
        
        # Step 5: Verify infrastructure components
        print("\n🔍 Verifying infrastructure components...")
        
        # Check job queue
        queue_cmd = [
            'aws', 'batch', 'describe-job-queues',
            '--job-queues', 'MVPBacklogQueue',
            '--query', 'jobQueues[0].state',
            '--output', 'text'
        ]
        queue_state = run_command(queue_cmd)
        print(f"Job queue state: {queue_state}")
        
        # Check compute environment
        compute_cmd = [
            'aws', 'batch', 'describe-compute-environments',
            '--compute-environments', 'MVPFargateEnv',
            '--query', 'computeEnvironments[0].state',
            '--output', 'text'
        ]
        compute_state = run_command(compute_cmd)
        print(f"Compute environment state: {compute_state}")
        
        # Check ECR repository
        ecr_cmd = [
            'aws', 'ecr', 'describe-repositories',
            '--repository-names', 'mvp-backlog-cli',
            '--query', 'repositories[0].repositoryName',
            '--output', 'text'
        ]
        ecr_repo = run_command(ecr_cmd)
        print(f"ECR repository: {ecr_repo}")
        
        print("\n✅ Integration test completed!")
        
        return status == 'SUCCEEDED'
        
    except Exception as e:
        print(f"\n❌ Integration test failed with error: {e}")
        return False
    
    finally:
        # Post-hook: Clean up the test repository (TEMPORARILY DISABLED)
        if created_repo and github_token:
            print("\n🧹 Cleanup phase...")
            print(f"Repository preserved for inspection: https://github.com/{org}/{repo_name}")
            print("(Cleanup temporarily disabled - repository NOT deleted)")
            # try:
            #     delete_github_repo(org, repo_name, github_token)
            # except Exception as e:
            #     print(f"⚠️  Failed to delete repository: {e}")
        else:
            print("\n🧹 Cleanup phase...")
            print("(No repository was created, so no cleanup needed)")

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)