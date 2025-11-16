# CI/CD Documentation

This document describes the continuous integration and deployment pipelines for the GitLab Terraform Importer project.

## Overview

The project uses two parallel CI/CD systems:
- **GitHub Actions** - For repositories hosted on GitHub
- **GitLab CI/CD** - For repositories hosted on GitLab

Both pipelines run the same set of checks and tests to ensure code quality and correctness.

## GitHub Actions

### Configuration

File: `.github/workflows/tests.yml`

### Triggers

The workflow is triggered on:
- Push to `main`, `develop`, or `claude/**` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

### Jobs

#### 1. Lint Job (`lint`)

**Purpose**: Ensure code follows style guidelines

**Steps**:
- Check out code
- Set up Python 3.13
- Install Poetry
- Cache virtual environment
- Install dependencies
- Run Black formatter check
- Run Ruff linter

**Required**: Yes (pipeline fails if this job fails)

#### 2. Test Job (`test`)

**Purpose**: Run test suite on multiple Python versions

**Matrix**:
- Python 3.13 (required)
- Python 3.14 (pre-release, optional)

**Steps**:
- Check out code
- Set up Python (matrix version)
- Install Poetry
- Cache virtual environment
- Install dependencies
- Run pytest with coverage
- Upload coverage to Codecov (Python 3.13 only)
- Archive HTML coverage report
- Upload test results as artifacts

**Artifacts**:
- `coverage-report-html/` - HTML coverage report (30 days)
- `test-results-{version}/` - Coverage XML and .coverage files (30 days)

**Required**: Yes

#### 3. Type Check Job (`type-check`)

**Purpose**: Static type checking with MyPy

**Steps**:
- Check out code
- Set up Python 3.13
- Install Poetry
- Cache virtual environment
- Install dependencies
- Run MyPy type checker

**Required**: No (continues on error)

#### 4. Security Job (`security`)

**Purpose**: Scan dependencies for known vulnerabilities

**Steps**:
- Check out code
- Set up Python 3.13
- Install Poetry
- Export dependencies to requirements.txt
- Run Safety security scanner

**Required**: No (continues on error)

#### 5. Build Job (`build`)

**Purpose**: Build Python package

**Dependencies**: `lint` and `test` jobs must pass

**Steps**:
- Check out code
- Set up Python 3.13
- Install Poetry
- Build package (wheel and sdist)
- Upload build artifacts

**Artifacts**:
- `dist-packages/` - Built packages (30 days)

**Required**: Yes (but only after lint and test pass)

#### 6. Test Summary Job (`test-summary`)

**Purpose**: Aggregate and report test results

**Dependencies**: All test jobs

**Steps**:
- Check results of lint, test, and type-check jobs
- Fail if lint or test jobs failed
- Report summary

**Required**: Yes

### Caching

The workflow caches Poetry virtual environments using the following cache key:
```
venv-${{ runner.os }}-${{ matrix.python-version }}-${{ hashFiles('**/poetry.lock') }}
```

This significantly speeds up subsequent runs.

---

## GitLab CI/CD

### Configuration

File: `.gitlab-ci.yml`

### Stages

1. `lint` - Code quality checks
2. `test` - Run test suite
3. `security` - Security scanning
4. `build` - Build package
5. `report` - Generate reports

### Global Variables

```yaml
PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"
POETRY_VERSION: "1.8.0"
POETRY_HOME: "$CI_PROJECT_DIR/.poetry"
POETRY_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pypoetry"
POETRY_VIRTUALENVS_IN_PROJECT: "true"
```

### Cache Configuration

```yaml
cache:
  key: "${CI_COMMIT_REF_SLUG}-${CI_JOB_NAME}"
  paths:
    - .cache/pip
    - .cache/pypoetry
    - .venv
```

### Jobs

#### Stage: Lint

##### `lint:black`
- **Purpose**: Check code formatting with Black
- **Failure**: Pipeline fails if this job fails
- **Command**: `poetry run black --check src/ tests/`

##### `lint:ruff`
- **Purpose**: Lint code with Ruff
- **Failure**: Pipeline fails if this job fails
- **Command**: `poetry run ruff check src/ tests/`

##### `type-check:mypy`
- **Purpose**: Type checking with MyPy
- **Failure**: Continues on error
- **Command**: `poetry run mypy src/gitlab_terraform_importer --ignore-missing-imports`

#### Stage: Test

##### `test:python3.13`
- **Image**: `python:3.13`
- **Purpose**: Run full test suite with coverage
- **Coverage**: Reports coverage percentage
- **Artifacts**:
  - `htmlcov/` - HTML coverage report
  - `coverage.xml` - Cobertura XML for GitLab
  - `.coverage` - Raw coverage data
- **Reports**: Coverage report for GitLab UI
- **Retention**: 30 days

##### `test:python3.14`
- **Image**: `python:3.14-rc`
- **Purpose**: Test on pre-release Python
- **Trigger**: Manual
- **Failure**: Allowed to fail

