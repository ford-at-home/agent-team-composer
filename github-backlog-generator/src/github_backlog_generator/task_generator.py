"""Task Generator - Creates tasks for an epic and detailed descriptions for each task."""

import json
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


class TaskGenerator:
    """Generator for creating tasks and their detailed descriptions."""
    
    def __init__(self, api_key: str):
        self.anthropic = Anthropic(api_key=api_key)
        self.max_retries = 3
    
    def generate_tasks_for_epic(self, epic: Dict[str, any], phase_name: str, 
                               project_data: Dict[str, any]) -> List[Dict[str, any]]:
        """Generate 5-10 tasks for a given epic."""
        
        for attempt in range(self.max_retries):
            try:
                prompt = self._build_tasks_prompt(epic, phase_name, project_data)
                
                message = self.anthropic.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=2048,
                    temperature=0.7,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                
                response_text = message.content[0].text
                epic_tasks = self._extract_and_validate_tasks(response_text)
                
                return epic_tasks['tasks']
                
            except (json.JSONDecodeError, ValidationError) as e:
                if attempt < self.max_retries - 1:
                    print(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")
                    continue
                else:
                    raise Exception(f"Failed to generate valid tasks after {self.max_retries} attempts: {str(e)}")
            except Exception as e:
                raise Exception(f"Failed to generate tasks: {str(e)}")
    
    def generate_task_description(self, task: Dict[str, any], epic: Dict[str, any], 
                                 phase_name: str, project_data: Dict[str, any]) -> Dict[str, any]:
        """Generate detailed description for a single task."""
        
        for attempt in range(self.max_retries):
            try:
                prompt = self._build_description_prompt(task, epic, phase_name, project_data)
                
                message = self.anthropic.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=1500,
                    temperature=0.7,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                
                response_text = message.content[0].text
                task_description = self._extract_and_validate_description(response_text)
                
                return task_description
                
            except (json.JSONDecodeError, ValidationError) as e:
                if attempt < self.max_retries - 1:
                    print(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")
                    continue
                else:
                    raise Exception(f"Failed to generate valid description after {self.max_retries} attempts: {str(e)}")
            except Exception as e:
                raise Exception(f"Failed to generate task description: {str(e)}")
    
    def _build_tasks_prompt(self, epic: Dict[str, any], phase_name: str, project_data: Dict[str, any]) -> str:
        """Build the prompt for task generation."""
        
        return f"""You are an expert agile project manager breaking down an epic into specific tasks.

PROJECT CONTEXT:
- Project: {project_data.get('title', 'Software Project')}
- Description: {project_data.get('description', '')}
- Domain: {project_data.get('domain', 'general')}
- Technologies: {', '.join(project_data.get('techStack', [])) if project_data.get('techStack') else 'Not specified'}

PHASE CONTEXT:
Phase: {phase_name}

EPIC CONTEXT:
Epic Title: {epic['title']}
Epic Description: {epic['description']}
Team Roles: {', '.join(epic.get('suggestedRoles', []))}

YOUR TASK:
Generate 5-10 specific, actionable tasks that need to be completed to deliver this epic.

CRITICAL REQUIREMENTS:
1. Each task should be a concrete piece of work that can be completed by one person
2. Tasks should be specific to this project and epic, not generic
3. Assign the most appropriate role from the team roles listed above
4. Estimate effort and priority for each task
5. Ensure logical sequencing - earlier tasks should enable later ones

IMPORTANT: You MUST return your response as a valid JSON object with EXACTLY this structure:
{{
  "epicTitle": "{epic['title']}",
  "tasks": [
    {{
      "title": "Specific, actionable task title",
      "suggestedRole": "Role Name",
      "priority": "high|medium|low",
      "estimatedEffort": "small|medium|large"
    }}
  ]
}}

EXAMPLE of GOOD tasks:
{{
  "tasks": [
    {{
      "title": "Design database schema for user authentication",
      "suggestedRole": "Data Architect",
      "priority": "high",
      "estimatedEffort": "medium"
    }},
    {{
      "title": "Implement JWT token generation and validation",
      "suggestedRole": "Backend Developer",
      "priority": "high",
      "estimatedEffort": "medium"
    }}
  ]
}}

Remember: Create 5-10 specific tasks that together complete the epic "{epic['title']}" for this project."""
    
    def _build_description_prompt(self, task: Dict[str, any], epic: Dict[str, any], 
                                 phase_name: str, project_data: Dict[str, any]) -> str:
        """Build the prompt for task description generation."""
        
        return f"""You are a technical writer creating a detailed GitHub issue for a specific development task.

PROJECT CONTEXT:
- Project: {project_data.get('title', 'Software Project')}
- Description: {project_data.get('description', '')}
- Domain: {project_data.get('domain', 'general')}
- Technologies: {', '.join(project_data.get('techStack', [])) if project_data.get('techStack') else 'Not specified'}

PHASE: {phase_name}

EPIC: {epic['title']}
Epic Description: {epic['description']}

TASK: {task['title']}
Assigned Role: {task['suggestedRole']}
Priority: {task['priority']}
Effort: {task['estimatedEffort']}

YOUR TASK:
Create a detailed description for this task that provides all the information needed for the assigned role to complete it successfully.

CRITICAL REQUIREMENTS:
1. The description should be specific to this project and use actual project technologies
2. Include clear acceptance criteria that define "done"
3. Note any technical considerations specific to the tech stack
4. Identify dependencies on other tasks or systems
5. Be detailed enough that someone can start work immediately

IMPORTANT: You MUST return your response as a valid JSON object with EXACTLY this structure:
{{
  "title": "{task['title']}",
  "description": "Detailed description of what needs to be done, why it's important, and how it fits into the larger epic and project goals...",
  "acceptanceCriteria": [
    "Specific, measurable criterion 1",
    "Specific, measurable criterion 2",
    "Specific, measurable criterion 3"
  ],
  "technicalNotes": "Any technical considerations, architecture decisions, or implementation notes specific to the project's tech stack...",
  "dependencies": [
    "Dependency 1",
    "Dependency 2"
  ]
}}

Remember: Be specific to the {project_data.get('title', 'project')} project and reference actual technologies and features."""
    
    def _extract_and_validate_tasks(self, response_text: str) -> Dict[str, any]:
        """Extract and validate task data from LLM response."""
        
        # Try to extract JSON from various formats
        json_text = None
        
        # Method 1: Direct JSON
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            json_text = json_match.group(0)
        
        # Method 2: JSON in code block
        if not json_text:
            code_block_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response_text)
            if code_block_match:
                json_text = code_block_match.group(1)
        
        if not json_text:
            raise ValueError("No JSON found in response")
        
        # Parse and validate
        try:
            parsed = json.loads(json_text)
            validated = EpicTasks(**parsed)
            return validated.dict()
        except json.JSONDecodeError as e:
            # Try to fix common JSON errors
            json_text = re.sub(r',\s*}', '}', json_text)
            json_text = re.sub(r',\s*]', ']', json_text)
            
            # Try again
            parsed = json.loads(json_text)
            validated = EpicTasks(**parsed)
            return validated.dict()
    
    def _extract_and_validate_description(self, response_text: str) -> Dict[str, any]:
        """Extract and validate task description from LLM response."""
        
        # Try to extract JSON from various formats
        json_text = None
        
        # Method 1: Direct JSON
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            json_text = json_match.group(0)
        
        # Method 2: JSON in code block
        if not json_text:
            code_block_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response_text)
            if code_block_match:
                json_text = code_block_match.group(1)
        
        if not json_text:
            raise ValueError("No JSON found in response")
        
        # Parse and validate
        try:
            parsed = json.loads(json_text)
            validated = TaskDescription(**parsed)
            return validated.dict()
        except json.JSONDecodeError as e:
            # Try to fix common JSON errors
            json_text = re.sub(r',\s*}', '}', json_text)
            json_text = re.sub(r',\s*]', ']', json_text)
            
            # Try again
            parsed = json.loads(json_text)
            validated = TaskDescription(**parsed)
            return validated.dict()