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

## Project Structure

```
github-backlog-generator/
├── src/
│   └── github_backlog_generator/
│       ├── __init__.py
│       ├── cli.py              # Main CLI entry point
│       ├── github_client.py    # GitHub API interactions
│       ├── phase_generator.py  # Phase generation logic
│       ├── epic_generator.py   # Epic creation logic
│       └── readme_parser.py    # README parsing utilities
├── tests/                      # Test files
├── setup.py                    # Package configuration
├── pyproject.toml             # Modern package config
├── requirements.txt           # Dependencies
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