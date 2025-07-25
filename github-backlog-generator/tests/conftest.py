"""Pytest configuration and shared fixtures."""

import os
import sys
import pytest
from unittest.mock import Mock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'test-anthropic-key')
    monkeypatch.setenv('GITHUB_TOKEN', 'test-github-token')
    monkeypatch.setenv('GITHUB_BACKLOG_MODEL', 'claude-3-sonnet-20240229')


@pytest.fixture
def sample_readme():
    """Sample README content for various tests."""
    return """# Awesome Project

A comprehensive project management platform built for modern teams.

## Features
- Task management with Kanban boards
- Real-time collaboration
- Time tracking and reporting
- Integration with popular tools
- AI-powered insights

## Tech Stack
- Backend: Python, FastAPI, PostgreSQL
- Frontend: React, TypeScript, TailwindCSS
- Infrastructure: Docker, Kubernetes, AWS
- AI/ML: OpenAI, LangChain

## Getting Started
1. Clone the repository
2. Install dependencies
3. Run the application

## Contributing
Please read CONTRIBUTING.md for details.

## License
MIT License"""


@pytest.fixture
def sample_phase():
    """Sample phase data."""
    return {
        'id': 'discovery',
        'title': '📚 Research & Discovery',
        'description': 'Initial research and requirements gathering phase',
        'suggestedRoles': ['Product Manager', 'UX Researcher', 'Business Analyst'],
        'dueDate': '2024-02-15T00:00:00Z'
    }


@pytest.fixture
def sample_epic():
    """Sample epic data."""
    return {
        'title': 'User Authentication System',
        'description': 'Build a secure, scalable authentication system with SSO support',
        'suggestedRoles': ['Backend Developer', 'Security Engineer', 'DevOps'],
        'tasks': [
            {
                'title': 'Design authentication architecture',
                'description': 'Create detailed architecture for auth system',
                'suggestedRole': 'System Architect'
            },
            {
                'title': 'Implement JWT token management',
                'description': 'Build JWT token generation and validation',
                'suggestedRole': 'Backend Developer'
            }
        ]
    }


@pytest.fixture
def sample_task():
    """Sample task data."""
    return {
        'title': 'Implement password reset flow',
        'suggestedRole': 'Backend Developer',
        'priority': 'high',
        'estimatedEffort': 'medium'
    }


@pytest.fixture
def sample_task_description():
    """Sample task description data."""
    return {
        'title': 'Implement password reset flow',
        'description': '### Description\n\nImplement secure password reset functionality...',
        'acceptanceCriteria': [
            '✅ User can request password reset via email',
            '✅ Reset tokens expire after 1 hour',
            '✅ Passwords are validated for strength'
        ],
        'technicalNotes': 'Use Django\'s built-in password reset views...',
        'dependencies': [
            'Email service must be configured',
            'User model must have email field'
        ]
    }