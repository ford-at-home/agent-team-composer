# Contributing to GitHub Backlog Generator

Thank you for your interest in contributing to GitHub Backlog Generator! We welcome contributions from the community and are grateful for any help you can provide.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Style Guidelines](#style-guidelines)
- [Reporting Issues](#reporting-issues)

## 📜 Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Show empathy towards other community members

## 🚀 Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a new branch for your feature or bug fix
4. Make your changes
5. Push to your fork and submit a pull request

## 🤝 How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- A clear and descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- System information (OS, Python version, etc.)
- Any relevant error messages or logs

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- A clear and descriptive title
- A detailed description of the proposed functionality
- Any possible drawbacks or considerations
- Examples of how the feature would be used

### Pull Requests

1. Follow the [development setup](#development-setup) instructions
2. Create a new branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes and commit them with clear messages
4. Write or update tests as needed
5. Update documentation if necessary
6. Push to your fork and create a pull request

## 🛠️ Development Setup

### Prerequisites

- Python 3.8 or higher
- pip
- git

### Setup Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/ford-at-home/agent-team-composer.git
   cd agent-team-composer/github-backlog-generator
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   pip install -r requirements-dev.txt
   ```

4. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

5. Create a `.env` file with your API keys:
   ```bash
   cp .env.example .env
   # Edit .env and add your keys
   ```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=github_backlog_generator

# Run specific test file
pytest tests/test_cli.py

# Run with verbose output
pytest -v
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files with `test_` prefix
- Use descriptive test function names
- Include both positive and negative test cases
- Mock external API calls

Example test:
```python
def test_parse_github_url():
    """Test that GitHub URLs are parsed correctly."""
    url = "https://github.com/owner/repo"
    owner, repo = parse_github_url(url)
    assert owner == "owner"
    assert repo == "repo"
```

## 📝 Style Guidelines

### Python Style

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with these additions:

- Use type hints where possible
- Maximum line length: 88 characters (Black default)
- Use descriptive variable names
- Add docstrings to all functions and classes

### Code Formatting

We use the following tools for code formatting:

- **Black** for Python code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

Run formatting:
```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Check linting
flake8 src/ tests/

# Type checking
mypy src/
```

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Test additions or changes
- `chore:` Maintenance tasks

Examples:
```
feat: add support for private repositories
fix: handle empty README files gracefully
docs: update installation instructions
```

## 🚀 Submitting Changes

1. Ensure all tests pass
2. Update documentation as needed
3. Add an entry to CHANGELOG.md
4. Create a pull request with:
   - Clear title and description
   - Reference to any related issues
   - Screenshots if applicable

### Pull Request Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] Commit messages follow conventions
- [ ] Branch is up to date with main

## 📮 Getting Help

If you need help, you can:

1. Check the [documentation](../README.md)
2. Search [existing issues](https://github.com/ford-at-home/agent-team-composer/issues)
3. Create a [discussion](https://github.com/ford-at-home/agent-team-composer/discussions)
4. Reach out on our community channels

## 🙏 Recognition

Contributors will be recognized in our README.md file. Thank you for helping make GitHub Backlog Generator better!

---

Thank you for contributing! 🎉