"""Unified Generator - Creates phases with epics and tasks in a single LLM call."""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from anthropic import Anthropic
from pydantic import BaseModel, Field, ValidationError


class Task(BaseModel):
    """Model for a task within an epic."""
    title: str = Field(description="Clear, actionable task title")
    description: str = Field(description="Detailed description of what needs to be done")
    suggestedRole: str = Field(description="The role best suited for this task")


class Phase(BaseModel):
    """Model for a complete phase with epic and tasks."""
    id: str = Field(description="Unique phase ID (lowercase, no spaces)")
    title: str = Field(description="Phase title")
    description: str = Field(description="Detailed phase description")
    suggestedRoles: List[str] = Field(description="List of roles needed for this phase")
    epicSummary: str = Field(description="Brief summary of what this epic encompasses")
    tasks: List[Task] = Field(description="List of 5-10 specific tasks for this phase")


class UnifiedGenerator:
    """Generator for creating complete phase data with epic and tasks in one call."""
    
    def __init__(self, api_key: str):
        self.anthropic = Anthropic(api_key=api_key)
        self.max_retries = 3
    
    def generate_phase_with_epic(self, phase_number: int, phase_name: str, 
                                project_data: Dict[str, any]) -> Dict[str, any]:
        """Generate a complete phase with epic and tasks in a single LLM call."""
        
        for attempt in range(self.max_retries):
            try:
                prompt = self._build_prompt(phase_number, phase_name, project_data)
                
                message = self.anthropic.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=4000,
                    temperature=0.7,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                
                response_text = message.content[0].text
                phase_data = self._extract_and_validate_phase(response_text)
                
                # Add due date
                phase_data['dueDate'] = (datetime.now() + timedelta(days=phase_number * 14)).isoformat()
                
                return phase_data
                
            except (json.JSONDecodeError, ValidationError) as e:
                if attempt < self.max_retries - 1:
                    print(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")
                    continue
                else:
                    raise Exception(f"Failed to generate valid phase data after {self.max_retries} attempts: {str(e)}")
            except Exception as e:
                raise Exception(f"Failed to generate phase: {str(e)}")
    
    def _build_prompt(self, phase_number: int, phase_name: str, project_data: Dict[str, any]) -> str:
        """Build the unified prompt for phase and epic generation."""
        
        # Define phase-specific context
        phase_contexts = {
            1: "Discovery & Requirements - Focus on understanding the problem, user needs, and project scope",
            2: "Technical Planning & Architecture - Focus on system design, technology choices, and technical roadmap",
            3: "UI/UX Design & Prototyping - Focus on user interface, user experience, and visual design",
            4: "Core Development - Focus on implementing the main features and functionality",
            5: "System Integration & Testing - Focus on connecting components and validating integrations",
            6: "Quality Assurance & Testing - Focus on comprehensive testing and quality validation",
            7: "Deployment & Distribution - Focus on packaging, deployment, and distribution setup",
            8: "Launch & Documentation - Focus on documentation, marketing, and go-to-market activities"
        }
        
        phase_context = phase_contexts.get(phase_number, phase_name)
        
        return f"""You are an expert product manager and agile coach creating a detailed project phase for a software development project.

PROJECT CONTEXT:
- Project: {project_data.get('title', 'Software Project')}
- Description: {project_data.get('description', '')}
- Domain: {project_data.get('domain', 'general')}
- Technologies: {', '.join(project_data.get('techStack', [])) if project_data.get('techStack') else 'Not specified'}
- Features: {', '.join(project_data.get('features', [])) if project_data.get('features') else 'See description'}

PHASE TO GENERATE:
Phase {phase_number}: {phase_context}

YOUR TASK:
Create a comprehensive phase plan that includes:
1. A detailed phase description tailored to this specific project
2. The roles needed for this phase
3. An epic summary that captures the main goal
4. 5-10 specific, actionable tasks that must be completed

CRITICAL REQUIREMENTS:
- Be HIGHLY SPECIFIC to this project - reference actual features, technologies, and goals from the context
- Tasks should be concrete and achievable, not generic
- Each task should clearly indicate what needs to be built/done
- Assign the most appropriate role to each task
- Ensure logical task sequencing

IMPORTANT: You MUST return your response as a valid JSON object with EXACTLY this structure:
{{
  "id": "phase-id-lowercase-no-spaces",
  "title": "{phase_name}",
  "description": "Detailed description specific to this project and phase...",
  "suggestedRoles": ["Role 1", "Role 2", "Role 3"],
  "epicSummary": "One sentence summary of what this epic accomplishes",
  "tasks": [
    {{
      "title": "Specific task title",
      "description": "Detailed description of what needs to be done and why",
      "suggestedRole": "Role Name"
    }},
    // ... 5-10 tasks total
  ]
}}

EXAMPLE of a GOOD task (specific and actionable):
{{
  "title": "Design RESTful API endpoints for user authentication",
  "description": "Create OpenAPI specification for login, logout, and token refresh endpoints. Define request/response schemas, error codes, and security requirements using JWT tokens.",
  "suggestedRole": "Backend Developer"
}}

EXAMPLE of a BAD task (too generic):
{{
  "title": "Work on API",
  "description": "Develop the API for the system",
  "suggestedRole": "Developer"
}}

Remember: Be specific to the actual project described above. Reference real features and technologies."""
    
    def _extract_and_validate_phase(self, response_text: str) -> Dict[str, any]:
        """Extract and validate phase data from LLM response."""
        
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
            validated = Phase(**parsed)
            return validated.dict()
        except json.JSONDecodeError as e:
            # Try to fix common JSON errors
            # Remove trailing commas
            json_text = re.sub(r',\s*}', '}', json_text)
            json_text = re.sub(r',\s*]', ']', json_text)
            
            # Try again
            parsed = json.loads(json_text)
            validated = Phase(**parsed)
            return validated.dict()