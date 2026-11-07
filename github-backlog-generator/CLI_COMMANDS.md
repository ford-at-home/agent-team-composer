# GitHub Backlog Generator - CLI Commands Reference

## 🚀 **New Streamlined Commands**

The CLI now provides intuitive primitive commands that auto-detect your project repository when possible.

---

## 📋 **Command Overview**

| Command | Purpose | Key Features |
|---------|---------|--------------|
| `phases` | Create all GitHub milestones | Auto-detects repo, calls `milestones` internally |
| `epics` | Generate epics for phases | Supports `--phase N` for targeting specific phases |
| `issues` | Generate issues for epics | Supports `--phase N --epic N` for fine-grained control |
| `status` | View project hierarchy | Supports `--output json\|table` formats |

---

## 🔧 **Command Details**

### `github-backlog-generator phases`

Create all GitHub milestones from generated phases.

**Usage:**
```bash
# Auto-detect repository from initialized project
github-backlog-generator phases

# Specify repository explicitly  
github-backlog-generator phases https://github.com/owner/repo

# Dry run to preview what would be created
github-backlog-generator phases --dry-run

# With specific GitHub token
github-backlog-generator phases --github-token <token>
```

**Options:**
- `--github-token TEXT` - GitHub personal access token
- `--dry-run` - Show what would be created without actually creating it
- `--help` - Show command help

**Notes:**
- This is an alias for the `milestones` command with enhanced auto-detection
- Requires phases to be generated first via `init`
- Auto-detects repository from `.backlog-*` directories

---

### `github-backlog-generator epics`

Generate epics for all phases or a specific phase.

**Usage:**
```bash
# Generate epics for all phases (auto-detect repo)
github-backlog-generator epics

# Generate epics for specific phase only
github-backlog-generator epics --phase 3

# Specify repository explicitly
github-backlog-generator epics https://github.com/owner/repo

# Dry run mode
github-backlog-generator epics --phase 2 --dry-run
```

**Options:**
- `--api-key TEXT` - Anthropic API key (or set ANTHROPIC_API_KEY)
- `--github-token TEXT` - GitHub personal access token (or set GITHUB_TOKEN)
- `-p, --phase TEXT` - Phase number to generate epics for (1-8 typically)
- `--dry-run` - Generate without creating GitHub items
- `--help` - Show command help

**Behavior:**
- **Without `--phase`**: Generates epics for all phases sequentially
- **With `--phase N`**: Generates epics only for the specified phase
- Auto-detects repository from existing `.backlog-*` directories
- Creates epic issues in GitHub with appropriate milestone assignment

---

### `github-backlog-generator issues`

Generate issues for all epics across all phases, or for specific combinations.

**Usage:**
```bash
# Generate issues for all epics across all phases
github-backlog-generator issues

# Generate issues for all epics in specific phase
github-backlog-generator issues --phase 5

# Generate issues for specific epic in specific phase  
github-backlog-generator issues --phase 4 --epic 2

# Specify repository explicitly
github-backlog-generator issues https://github.com/owner/repo --phase 3
```

**Options:**
- `--api-key TEXT` - Anthropic API key (or set ANTHROPIC_API_KEY)
- `--github-token TEXT` - GitHub personal access token (or set GITHUB_TOKEN)
- `-p, --phase TEXT` - Phase number to target
- `-e, --epic TEXT` - Epic number to target
- `--dry-run` - Generate without creating GitHub items
- `--help` - Show command help

**Behavior:**
- **No flags**: Generates issues for all epics across all phases
- **`--phase N` only**: Generates issues for all epics in phase N
- **`--phase N --epic M`**: Generates issues for epic M in phase N
- Auto-detects repository from existing `.backlog-*` directories
- Links issues to appropriate epic and milestone in GitHub

---

### `github-backlog-generator status`

Show hierarchical status of phases, epics, and issues with multiple output formats.

**Usage:**
```bash
# Table view with hierarchical structure (default)
github-backlog-generator status

# JSON output for programmatic use
github-backlog-generator status --output json

# View specific repository status
github-backlog-generator status https://github.com/owner/repo

# JSON output piped to jq for processing
github-backlog-generator status --output json | jq '.phases[0].epics'
```

