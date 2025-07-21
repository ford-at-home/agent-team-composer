# Publishing to PyPI

This guide walks you through publishing `github-backlog-generator` to PyPI.

## Prerequisites

1. **PyPI Account**: Create accounts at:
   - [PyPI](https://pypi.org/account/register/)
   - [TestPyPI](https://test.pypi.org/account/register/) (for testing)

2. **API Tokens**: Generate API tokens for both PyPI and TestPyPI:
   - Go to Account Settings → API tokens
   - Create a token with "Entire account" scope

3. **Configure .pypirc**: Copy `.pypirc.template` to `~/.pypirc` and add your tokens:
   ```bash
   cp .pypirc.template ~/.pypirc
   chmod 600 ~/.pypirc
   ```

## Pre-flight Checklist

Before publishing, ensure:

- [ ] Update version number in `setup.py` and `pyproject.toml`
- [ ] Update version in `src/github_backlog_generator/__init__.py`
- [ ] Update author email in `setup.py` and `pyproject.toml`
- [ ] Update GitHub URLs in `setup.py` and `pyproject.toml`
- [ ] All tests pass
- [ ] Documentation is up to date
- [ ] CHANGELOG is updated (if you have one)

## Publishing Steps

### 1. Clean Previous Builds

```bash
rm -rf dist build *.egg-info src/*.egg-info
```

### 2. Build the Package

```bash
python -m build
```

### 3. Validate the Package

```bash
python -m twine check dist/*
```

### 4. Test Upload to TestPyPI

```bash
python -m twine upload --repository testpypi dist/*
```

Test installation from TestPyPI:
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ github-backlog-generator
```

### 5. Upload to PyPI

Once you're confident everything works:

```bash
python -m twine upload dist/*
```

### 6. Verify Installation

```bash
pip install github-backlog-generator
github-backlog --help
```

## Post-Publishing

1. **Create a Git Tag**:
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

2. **Create a GitHub Release**:
   - Go to your repository on GitHub
   - Click "Releases" → "Create a new release"
   - Choose the tag you just created
   - Add release notes

3. **Update README Badge** (optional):
   Add a PyPI badge to your README:
   ```markdown
   [![PyPI version](https://badge.fury.io/py/github-backlog-generator.svg)](https://pypi.org/project/github-backlog-generator/)
   ```

## Troubleshooting

- **"Invalid distribution file"**: Run `python -m twine check dist/*` to identify issues
- **"Package already exists"**: Increment the version number
- **Authentication failed**: Check your API token in `~/.pypirc`

## Version Management

To update the version:
1. Update version in `setup.py`, `pyproject.toml`, and `__init__.py`
2. Rebuild the package
3. Upload the new version

Remember: You cannot overwrite an existing version on PyPI. Always increment the version number for updates.