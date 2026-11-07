"""Phase Generator - Creates SDLC phases using AI."""

import json
import os
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
        """Generate project phases based on README analysis using Claude tool calling."""
        prompt = self._build_prompt(project_data)
        
        # Define the tool schema for phase generation
        phase_tool = {
            "name": "create_project_phases",
            "description": "Create comprehensive project phases with detailed descriptions",
            "input_schema": {
                "type": "object",
                "properties": {
                    "phases": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "description": "Unique phase identifier (lowercase, hyphenated)"
                                },
                                "title": {
                                    "type": "string", 
                                    "description": "Phase title with emoji and specific project context"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Comprehensive phase description with all 7 required sections"
                                },
                                "suggestedRoles": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of roles needed for this phase"
                                }
                            },
                            "required": ["id", "title", "description", "suggestedRoles"]
                        }
                    }
                },
                "required": ["phases"]
            }
        }
        
        try:
            message = self.anthropic.messages.create(
                model=os.getenv('GITHUB_BACKLOG_MODEL', 'claude-3-5-sonnet-20241022'),
                max_tokens=8000,
                temperature=0.0,
                messages=[{
                    "role": "user", 
                    "content": prompt
                }],
                tools=[phase_tool],
                tool_choice={"type": "tool", "name": "create_project_phases"}
            )
            
            # Extract the tool result - guaranteed to be valid JSON
            tool_result = message.content[0].input
            phases = tool_result["phases"]
            
            # Add due dates to phases
            phases_with_dates = self._calculate_due_dates(phases)
            
            return phases_with_dates
            
        except Exception as e:
            raise Exception(f"Failed to generate phases: {str(e)}")
    
    def _build_prompt(self, project_data: Dict[str, any]) -> str:
        """Build the prompt for phase generation."""
        return f"""Create a comprehensive project phase breakdown for this GitHub repository. You MUST return valid JSON with detailed phase descriptions.

PROJECT: {project_data.get('title', 'Software Project')}
DOMAIN: {project_data.get('domain', 'general')}
README CONTENT:
{project_data.get('rawContent', '')}

Each phase description MUST include ALL 7 sections:
**PHASE PURPOSE & OBJECTIVES:** - Core mission and strategic objectives
**PROJECT ADVANCEMENT IMPACT:** - How this advances the project
**SPECIFIC PROJECT CONTEXT:** - Reference actual features/tech from README
**DELIVERABLES & SUCCESS CRITERIA:** - Measurable outputs and acceptance criteria
**STAKEHOLDER VALUE:** - Value created for users and business impact
**TECHNICAL CONTEXT & APPROACH:** - Technical decisions and architectural patterns
**RISK FACTORS & MITIGATION:** - Potential blockers and mitigation strategies

REQUIRED OUTPUT FORMAT:
{{
  "phases": [
    {{
      "id": "research-discovery-ourchants",
      "title": "📚 Research & Discovery - Song Data Requirements Analysis",
      "description": "**PHASE PURPOSE & OBJECTIVES:**\\nDefine comprehensive song data requirements and establish foundational understanding of music metadata management needs. This phase exists to prevent costly rework by thoroughly understanding the domain before implementation begins.\\n\\n**PROJECT ADVANCEMENT IMPACT:**\\nAdvances project from concept to validated requirements with clear data models. Unlocks ability to design appropriate database schemas and API contracts for subsequent phases.\\n\\n**SPECIFIC PROJECT CONTEXT:**\\nAnalyze OurChants' song data model requirements including id, name, artist, album, release_date, genre, duration_in_seconds fields. Research music metadata standards and integration needs with existing Python dataclass implementation.\\n\\n**DELIVERABLES & SUCCESS CRITERIA:**\\nComplete requirements document, validated data dictionary, stakeholder interview notes, competitive analysis report, and technical constraints documentation.\\n\\n**STAKEHOLDER VALUE:**\\nEnsures the final system meets actual user needs for song data management and prevents feature gaps that would require expensive post-launch fixes.\\n\\n**TECHNICAL CONTEXT & APPROACH:**\\nLeverage existing Python dataclass foundation, research music industry metadata standards like ID3, analyze pytest testing patterns, and evaluate database design options.\\n\\n**RISK FACTORS & MITIGATION:**\\nRisk of incomplete requirements leading to rework. Mitigate through thorough stakeholder interviews and prototype validation sessions.",
      "suggestedRoles": ["Product Manager", "Domain Expert", "Data Architect"]
    }}
  ]
}}

Generate 6-8 phases with unique IDs and comprehensive descriptions. Make titles specific to this project. Return ONLY the JSON."""
    
    
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