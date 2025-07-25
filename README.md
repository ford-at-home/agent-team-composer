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

1. **Set up your API keys**:
   ```bash
   export ANTHROPIC_API_KEY="your-anthropic-api-key"
   export GITHUB_TOKEN="your-github-token-with-repo-scope"
   ```

2. **Generate a backlog**:
   ```bash
   github-backlog generate https://github.com/owner/repo
   ```

3. **Choose a phase** when prompted (1-8)

4. **Review and confirm** the generated plan

That's it! Check your GitHub repository for the newly created milestone, epic, and task issues.

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

## 🛠️ Advanced Usage

### Dry Run Mode
Preview the generated content without creating GitHub issues:
```bash
github-backlog generate https://github.com/owner/repo --dry-run
```

### Export to JSON
Save the generated phase for later use:
```bash
github-backlog generate https://github.com/owner/repo --output phase.json
```

### Process from JSON
Create GitHub issues from a previously exported phase:
```bash
github-backlog process phase.json --repo owner/repo
```

### Specify Phase Directly
Skip the interactive prompt:
```bash
github-backlog generate https://github.com/owner/repo --phase 3
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

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

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