# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Fixed critical ESM module resolution issues where same-directory imports were missing .js extensions
- Fixed build script regex patterns to handle all import types (regular, dynamic, export, side-effect)
- Fixed validation script with correct regex patterns
- Added comprehensive build validation and testing

### Added
- Build validation script (`scripts/validate-build.js`)
- Build integration tests (`test/build.integration.test.js`)
- GitHub Actions workflows for CI/CD and NPM publishing
- Comprehensive build system documentation
- Contributing guidelines

### Changed
- Improved build script to handle all ESM import patterns
- Enhanced error messages in build validation
- Updated build process to include automatic validation

## [0.1.2] - 2024-01-XX

### Added
- Initial release of agent-team-composer
- CLI tool for generating GitHub project plans from README files
- Integration with Anthropic Claude API
- Support for multi-phase project planning
- Automatic role assignment for tasks