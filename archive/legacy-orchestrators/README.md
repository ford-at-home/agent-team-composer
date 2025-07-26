# Legacy Orchestrator Scripts Archive

This directory contains the archived orchestrator scripts that have been replaced by the unified orchestrator.

## Archived Scripts

- **`github-backlog-orchestrator.sh`** - v1.0 Basic orchestration
  - Status: Legacy, no longer maintained
  - Features: Basic workflow without cost tracking

- **`github-backlog-orchestrator-v2.sh`** - v2.0 Enhanced orchestration
  - Status: Migrated to unified version
  - Features: Native CLI cost/timing tracking

- **`github-backlog-orchestrator-with-costs.sh`** - v1.1 External cost estimation
  - Status: Legacy, replaced by native tracking
  - Features: External cost calculations with `bc`

## Migration

All functionality has been consolidated into `github-backlog-orchestrator-unified.sh` which provides:

- ✅ Native CLI cost and timing tracking via `--cost` and `--time` flags
- ✅ All existing orchestration workflows
- ✅ Enhanced error handling and reporting
- ✅ Consistent command patterns

## Usage

Replace any existing orchestrator script calls with:

```bash
# Old
./github-backlog-orchestrator-v2.sh --cost https://github.com/owner/repo

# New
./github-backlog-orchestrator-unified.sh --cost https://github.com/owner/repo
```

## Date Archived

$(date)