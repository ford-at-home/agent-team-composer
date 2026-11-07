# GitHub Backlog Generator 🚀

> Transform any GitHub repository README into a structured project backlog with AI-powered analysis

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI Version](https://img.shields.io/pypi/v/github-backlog-generator.svg)](https://pypi.org/project/github-backlog-generator/)

## 🎯 What is GitHub Backlog Generator?

GitHub Backlog Generator is a powerful CLI tool that analyzes any GitHub repository's README and automatically generates a complete project backlog with:

- **📅 Milestones**: Organized project phases with timelines
- **📋 Epics**: High-level feature groupings with team composition
- **✅ Tasks**: Detailed, actionable items with role assignments
- **🏷️ Labels**: Automatic categorization for better organization

All generated content is created directly in your GitHub repository, ready for your team to start working!

## ✨ Features

- **🔗 GitHub Integration**: Works with any public or private GitHub repository
- **🤖 AI-Powered Analysis**: Uses Claude to understand project context and requirements
- **📊 8-Phase Lifecycle**: Covers the complete software development lifecycle
- **👥 Team Composition**: Suggests optimal team roles for each phase
- **🔄 Smart Dependencies**: Creates linked issues with proper relationships
- **💾 Export Options**: Save generated plans as JSON for review
- **🧪 Dry Run Mode**: Preview before creating GitHub issues

## 📦 Installation

### From PyPI (Recommended)

```bash
pip install github-backlog-generator
```

### From Source

```bash
# Clone the repository
git clone https://github.com/ford-at-home/agent-team-composer.git
cd agent-team-composer

# Install the package
pip install ./github-backlog-generator
```

## 🚀 Quick Start

### Simple Workflow (Recommended)

Navigate to the `github-backlog-generator` directory and use our Makefile commands:

```bash
cd github-backlog-generator

# 1. Install dependencies
make install

# 2. Set up your API keys
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export GITHUB_TOKEN="your-github-token-with-repo-scope"

# 3. Initialize project (interactive - you'll be prompted for repo URL)
make init

# 4. Create GitHub milestones for all phases
make phases

# 5. Generate epics for all phases
make epics

# 6. Create detailed issues for all epics
make issues
```

**That's it!** Your GitHub repository now has a complete structured backlog with milestones, epics, and detailed task issues.

### Manual CLI Usage

#### 🚀 **New Streamlined Commands (Recommended)**

The CLI now provides intuitive primitive commands that auto-detect your project:

```bash
# 1. Initialize project
github-backlog-generator init https://github.com/owner/repo

# 2. Create all phases (GitHub milestones) 
github-backlog-generator phases

# 3. Generate epics for all phases
github-backlog-generator epics

# 4. Generate issues for all epics across all phases  
github-backlog-generator issues

# 5. View hierarchical project status
github-backlog-generator status --output table
github-backlog-generator status --output json
```

#### 🎯 **Targeted Generation Commands**

For fine-grained control over specific phases and epics:

```bash
# Generate epics for specific phase only
github-backlog-generator epics --phase 3

# Generate issues for specific phase (all epics)
github-backlog-generator issues --phase 5

# Generate issues for specific epic in specific phase
github-backlog-generator issues --phase 4 --epic 2
```

#### 📊 **Enhanced Status and Monitoring**

```bash
# Table view with both summary and hierarchical structure
github-backlog-generator status

# JSON output for programmatic use
github-backlog-generator status --output json

# View specific repository status
github-backlog-generator status https://github.com/owner/repo
```

#### 🔧 **Legacy CLI Usage (Still Supported)**

If you prefer the original command structure:

1. **Initialize your project**:
   ```bash
   github-backlog init https://github.com/owner/repo
   ```

2. **Create milestones** (optional):
   ```bash
   github-backlog milestones https://github.com/owner/repo
   ```

3. **Generate epics and tasks**:
   ```bash
   github-backlog generate --phase 1 https://github.com/owner/repo
   # Or generate all epics first:
   github-backlog generate --all-epics https://github.com/owner/repo
   ```

4. **Check project status**:
   ```bash
   github-backlog status https://github.com/owner/repo
   ```

## 📋 Available Phases

The tool generates backlogs for 8 standard development phases:

1. **Discovery & Planning** - Requirements gathering and feasibility
2. **Design & Architecture** - System design and technical planning  
3. **Development Setup** - Environment and tooling configuration
4. **Core Development** - Main feature implementation
5. **Testing & QA** - Quality assurance and testing
6. **Documentation** - User and technical documentation
7. **Deployment** - Production deployment and DevOps
8. **Maintenance & Growth** - Ongoing improvements and scaling

## 🎼 Workflow Composition with run.sh

For advanced users who need custom orchestration, we provide `run.sh` - a comprehensive example script that demonstrates how to compose CLI commands into sophisticated workflows:

```bash
# Basic orchestration - generates complete backlog
./run.sh https://github.com/owner/repo

# With cost tracking
./run.sh --cost https://github.com/owner/repo

# With timing analysis and verbose output
./run.sh --time --verbose https://github.com/owner/repo

# Selective phase processing (only phases 1-3)
./run.sh --phases 1-3 https://github.com/owner/repo

# Generate only epics, skip issues
./run.sh --epics-only https://github.com/owner/repo

# Dry run mode - preview without creating GitHub items
./run.sh --dry-run https://github.com/owner/repo
```

### Why run.sh Exists

The `run.sh` script serves as a **workflow composition example** showing how to:

- **Chain commands**: Initialize → Create milestones → Generate epics → Create issues
- **Add orchestration logic**: Error handling, progress tracking, timing analysis
- **Enable advanced features**: Cost tracking, selective processing, dry runs
- **Provide user experience**: Colored output, progress reporting, summary generation

**Key Features of run.sh:**
- 🎯 **Orchestration**: Handles the complete workflow from start to finish
- 💰 **Cost Tracking**: Real-time API cost monitoring with persistent data
- ⏱️ **Timing Analysis**: Performance tracking for each workflow step  
- 🎨 **Rich Output**: Colored progress indicators and detailed summaries
- 🔍 **Selective Processing**: Target specific phases or epic generation only
- 🧪 **Dry Run Mode**: Preview generated content without creating GitHub items
- 📊 **Historical Analysis**: Persistent tracking data for multiple runs

Use `run.sh` as inspiration for building your own custom workflows that fit your team's specific needs.

## 🛠️ Advanced Usage

### Cost and Timing Tracking
Track API costs and execution time with any command:
```bash
# Track costs for any command (new or legacy)
github-backlog-generator --cost init https://github.com/owner/repo
github-backlog-generator --cost epics --phase 1
github-backlog-generator --cost issues

# Track timing for performance analysis
github-backlog-generator --time epics
github-backlog-generator --time issues --phase 3

# Use both together
github-backlog-generator --cost --time status
```

### 🎯 **New Streamlined Workflow**
Work with the intuitive new commands:
```bash
# Complete workflow with auto-detection
github-backlog-generator init https://github.com/owner/repo
github-backlog-generator phases
github-backlog-generator epics
github-backlog-generator issues
github-backlog-generator status --output json

# Selective generation
github-backlog-generator epics --phase 2
github-backlog-generator issues --phase 3 --epic 1
```

### 🔧 **Legacy Modular Workflow** 
Original command structure (still fully supported):
```bash
# Initialize project structure
github-backlog init https://github.com/owner/repo

# Create GitHub milestones for all phases
github-backlog milestones https://github.com/owner/repo

# Generate epics for specific phase
github-backlog generate --phase 2 https://github.com/owner/repo

# Generate all epics at once
github-backlog generate --all-epics https://github.com/owner/repo

# Generate issues for specific epic
github-backlog generate --epic "Epic Title" https://github.com/owner/repo

# Check current status
github-backlog status https://github.com/owner/repo
```

### 📊 **Status and Monitoring**
Enhanced status command with multiple output formats:
```bash
# Table view with hierarchical structure (default)
github-backlog-generator status

# JSON output for integration with other tools
github-backlog-generator status --output json | jq '.phases[0].epics'

# Monitor specific repository
github-backlog-generator status https://github.com/owner/repo --output json
```

### Model Selection
Choose different Claude models for cost optimization:
```bash
# Use faster, cheaper model for development
export GITHUB_BACKLOG_MODEL=claude-3-5-haiku-20241022
github-backlog init https://github.com/owner/repo

# Check current pricing
github-backlog pricing
```

## 🔧 Configuration

### Environment Variables

- `ANTHROPIC_API_KEY` - Your Anthropic API key for Claude
- `GITHUB_TOKEN` - GitHub personal access token with `repo` scope
- `GITHUB_BACKLOG_MODEL` - Claude model to use (default: `claude-3-5-sonnet-20241022`)

### GitHub Token Permissions

Your GitHub token needs the following scopes:
- `repo` - Full repository access (for creating issues and milestones)
- `read:org` - Read organization data (optional, for org repos)

## 📚 How It Works

1. **Fetch**: Downloads and analyzes the repository README
2. **Analyze**: AI extracts project context, tech stack, and complexity
3. **Generate**: Creates structured phase plan with epics and tasks
4. **Validate**: Ensures all generated content meets format requirements
5. **Create**: Posts milestone, epic issue, and task issues to GitHub

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](github-backlog-generator/CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repo
git clone https://github.com/ford-at-home/agent-team-composer.git
cd agent-team-composer/github-backlog-generator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
pip install -r requirements-dev.txt

# Run tests
pytest
```

## 📄 License

This software is proprietary and confidential, exclusively owned by Ford Prior. All rights reserved. See the [LICENSE](LICENSE) file for full terms.

## 🙏 Acknowledgments

- Built with [Claude](https://www.anthropic.com/claude) by Anthropic
- Uses [PyGithub](https://github.com/PyGithub/PyGithub) for GitHub API interaction
- CLI powered by [Click](https://click.palletsprojects.com/)
- Beautiful terminal output with [Rich](https://github.com/Textualize/rich)

## 📮 Support

- 📧 Email: ford@flyingpig.ai
- 🐛 Issues: [GitHub Issues](https://github.com/ford-at-home/agent-team-composer/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/ford-at-home/agent-team-composer/discussions)

---

<p align="center">
  Made with ❤️ by the GitHub Backlog Generator team
</p>