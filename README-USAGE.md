# Agent Team Composer

A CLI tool that transforms any README.md into a comprehensive development roadmap with AI-powered agent teams, automatically generating GitHub issues and epics optimized for Claude Flow SPARC methodology.

## How It Works

1. **README Analysis**: Reads your project's README.md and extracts key information
2. **AI-Powered Planning**: Uses Claude to generate project-specific phases, epics, and issues based on the 8-phase lifecycle template
3. **Interactive UI**: Launches a localhost UI to review and customize the generated plan
4. **GitHub Integration**: Creates issues and epics directly in your GitHub repository

## Prerequisites

- Node.js 16+
- GitHub CLI (`gh`) installed and authenticated
- Anthropic API key

## Installation

```bash
npm install -g agent-team-composer
```

Or run locally:

```bash
npm install
npm run build
```

## Usage

1. **Set your Anthropic API key**:
   ```bash
   export ANTHROPIC_API_KEY=your-api-key
   ```

2. **Navigate to your project directory** (must have a README.md):
   ```bash
   cd your-project
   ```

3. **Run the tool**:
   ```bash
   agent-team-composer init
   ```

   Or with custom options:
   ```bash
   agent-team-composer init --port 4000 --readme docs/README.md
   ```

4. **Review in browser**: The tool will automatically open your browser to review:
   - Project summary and detected features
   - Generated lifecycle phases with role assignments
   - Individual issues for each phase

5. **Approve and push**: Click "Push to GitHub" to create the issues in your repository

## Command Options

### `init`
Initialize agent team composer in current repository

Options:
- `-p, --port <port>`: Port for localhost UI (default: 3000)
- `-r, --readme <path>`: Path to README.md file (default: README.md)
- `--skip-gh-check`: Skip GitHub CLI verification

### `validate`
Validate environment setup

## Architecture

The tool uses a multi-stage LLM cascade:

1. **Phase Generation**: Analyzes README and generates 8 lifecycle phases customized to your product
2. **Epic Generation**: For each phase, generates epics with role assignments
3. **Issue Creation**: Formats each task as a GitHub issue optimized for AI agents

## The 8-Phase Lifecycle

1. **Discovery & Requirements**: Market research, user interviews, problem validation
2. **Technical Planning & Architecture**: System design, technology selection
3. **UI/UX Design & Prototyping**: Interface design, user experience
4. **Core Development**: Implementation of features
5. **System Integration & Testing**: End-to-end testing, integration
6. **Quality Assurance & Testing**: Comprehensive testing, bug fixes
7. **Deployment & Distribution**: Packaging, deployment automation
8. **Launch & Documentation**: Documentation, go-to-market

## Agent Roles

The tool assigns specialized roles to each task:
- Market Research Analyst
- User Research Specialist
- Product Requirements Author
- UI/UX Designer
- System Architect
- Frontend/Backend Developers
- DevOps Engineer
- QA Engineer
- And many more...

## Example Output

For a project management platform:
- **8 Phases** with specific objectives
- **22+ Issues** with detailed descriptions
- **10+ Specialized Roles** assigned to tasks
- **20 Week Timeline** estimated

## Troubleshooting

### Missing GitHub CLI
```bash
# macOS
brew install gh

# Windows
winget install --id GitHub.cli

# Then authenticate
gh auth login
```

### Missing Anthropic API Key
```bash
export ANTHROPIC_API_KEY=sk-ant-api...
```

### Port Already in Use
```bash
agent-team-composer init --port 4000
```

## Development

```bash
# Install dependencies
npm install

# Run in development mode
npm run dev

# Build for production
npm run build

# Type check
npm run typecheck
```

## License

MIT