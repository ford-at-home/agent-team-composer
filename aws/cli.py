#!/usr/bin/env python3
"""
MVP Backlog CLI - Real implementation
Generates phases, epics, and issues for MVP development using AI
"""

import sys
import json
import os
import argparse
import requests
import base64
from datetime import datetime
from typing import Dict, List, Any

class MVPBacklogCLI:
    def __init__(self):
        # Parse GitHub token from JSON if needed
        raw_github_token = os.environ.get("GITHUB_TOKEN", "")
        if raw_github_token.startswith('{"github_token"'):
            try:
                token_data = json.loads(raw_github_token)
                self.github_token = token_data.get('github_token', '')
            except json.JSONDecodeError:
                self.github_token = raw_github_token
        else:
            self.github_token = raw_github_token
            
        self.anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.openai_key = os.environ.get("OPENAI_API_KEY", "")
        
        # Validate required tokens
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable required")
        
        self.github_headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github+json',
            'Content-Type': 'application/json',
            'User-Agent': 'mvp-backlog-cli-aws-batch'  # REQUIRED by GitHub!
        }

    def get_repo_readme(self, repo: str) -> str:
        """Fetch README content from GitHub repository"""
        url = f"https://api.github.com/repos/{repo}/contents/README.md"
        
        response = requests.get(url, headers=self.github_headers)
        if response.status_code == 200:
            content_data = response.json()
            # Decode base64 content
            content = base64.b64decode(content_data['content']).decode('utf-8')
            return content
        else:
            print(f"Warning: Could not fetch README from {repo}")
            return ""

    def generate_phases(self, repo: str, readme_content: str) -> List[Dict[str, Any]]:
        """Generate development phases based on README content using AI"""
        if not self.anthropic_key:
            print("⚠️  No Anthropic API key - using fallback template")
            return self._fallback_phases()
        
        try:
            prompt = f"""Analyze this MVP README and generate a detailed development phase for building this product:

{readme_content}

Based on this MVP idea, create a JSON object for ONE comprehensive development phase that covers the most critical MVP features. The phase should be ambitious but achievable for a 4-6 week sprint.

Return ONLY a valid JSON object in this exact format:
{{
    "id": 1,
    "name": "Descriptive Phase Name",
    "description": "Detailed description of what this phase accomplishes",
    "duration_weeks": 4-6,
    "priority": "high",
    "status": "planned",
    "deliverables": [
        "Specific deliverable 1",
        "Specific deliverable 2", 
        "Specific deliverable 3",
        "Specific deliverable 4"
    ]
}}

Make the phase name, description, and deliverables highly specific to this MVP idea. Focus on the core value proposition and essential features needed for market validation."""

            print("🤖 Generating AI-powered development phase...")
            
            # Call Anthropic API
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers={
                    'Authorization': f'Bearer {self.anthropic_key}',
                    'Content-Type': 'application/json',
                    'anthropic-version': '2023-06-01'
                },
                json={
                    'model': 'claude-3-sonnet-20240229',
                    'max_tokens': 1000,
                    'messages': [
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ]
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['content'][0]['text'].strip()
                
                # Parse JSON response
                try:
                    phase_data = json.loads(content)
                    print("✅ AI-generated phase created successfully")
                    return [phase_data]
                except json.JSONDecodeError as e:
                    print(f"⚠️  AI response parsing failed: {e}")
                    print(f"Raw response: {content[:200]}...")
                    return self._fallback_phases()
            else:
                print(f"⚠️  Anthropic API error: {response.status_code}")
                return self._fallback_phases()
                
        except Exception as e:
            print(f"⚠️  AI generation failed: {e}")
            return self._fallback_phases()
    
    def _fallback_phases(self):
        """Fallback to template phases if AI fails"""
        return [
            {
                "id": 1,
                "name": "Foundation & Core Features",
                "description": "Build the fundamental architecture and core MVP features",
                "duration_weeks": 4,
                "priority": "high",
                "status": "planned",
                "deliverables": [
                    "Basic application architecture",
                    "Core feature implementation",
                    "Database setup",
                    "Basic UI/UX"
                ]
            }
        ]

    def create_github_issue(self, repo: str, title: str, body: str, labels: List[str] = None) -> Dict[str, Any]:
        """Create a GitHub issue"""
        url = f"https://api.github.com/repos/{repo}/issues"
        
        data = {
            'title': title,
            'body': body,
            'labels': labels or []
        }
        
        response = requests.post(url, headers=self.github_headers, json=data)
        
        if response.status_code == 201:
            return response.json()
        else:
            print(f"Failed to create issue: {response.status_code}")
            print(f"Response: {response.text}")
            return {}

    def create_epic(self, repo: str, phase: Dict[str, Any]) -> Dict[str, Any]:
        """Create an AI-enhanced epic (GitHub issue with epic label)"""
        
        if not self.anthropic_key:
            return self._create_template_epic(repo, phase)
        
        try:
            prompt = f"""Create a detailed GitHub epic description for this development phase:

Phase Name: {phase['name']}
Description: {phase['description']}
Duration: {phase['duration_weeks']} weeks
Deliverables: {', '.join(phase['deliverables'])}

Generate a comprehensive epic description that includes:
1. Clear problem statement and objectives
2. Detailed acceptance criteria  
3. Technical approach overview
4. Risk considerations
5. Success metrics

Write this as if you're a senior product manager creating an epic for an experienced development team. Be specific and actionable.

Format as GitHub markdown with clear sections."""

            print("🤖 Generating AI-powered epic content...")
            
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers={
                    'Authorization': f'Bearer {self.anthropic_key}',
                    'Content-Type': 'application/json',
                    'anthropic-version': '2023-06-01'
                },
                json={
                    'model': 'claude-3-sonnet-20240229',
                    'max_tokens': 1500,
                    'messages': [
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ]
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_content = result['content'][0]['text'].strip()
                
                title = f"Epic: {phase['name']}"
                body = f"{ai_content}\n\n---\n*This epic was generated by MVP Backlog CLI with AI assistance*"
                
                print("✅ AI-enhanced epic content generated")
                return self.create_github_issue(repo, title, body, ['epic', 'enhancement'])
            else:
                print(f"⚠️  AI epic generation failed: {response.status_code}")
                return self._create_template_epic(repo, phase)
                
        except Exception as e:
            print(f"⚠️  AI epic generation error: {e}")
            return self._create_template_epic(repo, phase)
    
    def _create_template_epic(self, repo: str, phase: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback template epic creation"""
        title = f"Epic: {phase['name']}"
        body = f"""# {phase['name']}

## Description
{phase['description']}

## Duration
{phase['duration_weeks']} weeks

## Priority
{phase['priority']}

## Deliverables
{chr(10).join(f"- {item}" for item in phase['deliverables'])}

## Status
- [ ] Planning phase
- [ ] Development phase  
- [ ] Testing phase
- [ ] Deployment phase

---
*This epic was generated automatically by MVP Backlog CLI*
"""
        
        return self.create_github_issue(repo, title, body, ['epic', 'enhancement'])

    def create_issues_for_phase(self, repo: str, phase: Dict[str, Any], num_issues: int = 3) -> List[Dict[str, Any]]:
        """Create individual issues for a phase"""
        issues = []
        
        issue_templates = [
            {
                'title': f"Setup project architecture for {phase['name']}",
                'body': f"Initialize the foundational architecture needed for {phase['name']}.\n\n**Acceptance Criteria:**\n- [ ] Project structure created\n- [ ] Dependencies configured\n- [ ] Basic framework setup\n\n*Auto-generated from phase: {phase['name']}*",
                'labels': ['enhancement', 'architecture']
            },
            {
                'title': f"Implement core functionality for {phase['name']}",
                'body': f"Build the main features defined in {phase['name']}.\n\n**Acceptance Criteria:**\n- [ ] Core features implemented\n- [ ] Basic error handling\n- [ ] Unit tests added\n\n*Auto-generated from phase: {phase['name']}*",
                'labels': ['feature', 'development']
            },
            {
                'title': f"Create documentation for {phase['name']}",
                'body': f"Document the implementation and usage of {phase['name']}.\n\n**Acceptance Criteria:**\n- [ ] API documentation\n- [ ] User guide\n- [ ] Code comments\n\n*Auto-generated from phase: {phase['name']}*",
                'labels': ['documentation']
            }
        ]
        
        for i, template in enumerate(issue_templates[:num_issues]):
            issue = self.create_github_issue(
                repo, 
                template['title'], 
                template['body'], 
                template['labels']
            )
            if issue:
                issues.append(issue)
        
        return issues

    def commit_phases_file(self, repo: str, phases: List[Dict[str, Any]]) -> bool:
        """Commit phases.json file to the repository"""
        url = f"https://api.github.com/repos/{repo}/contents/phases.json"
        
        phases_json = json.dumps(phases, indent=2)
        encoded_content = base64.b64encode(phases_json.encode()).decode()
        
        data = {
            'message': 'Add MVP development phases',
            'content': encoded_content
        }
        
        response = requests.put(url, headers=self.github_headers, json=data)
        
        if response.status_code == 201:
            print("✅ phases.json file created successfully")
            return True
        else:
            print(f"❌ Failed to create phases.json: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    def run(self, repo: str, num_phases: int = 1, num_epics: int = 1, num_issues: int = 3):
        """Main CLI execution - mimics real CLI workflow"""
        print(f"🚀 MVP Backlog CLI started at {datetime.now()}")
        print(f"📋 Processing repository: {repo}")
        print(f"🎯 Real MVP generation workflow:")
        print(f"   - Generate ALL phases for the MVP")
        print(f"   - Generate ALL epics for the FIRST phase") 
        print(f"   - Generate ALL issues for the FIRST epic of the FIRST phase")
        
        # Validate tokens
        github_status = "YES" if self.github_token else "NO"
        anthropic_status = "YES" if self.anthropic_key else "NO"
        openai_status = "YES" if self.openai_key else "NO"
        
        print(f"🔐 GitHub Token configured: {github_status}")
        print(f"🔐 Anthropic API Key configured: {anthropic_status}")
        print(f"🔐 OpenAI API Key configured: {openai_status}")
        
        # Diagnostic logging for token format
        if self.github_token:
            print(f"🔍 Token format check: {repr(self.github_token[:20])}...{repr(self.github_token[-10:])}")
            print(f"🔍 Token length: {len(self.github_token)}")
        
        # Test GitHub connectivity and authentication
        print(f"\n🧪 Testing GitHub API connectivity...")
        try:
            test_response = requests.get("https://api.github.com/user", headers=self.github_headers)
            print(f"🔗 GitHub API test - Status: {test_response.status_code}")
            if test_response.status_code == 200:
                user_data = test_response.json()
                print(f"✅ Authenticated as: {user_data.get('login', 'unknown')}")
            else:
                print(f"❌ GitHub API error: {test_response.text}")
        except Exception as e:
            print(f"❌ GitHub connectivity failed: {e}")
        
        # Check outbound IP and DNS resolution
        try:
            print(f"\n🌐 Network diagnostics...")
            ip_response = requests.get("https://ifconfig.me", timeout=10)
            print(f"📡 Outbound IP: {ip_response.text}")
        except Exception as e:
            print(f"⚠️  Could not determine outbound IP: {e}")
        
        try:
            dns_test = requests.get("https://api.github.com", timeout=5)
            print(f"🔍 DNS resolution to GitHub: OK ({dns_test.status_code})")
        except Exception as e:
            print(f"❌ DNS/connectivity issue: {e}")
        
        try:
            # Step 1: Fetch README content
            print(f"\n📖 Fetching README from {repo}...")
            readme_content = self.get_repo_readme(repo)
            
            if readme_content:
                print(f"✅ README fetched ({len(readme_content)} characters)")
            else:
                print("⚠️  No README found, proceeding with default phases")
            
            # Step 2: Generate phases
            print(f"\n🏗️  Generating {num_phases} development phase(s)...")
            phases = self.generate_phases(repo, readme_content)[:num_phases]
            print(f"✅ Generated {len(phases)} phase(s)")
            
            # Step 3: Commit phases.json
            print(f"\n💾 Committing phases.json to repository...")
            phases_committed = self.commit_phases_file(repo, phases)
            
            # Step 4: Create epics
            print(f"\n📝 Creating {num_epics} epic(s)...")
            epics_created = []
            for i, phase in enumerate(phases[:num_epics]):
                epic = self.create_epic(repo, phase)
                if epic:
                    epics_created.append(epic)
                    print(f"✅ Epic created: {epic.get('title', 'Unknown')}")
            
            # Step 5: Create issues
            print(f"\n🎫 Creating {num_issues} issue(s)...")
            issues_created = []
            if phases:
                phase_issues = self.create_issues_for_phase(repo, phases[0], num_issues)
                issues_created.extend(phase_issues)
                print(f"✅ Created {len(phase_issues)} issues")
            
            # Summary
            print(f"\n📊 Execution Summary:")
            print(f"   Repository: {repo}")
            print(f"   Phases file: {'✅' if phases_committed else '❌'}")
            print(f"   Epics created: {len(epics_created)}")
            print(f"   Issues created: {len(issues_created)}")
            print(f"   Total GitHub items: {len(epics_created) + len(issues_created)}")
            
            result = {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "repository": repo,
                "phases_created": len(phases),
                "phases_committed": phases_committed,
                "epics_created": len(epics_created),
                "issues_created": len(issues_created),
                "total_items": len(epics_created) + len(issues_created)
            }
            
            print(f"\n🎉 MVP Backlog CLI completed successfully!")
            print(json.dumps(result, indent=2))
            return 0
            
        except Exception as e:
            print(f"\n❌ CLI execution failed: {e}")
            return 1

def main():
    parser = argparse.ArgumentParser(description='MVP Backlog CLI - Generate phases, epics, and issues')
    parser.add_argument('command', choices=['run'], help='Command to execute')
    parser.add_argument('--repo', required=True, help='GitHub repository (format: owner/repo)')
    parser.add_argument('--phases', type=int, default=1, help='Number of phases to generate')
    parser.add_argument('--epics', type=int, default=1, help='Number of epics to create')  
    parser.add_argument('--issues', type=int, default=3, help='Number of issues to create')
    
    args = parser.parse_args()
    
    try:
        cli = MVPBacklogCLI()
        return cli.run(args.repo, args.phases, args.epics, args.issues)
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())