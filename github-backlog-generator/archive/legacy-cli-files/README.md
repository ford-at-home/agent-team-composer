# Legacy CLI Files Archive

This directory contains the archived CLI implementations that have been replaced by the unified CLI (`cli_unified.py`).

## Archived Files

- **`cli.py`** - Original single-phase CLI (442 lines)
  - Entry point: `github-backlog-v1` (removed)
  - Status: Legacy, no longer maintained

- **`cli_new.py`** - Subcommand-based structure (616 lines)
  - Entry point: `github-backlog-v2` (removed)  
  - Status: Legacy, no longer maintained

- **`cli_modular.py`** - Primary modular CLI (763 lines)
  - Entry point: `github-backlog` (migrated to unified)
  - Status: Replaced by unified CLI

- **`cli_enhanced.py`** - Enhanced with cost tracking (631 lines)
  - Entry point: None (was imported functionality)
  - Status: Merged into unified CLI

## Migration

All functionality from these files has been consolidated into `cli_unified.py` which provides:

- ✅ Full modular workflow (init → milestones → generate)
- ✅ Cost and timing tracking via `--cost` and `--time` flags
- ✅ All existing commands and options
- ✅ Backward compatibility for current workflows

## Total Reduction

- **Before**: 5 CLI files, 2,611 lines of code
- **After**: 1 unified CLI file, ~1,200 lines of code
- **Savings**: ~60% reduction in CLI complexity

## Date Archived

$(date)