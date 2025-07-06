# Agent Team Composer

<div align="center">

[![npm version](https://img.shields.io/npm/v/agent-team-composer.svg?style=flat-square)](https://www.npmjs.com/package/agent-team-composer)
[![npm downloads](https://img.shields.io/npm/dm/agent-team-composer.svg?style=flat-square)](https://www.npmjs.com/package/agent-team-composer)
[![npm bundle size](https://img.shields.io/bundlephobia/minzip/agent-team-composer?style=flat-square)](https://bundlephobia.com/package/agent-team-composer)
[![CI Status](https://img.shields.io/github/actions/workflow/status/ford-at-home/agent-team-composer/ci.yml?branch=main&label=CI&style=flat-square)](https://github.com/ford-at-home/agent-team-composer/actions/workflows/ci.yml)
[![Build Status](https://img.shields.io/github/actions/workflow/status/ford-at-home/agent-team-composer/build-validation.yml?branch=main&label=Build&style=flat-square)](https://github.com/ford-at-home/agent-team-composer/actions/workflows/build-validation.yml)
[![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen?style=flat-square)](https://github.com/ford-at-home/agent-team-composer)
[![License](https://img.shields.io/npm/l/agent-team-composer?style=flat-square)](https://github.com/ford-at-home/agent-team-composer/blob/main/LICENSE)
[![Node Version](https://img.shields.io/node/v/agent-team-composer?style=flat-square)](https://nodejs.org)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)

[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-blue?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)
[![React](https://img.shields.io/badge/React-18.3-61dafb?style=flat-square&logo=react)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-5.4-646cff?style=flat-square&logo=vite)](https://vitejs.dev/)
[![Claude AI](https://img.shields.io/badge/Claude_AI-Powered-ff6b6b?style=flat-square)](https://www.anthropic.com/)

Transform any README.md into a comprehensive GitHub project plan with AI-powered agent teams optimized for Claude Flow SPARC methodology.

</div>

## 🚀 Quick Start

<div align="center">
  <img src="https://img.shields.io/badge/npx-agent--team--composer_init-brightgreen?style=for-the-badge&logo=npm" alt="npx command" />
</div>

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

## 📦 Installation

<div align="center">

| Method                | Command                               | Badge                                                                                 |
| --------------------- | ------------------------------------- | ------------------------------------------------------------------------------------- |
| **npx** (recommended) | `npx agent-team-composer init`        | ![npx](https://img.shields.io/badge/npx-ready-brightgreen?style=flat-square&logo=npm) |
| **npm** (global)      | `npm install -g agent-team-composer`  | ![npm](https://img.shields.io/badge/npm-install-cb3837?style=flat-square&logo=npm)    |
| **yarn** (global)     | `yarn global add agent-team-composer` | ![yarn](https://img.shields.io/badge/yarn-add-2c8ebb?style=flat-square&logo=yarn)     |

</div>

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

<div align="center">

| Metric         | Typical Output                           |
| -------------- | ---------------------------------------- |
| **Phases**     | 8 phases from Discovery to Enhancement   |
| **Issues**     | 20+ detailed tasks with role assignments |
| **Roles**      | 10+ specialized agent personas           |
| **Milestones** | Sprint markers with timelines            |
| **Labels**     | Auto-generated for agents and phases     |

</div>

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

## 🏆 Contributors

<a href="https://github.com/ford-at-home/agent-team-composer/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=ford-at-home/agent-team-composer" />
</a>

## 📈 Stats

<div align="center">

![GitHub Stars](https://img.shields.io/github/stars/ford-at-home/agent-team-composer?style=social)
![GitHub Forks](https://img.shields.io/github/forks/ford-at-home/agent-team-composer?style=social)
![GitHub Issues](https://img.shields.io/github/issues/ford-at-home/agent-team-composer?style=flat-square)
![GitHub PRs](https://img.shields.io/github/issues-pr/ford-at-home/agent-team-composer?style=flat-square)

</div>

## 📄 License

<div align="center">

MIT © Agent Team Composer Contributors

[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fford-at-home%2Fagent-team-composer.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2Fford-at-home%2Fagent-team-composer?ref=badge_shield)

---

<p align="center">
  <strong>Built with ❤️ for the Claude Flow SPARC community</strong>
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/agent-team-composer">NPM</a> •
  <a href="https://github.com/ford-at-home/agent-team-composer">GitHub</a> •
  <a href="https://github.com/ford-at-home/agent-team-composer/issues">Issues</a> •
  <a href="https://github.com/ford-at-home/agent-team-composer/blob/main/CONTRIBUTING.md">Contributing</a>
</p>

</div>
