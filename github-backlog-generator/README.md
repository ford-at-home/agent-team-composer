# GitHub Backlog Generator 🚀

Transform any GitHub repository into a comprehensive project backlog with AI-powered analysis. This tool reads your README and generates a complete project plan with phases (milestones), epics, and detailed task issues - all created directly in your GitHub repository.

## 🎯 What Does It Do?

Given a GitHub repository URL, this tool:
1. **Analyzes** your README to understand the project
2. **Generates** a complete project plan with 6-10 phases
3. **Creates** GitHub milestones for each phase
4. **Builds** epic issues with team composition and task lists
5. **Generates** individual task issues with acceptance criteria

All content is created directly in your GitHub repository, ready for your team to start working!

## ✨ Key Features

- **🤖 AI-Powered Analysis**: Uses Claude to understand your project context
- **📊 Structured Planning**: Follows software engineering best practices
- **🧠 Cognitive Bias Mitigation**: Built-in frameworks to avoid common planning pitfalls
- **🎯 Mental Models**: Applies JTBD, MoSCoW, Double Diamond, and more
- **📝 GitHub Native**: Creates real milestones, epics, and issues
- **🔄 Customizable Phases**: Adapts to your project type (AI/ML, e-commerce, etc.)
- **✅ Acceptance Criteria**: Every issue includes testable completion criteria

## 📦 Installation

### From PyPI (Coming Soon)
```bash
pip install github-backlog-generator
```

### From Source
```bash
# Clone the repository
git clone https://github.com/ford-at-home/agent-team-composer.git
cd agent-team-composer/github-backlog-generator

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .

# Or just install dependencies
pip install -r requirements.txt
```

## 🔧 Configuration

### 1. Set Up API Keys

Create a `.env` file in the project directory:
```bash
cp .env.example .env
```

Edit `.env` and add your keys:
```env
# Required: Get from https://console.anthropic.com/account/keys
ANTHROPIC_API_KEY=sk-ant-api03-...

# Required: Create at https://github.com/settings/tokens
# Token needs 'repo' scope for creating issues/milestones
GITHUB_TOKEN=ghp_...

# Optional: Choose Claude model (default: claude-3-5-sonnet-20241022)
GITHUB_BACKLOG_MODEL=claude-3-5-sonnet-20241022
```

### 2. GitHub Token Permissions

Your GitHub token needs these scopes:
- ✅ `repo` - Full repository access (required)
- ✅ `read:org` - Read organization data (optional, for org repos)

## 🚀 Usage

### Modular Workflow (Recommended)

The tool now supports a fully modular workflow where each component can be generated and tested independently:

#### Step 1: Initialize Project
```bash
# Analyze README and create local file structure
github-backlog init https://github.com/owner/repo
```

This creates:
- Local directory `.backlog-owner-repo/` with cascading structure
- Generates all 8 phase definitions
- Saves project metadata from README analysis

#### Step 2: Create GitHub Milestones
```bash
# Create all 8 milestones in GitHub
github-backlog milestones https://github.com/owner/repo
```

#### Step 3: Generate Epics for a Phase
```bash
# Generate epics for phase 1 (creates epic issues in GitHub)
github-backlog generate https://github.com/owner/repo --phase 1
```

#### Step 4: Generate Issues for Epics
```bash
# Generate issues for epic 2 in phase 1
github-backlog generate https://github.com/owner/repo --phase 1 --epic 2

# Or generate issues for all epics in phase 1
github-backlog generate https://github.com/owner/repo --phase 1 --all-epics
```

### Check Status
```bash
# See what's been generated
github-backlog status https://github.com/owner/repo
```

### File Structure Created
```
.backlog-owner-repo/
├── metadata.json          # Project information from README
├── milestone_mapping.json # GitHub milestone numbers
└── phases/
    ├── phases.json        # All phase definitions
    ├── phase1/
    │   ├── phase.json    # Phase 1 details
    │   ├── epics.json    # All epics for phase 1
    │   ├── epic1/
    │   │   ├── epic.json # Epic 1 details
    │   │   └── issues.json # Issues for epic 1
    │   └── epic2/
    │       ├── epic.json
    │       └── issues.json
    └── phase2/
        └── ...
```


### Command Reference

```bash
# Initialize project (required first step)
github-backlog init [OPTIONS] REPO_URL

# Create GitHub milestones
github-backlog milestones [OPTIONS] REPO_URL

# Generate epics or issues
github-backlog generate [OPTIONS] REPO_URL
  --phase INTEGER    Phase number (1-8) [required]
  --epic INTEGER     Epic number (generates issues for that epic)
  --all-epics        Generate issues for all epics in the phase
  --dry-run          Preview without creating GitHub items

# Check generation status
github-backlog status REPO_URL

Global Options:
  --api-key TEXT     Override Anthropic API key
  --github-token TEXT Override GitHub token
  --help             Show help message
```