#### Stage: Security

##### `security:safety`
- **Purpose**: Check dependencies for vulnerabilities
- **Tools**: Safety
- **Failure**: Allowed to fail
- **Artifacts**: `requirements.txt` (7 days)

##### `security:bandit`
- **Purpose**: Static security analysis of Python code
- **Tools**: Bandit
- **Output**: JSON and text reports
- **Failure**: Allowed to fail
- **Artifacts**: `bandit-report.json` (7 days)

#### Stage: Build

##### `build:package`
- **Purpose**: Build Python package
- **Trigger**: Only on `main`, `develop`, `tags`, and merge requests
- **Artifacts**: `dist/` (30 days)

#### Stage: Report

##### `report:coverage`
- **Purpose**: Generate final coverage report
- **Dependencies**: `test:python3.13`
- **Trigger**: Only on `main`, `develop`, and merge requests
- **Artifacts**: `htmlcov/` (30 days)

##### `pages`
- **Purpose**: Publish coverage to GitLab Pages
- **Dependencies**: `test:python3.13`
- **Trigger**: Only on `main` branch
- **URL**: `https://<username>.gitlab.io/<project>`
- **Artifacts**: `public/` (30 days)

#### Special Jobs

##### `integration:test`
- **Purpose**: Run integration tests
- **Trigger**: Manual
- **Failure**: Allowed to fail

##### `release:pypi`
- **Purpose**: Publish package to PyPI
- **Trigger**: Manual on tags only
- **Requirements**: `PYPI_TOKEN` secret variable
- **Failure**: Allowed to fail

---

## Local CI Simulation

You can run the same checks locally using Taskfile:

### Run All CI Checks

```bash
task ci
```

This will run:
1. Format check (Black)
2. Lint (Ruff)
3. Type check (MyPy)
4. Tests with coverage

### Fix Code and Run CI

```bash
task ci-fix
```

This will:
1. Format code (Black)
2. Auto-fix lint issues (Ruff)
3. Run tests with coverage

### Individual Checks

```bash
# Format checking
task format-check

# Auto-format code
task format

# Lint checking
task lint

# Auto-fix lint issues
task lint-fix

# Type checking
task type-check

# Run tests
task test

# Run tests with coverage
task test-cov
```

---

## Coverage Reports

### GitHub Actions

Coverage reports are:
1. Uploaded to Codecov (if `CODECOV_TOKEN` is configured)
2. Stored as workflow artifacts (HTML format)
3. Available for download from Actions tab

### GitLab CI/CD

Coverage reports are:
1. Displayed in merge request UI
2. Published to GitLab Pages (main branch only)
3. Stored as job artifacts (30 days)

**Access GitLab Pages Coverage**:
```
https://<username>.gitlab.io/<project>/
```

---

## Secrets and Variables

### GitHub Actions

Required secrets (optional):
- `CODECOV_TOKEN` - For uploading coverage to Codecov

### GitLab CI/CD

Required variables (for release):
- `PYPI_TOKEN` - PyPI authentication token (for manual release job)

---

## Troubleshooting

### GitHub Actions

**Problem**: Workflow not running
- Check if workflow file is in `.github/workflows/`
- Verify branch name matches trigger conditions
- Check repository Actions permissions

**Problem**: Cache not working
- Clear cache from Actions > Caches
- Verify `poetry.lock` file is committed

### GitLab CI/CD

**Problem**: Pipeline not starting
- Check if `.gitlab-ci.yml` is in repository root
- Verify CI/CD is enabled in project settings
- Check runner availability

**Problem**: Job fails with "cache not found"
- Clear runner cache
- Verify cache paths in configuration

**Problem**: Coverage not showing in MR
- Check if `coverage.xml` artifact exists
- Verify coverage report format is Cobertura
- Check pipeline passed on the branch

---

## Best Practices

1. **Always run local checks before pushing**:
   ```bash
   task ci
   ```

2. **Keep poetry.lock up to date**:
   ```bash
   task lock
   ```

3. **Review coverage reports regularly**
   - Aim for >80% coverage
   - Focus on critical business logic

4. **Fix linting issues immediately**
   ```bash
   task ci-fix
   ```

5. **Don't skip failing checks**
   - All required jobs must pass
   - Investigate and fix failures

6. **Update dependencies regularly**
   ```bash
   task update
   ```

7. **Monitor security alerts**
   - Review Safety and Bandit reports
   - Update vulnerable dependencies promptly

---

## Continuous Improvement

The CI/CD pipeline should be continuously improved:

- Add new tests as features are added
- Update Python versions as new releases come out
- Add new security scanning tools
- Optimize cache strategies
- Monitor pipeline execution time

---

## Questions?

For questions or issues with CI/CD:
1. Check this documentation
2. Review job logs in GitHub Actions / GitLab CI/CD
3. Check `.github/workflows/tests.yml` or `.gitlab-ci.yml`
4. Open an issue in the project repository