**Options:**
- `-o, --output [table|json]` - Output format (default: table)
- `--help` - Show command help

**Output Formats:**

**Table Format (default):**
- Project information header
- Generation status table with phase/epic/issue counts
- Hierarchical structure showing:
  - 📅 Phase N: Title
    - 📋 Epic N: Title
      - ✅ Issue Title (priority)

**JSON Format:**
```json
{
  "project": {
    "title": "Project Name",
    "repository": "owner/repo",
    "created": "2024-01-01"
  },
  "phases": [
    {
      "number": 1,
      "title": "Phase Title",
      "epics": [
        {
          "number": 1,
          "title": "Epic Title",
          "issues": [
            {
              "title": "Issue Title",
              "priority": "high"
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 🔄 **Auto-Detection Logic**

All commands support automatic repository detection:

1. **When no repository URL is provided:**
   - Searches for `.backlog-*` directories in the parent directories
   - Extracts owner/repo from directory names (format: `.backlog-owner-repo`)
   - Uses the first match found
   - Displays "Auto-detected repository: ..." message

2. **When explicit repository URL is provided:**
   - Uses the provided URL
   - Overrides any auto-detection

3. **When no repository can be determined:**
   - Shows helpful error message with usage instructions
   - Exits with code 1

---

## ⚡ **Quick Workflow Examples**

### Complete Project Setup
```bash
# Initialize new project
github-backlog-generator init https://github.com/myorg/myproject

# Generate complete backlog
github-backlog-generator phases
github-backlog-generator epics  
github-backlog-generator issues

# Check final status
github-backlog-generator status
```

### Selective Generation
```bash
# Initialize project
github-backlog-generator init https://github.com/myorg/myproject

# Create milestones
github-backlog-generator phases

# Generate epics for first 3 phases only
github-backlog-generator epics --phase 1
github-backlog-generator epics --phase 2  
github-backlog-generator epics --phase 3

# Generate issues for specific epic
github-backlog-generator issues --phase 2 --epic 1

# Export status as JSON
github-backlog-generator status --output json > project-status.json
```

### Development Workflow
```bash
# Work in initialized project directory - commands auto-detect
cd my-project-dir

# Check current status
github-backlog-generator status

# Generate more epics as needed
github-backlog-generator epics --phase 4

# Generate issues for new epics
github-backlog-generator issues --phase 4

# Monitor progress
github-backlog-generator status --output json | jq '.phases[3].epics | length'
```

---

## 🔧 **Legacy Commands (Still Supported)**

The original command structure remains fully functional:

- `github-backlog-generator init` - Initialize project
- `github-backlog-generator generate` - Generate epics/issues (original syntax)
- `github-backlog-generator milestones` - Create milestones (original command)
- `github-backlog-generator pricing` - Show API pricing information

---

## 💡 **Tips and Best Practices**

1. **Always initialize first**: Run `init` before using other commands
2. **Use auto-detection**: After init, commands work without specifying repository
3. **Leverage dry-run**: Use `--dry-run` to preview changes before creating GitHub items
4. **Export status**: Use `--output json` for integration with other tools
5. **Incremental workflow**: Generate phases → epics → issues in stages
6. **Monitor progress**: Use `status` command regularly to track completion

---

## 🐛 **Troubleshooting**

**"No repository URL provided and no initialized project found"**
- Run `github-backlog-generator init <repo-url>` first
- Or provide explicit repository URL to commands

**"No phases found"**  
- Ensure you've run `init` to generate the initial phases
- Check that `.backlog-*` directory exists and contains `phases/phases.json`

**"GitHub API error: Not Found"**
- Verify your `GITHUB_TOKEN` environment variable is set
- Ensure the token has `repo` scope permissions
- Check that the repository URL is correct and accessible

**Auto-detection picks wrong repository**
- Multiple `.backlog-*` directories exist
- Use explicit repository URL: `github-backlog-generator status https://github.com/correct/repo`