# 🚀 DEMO INSTRUCTIONS - Agent Team Composer

## ✅ VERIFIED WORKING - Ready for Demo

### Prerequisites

- Node.js 18+ installed
- GitHub CLI (`gh`) installed
- Anthropic API key set: `export ANTHROPIC_API_KEY=your-key`

### Step 1: Build the Package (if not already done)

```bash
npm run build:npm
```

### Step 2: Prepare Demo Directory

```bash
# Create a demo directory
mkdir demo-project
cd demo-project

# Create a sample README.md
cat > README.md << 'EOF'
# Awesome Product Demo

A revolutionary productivity tool that will change how teams work.

## Overview
This is an AI-powered project management tool that helps teams collaborate more effectively.

## Features
- Smart task management
- AI-powered insights
- Real-time collaboration
- Advanced analytics

## Tech Stack
- React/TypeScript frontend
- Node.js backend
- PostgreSQL database
- Redis caching
EOF
```

### Step 3: Run Agent Team Composer

```bash
# From the demo-project directory
node ../agent-team-composer/bin/agent-team-composer.js init
```

### What Will Happen:

1. ✅ Environment validation
2. ✅ README parsing
3. ⏳ AI generation (takes 30-60 seconds)
4. ✅ Server starts on http://localhost:3000
5. ✅ Browser opens automatically
6. ✅ Beautiful UI displays your project plan

### Demo Talking Points:

- "Agent Team Composer transforms a simple README into a complete GitHub project plan"
- "It uses Claude AI to understand your project and generate phases, epics, and issues"
- "The UI provides an intuitive way to review and customize the plan before pushing to GitHub"
- "With one click, create all milestones, epics, and issues in your GitHub repository"

### Troubleshooting:

- If port 3000 is busy, use: `--port 3001`
- To skip GitHub check: `--skip-gh-check`
- For fresh generation: `--fresh`

### UI Features to Show:

1. **Phase View**: Shows project timeline
2. **Epic Cards**: Drag and drop to reorganize
3. **Issue Details**: Click to see full requirements
4. **GitHub Integration**: One-click to create everything

### To Stop the Demo:

Press `Ctrl+C` in the terminal (signal handling has been fixed)

## 🎯 KEY POINTS FOR SUCCESS:

1. The build MUST use `npm run build:npm` (not just `npm run build`)
2. Run from a directory with a README.md file
3. Have your Anthropic API key set
4. Allow 30-60 seconds for AI generation

## 💡 Pro Tips:

- Pre-generate a project before the demo to skip waiting
- Use a simple README for faster generation
- Have GitHub token ready if you want to show the push feature

---

**TESTED AND VERIFIED** ✅

- Server starts correctly
- UI loads without errors
- API endpoints work
- Assets are served properly
- Process can be terminated with Ctrl+C

Good luck with your demo! 🚀
