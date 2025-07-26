# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Cost and timing tracking at CLI level with `--cost` and `--time` flags
- Native CLI integration for accurate API usage data
- Persistent cost storage to project directory for historical analysis
- Enhanced orchestrator scripts with CLI integration (v2.0)
- Comprehensive .gitignore for Python project with venv and backlog exclusions

### Enhanced
- CLI architecture with global cost/timing flags on all commands
- Orchestrator scripts simplified by removing internal cost estimation
- Clean delegation to CLI for all tracking functionality
- Better error handling and validation in orchestrator scripts

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