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
      "description": "Clear description of what this epic accomplishes, its strategic importance, and key deliverables. Should reference specific project features and goals.",
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