### Examples

```bash
# Complete workflow for new project
# 1. Initialize and analyze project
github-backlog init https://github.com/owner/repo

# 2. Check what was generated
github-backlog status https://github.com/owner/repo

# 3. Create all milestones in GitHub
github-backlog milestones https://github.com/owner/repo

# 4. Generate epics for phase 1
github-backlog generate owner/repo --phase 1

# 5. Generate issues for specific epic
github-backlog generate owner/repo --phase 1 --epic 2

# 6. Generate issues for all epics in phase 1
github-backlog generate owner/repo --phase 1 --all-epics

# Incremental workflow (test each component)
# Test epic generation without GitHub
github-backlog generate owner/repo --phase 1 --dry-run

# Test issue generation for one epic
github-backlog generate owner/repo --phase 1 --epic 1 --dry-run

# When ready, create in GitHub
github-backlog generate owner/repo --phase 1 --epic 1
```

## 📋 What Gets Created?

### 1. GitHub Milestone (Phase)
- **Title**: "Phase 1 - 📚 Research & Discovery"
- **Description**: Detailed phase objectives and deliverables
- **Due Date**: 2-4 weeks from creation

### 2. Epic Issues
Each phase gets 5-10 epic issues:
- **Title**: "[EPIC] User Research and Persona Development"
- **Label**: `epic`
- **Body**: Contains:
  - Epic description and objectives
  - Team composition with required roles
  - Checklist of all child tasks
  - Links to related issues

### 3. Task Issues
Each epic gets 3-7 task issues:
- **Title**: "Implement JWT authentication with refresh tokens"
- **Labels**: `priority:high`, `role:backend`
- **Body**: Contains:
  - Detailed description
  - Acceptance criteria (testable requirements)
  - Technical notes and implementation guidance
  - Dependencies and blockers
  - Assigned role and effort estimate

## 🧠 Built-in Intelligence

### Mental Models Applied
- **Double Diamond**: Divergent/convergent thinking in phases
- **Jobs To Be Done**: Epics focused on user outcomes
- **MoSCoW**: Prioritization of must/should/could haves
- **Test-First Thinking**: Acceptance criteria before implementation

### Cognitive Bias Mitigation
- **Planning Fallacy**: Adds 30% buffer to estimates
- **Feature Creep**: Keeps epics focused on single outcomes
- **Overconfidence**: Adds 50% buffer to complex technical tasks
- **Tunnel Vision**: Considers ripple effects and dependencies

## 🔄 Workflow Examples

### Option 1: Create Everything at Once (Original)
```bash
# Generate all phases with milestones and issues
github-backlog generate mycompany/new-project --all-phases
```

### Option 2: Two-Step Process (Recommended)
```bash
# 1. Create all milestones first (instant)
github-backlog milestones mycompany/new-project

# 2. Review milestones on GitHub, then populate them
github-backlog generate mycompany/new-project --all-phases

# OR populate incrementally
github-backlog generate mycompany/new-project --phase 1

# 2. After research is complete, generate phase 2 (Planning)
github-backlog generate mycompany/new-project --phase 2

# 3. Continue through all phases as project progresses
# Each phase builds on the previous work
```

## 🧪 Development

### Running Tests
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test file
pytest tests/test_phase_generator.py -v
```

### Code Quality
```bash
# Format code
make format

# Run linting
make lint

# Type checking
mypy src/
```

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

## 🙋 FAQ

**Q: Can I customize the phases?**
A: Yes! The tool adapts phases based on your project type. AI projects get ML-specific phases, e-commerce gets marketplace phases, etc.

**Q: What if I already have some milestones?**
A: The tool creates new milestones. You can use `--dry-run` to preview first.

**Q: Can I modify the generated issues?**
A: Absolutely! The generated issues are starting points. Edit them to match your team's needs.

**Q: Does it work with private repositories?**
A: Yes, as long as your GitHub token has access to the repository.

**Q: How much does it cost?**
A: You only pay for Anthropic API usage (~$0.01-0.03 per phase generation).

## 🐛 Troubleshooting

### "Repository not found"
- Check your GitHub token has access to the repository
- Verify the repository URL is correct
- For private repos, ensure token has `repo` scope

### "API rate limit exceeded"
- GitHub has rate limits; wait a few minutes
- Consider using `--dry-run` for testing

### "Invalid API key"
- Verify your Anthropic API key is correct
- Check you have credits in your Anthropic account

## 📮 Support

- 📧 Email: ford@flyingpig.ai
- 🐛 Issues: [GitHub Issues](https://github.com/ford-at-home/agent-team-composer/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/ford-at-home/agent-team-composer/discussions)