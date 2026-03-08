# Packaging & Release Guide

Step-by-step guide for packaging and releasing `db-query-agent` to PyPI.

---

## Prerequisites

1. **Install build tools:**

```bash
pip install --upgrade pip
pip install build twine
```

2. **Create PyPI account:**
   - Register at https://pypi.org/account/register/
   - Register at https://test.pypi.org/account/register/ (for testing)

3. **Create API tokens:**
   - Go to https://pypi.org/manage/account/token/
   - Create a new API token
   - Save it securely (you'll only see it once)

---

## Step 1: Test Installation Locally

### 1.1 Create Clean Virtual Environment

```bash
# Create fresh environment
python -m venv test_env

# Activate it
# On Windows:
test_env\Scripts\activate
# On macOS/Linux:
source test_env/bin/activate
```

### 1.2 Install in Development Mode

```bash
# Install package in editable mode
pip install -e .

# Or with optional dependencies
pip install -e ".[dev]"
pip install -e ".[postgres]"
pip install -e ".[all]"
```

### 1.3 Test Import

```bash
python -c "from db_agent_sql import DatabaseQueryAgent; print('Success!')"
```

### 1.4 Run Tests

```bash
pytest tests/ -v
```

---

## Step 2: Build Distribution Packages

### 2.1 Clean Previous Builds

```bash
# Remove old builds
rm -rf build/ dist/ *.egg-info

# On Windows:
# rmdir /s /q build dist
# del /s /q *.egg-info
```

### 2.2 Build Packages

```bash
# Build both wheel and source distribution
python -m build

# This creates:
# - dist/db_agent_sql-0.1.0-py3-none-any.whl (wheel)
# - dist/db-query-agent-0.1.0.tar.gz (source)
```

### 2.3 Verify Build

```bash
# Check package contents
tar -tzf dist/db-query-agent-0.1.0.tar.gz

# Or on Windows:
# tar -tzf dist/db-query-agent-0.1.0.tar.gz
```

### 2.4 Check Package Quality

```bash
# Run twine check
twine check dist/*

# Should output:
# Checking dist/db_agent_sql-0.1.0-py3-none-any.whl: PASSED
# Checking dist/db-query-agent-0.1.0.tar.gz: PASSED
```

---

## Step 3: Test on TestPyPI

### 3.1 Upload to TestPyPI

```bash
# Upload to test.pypi.org
twine upload --repository testpypi dist/*

# You'll be prompted for:
# username: __token__
# password: <your-testpypi-token>
```

### 3.2 Test Installation from TestPyPI

```bash
# Create new test environment
python -m venv testpypi_env
source testpypi_env/bin/activate  # or testpypi_env\Scripts\activate on Windows

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    db-query-agent

# Test import
python -c "from db_agent_sql import DatabaseQueryAgent; print('Success!')"
```

### 3.3 Test Basic Functionality

```python
from db_agent_sql import DatabaseQueryAgent

# Create agent
agent = DatabaseQueryAgent(
    database_url="sqlite:///:memory:",
    openai_api_key="sk-test"
)

print("Package works!")
agent.close()
```

---

## Step 4: Release to PyPI

### 4.1 Update Version

Update version in `pyproject.toml`:

```toml
[project]
name = "db-query-agent"
version = "0.1.0"  # Update this
```

### 4.2 Update CHANGELOG

Add release notes to `CHANGELOG.md`:

```markdown
## [0.1.0] - 2025-10-23

### Added
- Initial release
- Natural language database querying
- Streaming responses
- Session management
- Multi-framework support
```

### 4.3 Create Git Tag

```bash
# Commit changes
git add .
git commit -m "Release v0.1.0"

# Create tag
git tag -a v0.1.0 -m "Release version 0.1.0"

# Push tag
git push origin v0.1.0
```

### 4.4 Upload to PyPI

```bash
# Upload to production PyPI
twine upload dist/*

# You'll be prompted for:
# username: __token__
# password: <your-pypi-token>
```

### 4.5 Verify on PyPI

Visit: https://pypi.org/project/db-query-agent/

---

## Step 5: Create GitHub Release

### 5.1 Go to GitHub Releases

Navigate to: `https://github.com/Ocolus1/db-query-agent/releases/new`

### 5.2 Fill Release Form

- **Tag:** v0.1.0
- **Title:** v0.1.0 - Initial Release
- **Description:** Copy from CHANGELOG.md

### 5.3 Attach Files

Upload distribution files:
- `db_agent_sql-0.1.0-py3-none-any.whl`
- `db-query-agent-0.1.0.tar.gz`

### 5.4 Publish Release

Click "Publish release"

---

## Step 6: Automated Releases (GitHub Actions)

### 6.1 Add PyPI Token to GitHub Secrets

1. Go to repository Settings → Secrets → Actions
2. Add new secret: `PYPI_API_TOKEN`
3. Paste your PyPI API token

### 6.2 Create Release via GitHub

```bash
# Push tag (triggers release workflow)
git tag -a v0.1.1 -m "Release v0.1.1"
git push origin v0.1.1

# Or create release via GitHub UI
# This will automatically:
# - Run tests
# - Build packages
# - Upload to PyPI
```

---

## Troubleshooting

### Issue: "File already exists"

**Cause:** Version already uploaded to PyPI

**Solution:**
```bash
# Increment version in pyproject.toml
version = "0.1.1"  # Bump version

# Rebuild
python -m build

# Upload new version
twine upload dist/*
```

### Issue: "Invalid distribution"

**Cause:** Missing files or incorrect structure

**Solution:**
```bash
# Check MANIFEST.in includes all necessary files
# Rebuild package
rm -rf dist/
python -m build
twine check dist/*
```

### Issue: "Authentication failed"

**Cause:** Wrong token or username

**Solution:**
```bash
# Use __token__ as username
# Use your API token as password (starts with pypi-)

# Or configure in ~/.pypirc:
[pypi]
username = __token__
password = pypi-...
```

---

## Checklist

Before releasing, ensure:

- [ ] All tests pass (`pytest tests/ -v`)
- [ ] Version bumped in `pyproject.toml`
- [ ] CHANGELOG.md updated
- [ ] README.md up to date
- [ ] Documentation complete
- [ ] LICENSE file present
- [ ] .gitignore configured
- [ ] Build succeeds (`python -m build`)
- [ ] Twine check passes (`twine check dist/*`)
- [ ] Tested on TestPyPI
- [ ] Git tag created
- [ ] GitHub release created

---

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR:** Breaking changes
- **MINOR:** New features (backward compatible)
- **PATCH:** Bug fixes (backward compatible)

Examples:
- `0.1.0` - Initial release
- `0.1.1` - Bug fix
- `0.2.0` - New feature
- `1.0.0` - First stable release

---

## Post-Release

### Announce Release

- [ ] Update README.md badges
- [ ] Post on social media
- [ ] Update documentation site
- [ ] Notify users

### Monitor

- [ ] Check PyPI download stats
- [ ] Monitor GitHub issues
- [ ] Watch for bug reports
- [ ] Collect user feedback

---

## Quick Reference

```bash
# Complete release workflow
rm -rf dist/
python -m build
twine check dist/*
twine upload --repository testpypi dist/*  # Test first
twine upload dist/*  # Production release
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

---

## See Also

- [Python Packaging Guide](https://packaging.python.org/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [PyPI Help](https://pypi.org/help/)
- [Semantic Versioning](https://semver.org/)
