"""Task Generator - Creates tasks for an epic and detailed descriptions for each task."""

import json
import os
import re
from typing import Dict, List, Optional

from anthropic import Anthropic
from pydantic import BaseModel, Field, ValidationError


class Task(BaseModel):
    """Model for a task within an epic."""
    title: str = Field(description="Clear, actionable task title")
    suggestedRole: str = Field(description="The role best suited for this task")
    priority: str = Field(description="Task priority: high, medium, or low")
    estimatedEffort: str = Field(description="Estimated effort: small, medium, large")


class EpicTasks(BaseModel):
    """Model for all tasks within an epic."""
    epicTitle: str = Field(description="Epic title")
    tasks: List[Task] = Field(description="List of 5-10 specific tasks for this epic")


class TaskDescription(BaseModel):
    """Model for a detailed task description."""
    title: str = Field(description="Task title")
    description: str = Field(description="Detailed description of the task")
    acceptanceCriteria: List[str] = Field(description="List of acceptance criteria")
    technicalNotes: str = Field(description="Technical considerations or notes")
    dependencies: List[str] = Field(description="List of dependencies or prerequisites")
    suggestedRole: str = Field(description="Suggested role for task execution")
    priority: str = Field(description="Task priority level")
    estimatedEffort: str = Field(description="Estimated effort or complexity")


