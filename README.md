# Agent Team Composer

Transform any README.md into a comprehensive GitHub project plan with AI-powered agent teams optimized for Claude Flow SPARC methodology.

## 🚀 Quick Start

```bash
npx agent-team-composer init
```

That's it! The tool will:
1. Read your project's README.md
2. Use Claude AI to generate a complete project plan
3. Launch a localhost UI for review and editing
4. Push approved plans to GitHub as issues and epics

## 📋 Prerequisites

- Node.js 16+
- GitHub repository with a README.md
- Anthropic API key
- GitHub CLI (optional, for enhanced features)

## 🔧 Installation

### Run without installing:
```bash
npx agent-team-composer init
```

### Or install globally:
```bash
npm install -g agent-team-composer
agent-team-composer init
```

## 🌟 Features

- **AI-Powered Planning**: Uses Claude to generate project-specific phases, epics, and issues
- **5-Step Interactive UI**: Review and edit every aspect before pushing to GitHub
- **SPARC Optimization**: Issues formatted for autonomous agent execution
- **Smart Parsing**: Automatically extracts project info from your README
- **GitHub Integration**: Creates epics, issues, milestones, and labels
- **Customizable**: Edit phases, roles, and issues to match your needs

## 🎯 How It Works

1. **Parse Product**: Analyzes your README and extracts project metadata
2. **Sprint View**: AI generates 3-8 development phases based on your project
3. **Epic View**: Breaks down each phase into epics with role assignments  
4. **Issues View**: Creates detailed issues for each epic with SPARC formatting
5. **GitHub Sync**: Select repository/branch and push everything to GitHub

## 🛠️ Configuration

Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY=your-api-key
```

Optional: Configure GitHub token for enhanced features:
```bash
export GITHUB_TOKEN=ghp_your-token
```

## 📖 Command Options

```bash
agent-team-composer init [options]

Options:
  -p, --port <port>        Port for localhost UI (default: 3000)
  -r, --readme <path>      Path to README.md (default: README.md)
  --skip-gh-check          Skip GitHub CLI verification
  -h, --help               Display help
```

## 🤖 SPARC Agent Integration

Generated issues include:
- Role assignments for autonomous agents
- Structured markdown with clear deliverables
- Dependency mapping between tasks
- Labels: `sparc-enabled:true`, `role:<persona>`, `phase:<phase>`
- Execution hints for parallel vs sequential work

## 🔍 Example Output

For a typical project, Agent Team Composer generates:
- **8 Phases**: Discovery through Enhancement
- **20+ Issues**: Detailed tasks with role assignments
- **10+ Roles**: Specialized agent personas
- **Milestones**: Sprint markers with timelines

## 🐛 Troubleshooting

### Missing Anthropic API Key
```bash
export ANTHROPIC_API_KEY=sk-ant-api...
```

### GitHub Authentication Issues
```bash
# Option 1: Use GitHub CLI
gh auth login

# Option 2: Use token
export GITHUB_TOKEN=ghp_...
```

### Port Already in Use
```bash
agent-team-composer init --port 4000
```

## 🚀 Release Process

See [docs/RELEASE.md](docs/RELEASE.md) for detailed release instructions.

### Automatic Releases

Every PR merged to main automatically triggers a release! Version is determined by PR labels:
- `feature` → Minor version bump (new features)
- `breaking-change` → Major version bump  
- No label → Patch version bump (bug fixes)
- `skip-release` → No release

### Manual Releases

1. **Create Release PR**: Actions → "Create Release PR" → Choose version → Run
2. **Direct Publish**: Actions → "Publish to NPM" → Choose version → Run

### Setup NPM Publishing

To enable automated NPM publishing:

1. Create NPM access token at https://www.npmjs.com/
2. Add to GitHub: Settings → Secrets → Actions → New repository secret
   - Name: `NPM_TOKEN`
   - Value: Your NPM access token

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

### Development Setup

```bash
# Clone and install
git clone https://github.com/ford-at-home/agent-team-composer
cd agent-team-composer
npm install

# Run tests
npm run test
npm run build:npm
npm run test:build

# Test locally
npm link
agent-team-composer init
```

## 📄 License

MIT © Agent Team Composer Contributors

---

Built with ❤️ for the Claude Flow SPARC community