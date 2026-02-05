# GitHub Actions Workflows Documentation

## Overview

This project uses GitHub Actions for continuous integration and delivery. All workflows are configured to run automatically on every commit to ensure code quality and reliability.

## Workflows

### 1. Tests (`test.yml`)

**Triggers:**
- Every push to any branch
- All pull requests
- Manual dispatch from GitHub UI

**Jobs:**
- Runs tests on Python 3.11, 3.12, and 3.13
- Installs dependencies from `requirements.txt`
- Executes pytest with coverage reporting
- Uploads coverage to Codecov (optional)
- Enforces minimum 85% code coverage

**Duration:** ~2-3 minutes

**Status:** Required for merge

### 2. Code Quality (`quality.yml`)

**Triggers:**
- Every push to any branch
- All pull requests

**Jobs:**
- Linting with `ruff`
- Format checking with `ruff format`
- Type checking with `mypy`

**Duration:** ~1 minute

**Status:** Advisory (continues on error)

### 3. Docker Build (`docker.yml`)

**Triggers:**
- Pushes to `main` or `master` branches
- Version tags (v*)
- Pull requests to `main` or `master`
- Manual dispatch

**Jobs:**
- Builds Docker image
- Tests Docker image (PR only)
- Pushes to GitHub Container Registry (main/tags only)
- Automatically tags with:
  - Branch name
  - Semantic version (from git tags)
  - Commit SHA

**Duration:** ~3-5 minutes

**Status:** Required for releases

## Local Testing

Before pushing, you can run the same checks locally:

```bash
# Run tests
make test
# or
pytest tests/ -v --cov=app

# Run linting
make lint
# or
ruff check app/ tests/

# Format code
make format
# or
ruff format app/ tests/

# Build Docker image
make docker-build
# or
docker build -t fx-service .
```

## Coverage Requirements

- Minimum code coverage: **85%**
- Current coverage: **92%**
- Coverage reports are generated in:
  - Terminal output
  - `htmlcov/` directory (HTML report)
  - `coverage.xml` (XML report for CI)

## Adding Secrets

To enable Codecov integration:

1. Go to repository Settings → Secrets and variables → Actions
2. Add `CODECOV_TOKEN` secret with your Codecov token

## Workflow Status Badges

The README includes status badges for workflows:

```markdown
![Tests](https://github.com/username/repo/actions/workflows/test.yml/badge.svg)
![Code Quality](https://github.com/username/repo/actions/workflows/quality.yml/badge.svg)
```

Replace `username/repo` with your actual GitHub repository path.

## Troubleshooting

### Tests failing in CI but passing locally

- Ensure you're using the same Python version
- Check for environment-specific dependencies
- Verify all test data files are committed

### Docker build failing

- Ensure all required files are not in `.dockerignore`
- Check that `data/sample_fx.json` exists
- Verify Dockerfile COPY commands

### Coverage threshold not met

- Run `pytest --cov=app --cov-report=html` locally
- Open `htmlcov/index.html` to see uncovered lines
- Add tests for missing coverage

## Best Practices

1. **Always run tests locally** before pushing
2. **Use `make test`** for consistency with CI
3. **Check coverage** after adding new code
4. **Fix linting issues** before committing
5. **Tag releases** properly (v1.0.0, v1.1.0, etc.)

## CI/CD Pipeline Flow

```
┌─────────────────┐
│   Git Push      │
└────────┬────────┘
         │
         ├──────────────────┬──────────────────┬──────────────────┐
         │                  │                  │                  │
         ▼                  ▼                  ▼                  ▼
   ┌──────────┐       ┌──────────┐      ┌──────────┐      ┌──────────┐
   │  Tests   │       │  Quality │      │  Docker  │      │  Deploy  │
   │  Python  │       │  Checks  │      │  Build   │      │ (future) │
   │ 3.11-13  │       │   Ruff   │      │   Test   │      │          │
   │          │       │   Mypy   │      │   Push   │      │          │
   └────┬─────┘       └────┬─────┘      └────┬─────┘      └────┬─────┘
        │                  │                  │                  │
        └──────────────────┴──────────────────┴──────────────────┘
                               │
                               ▼
                         ┌──────────┐
                         │  Merge   │
                         │ or Deploy│
                         └──────────┘
```

## Future Enhancements

- [ ] Add automatic deployment to cloud platforms
- [ ] Integrate with security scanning tools
- [ ] Add performance benchmarking
- [ ] Implement automated changelog generation
- [ ] Add container vulnerability scanning
