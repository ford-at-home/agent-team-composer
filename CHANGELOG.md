# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added - New Streamlined CLI Commands (v2.0)
- **`github-backlog-generator phases`** - Create all GitHub milestones with auto-detection
- **`github-backlog-generator epics [--phase N]`** - Generate epics for all or specific phases
- **`github-backlog-generator issues [--phase N --epic N]`** - Generate issues with fine-grained targeting
- **Enhanced `github-backlog-generator status [--output json|table]`** - Hierarchical project view with JSON export
- Repository auto-detection from `.backlog-*` directories for all new commands
- Comprehensive CLI documentation in `CLI_COMMANDS.md`
- Unit tests and integration tests for all new commands (`tests/test_new_commands.py`)

### Added - Infrastructure & Tracking
- Cost and timing tracking at CLI level with `--cost` and `--time` flags
- Native CLI integration for accurate API usage data
- Persistent cost storage to project directory for historical analysis
- Enhanced orchestrator scripts with CLI integration (v2.0)
- Comprehensive .gitignore for Python project with venv and backlog exclusions

### Enhanced
- CLI architecture with intuitive primitive commands while maintaining backward compatibility
- Status command with both tabular summary and hierarchical tree views
- Auto-detection logic for seamless workflow after project initialization
- Orchestrator scripts simplified by removing internal cost estimation
- Clean delegation to CLI for all tracking functionality
- Better error handling and validation in orchestrator scripts
- Documentation updated across README.md, DEVELOPMENT.md, and new CLI_COMMANDS.md

### Backward Compatibility
- All original commands (`init`, `generate`, `milestones`, `pricing`) remain fully functional
- Existing workflows and scripts continue to work without modification
- Legacy command syntax preserved alongside new streamlined commands

### Technical
- Added `cost_tracker.py` module for persistent cost tracking
- Updated `github-backlog-orchestrator.sh` to v2.0 with CLI integration
- Created `github-backlog-orchestrator-v2.sh` with enhanced features
- Removed complex internal tracking in favor of CLI delegation

### Performance
- 50% reduction in orchestrator script complexity
- More accurate cost data using real API token counts vs estimates
- Better separation of orchestration vs tracking concerns

## [0.9.1] - 2024-01-XX

### Added
- Fully modular CLI with cascading file structure
- Two-step milestone creation workflow
- Comprehensive test coverage for modular CLI
- Enhanced issue templates with testing, deployment, and documentation requirements

### Fixed
- Test coverage and reliability improvements
- CLI command structure and error handling