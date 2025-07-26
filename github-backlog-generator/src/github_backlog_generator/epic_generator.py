"""Epic Generator - Creates multiple epics per phase with tasks."""

import json
import os
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
        """Generate 5-10 epics for a given phase using Claude tool calling."""
        
        prompt = self._build_prompt(phase_number, phase_name, phase_description, project_data)
        
        # Define the tool schema for epic generation
        epic_tool = {
            "name": "create_phase_epics",
            "description": "Create comprehensive epics for a project phase with detailed descriptions and tasks",
            "input_schema": {
                "type": "object",
                "properties": {
                    "phaseId": {
                        "type": "string",
                        "description": "Phase identifier"
                    },
                    "phaseTitle": {
                        "type": "string",
                        "description": "Phase title"
                    },
                    "epics": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "Epic title without [EPIC] prefix"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Comprehensive epic description with all 5 required sections: PURPOSE & OBJECTIVES, DELIVERABLES & SUCCESS CRITERIA, TECHNICAL APPROACH, STAKEHOLDER VALUE, DEPENDENCIES & RISKS"
                                },
                                "suggestedRoles": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of roles needed for this epic"
                                },
                                "tasks": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "title": {
                                                "type": "string",
                                                "description": "Specific, actionable task title"
                                            },
                                            "description": {
                                                "type": "string", 
                                                "description": "Detailed description of what needs to be done"
                                            },
                                            "suggestedRole": {
                                                "type": "string",
                                                "description": "The role best suited for this task"
                                            }
                                        },
                                        "required": ["title", "description", "suggestedRole"]
                                    },
                                    "description": "3-7 specific tasks for this epic"
                                }
                            },
                            "required": ["title", "description", "suggestedRoles", "tasks"]
                        }
                    }
                },
                "required": ["phaseId", "phaseTitle", "epics"]
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
                tools=[epic_tool],
                tool_choice={"type": "tool", "name": "create_phase_epics"}
            )
            
            # Extract the tool result - guaranteed to be valid JSON
            tool_result = message.content[0].input
            return tool_result['epics']
                
        except Exception as e:
            raise Exception(f"Failed to generate epics: {str(e)}")
    
    def _build_prompt(self, phase_number: int, phase_name: str, phase_description: str, project_data: Dict[str, any]) -> str:
        """Build the prompt for epic generation."""
        
        return f"""You are an expert agile project manager and software architect working with GitHub-native workflows.

# 🧱 Understanding Epics in Software Engineering

In Agile and GitHub-centered workflows, an **epic** is a **large, goal-oriented body of work** that can be broken down into smaller, actionable issues. Epics group related work into a single strategic objective that aligns with broader milestones or phases.

## 🔍 Epic Definition

- **Epics** represent a **major feature, initiative, or deliverable** that spans multiple issues
- Too big to complete in a single sprint; require decomposition into smaller units
- In GitHub, modeled as a **standard issue** with special format:
  - Title starts with `[EPIC]`
  - Labeled with `epic`
  - Contains links or checkboxes for child issues

## 📐 Project Hierarchy

```
Milestone (Phase) → Epic (GitHub issue with `[EPIC]`) → Child Issues (user stories/tasks)
```

This structure allows teams to zoom out to strategic planning and zoom in to execution.

## 🛠️ Managing Epics in GitHub

Epics use **conventions** and **labels**:
- `[EPIC]` prefix in title for visibility
- `epic` label for filtering
- Link child issues using markdown checklists:
  ```markdown
  - [ ] #42 Implement login form
  - [ ] #45 Add password reset
  ```

## ✅ Why Use Epics?

| Benefit                | Description                                                     |
| ---------------------- | --------------------------------------------------------------- |
| **Clarity at scale**   | Breaks complex initiatives into manageable parts                |
| **Team coordination**  | Aligns contributors around shared goals                         |
| **Progress tracking**  | Shows completion of larger initiatives                          |
| **Roadmap visibility** | Helps stakeholders track features without granular details      |

## 🧠 Expert Judgment in Defining Epics

While some epics (like "Build Authentication") are common, others are highly contextual. Expert teams tailor epics to the **problem domain** and **technical strategy**.

### Custom Epic Examples
- `[EPIC] Optimize Large Dataset Uploads` - For data-intensive apps
- `[EPIC] Migrate Legacy Auth to Cognito` - Cloud service integration
- `[EPIC] Launch Beta with Pilot Customers` - Release coordination

# 🧱 EPIC PLANNING: Mental Models & Cognitive Biases

## 🧠 Mental Models & Frameworks for Epic Planning

| Tool | Purpose |
|------|---------|
| **Jobs To Be Done (JTBD)** | Frames epics around user value and desired outcomes, not features |
| **MoSCoW Prioritization** | Helps decide which epics are Must/Should/Could/Won't have |
| **Divide and Conquer** | Ensures epics are decomposable into separate, parallelizable issues |
| **Abstraction Laddering** | Checks whether the epic is too vague (high) or too specific (low) |
| **SPADE Framework** | Situation, Problem, Alternatives, Decision, Explanation - ensures epics are backed by analysis |

## ⚠️ Cognitive Biases to Watch

| Bias | How It Shows Up |
|------|-----------------|
| **Feature Creep** | Adding too many sub-goals to one epic |
| **Ambiguity Effect** | Avoiding epics that involve uncertainty, even if strategically important |
| **Confirmation Bias** | Writing epics to validate an idea rather than test it |
| **Anchoring** | Letting a past project structure overly dictate how current epics are framed |

# YOUR TASK

Given the project context and phase details below, generate 5-10 epics using the mental models above while avoiding the cognitive biases.

PROJECT CONTEXT:
- Project: {project_data.get('title', 'Software Project')}
- Description: {project_data.get('description', '')}
- Domain: {project_data.get('domain', 'general')}
- Technologies: {', '.join(project_data.get('techStack', [])) if project_data.get('techStack') else 'Not specified'}
- Features: {', '.join(project_data.get('features', [])) if project_data.get('features') else 'See description'}

PHASE CONTEXT:
Phase {phase_number}: {phase_name}
Description: {phase_description}

EPIC GENERATION RULES:

**Apply Mental Models:**
1. **JTBD**: Frame each epic around what job the user is trying to accomplish
2. **MoSCoW**: Indicate if this epic is Must-have for MVP or Should/Could have
3. **Divide & Conquer**: Ensure epic can be split into 3-7 independent issues
4. **Abstraction Level**: Not too high ("improve system") nor too low ("add button")
5. **SPADE**: Include rationale - why this epic, why now, what alternatives exist

**Avoid Biases:**
- **Feature Creep**: Keep epic scope focused on one clear outcome
- **Ambiguity Effect**: Don't shy away from necessary but uncertain work
- **Confirmation Bias**: Include epics that test assumptions, not just build features
- **Anchoring**: Think fresh about what THIS project needs, not past projects

**Technical Requirements:**
1. Each epic must be substantial enough to warrant 3-7 child tasks
2. Epics should be **specific to this project**, not generic templates
3. Consider the problem domain and suggest custom epics where appropriate
4. Each epic should have clear deliverables and success criteria
5. Epics should collectively cover all major work streams in the phase
6. Use descriptive titles that communicate the value delivered
7. Tasks within epics should be concrete, actionable items

IMPORTANT CONSIDERATIONS:
- If the project involves AI/ML, include epics for model training, prompt engineering, etc.
- For data-heavy projects, include data pipeline and migration epics
- For regulated industries, include compliance and security epics
- For consumer apps, include user testing and analytics epics
- For enterprise software, include integration and deployment epics

Return a JSON object with EXACTLY this structure:
{{
  "phaseId": "phase-{phase_number}",
  "phaseTitle": "{phase_name}",
  "epics": [
    {{
      "title": "Epic Title Without [EPIC] Prefix",
      "description": "COMPREHENSIVE EPIC DESCRIPTION:\\n\\n**EPIC PURPOSE & OBJECTIVES:**\\nWhat this epic fundamentally accomplishes and why it exists in the project lifecycle.\\n\\n**DELIVERABLES & SUCCESS CRITERIA:**\\nSpecific, measurable outputs that define epic completion and acceptance criteria.\\n\\n**TECHNICAL APPROACH:**\\nKey technical decisions, tools, frameworks, and integration points.\\n\\n**STAKEHOLDER VALUE:**\\nHow this epic creates value for end users and contributes to business objectives.\\n\\n**DEPENDENCIES & RISKS:**\\nWhat this epic depends on and potential blockers with mitigation strategies.",
      "suggestedRoles": ["Role 1", "Role 2"],
      "tasks": [
        {{
          "title": "Specific, actionable task title",
          "description": "Detailed description of what needs to be done, expected outcome, and any technical considerations",
          "suggestedRole": "Role Name"
        }},
        // 3-7 tasks total per epic
      ]
    }},
    // 5-10 epics total
  ]
}}

EXAMPLE EPIC STRUCTURE:
{{
  "title": "Build Multi-Tenant Authentication System",
  "description": "Design and implement a secure, scalable authentication system supporting multiple tenants with SSO, MFA, and role-based permissions. This epic ensures secure access control across all customer organizations.",
  "suggestedRoles": ["Security Engineer", "Backend Developer", "DevOps Engineer"],
  "tasks": [
    {{
      "title": "Design JWT token architecture for multi-tenancy",
      "description": "Create technical design for JWT tokens that securely encode tenant context, user roles, and session data. Include token rotation and revocation strategies.",
      "suggestedRole": "Security Engineer"
    }},
    {{
      "title": "Implement OAuth2/OIDC provider integration",
      "description": "Build adapters for major SSO providers (Google, Microsoft, Okta) with proper tenant isolation and credential management",
      "suggestedRole": "Backend Developer"
    }},
    {{
      "title": "Create tenant provisioning API",
      "description": "Develop RESTful API for creating new tenant accounts, setting authentication policies, and managing tenant-specific IdP configurations",
      "suggestedRole": "Backend Developer"
    }}
  ]
}}

Remember: Epics are the connective tissue between high-level phases and executable tasks. Make them meaningful and specific to {project_data.get('title', 'this project')}!

## 🧠 META-STRATEGY VALIDATION

Before finalizing each epic, validate against:

**Start from First Principles:**
- What job is the user trying to get done? (JTBD)
- What outcome does this epic deliver?
- Is this a Must-have for MVP or nice-to-have?
- What's the smallest version that delivers value?

**Validate Each Epic With:**
- **Traceability**: Does this epic clearly support its parent phase/milestone?
- **Visibility**: Can a developer understand the epic's goal in 2 minutes?
- **Risk Disclosure**: Are technical/business risks acknowledged?
- **Testability**: Can we measure when this epic is complete?"""
    
