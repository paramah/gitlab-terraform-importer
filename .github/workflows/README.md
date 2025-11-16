# GitHub Actions Workflows

This directory contains GitHub Actions workflow configurations for automated CI/CD.

## Available Workflows

### `tests.yml` - Main Test Pipeline

**Triggers:**
- Push to `main`, `develop`, or `claude/**` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

**Jobs:**

1. **lint** - Code quality checks
   - Black formatting check
   - Ruff linting

2. **test** - Run test suite
   - Python 3.13 (required)
   - Python 3.14 (pre-release, optional)
   - Coverage reporting
   - Codecov upload

3. **type-check** - Static type analysis
   - MyPy type checking
   - Continues on error

4. **security** - Security scanning
   - Safety dependency check
   - Continues on error

5. **build** - Package building
   - Build wheel and sdist
   - Upload artifacts

6. **test-summary** - Results aggregation
   - Checks all jobs passed
   - Fails pipeline if lint or test failed

**View Results:**
- Go to repository → Actions tab
- Select workflow run
- View job logs and artifacts

**Artifacts:**
- Coverage HTML reports (30 days)
- Test results XML (30 days)
- Built packages (30 days)

## Local Testing

Run the same checks locally:

```bash
# All CI checks
task ci

# Auto-fix issues
task ci-fix

# Individual checks
task format-check
task lint
task type-check
task test-cov
```

## Troubleshooting

**Workflow not running:**
- Check Actions are enabled in repository settings
- Verify branch name matches trigger pattern
- Check workflow syntax with `yamllint`

**Tests failing:**
- Review job logs in Actions tab
- Run tests locally: `task test`
- Check for environment-specific issues

**Cache issues:**
- Clear cache: Actions → Caches → Delete
- Verify `poetry.lock` is committed
- Check cache key configuration

## Adding New Workflows

1. Create new `.yml` file in this directory
2. Follow GitHub Actions syntax
3. Test locally with [act](https://github.com/nektos/act)
4. Document in this README

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Project CI/CD Docs](../../docs/CI_CD.md)
