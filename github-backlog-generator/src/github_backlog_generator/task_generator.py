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

# 🧾 ISSUE PLANNING: Mental Models & Cognitive Biases

## 🧠 Mental Models & Frameworks for Issue Planning

| Tool | Purpose |
|------|---------|
| **Acceptance Criteria** (Gherkin or "Given-When-Then") | Defines when the issue is "done" |
| **Test First Thinking** | Ensures that code and issue design are observable/verifiable |
| **One-Thing Rule** | Ensures each issue represents one atomic unit of value |
| **Checklist Decomposition** | Breaks complexity into subtasks without needing full issue explosion |
| **Design by Contract** | Assumes inputs/outputs and makes edge cases explicit |

## ⚠️ Cognitive Biases to Watch

| Bias | How It Shows Up |
|------|-----------------|
| **Overconfidence Bias** | Under-scoping the complexity of a technical issue |
| **Tunnel Vision** | Writing issues too narrowly, missing side effects or upstream/downstream work |
| **Neglect of Probability** | Ignoring failure modes or implementation risk in the issue plan |
| **Present Bias** | Favoring quick wins over necessary but hard foundational work |

# YOUR TASK

Given the epic below, generate 5-10 specific GitHub issues using the mental models above while avoiding the cognitive biases.

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

ISSUE GENERATION RULES:

**Apply Mental Models:**
1. **Acceptance Criteria**: Each issue must have clear "done" conditions
2. **Test First**: Consider how to verify the issue is complete before writing it
3. **One-Thing Rule**: One issue = one deliverable (avoid bundling)
4. **Checklist Decomposition**: Use subtasks for complexity, not multiple issues
5. **Design by Contract**: Make assumptions and edge cases explicit

**Avoid Biases:**
- **Overconfidence**: Add 50% to initial estimates for complex technical work
- **Tunnel Vision**: Consider ripple effects - what else might this change affect?
- **Neglect of Probability**: Include error handling and edge case considerations
- **Present Bias**: Balance quick wins with necessary foundation work

**Technical Requirements:**
1. Each issue should be a **discrete, completable unit of work**
2. Issues should be **specific to this project**, using actual technologies and features
3. Assign the most appropriate role from the epic's team
4. Set realistic priority and effort estimates (account for Overconfidence Bias)
5. Ensure logical sequencing—earlier issues enable later ones
6. Make titles action-oriented and specific
7. Consider different issue types:
   - Feature implementation
   - Bug fixes (if refactoring existing features)
   - Documentation updates
   - Testing tasks
   - Infrastructure/DevOps work
   - Error handling and edge cases (avoid Neglect of Probability)

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

Remember: Issues are where actual work happens. Make them clear, actionable, and specific to {project_data.get('title', 'this project')}!

## 🧠 META-STRATEGY VALIDATION

Before finalizing each issue, validate against:

**Start from First Principles:**
- What specific value does this issue deliver?
- Can it be tested/verified independently?
- Is the scope small enough for one person?
- Are edge cases considered?

**Validate Each Issue With:**
- **Traceability**: Does this issue clearly contribute to its parent epic?
- **Visibility**: Can a developer start work with just this issue description?
- **Risk Disclosure**: Are technical risks and assumptions explicit?
- **Independence**: Can this be worked on without blocking others?"""
    
    def _build_description_prompt(self, task: Dict[str, any], epic: Dict[str, any], 
                                 phase_name: str, project_data: Dict[str, any]) -> str:
        """Build the prompt for task description generation."""
        
        return f"""You are a technical writer creating a detailed GitHub issue body following best practices.

# 📌 GitHub Issue Best Practices

A well-written issue includes:
- **Clear description** of what needs to be done and why
- **Acceptance criteria** defining "done"
- **Technical context** for implementation
- **Dependencies** on other work
- **Subtasks** as checklist items

## Example Issue Body Structure

```markdown
### Description
Clear explanation of the work, its purpose, and value delivered.

**Epic:** #123 [EPIC] Parent Epic Title

### Acceptance Criteria
- [ ] Specific, testable criterion
- [ ] Another measurable outcome

### Technical Notes
Implementation guidance, architecture decisions, gotchas.

### Dependencies
- Requires completion of #456
- Needs API keys from DevOps team

### Tasks
- [ ] Subtask 1
- [ ] Subtask 2
```

# YOUR TASK

Create a detailed GitHub issue body for the following work item.

PROJECT CONTEXT:
- Project: {project_data.get('title', 'Software Project')}
- Description: {project_data.get('description', '')}
- Domain: {project_data.get('domain', 'general')}
- Technologies: {', '.join(project_data.get('techStack', [])) if project_data.get('techStack') else 'Not specified'}

WORK CONTEXT:
- Phase: {phase_name}
- Epic: {epic['title']}
- Epic Description: {epic['description']}

