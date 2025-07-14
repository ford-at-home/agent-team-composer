# Agent Team Composer

<div align="center">

![NPM Version](https://img.shields.io/npm/v/agent-team-composer.svg)

Transform any README.md into a comprehensive GitHub project plan with AI-powered agent teams optimized for Claude Flow SPARC methodology.

</div>

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

- Node.js 18+ (required for ES modules support)
- GitHub repository with a README.md
- Anthropic API key
- GitHub CLI (optional, for enhanced features)

## 📦 Installation

| Method                | Command                               |
| --------------------- | ------------------------------------- |
| **npx** (recommended) | `npx agent-team-composer init`        |
| **npm** (global)      | `npm install -g agent-team-composer`  |
| **yarn** (global)     | `yarn global add agent-team-composer` |

## 🌟 Features

<table>
<tr>
<td align="center" width="33%">

### 🤖 AI-Powered

Uses Claude to generate project-specific phases, epics, and issues

</td>
<td align="center" width="33%">

### 🎯 SPARC Ready

Issues formatted for autonomous agent execution

</td>
<td align="center" width="33%">

### 🔗 GitHub Native

Creates epics, issues, milestones, and labels

</td>
</tr>
<tr>
<td align="center" width="33%">

### 📝 Smart Parsing

Automatically extracts project info from README

</td>
<td align="center" width="33%">

### 🎨 Interactive UI

5-step wizard to review and edit everything

</td>
<td align="center" width="33%">

### ⚙️ Customizable

Edit phases, roles, and issues to match needs

</td>
</tr>
</table>

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

## 📊 Example Output

| Metric         | Typical Output                           |
| -------------- | ---------------------------------------- |
| **Phases**     | 8 phases from Discovery to Enhancement   |
| **Issues**     | 20+ detailed tasks with role assignments |
| **Roles**      | 10+ specialized agent personas           |
| **Milestones** | Sprint markers with timelines            |
| **Labels**     | Auto-generated for agents and phases     |

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

See [docs/RELEASE_WORKFLOW.md](docs/RELEASE_WORKFLOW.md) for detailed release instructions.

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

## 🏆 Contributors

<a href="https://github.com/ford-at-home/agent-team-composer/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=ford-at-home/agent-team-composer" />
</a>

## 📈 Stats

[![GitHub Stars](https://img.shields.io/github/stars/ford-at-home/agent-team-composer?style=social)](https://github.com/ford-at-home/agent-team-composer)
[![GitHub Forks](https://img.shields.io/github/forks/ford-at-home/agent-team-composer?style=social)](https://github.com/ford-at-home/agent-team-composer)
[![GitHub Issues](https://img.shields.io/github/issues/ford-at-home/agent-team-composer?style=flat-square)](https://github.com/ford-at-home/agent-team-composer/issues)
[![GitHub PRs](https://img.shields.io/github/issues-pr/ford-at-home/agent-team-composer?style=flat-square)](https://github.com/ford-at-home/agent-team-composer/pulls)

## 📄 License

MIT © Agent Team Composer Contributors

---

<div align="center">
  <strong>Built with ❤️ for the Claude Flow SPARC community</strong>
  
  <br />
  
  <a href="https://www.npmjs.com/package/agent-team-composer">NPM</a> •
  <a href="https://github.com/ford-at-home/agent-team-composer">GitHub</a> •
  <a href="https://github.com/ford-at-home/agent-team-composer/issues">Issues</a> •
  <a href="https://github.com/ford-at-home/agent-team-composer/blob/main/CONTRIBUTING.md">Contributing</a>
</div>