class TaskGenerator:
    """Generator for creating tasks and their detailed descriptions."""
    
    def __init__(self, api_key: str):
        self.anthropic = Anthropic(api_key=api_key)
        self.max_retries = 3
    
    def generate_tasks_for_epic(self, epic: Dict[str, any], phase_name: str, 
                               project_data: Dict[str, any]) -> List[Dict[str, any]]:
        """Generate 5-10 tasks for a given epic using Claude tool calling."""
        
        prompt = self._build_tasks_prompt(epic, phase_name, project_data)
        
        # Define the tool schema for task generation
        task_tool = {
            "name": "create_epic_tasks",
            "description": "Create comprehensive tasks for an epic with detailed descriptions",
            "input_schema": {
                "type": "object",
                "properties": {
                    "epicTitle": {
                        "type": "string",
                        "description": "Epic title"
                    },
                    "tasks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "Clear, actionable task title"
                                },
                                "suggestedRole": {
                                    "type": "string",
                                    "description": "The role best suited for this task"
                                },
                                "priority": {
                                    "type": "string",
                                    "enum": ["high", "medium", "low"],
                                    "description": "Task priority level"
                                },
                                "estimatedEffort": {
                                    "type": "string",
                                    "enum": ["small", "medium", "large"],
                                    "description": "Estimated effort required"
                                }
                            },
                            "required": ["title", "suggestedRole", "priority", "estimatedEffort"]
                        }
                    }
                },
                "required": ["epicTitle", "tasks"]
            }
        }
        
        try:
            message = self.anthropic.messages.create(
                model=os.getenv('GITHUB_BACKLOG_MODEL', 'claude-3-5-sonnet-20241022'),
                max_tokens=6000,
                temperature=0.0,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                tools=[task_tool],
                tool_choice={"type": "tool", "name": "create_epic_tasks"}
            )
            
            # Extract the tool result - guaranteed to be valid JSON
            tool_result = message.content[0].input
            return tool_result['tasks']
                
        except Exception as e:
            raise Exception(f"Failed to generate tasks: {str(e)}")
    
    def generate_task_description(self, task: Dict[str, any], epic: Dict[str, any], 
                                 phase_name: str, project_data: Dict[str, any]) -> Dict[str, any]:
        """Generate detailed markdown description for a single task using Claude tool calling."""
        
        prompt = self._build_description_prompt(task, epic, phase_name, project_data)
        
        # Define the tool schema for task description generation
        description_tool = {
            "name": "create_task_description",
            "description": "Create detailed markdown description for a GitHub issue",
            "input_schema": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Task title"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed markdown description for the GitHub issue"
                    },
                    "acceptanceCriteria": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of specific acceptance criteria"
                    },
                    "technicalNotes": {
                        "type": "string",
                        "description": "Technical implementation notes and considerations"
                    },
                    "dependencies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of dependencies or prerequisites"
                    },
                    "suggestedRole": {
                        "type": "string",
                        "description": "Suggested role for task execution (e.g., Backend Developer, Frontend Developer, DevOps Engineer)"
                    },
                    "priority": {
                        "type": "string",
                        "description": "Task priority level (high, medium, low)"
                    },
                    "estimatedEffort": {
                        "type": "string",
                        "description": "Estimated effort or complexity (small, medium, large)"
                    }
                },
                "required": ["title", "description", "acceptanceCriteria", "technicalNotes", "dependencies", "suggestedRole", "priority", "estimatedEffort"]
            }
        }
        
        try:
            message = self.anthropic.messages.create(
                model=os.getenv('GITHUB_BACKLOG_MODEL', 'claude-3-5-sonnet-20241022'),
                max_tokens=4000,
                temperature=0.0,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                tools=[description_tool],
                tool_choice={"type": "tool", "name": "create_task_description"}
            )
            
            # Extract the tool result - guaranteed to be valid JSON
            tool_result = message.content[0].input
            return {
                "title": tool_result["title"],
                "description": tool_result["description"],
                "acceptanceCriteria": tool_result["acceptanceCriteria"],
                "technicalNotes": tool_result["technicalNotes"],
                "dependencies": tool_result["dependencies"],
                "suggestedRole": tool_result["suggestedRole"],
                "priority": tool_result["priority"],
                "estimatedEffort": tool_result["estimatedEffort"]
            }
                
        except Exception as e:
            raise Exception(f"Failed to generate task description: {str(e)}")
    
    def _build_description_prompt(self, task: Dict[str, any], epic: Dict[str, any], 
                                 phase_name: str, project_data: Dict[str, any]) -> str:
        """Build the prompt for task description generation."""
        
        return f"""You are a technical writer creating a detailed GitHub issue description with rich markdown formatting.

# 📌 Task: Create Comprehensive GitHub Issue Description

Create a detailed, actionable GitHub issue description that developers can use to implement the work immediately.

## PROJECT CONTEXT:
- **Project:** {project_data.get('title', 'Software Project')}
- **Description:** {project_data.get('description', '')}
- **Domain:** {project_data.get('domain', 'general')}
- **Technologies:** {', '.join(project_data.get('techStack', [])) if project_data.get('techStack') else 'Not specified'}

## WORK CONTEXT:
- **Phase:** {phase_name}
- **Epic:** {epic.get('title', 'Epic')}
- **Task Title:** {task.get('title', 'Task')}
- **Assigned Role:** {task.get('suggestedRole', 'Developer')}
- **Priority:** {task.get('priority', 'medium')}
- **Effort:** {task.get('estimatedEffort', 'medium')}

## EPIC DESCRIPTION FOR CONTEXT:
{epic.get('description', 'No epic description available')}

# REQUIREMENTS:

Generate a comprehensive GitHub issue description with:

1. **Rich Markdown Description** - Explain what needs to be built and why it's valuable
2. **Specific Acceptance Criteria** - Measurable, testable outcomes 

## MARKDOWN FORMATTING GUIDELINES:

Use proper GitHub markdown including:
- `### Headers` for sections
- `- [ ]` for checklists
- `` `code` `` for inline code
- ``` code blocks ``` for multi-line code
- **bold** for emphasis
- Links where appropriate

## CONTENT FOCUS:

Make this specific to **{project_data.get('title', 'this project')}** by:
- Referencing actual technologies: {', '.join(project_data.get('techStack', []))}
- Mentioning specific project features and components
- Including project-specific implementation details
- Using domain-specific terminology

The description should contain rich markdown that will look great when rendered in GitHub. Include sections like:
- ### Description
- ### Implementation Notes  
- ### Technical Requirements
- ### Testing Strategy
- etc.

Make it comprehensive but focused on this specific task within the broader epic context."""
    
    def _build_tasks_prompt(self, epic: Dict[str, any], phase_name: str, project_data: Dict[str, any]) -> str:
        """Build the prompt for task generation."""
        
        return f"""You are an expert agile project manager and software architect creating GitHub issues for a development team.

# 🧾 Understanding Issues in Software Engineering

In GitHub-centric Agile workflows, an **issue** is the **core unit of trackable work**. Issues capture bugs, features, enhancements, or tasks that need attention. They are the fundamental objects connecting planning, collaboration, and execution.

## 🔍 Issue Definition

- An **issue** is a **discrete, actionable work item** tracked in a repository
- In Agile terms, most issues map to **user stories**—small, user-facing deliverables
- Issues can also serve as bug reports, documentation TODOs, refactoring tasks, or design spikes

Each issue has:
- Title (brief, action-oriented)
- Body (description, checklists, notes)
- Labels (type, priority, phase)
- Comments (for discussion)
- Optional assignee, milestone, or epic link

## 📐 Project Hierarchy

```
Milestone → Epic → Issue → Task (checklist item)
```

- **Issues** are the smallest **standalone, trackable work items**
- **Tasks** are internal steps within an issue (not separately tracked)

## 🧰 What Makes a Good Issue?

| Element       | Description                                                     |
| ------------- | --------------------------------------------------------------- |
| **Title**     | Brief, action-oriented ("Fix broken redirect on login")         |
| **Body**      | Clear description, acceptance criteria, context                 |
| **Checklist** | Use `- [ ]` items to break into subtasks                       |
| **Labels**    | Helps with filtering (e.g., `backend`, `priority:high`)        |
| **Linkages**  | References to PRs, parent epics, or related issues             |

## 🧭 Best Practices

- **One issue = one unit of value**
- Don't let issues sprawl—split when too complex
- Keep descriptions updated as implementation evolves
- Link PRs using closing keywords
- Reference parent epic for traceability

# YOUR TASK

Given the epic below, generate 5-10 specific GitHub issues.

PROJECT CONTEXT:
- Project: {project_data.get('title', 'Software Project')}
- Description: {project_data.get('description', '')}
- Domain: {project_data.get('domain', 'general')}
- Technologies: {', '.join(project_data.get('techStack', [])) if project_data.get('techStack') else 'Not specified'}

PHASE: {phase_name}

EPIC DETAILS:
- Title: {epic['title']}
- Description: {epic['description']}
- Team Roles: {', '.join(epic.get('suggestedRoles', []))}

Return a JSON object with EXACTLY this structure:
{{
  "epicTitle": "{epic['title']}",
  "tasks": [
    {{
      "title": "Action-oriented issue title",
      "suggestedRole": "Role Name",
      "priority": "high|medium|low",
      "estimatedEffort": "small|medium|large"
    }},
    // 5-10 issues total
  ]
}}

EXAMPLE of GOOD issue titles:
- "Implement password strength validator with zxcvbn"
- "Add rate limiting to authentication endpoints"
- "Create E2E tests for login flow"
- "Document SSO integration process"
- "Fix memory leak in session cleanup"

BAD issue titles (too vague):
- "Work on authentication"
- "Fix bugs"
- "Update docs"

Remember: Issues are where actual work happens. Make them clear, actionable, and specific to {project_data.get('title', 'this project')}!"""