ISSUE DETAILS:
- Title: {task['title']}
- Assigned Role: {task['suggestedRole']}
- Priority: {task['priority']}
- Effort: {task['estimatedEffort']}

GENERATION REQUIREMENTS:

**Apply Mental Models:**
1. **Acceptance Criteria**: Use Given-When-Then format for clarity
2. **Test First Thinking**: Include how to verify completion
3. **Design by Contract**: State assumptions about inputs/outputs
4. **Edge Cases**: Explicitly address failure scenarios
5. **One-Thing Rule**: Keep description focused on the single deliverable

**Content Requirements:**
1. **Description** must explain the "what" and "why" specific to this project
2. **Acceptance criteria** should be testable using Given-When-Then format AND include:
   - Component can be unit tested in isolation
   - Component can be integration tested with existing components
3. **Technical notes** must reference actual project technologies and patterns
4. **Dependencies** should consider logical work sequence and blockers
5. Include enough detail for the {task['suggestedRole']} to start immediately
6. Use GitHub markdown formatting with checklists for subtasks
7. Reference specific features, APIs, or components from the project
8. Address potential failure modes and edge cases (avoid Neglect of Probability)
9. **Before starting work**, the implementer must:
   - Search for existing CDK stacks to understand the infrastructure
   - Determine exact naming, location, and configuration of upstream dependencies
   - Document all discovered components they'll integrate with
10. **Deployment Requirements**:
   - There is only ONE environment (no dev/staging/prod separation)
   - Do not use environment-specific naming conventions
   - Include exact deployment commands (CDK deploy, etc.)
   - Must deploy automatically after tests pass and product owner review
11. **Documentation Requirements**:
   - All code must be heavily documented with "why" not just "what"
   - Update all relevant documentation before closing issue
   - Do not commit experimental or troubleshooting files
   - Only commit the bare minimum files needed for functionality

Return a JSON object with this structure:
{{
  "title": "{task['title']}",
  "description": "### Description\n\nDetailed explanation of the work, linking to project goals and user value. Mention specific {project_data.get('title', 'project')} features.\n\n**Epic:** #{epic.get('number', 'XX')} [EPIC] {epic['title']}",
  "acceptanceCriteria": [
    "✅ Specific, measurable outcome using project terminology",
    "✅ Another testable criterion referencing actual features",
    "✅ Component can be unit tested in isolation with mocked dependencies",
    "✅ Component successfully integrates with existing [specific component names discovered during investigation]",
    "✅ Performance or quality metric if applicable",
    "✅ All upstream dependencies identified and documented",
    "✅ Deployment commands execute successfully in the single environment",
    "✅ Documentation updated with 'why' explanations for key decisions"
  ],
  "technicalNotes": "### Pre-work Investigation\n\nBefore starting implementation:\n1. Run `cdk list` to discover existing stacks\n2. Search for existing components: `grep -r 'ComponentName' .`\n3. Document all discovered upstream dependencies\n\n### Implementation Guidance\n\nImplementation guidance specific to {', '.join(project_data.get('techStack', ['the tech stack']))}. Include architecture decisions, API endpoints, data models, or algorithms relevant to this issue.\n\n### Deployment Instructions\n\n**Environment:** Single environment only (no dev/staging/prod)\n\n1. Run unit tests: `npm test`\n2. Run integration tests: `npm run test:integration`\n3. Deploy to AWS: `cdk deploy StackName --require-approval never`\n4. Verify deployment: `aws cloudformation describe-stacks --stack-name StackName`\n\n### Documentation Requirements\n\n- Every function/class must have a docstring explaining WHY it exists\n- Update README.md with any new setup steps\n- Do NOT commit: test files, debug logs, experimental code\n- ONLY commit: source code, tests, documentation",
  "dependencies": [
    "Clear dependency with rationale",
    "External requirement or blocker if any"
  ]
}}

EXAMPLE of GOOD technical notes:
"### Pre-work Investigation
1. Run `cdk list` - found existing stacks: UserAuthStack, APIGatewayStack
2. Discovered auth components in `/src/auth/`: TokenManager, SessionValidator
3. API client exists at `/src/services/api.ts` with retry logic

### Implementation Guidance
Implement using React hooks for state management, integrating with our existing Redux store for user preferences. Use the established API client in `/src/services/api.ts`. Follow the component patterns in `/src/components/auth/` for consistency. Note: The backend expects JWT tokens in the Authorization header.

### Deployment Instructions
1. Run tests: `npm test src/auth/NewComponent.test.ts`
2. Integration test: `npm run test:integration -- --grep 'auth flow'`
3. Deploy: `cdk deploy UserAuthStack --require-approval never`
4. Verify: `curl -X POST https://api.domain.com/auth/test`"

BAD technical notes (too generic):
"Use best practices. Follow existing patterns. Deploy when ready."

Remember: This issue will be read by developers who need to implement it. Be specific, technical, and helpful!"""
    
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