# GitHub Backlog Generator

A Python CLI tool that takes a GitHub repository URL, fetches its README, and creates AI-generated project milestones with complete epic breakdowns and task issues.

## Features

- **GitHub URL Input**: Takes any GitHub repository URL as a CLI argument
- **Interactive Phase Selection**: Choose which phase (1-8) to generate
- **Single AI Call**: Efficiently generates phase, epic, and tasks in one LLM request
- **Complete Backlog Creation**: Automatically generates:
  - GitHub Milestone for the phase (with due date)
  - Epic issue (labeled "[Epic]") containing team composition and task checklist
  - Individual task issues linked to the epic with role assignments
- **Smart Analysis**: Extracts project domain, complexity, tech stack from README
- **Retry Logic**: Automatically retries if AI response format is incorrect
- **Dry Run Mode**: Preview phase before creating GitHub content
- **JSON Export**: Save generated phase for later use

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd github-backlog-generator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Add your API keys:
   ```
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   GITHUB_TOKEN=your_github_token_here
   ```

   **Note**: GitHub token must have `repo` scope to create milestones.

## Usage

### Basic Usage

```bash
# Run the tool - it will prompt you to select a phase
python run.py https://github.com/owner/repo

# Or use shorthand format
python run.py owner/repo
```

The tool will:
1. Fetch and analyze the README
2. Show project information
3. List all 8 phases
4. Prompt you to enter a number (1-8) to select a phase
5. Generate the phase with AI
6. Create a milestone in GitHub
7. Generate an epic with 5-10 tasks
8. Create an epic issue with task checklist
9. Create individual task issues linked to the epic

### Command Options

```bash
python run.py [OPTIONS] REPO_URL

Arguments:
  REPO_URL              GitHub repository URL (e.g., https://github.com/owner/repo)

Options:
  --api-key TEXT        Anthropic API key (or use ANTHROPIC_API_KEY env var)
  --github-token TEXT   GitHub token (or use GITHUB_TOKEN env var)
  --dry-run            Generate phases without creating milestones
  -o, --output PATH    Save phases to JSON file
  --help               Show this message and exit
```

### Examples

```bash
# Dry run to preview phase without creating milestone
python run.py https://github.com/facebook/react --dry-run
# Then select phase number when prompted

# Create milestone and save phase to file
python run.py owner/repo --output phase.json

# Use different API keys
python run.py owner/repo --api-key sk-ant-... --github-token ghp_...
```

### Interactive Selection Example

```
Select a phase to generate:

  1. Discovery & Requirements
  2. Technical Planning & Architecture
  3. UI/UX Design & Prototyping
  4. Core Development
  5. System Integration & Testing
  6. Quality Assurance & Testing
  7. Deployment & Distribution
  8. Launch & Documentation

Enter phase number (1-8): 1
```

## Workflow

1. **Parse URL**: Extracts owner and repository name from GitHub URL
2. **Validate Access**: Checks that your token has write access to the repo
3. **Sparse Checkout**: Fetches only the README file from the repository
4. **Analyze README**: Extracts project information:
   - Title and description
   - Technology stack
   - Project domain (web, mobile, AI, etc.)
   - Complexity assessment
5. **Generate Phases**: AI creates 8 SDLC phases with:
   - Unique IDs
   - Descriptive titles
   - Detailed descriptions
   - Suggested roles
   - Due dates (14 days apart)
6. **Interactive Selection**: User selects which phase to generate
7. **Create Milestone**: Pushes single milestone directly to GitHub

## Generated Phases

The tool creates 8 standard SDLC phases, customized for your project:

1. **Discovery & Requirements** - Initial analysis and planning
2. **Technical Planning & Architecture** - System design and tech selection
3. **UI/UX Design & Prototyping** - User interface and experience design
4. **Core Development** - Main feature implementation
5. **System Integration & Testing** - Integration and API testing
6. **Quality Assurance & Testing** - Comprehensive testing and fixes
7. **Deployment & Distribution** - Packaging and deployment setup
8. **Launch & Documentation** - Documentation and go-to-market

## Output Format

Milestones are created with:
- **Title**: "Phase N: Phase Title"
- **Description**: Detailed phase description
- **Due Date**: Calculated 14 days apart
- **State**: Open

JSON output includes:
```json
{
  "repository": "owner/repo",
  "project": {
    "title": "Project Name",
    "domain": "web",
    "complexity": "moderate"
  },
  "phases": [
    {
      "id": "discovery",
      "title": "Discovery & Requirements",
      "description": "...",
      "suggestedRoles": ["Product Owner", "UX Researcher"],
      "dueDate": "2025-08-04"
    }
  ]
}
```

## Requirements

- Python 3.8+
- Git (for sparse checkout)
- Anthropic API key
- GitHub personal access token with `repo` scope

## Error Handling

- Validates repository access before attempting to create milestones
- Handles various GitHub URL formats
- Checks for existing milestones to avoid duplicates
- Provides clear error messages for common issues

## License

MIT