"""Epic Generator - Creates multiple epics per phase with tasks."""

import json
import re
from typing import Dict, List, Optional

from anthropic import Anthropic
from pydantic import BaseModel, Field, ValidationError


class Task(BaseModel):
    """Model for a task within an epic."""
    title: str = Field(description="Clear, actionable task title")
    description: str = Field(description="Detailed description of what needs to be done")
    suggestedRole: str = Field(description="The role best suited for this task")


class Epic(BaseModel):
    """Model for an epic with its tasks."""
    title: str = Field(description="Epic title (without [Epic] prefix)")
    description: str = Field(description="Epic overview and objectives")
    tasks: List[Task] = Field(description="List of 3-7 specific tasks for this epic")
    suggestedRoles: List[str] = Field(description="List of roles needed for this epic")


class PhaseEpics(BaseModel):
    """Model for all epics within a phase."""
    phaseId: str = Field(description="Phase ID")
    phaseTitle: str = Field(description="Phase title")
    epics: List[Epic] = Field(description="List of 5-10 epics for this phase")


class EpicGenerator:
    """Generator for creating multiple epics per phase."""
    
    def __init__(self, api_key: str):
        self.anthropic = Anthropic(api_key=api_key)
        self.max_retries = 3
    
    def generate_epics_for_phase(self, phase_number: int, phase_name: str, 
                                phase_description: str, project_data: Dict[str, any]) -> List[Dict[str, any]]:
        """Generate 5-10 epics for a given phase."""
        
        for attempt in range(self.max_retries):
            try:
                prompt = self._build_prompt(phase_number, phase_name, phase_description, project_data)
                
                message = self.anthropic.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=4096,
                    temperature=0.7,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                
                response_text = message.content[0].text
                phase_epics = self._extract_and_validate_epics(response_text)
                
                return phase_epics['epics']
                
            except (json.JSONDecodeError, ValidationError) as e:
                if attempt < self.max_retries - 1:
                    print(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")
                    continue
                else:
                    raise Exception(f"Failed to generate valid epics after {self.max_retries} attempts: {str(e)}")
            except Exception as e:
                raise Exception(f"Failed to generate epics: {str(e)}")
    
    def _build_prompt(self, phase_number: int, phase_name: str, phase_description: str, project_data: Dict[str, any]) -> str:
        """Build the prompt for epic generation."""
        
        # Phase-specific epic examples to guide generation
        epic_examples = {
            1: [
                "Stakeholder Analysis and Interviews",
                "Market Research and Competitive Analysis", 
                "User Research and Persona Development",
                "Technical Feasibility Assessment",
                "Product Vision and Success Metrics"
            ],
            2: [
                "System Architecture Design",
                "Technology Stack Selection",
                "Database Design and Modeling",
                "API Design and Contracts",
                "Security Architecture Planning"
            ],
            3: [
                "User Experience Research",
                "Information Architecture",
                "Visual Design System",
                "Interactive Prototypes",
                "Usability Testing"
            ],
            4: [
                "Core Backend Services",
                "Frontend Application Framework",
                "Data Processing Pipeline",
                "User Authentication System",
                "Core Feature Implementation"
            ]
        }
        
        examples = epic_examples.get(phase_number, [])
        
        return f"""You are an expert agile project manager breaking down a project phase into multiple epics.

PROJECT CONTEXT:
- Project: {project_data.get('title', 'Software Project')}
- Description: {project_data.get('description', '')}
- Domain: {project_data.get('domain', 'general')}
- Technologies: {', '.join(project_data.get('techStack', [])) if project_data.get('techStack') else 'Not specified'}
- Features: {', '.join(project_data.get('features', [])) if project_data.get('features') else 'See description'}

PHASE CONTEXT:
Phase {phase_number}: {phase_name}
Description: {phase_description}

YOUR TASK:
Generate 5-10 distinct epics for this phase. Each epic should represent a major work stream or deliverable within the phase.

CRITICAL REQUIREMENTS:
1. Each epic should be a substantial piece of work that can be broken into tasks
2. Epics should be specific to this project, not generic
3. Each epic should have 3-7 concrete tasks
4. Epics should cover different aspects of the phase work
5. Consider these types of epics for inspiration: {', '.join(examples) if examples else 'various work streams'}

IMPORTANT: You MUST return your response as a valid JSON object with EXACTLY this structure:
{{
  "phaseId": "phase-{phase_number}",
  "phaseTitle": "{phase_name}",
  "epics": [
    {{
      "title": "Epic Title (descriptive, without [Epic] prefix)",
      "description": "Overview of what this epic accomplishes and why it's important...",
      "suggestedRoles": ["Role 1", "Role 2"],
      "tasks": [
        {{
          "title": "Specific task title",
          "description": "What needs to be done and expected outcome",
          "suggestedRole": "Role Name"
        }}
      ]
    }}
  ]
}}

EXAMPLE of GOOD epics structure for Discovery phase:
{{
  "epics": [
    {{
      "title": "Stakeholder Analysis and Engagement",
      "description": "Identify and engage with all project stakeholders to understand their needs, concerns, and success criteria. This epic ensures we have buy-in and clear requirements from all parties.",
      "suggestedRoles": ["Business Analyst", "Product Manager"],
      "tasks": [
        {{
          "title": "Map stakeholder ecosystem",
          "description": "Create comprehensive stakeholder map identifying all internal and external parties, their influence levels, and communication preferences",
          "suggestedRole": "Business Analyst"
        }},
        {{
          "title": "Conduct executive interviews",
          "description": "Interview C-level executives to understand strategic goals, success metrics, and constraints for the project",
          "suggestedRole": "Product Manager"
        }}
      ]
    }},
    {{
      "title": "User Research and Persona Development",
      "description": "Conduct comprehensive user research to understand target users, their needs, pain points, and workflows. Develop detailed personas to guide product decisions.",
      "suggestedRoles": ["UX Researcher", "Product Designer"],
      "tasks": [...]
    }}
  ]
}}

Remember: Create 5-10 distinct epics that together comprehensively cover all work needed for the {phase_name} phase of this specific project."""
    
    def _extract_and_validate_epics(self, response_text: str) -> Dict[str, any]:
        """Extract and validate epic data from LLM response."""
        
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
            validated = PhaseEpics(**parsed)
            return validated.dict()
        except json.JSONDecodeError as e:
            # Try to fix common JSON errors
            # Remove trailing commas
            json_text = re.sub(r',\s*}', '}', json_text)
            json_text = re.sub(r',\s*]', ']', json_text)
            
            # Try again
            parsed = json.loads(json_text)
            validated = PhaseEpics(**parsed)
            return validated.dict()