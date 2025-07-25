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
        return f"""You are an expert product manager and software architect working to plan a software project using GitHub-native workflows.

# 🔀 Understanding Phases (Milestones) in Software Engineering

In Agile and project-based software engineering, **phases** represent **time-boxed cycles or logical stages** that define the flow of work from idea to production. While sprints are fixed-length (e.g., 2-week cycles), **phases** refer to broader conceptual or strategic stages that a project passes through.

## ⛓️ Core Phases Theory

Most software projects naturally move through these core phases:

### 1. 📚 Research & Discovery
- Identify the core problem
- Interview users, scan competitors, gather technical constraints
- Output: Requirements, user insights, risk assessments

### 2. 🧐 Planning & Design
- Define MVP scope and priorities
- Sketch flows, architecture, and UI
- Break work into epics and stories
- Output: Diagrams, issue plans, milestone roadmap

### 3. 🔨 Build (Implementation)
- Write and review code, develop infrastructure
- Stories executed via pull requests and tasks
- Output: Working software components

### 4. 🧪 Test & QA
- Write unit, integration, and E2E tests
- Perform manual and automated QA
- Output: Verified and stable features

### 5. 🚀 Deployment
- Roll out to staging and production
- Configure CI/CD, observability, alerts
- Output: Live production system

### 6. 🔁 Refinement & Iteration
- Address feedback, UX gaps, edge cases
- Improve performance, fix bugs, explore enhancements
- Output: Stable, usable, improved system

## 🛠️ GitHub Workflow Structure

In GitHub-native workflows:
- **Milestones** = phases (e.g., "Phase 1 – Research")
- **Epics** = GitHub issues labeled 'epic' and titled with '[EPIC]'
- **Child Issues** = linked inside the epic body
- **Tracking** = GitHub shows progress of issues completed per milestone

## ⚖️ Expert Judgment: Custom Phases

Expert teams frequently add custom milestones based on domain-specific needs:
- Data Audit & Cleanup - Validate, migrate, or cleanse legacy data sources
- AI Prompt Tuning - Optimize prompt engineering for LLM-based systems
- Migration Planning - Prepare infrastructure or app for cloud transition
- Security Hardening - Apply infosec practices before major deployment
- UX Validation Loop - Run rapid feedback cycles with real end-users

# 🏁 PHASE PLANNING: Mental Models & Cognitive Biases

## 🧠 Mental Models & Frameworks for Phase Planning

| Tool | Purpose |
|------|---------|
| **Double Diamond** (Discover → Define → Develop → Deliver) | Guides how to structure exploratory vs. execution phases |
| **Systems Thinking** | Encourages holistic phase planning across interconnected functions (infra, UX, backend, QA) |
| **Timeboxing** | Forces prioritization within constraints; helps bound each milestone by realistic effort |
| **Critical Path Analysis** | Surfaces the minimal sequence of phases to hit MVP efficiently |
| **Inverse Planning** | Work backwards from the launch to ensure each phase ladders into the outcome |

## ⚠️ Cognitive Biases to Watch

| Bias | How It Shows Up |
|------|-----------------|
| **Planning Fallacy** | Underestimating how long phases will take—especially early ones |
| **Recency Bias** | Over-indexing on current blockers rather than upcoming risks |
| **Sunk Cost Fallacy** | Continuing unnecessary phases just because effort has already been spent |
| **Optimism Bias** | Overconfident timelines that don't buffer for unknowns |

# YOUR TASK

Given the README.md file below, analyze the product specification and generate a comprehensive project phase breakdown using the mental models above while avoiding the cognitive biases.

CRITICAL INSTRUCTIONS:
1. Apply **Double Diamond** thinking: Include both divergent (explore) and convergent (decide) activities
2. Use **Systems Thinking**: Consider how each phase impacts others (e.g., architecture affects testing)
3. Apply **Timeboxing**: Each phase should be 2-4 weeks to avoid Planning Fallacy
4. Use **Critical Path Analysis**: Order phases to unblock the next efficiently
5. Apply **Inverse Planning**: Work backwards from MVP launch to ensure completeness

BIAS MITIGATION STRATEGIES:
- Add 30% buffer to initial time estimates (Planning Fallacy)
- Include risk assessment in each phase (Recency Bias)
- Question whether each phase truly adds MVP value (Sunk Cost)
- Include explicit "unknown unknowns" time (Optimism Bias)

PHASE REQUIREMENTS:
1. Start with the 6 core phases as your foundation
2. ADD custom phases if the project requires them (e.g., if it's an AI project, add "AI Prompt Tuning")
3. Each phase description MUST be specifically tailored to the actual project:
   - Reference specific features, technologies, and goals from the README
   - Use the actual project name and terminology
   - Describe concrete tasks that relate to the specific business idea
   - Mention specific integrations, data sources, or systems identified
   - Address the specific problems or needs the project aims to solve

PROJECT CONTEXT:
Domain: {project_data.get('domain', 'general')}
Key features: {', '.join(project_data.get('features', [])) if project_data.get('features') else 'See README below'}
Technologies: {', '.join(project_data.get('techStack', [])) if project_data.get('techStack') else 'See README below'}

README CONTENT:
{project_data.get('rawContent', '')}

PHASE GENERATION RULES:
1. Generate 6-10 phases total (6 core + any needed custom phases)
2. Each phase should represent 2-4 weeks of work
3. Phases should follow logical progression from idea to production
4. Include specific roles needed for each phase based on the project's technical requirements
5. Make phase titles and descriptions highly specific to this project

Return a JSON object with this structure:
{{
  "phases": [
    {{
      "id": "research-discovery",
      "title": "📚 Research & Discovery - [Specific Project Focus]",
      "description": "SPECIFIC description mentioning actual project features and goals...",
      "suggestedRoles": ["Product Owner", "UX Researcher", "Domain Expert"]
    }},
    {{
      "id": "planning-design",
      "title": "🧐 Planning & Design - [Specific Architecture/UX Focus]",
      "description": "Define MVP scope for [specific features], design [specific UI components]...",
      "suggestedRoles": ["System Architect", "UX Designer", "Tech Lead"]
    }}
    // ... continue with all phases
  ]
}}

Remember: Phases are GitHub milestones that will contain multiple epics and issues. Make them substantial and meaningful!

## 🧠 META-STRATEGY VALIDATION

Before finalizing, validate each phase against:

**Start from First Principles:**
- What does the user need? (not what we think they need)
- What outcomes are required? (measurable results)
- What constraints exist? (time, budget, tech debt)
- What is the minimum set of validated deliverables?

**Validate Each Phase With:**
- **Traceability**: Will epics clearly support this milestone's goals?
- **Visibility**: Can a new team member understand this phase in 15 minutes?
- **Risk Disclosure**: Are assumptions and risks explicit in the description?"""
    
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