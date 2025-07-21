"""Phase Generator - Creates SDLC phases using AI."""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from anthropic import Anthropic
from pydantic import BaseModel, ValidationError


class Phase(BaseModel):
    """Model for a project phase."""
    id: str
    title: str
    description: str
    suggestedRoles: List[str]
    dueDate: Optional[str] = None


class PhasesResponse(BaseModel):
    """Model for the AI response containing phases."""
    phases: List[Phase]


class PhaseGenerator:
    """Generator for creating SDLC phases using Claude AI."""
    
    def __init__(self, api_key: str):
        self.anthropic = Anthropic(api_key=api_key)
    
    def generate_phases(self, project_data: Dict[str, any]) -> List[Dict[str, any]]:
        """Generate project phases based on README analysis."""
        prompt = self._build_prompt(project_data)
        
        try:
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
            phases = self._extract_phases(response_text)
            
            # Add due dates to phases
            phases_with_dates = self._calculate_due_dates(phases)
            
            return phases_with_dates
            
        except Exception as e:
            raise Exception(f"Failed to generate phases: {str(e)}")
    
    def _build_prompt(self, project_data: Dict[str, any]) -> str:
        """Build the prompt for phase generation."""
        return f"""You are an expert product manager working with a CEO and engineer to plan a digital product MVP.

Given a README.md file from a GitHub repository, analyze the product specification and generate a comprehensive project phase breakdown.

CRITICAL INSTRUCTION: Each phase description MUST be specifically tailored to the actual project described in the README. Do not use generic descriptions. Instead:
- Reference specific features, technologies, and goals mentioned in the README
- Use the actual project name and terminology from the README
- Describe concrete tasks that relate to the specific business idea
- Mention specific integrations, data sources, or systems identified in the README
- Address the specific problems or needs the project aims to solve

Use these 8 standard phases as a template, but HEAVILY CUSTOMIZE them based on the specific product:

1. Discovery & Requirements - Initial project analysis, stakeholder alignment, and requirement gathering
2. Technical Planning & Architecture - System design, technology selection, and implementation roadmap  
3. UI/UX Design & Prototyping - User interface design, prototyping, and user experience optimization
4. Core Development - Implementation of core features and functionality
5. System Integration & Testing - Integration testing, API connections, and end-to-end workflow validation
6. Quality Assurance & Testing - Comprehensive testing, bug fixes, and quality validation
7. Deployment & Distribution - Packaging, distribution setup, and deployment automation
8. Launch & Documentation - Documentation, marketing materials, and go-to-market preparation

For each phase, provide:
- A unique ID (lowercase, no spaces)
- A clear title (can be customized based on the project type)
- A HIGHLY SPECIFIC description that directly references the project's goals, features, and technologies
- Suggested roles needed (specific to this project's requirements)

The product domain is: {project_data.get('domain', 'general')}
Key features identified: {', '.join(project_data.get('features', [])) if project_data.get('features') else 'See README below'}
Technologies identified: {', '.join(project_data.get('techStack', [])) if project_data.get('techStack') else 'See README below'}

The README content is:
{project_data.get('rawContent', '')}

Important considerations:
- Every phase description should mention specific aspects from the README
- If the README mentions specific data sources, APIs, or integrations, reference them
- If there are specific user types or use cases mentioned, include them
- For technical phases, mention the actual technologies and frameworks from the project
- For business phases, reference the actual business goals and metrics mentioned

Return a JSON object with this structure:
{{
  "phases": [
    {{
      "id": "discovery",
      "title": "Discovery & Requirements", 
      "description": "SPECIFIC description mentioning actual project features...",
      "suggestedRoles": ["Product Owner", "UX Researcher"]
    }}
  ]
}}"""
    
    def _extract_phases(self, response_text: str) -> List[Dict[str, any]]:
        """Extract phases from the AI response."""
        # Try to find JSON in the response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if not json_match:
            raise ValueError("No JSON found in response")
        
        try:
            # First attempt: direct JSON parsing
            parsed = json.loads(json_match.group(0))
            validated = PhasesResponse(**parsed)
            return [phase.dict() for phase in validated.phases]
        except (json.JSONDecodeError, ValidationError):
            # Second attempt: extract from code block
            code_block_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response_text)
            if code_block_match:
                try:
                    parsed = json.loads(code_block_match.group(1))
                    validated = PhasesResponse(**parsed)
                    return [phase.dict() for phase in validated.phases]
                except (json.JSONDecodeError, ValidationError) as e:
                    raise ValueError(f"Failed to parse phases: {str(e)}")
            
            raise ValueError("Failed to parse phases from response")
    
    def _calculate_due_dates(self, phases: List[Dict[str, any]], start_date: Optional[datetime] = None) -> List[Dict[str, any]]:
        """Calculate due dates for milestones (14 days per phase)."""
        if start_date is None:
            start_date = datetime.now()
        
        phases_with_dates = []
        for i, phase in enumerate(phases):
            due_date = start_date + timedelta(days=(i + 1) * 14)
            phase_copy = phase.copy()
            phase_copy['dueDate'] = due_date.isoformat()
            phases_with_dates.append(phase_copy)
        
        return phases_with_dates