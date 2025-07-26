# Development Guide

## Setting Up Development Environment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/github-backlog-generator
   cd github-backlog-generator
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in development mode**:
   ```bash
   pip install -e .
   pip install -r requirements.txt
   ```

4. **Install development dependencies**:
   ```bash
   pip install pytest pytest-cov black flake8 mypy
   ```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=github_backlog_generator

# Run specific test file
pytest tests/test_cli.py

# Run tests for new CLI commands
pytest tests/test_new_commands.py -v

# Run integration tests
python3 test_integration.py
```

## Code Style

We use:
- **Black** for code formatting
- **Flake8** for linting
- **MyPy** for type checking

```bash
# Format code
black src/

# Check linting
flake8 src/

# Type checking
mypy src/
```

## CLI Architecture

### New Streamlined Commands (v2.0+)

The CLI now provides intuitive primitive commands with auto-detection:

- **`phases`** - Create all GitHub milestones (alias for `milestones`)
- **`epics`** - Generate epics for all phases or specific phase (`--phase N`)
- **`issues`** - Generate issues for all epics or specific combinations (`--phase N --epic N`)
- **`status`** - Enhanced hierarchical status with JSON/table output (`--output json|table`)

### Auto-Detection Logic

All new commands support repository auto-detection:
1. Searches for `.backlog-*` directories
2. Extracts owner/repo from directory names
3. Falls back to error if no repository found

### Command Implementation

The new commands are implemented in `src/github_backlog_generator/cli.py`:
- `phases()` - Lines 878-909, calls existing `milestones()` function
- `epics()` - Lines 912-973, orchestrates multiple `generate()` calls  
- `issues()` - Lines 976-1043, handles phase/epic targeting logic
- `enhanced_status()` - Lines 779-958, enhanced with JSON output

### Backward Compatibility

All original commands remain fully functional:
- `init` - Initialize project and generate phases
- `generate` - Generate epics/issues (original syntax with --phase, --epic, --all-epics)
- `milestones` - Create GitHub milestones
- `status` - Show project status (enhanced with new features)
- `pricing` - Display API pricing information

## Project Structure

```
github-backlog-generator/
├── src/
│   └── github_backlog_generator/
│       ├── __init__.py
│       ├── cli.py              # Main CLI entry point (enhanced with new commands)
│       ├── github_client.py    # GitHub API interactions
│       ├── phase_generator.py  # Phase generation logic
│       ├── epic_generator.py   # Epic creation logic
│       └── readme_parser.py    # README parsing utilities
├── tests/                      # Test files
│   ├── test_simple.py         # Basic import tests
│   └── test_new_commands.py   # Tests for new CLI commands
├── CLI_COMMANDS.md            # Comprehensive CLI documentation
├── test_integration.py        # Integration tests for new commands
├── setup.py                   # Package configuration
├── pyproject.toml            # Modern package config
├── requirements.txt          # Dependencies
└── README.md                  # User documentation
```

## Making Changes

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and test thoroughly

3. Update documentation if needed

4. Submit a pull request

## Adding New Features

When adding new features:
1. Update the CLI help text
2. Add appropriate tests
3. Update README.md with examples
4. Consider backward compatibility

## Release Process

1. Update version numbers in:
   - `setup.py`
   - `pyproject.toml`
   - `src/github_backlog_generator/__init__.py`

2. Update CHANGELOG (if exists)

3. Create a pull request for the release

4. After merging, tag the release:
   ```bash
   git tag -a v1.0.1 -m "Release version 1.0.1"
   git push origin v1.0.1
   ```

5. Build and publish to PyPI (see PUBLISHING.md)

## Debugging

To debug the CLI:
```python
# Add to your code for debugging
import pdb; pdb.set_trace()

# Or use rich's inspect
from rich import inspect
inspect(your_object)
```

## Common Issues

1. **Import errors**: Ensure you're in the virtual environment
2. **API rate limits**: Use a GitHub token with appropriate permissions
3. **Package not found**: Install in development mode with `pip install -e .`