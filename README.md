# GitLab Terraform Importer - Clean Architecture Edition

[![Tests](https://github.com/paramah/gitlab-terraform-importer/actions/workflows/tests.yml/badge.svg)](https://github.com/paramah/gitlab-terraform-importer/actions/workflows/tests.yml)
[![GitLab CI/CD](https://gitlab.com/paramah/gitlab-terraform-importer/badges/main/pipeline.svg)](https://gitlab.com/paramah/gitlab-terraform-importer/-/pipelines)
[![Coverage](https://gitlab.com/paramah/gitlab-terraform-importer/badges/main/coverage.svg)](https://gitlab.com/paramah/gitlab-terraform-importer/-/pipelines)
[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Advanced tool for importing GitLab group and project structure into Terraform configuration, built with Clean Architecture. Enables custom Terraform module analysis, plan parsing, and automatic import generation.

**[Wersja Polska / Polish Version](README_PL.md)**

## 🎯 Features

- 🏗️ **Clean Architecture** - Layer separation: Domain, Application, Infrastructure, Interface
- 🔄 **GitLab Structure Import** - Recursive import of group and project hierarchies
- 🌐 **Dual API Support** - Utilizes both REST API and GraphQL GitLab SDK
- 📦 **Terraform Module Analysis** - Parse and validate custom modules
- 📋 **Terraform Plan Parser** - Analyze Terraform plans (JSON format)
- 🔍 **Module Variable Analyzer** - Detailed analysis of module variables
- 🚀 **Auto-import Generator** - Automatic generation of `terraform import` scripts
- 📝 **Dual Format Support** - Generate both HCL (.tf) and JSON (.tf.json) Terraform files
- ⚙️ **ENV Configuration** - Full configuration via environment variables
- 🎨 **Rich CLI** - Colorful interface with progress bars and tree view

## 📐 Architecture

The project uses Clean Architecture with clear layer separation:

```
src/gitlab_terraform_importer/
├── domain/                    # Domain layer (entities, interfaces)
│   ├── entities/             # Group, Project, TerraformResource, etc.
│   └── repositories/         # Repository abstractions
├── application/              # Application layer (business logic)
│   └── use_cases/           # Use cases (Import, Analyze, Generate)
├── infrastructure/           # Infrastructure layer (implementations)
│   ├── gitlab/              # GitLab client (REST + GraphQL)
│   └── terraform/           # Terraform parser, analyzer, generator
└── interfaces/              # Interface layer
    └── cli/                # Click-based CLI
```

### Main Components:

#### Domain Layer
- **Entities** (Pydantic BaseModel): `Group`, `Project`, `TerraformResource`, `TerraformModule`, `TerraformPlan`, `TerraformState`
  - Automatic data validation
  - JSON serialization/deserialization
  - Computed fields (@computed_field)
  - Field validators
- **Repository Interfaces**: `GitLabRepository`, `TerraformRepository`

#### Application Layer
- **ImportGitLabStructureUseCase** - Import structure from GitLab
- **AnalyzeTerraformModulesUseCase** - Analyze Terraform modules
- **GenerateTerraformImportsUseCase** - Generate import configuration

#### Infrastructure Layer
- **GitLabClient** - GitLab API implementation (REST + GraphQL)
- **TerraformClient** - Terraform parser, analyzer and generator

## 🚀 Requirements

- Python 3.13+
- GitLab Personal Access Token with `api` permissions
- Terraform 1.0+ (optional, for using generated files)

## 📦 Installation

### Installation with Poetry (recommended)

```bash
# Clone repository
git clone <repository-url>
cd gitlab-terraform-importer

# Install with Poetry
poetry install

# Run CLI (without global installation)
poetry run gitlab-importer --help

# Install dev dependencies
poetry install --with dev
```

### Installation with pip

```bash
# Install in editable mode
pip install -e .

# After installation, available globally
gitlab-importer --help
```

### Building and Distribution

```bash
# Build package
poetry build
# or
task build

# Built files will be in dist/
# - gitlab-terraform-importer-0.2.0.tar.gz
# - gitlab_terraform_importer-0.2.0-py3-none-any.whl

# Install from wheel
pip install dist/gitlab_terraform_importer-0.2.0-py3-none-any.whl

# Publish to PyPI (for maintainers)
poetry publish
# or
task publish
```

### Taskfile - Task Runner (YAML)

The project uses [Task](https://taskfile.dev/) - a modern task runner in YAML.

#### Installing Task

```bash
# macOS
brew install go-task/tap/go-task

# Linux (snap)
snap install task --classic

# Windows (scoop)
scoop install task

# Or download binary:
# https://github.com/go-task/task/releases
```

#### Available Tasks

```bash
task                # List all tasks
task --list         # Detailed list with descriptions

# Development
task install        # Install with Poetry
task install-dev    # Install with dev dependencies
task dev-setup      # Complete dev environment setup

# CLI
task run            # Run CLI (--help)
task validate       # Validate configuration
task inspect        # Inspect GitLab
task inspect-json   # Inspect GitLab (JSON)
task import         # Import structure
task import-dry     # Import (dry run)

# Quality
task test           # Run tests
task test-cov       # Tests with coverage
task lint           # Linting (ruff)
task lint-fix       # Fix lint errors
task format         # Formatting (black)
task format-check   # Check formatting
task type-check     # Type checking (mypy)
task check          # All checks (lint+format+types+test)
task pre-commit     # Pre-commit checks

# Build & Deploy
task build          # Build package
task clean          # Remove build files
task publish        # Publish to PyPI
task publish-test   # Publish to TestPyPI

# Utils
task show-deps      # Show dependency tree
task update         # Update dependencies
task shell          # Poetry shell
```

#### Usage Examples

```bash
# Project setup
task dev-setup

# Development workflow
task run
task validate
task inspect

# Before commit
task pre-commit

# Build
task build
```

#### Examples with Arguments

```bash
# Analyze modules
task analyze -- ./modules/group ./modules/project

# Import with modules
task import-modules -- ./modules/group ./modules/project --output-dir ./tf
```

### Available CLI Commands

After installation, two aliases are available:
- `gitlab-importer` - main command (recommended)
- `gitlab-tf-import` - legacy alias (backward compatibility)

```bash
# Method 1: With Poetry (development - recommended)
poetry run gitlab-importer --help

# Method 2: dev-cli.sh script (without installation)
./dev-cli.sh --help
./dev-cli.sh validate-config

# Method 3: After global installation
gitlab-importer --help

# Legacy alias
gitlab-tf-import --help
```

### Dependencies

- `python-gitlab` - GitLab REST API
- `gql` - GitLab GraphQL API
- `python-hcl2` - Terraform file parsing (.tf)
- `python-terraform` - Terraform interaction
- `pydantic` & `pydantic-settings` - Configuration and validation
- `click` - CLI framework
- `rich` - Colorful output

## ⚙️ Configuration

### 1. Create `.env` file

```bash
cp .env.example .env
```

### 2. Fill in environment variables

```bash
# Required
GITLAB_URL=https://gitlab.com
GITLAB_TOKEN=your-personal-access-token

# Required (one of the following)
GITLAB_ROOT_GROUP_ID=12345
# OR
GITLAB_ROOT_GROUP_PATH=my-organization

# Optional
GITLAB_OUTPUT_DIR=./terraform
GITLAB_INCLUDE_ARCHIVED=false
GITLAB_MAX_DEPTH=5
GITLAB_TIMEOUT=60
GITLAB_VERIFY_SSL=true

# Terraform/OpenTofu Configuration
GITLAB_TERRAFORM_BINARY=terraform  # or 'tofu' for OpenTofu
GITLAB_OUTPUT_FORMAT=hcl           # or 'json' for .tf.json files
```

## 📖 Usage

### Quick Start

#### Method 1: With Taskfile (recommended)

```bash
# 1. Install Task (if you don't have it)
# macOS: brew install go-task/tap/go-task
# Linux: snap install task --classic

# 2. Setup dev environment
task dev-setup

# 3. Configure .env
cp .env.example .env
# Edit .env and add GITLAB_TOKEN and GITLAB_ROOT_GROUP_PATH

# 4. Check help
task run

# 5. Validate configuration
task validate

# 6. Review structure
task inspect

# 7. Generate Terraform
task import
```

#### Method 2: Directly with Poetry

```bash
# 1. Install with Poetry
poetry install

# 2. Configure .env
cp .env.example .env
# Edit .env and add GITLAB_TOKEN and GITLAB_ROOT_GROUP_PATH

# 3. Check help
poetry run gitlab-importer --help

# 4. Validate configuration
poetry run gitlab-importer validate-config

# 5. Review structure
poetry run gitlab-importer inspect

# 6. Generate Terraform
poetry run gitlab-importer import-structure
```

### Command List

```bash
gitlab-importer --help                    # Main help menu
gitlab-importer validate-config           # Validate .env
gitlab-importer inspect                   # Preview GitLab structure
gitlab-importer import-structure          # Import and generate Terraform
gitlab-importer analyze-modules           # Analyze Terraform modules
gitlab-importer import-with-modules       # Import with custom modules
```

### Configuration Validation

```bash
gitlab-importer validate-config
```

### GitLab Structure Inspection

```bash
# Tree view (with rich formatting)
gitlab-importer inspect

# JSON format
gitlab-importer inspect --format json
```

### Import and Generate Terraform (basic)

```bash
# Basic import
gitlab-importer import-structure

# With custom directory
gitlab-importer import-structure --output-dir ./my-terraform

# Dry run
gitlab-importer import-structure --dry-run

# Verbose mode
gitlab-importer -v import-structure
```

### Output Format Configuration

The tool supports generating Terraform files in two formats:

**HCL Format (.tf files)** - Default format:
```bash
# Set in .env
GITLAB_OUTPUT_FORMAT=hcl

# Generates: provider.tf, groups.tf, projects.tf
gitlab-importer import-structure
```

**JSON Format (.tf.json files)** - Alternative format:
```bash
# Set in .env
GITLAB_OUTPUT_FORMAT=json

# Generates: provider.tf.json, groups.tf.json, projects.tf.json
gitlab-importer import-structure
```

Both formats are fully compatible with Terraform and OpenTofu. The JSON format can be useful for:
- Programmatic generation and manipulation
- Integration with other tools that produce JSON
- Easier parsing and validation in automated pipelines
- Situations where HCL syntax might be problematic

### Terraform Module Analysis

New functionality! Analyze custom Terraform modules:

```bash
gitlab-importer analyze-modules \
  ./modules/gitlab-group \
  ./modules/gitlab-project
```

Output:
```
Module Analysis:

Group Module:
  Name:              gitlab-group
  Path:              ./modules/gitlab-group
  Variables:         8
  Required:          3
  Resources:         1
  Compatible:        ✓

Project Module:
  Name:              gitlab-project
  Path:              ./modules/gitlab-project
  Variables:         15
  Required:          5
  Resources:         1
  Compatible:        ✓
```

### Import with Custom Modules

Most important functionality! Import GitLab using your modules:

```bash
gitlab-importer import-with-modules \
  ./modules/gitlab-group \
  ./modules/gitlab-project \
  --output-dir ./terraform
```

This command:
1. Analyzes Terraform modules (variables, outputs, resources)
2. Imports GitLab structure
3. Maps GitLab data to module definitions
4. Generates `.tf` files compatible with modules
5. Creates import script `import.sh`

## 🔧 Advanced Usage

### Parsing Terraform Plan

```python
from gitlab_terraform_importer import TerraformClient
from pathlib import Path

client = TerraformClient()

# Parse plan
plan = client.parse_plan(Path("terraform-plan.json"))

# Analyze changes
resources_to_create = plan.get_resources_to_create()
resources_to_import = plan.get_resources_to_import()

print(f"Resources to create: {len(resources_to_create)}")
print(f"Resources to import: {len(resources_to_import)}")
```

### Working with Pydantic Models

All domain entities use Pydantic BaseModel, which provides:

```python
from gitlab_terraform_importer import Group, Project, TerraformModule

# Create with validation
group = Group(
    id=123,
    name="My Group",
    path="my-group",
    full_path="org/my-group",
    visibility="private"
)

# Automatic validation
# group = Group(id="invalid")  # Error: id must be int

# JSON serialization
group_json = group.model_dump_json()
group_dict = group.model_dump()

# Deserialization
group_from_dict = Group.model_validate(group_dict)

# Computed fields
print(group.terraform_resource_name)  # "org_my_group"

# Summary without nested objects
summary = group.model_dump_summary()
```

### Programmatic Usage

```python
from gitlab_terraform_importer import (
    load_config,
    GitLabClient,
    TerraformClient,
    ImportGitLabStructureUseCase,
    GenerateTerraformImportsUseCase,
)
from pathlib import Path

# Configuration
config = load_config()

# Clients
gitlab_client = GitLabClient(config)
terraform_client = TerraformClient()

# Use cases
import_uc = ImportGitLabStructureUseCase(gitlab_client)
generate_uc = GenerateTerraformImportsUseCase(terraform_client)

# Import
root_group = import_uc.execute(
    root_group_path="my-organization",
    max_depth=3
)

# Parse modules
group_module = terraform_client.parse_module(Path("./modules/gitlab-group"))
project_module = terraform_client.parse_module(Path("./modules/gitlab-project"))

# Generate
result = generate_uc.execute(
    gitlab_structure=root_group,
    group_module=group_module,
    project_module=project_module,
    output_dir=Path("./terraform")
)

print(f"Generated {result['resources_count']} resources")
```

## 📁 Generated File Structure

```
terraform/
├── provider.tf          # GitLab provider configuration
├── groups.tf           # All group definitions
├── projects.tf         # All project definitions
└── import.sh           # Import script (executable)
```

## 🎨 Sample CLI Output

```
✓ Configuration is valid!

Settings:
  GitLab URL:        https://gitlab.com
  Token:             ******** (set)
  Root Group Path:   my-organization
  Output Dir:        ./terraform

⠹ Importing GitLab structure...

Discovered:
  Groups:   15
  Projects: 47

⠹ Generating Terraform files...

✓ Success! Terraform files generated.

Generated:
  Resources:     62
  Files:         3
  Import Script: ./terraform/import.sh

Next steps:
  1. cd ./terraform
  2. terraform init
  3. Review generated files
  4. Run ./import.sh to import resources
  5. terraform plan
```

## 🧪 Use Cases

### Use Case 1: Migrating Existing Infrastructure

```bash
# 1. Check configuration
gitlab-importer validate-config

# 2. Review structure
gitlab-importer inspect

# 3. Generate Terraform
gitlab-importer import-structure

# 4. Import to state
cd terraform
terraform init
./import.sh

# 5. Verify
terraform plan  # Should show "no changes"
```

### Use Case 2: Working with Custom Modules

```bash
# 1. Analyze modules
gitlab-importer analyze-modules ./modules/group ./modules/project

# 2. Import with modules
gitlab-importer import-with-modules \
  ./modules/group \
  ./modules/project

# 3. Adjust generated files to modules
# 4. terraform import
```

### Use Case 3: GitLab Structure Audit

```bash
# Export to JSON for further analysis
gitlab-importer inspect --format json > gitlab-structure.json

# Analyze with jq
cat gitlab-structure.json | jq '.subgroups | length'
cat gitlab-structure.json | jq '.. | .projects? | select(. != null) | length'
```

## 🔍 Terraform Module Requirements

For modules to be compatible, they should:

1. Contain resource of type `gitlab_group` or `gitlab_project`
2. Define variables for basic attributes (name, path, visibility, etc.)
3. (Optional) Export outputs (id, full_path)

Example module:

```hcl
# modules/gitlab-group/main.tf
variable "name" {
  type        = string
  description = "Group name"
}

variable "path" {
  type = string
}

variable "visibility" {
  type    = string
  default = "private"
}

resource "gitlab_group" "this" {
  name             = var.name
  path             = var.path
  visibility_level = var.visibility
}

output "id" {
  value = gitlab_group.this.id
}
```

## 📊 Environment Variables

| Variable | Description | Required | Default |
|---------|------|----------|----------|
| `GITLAB_URL` | GitLab instance URL | No | `https://gitlab.com` |
| `GITLAB_TOKEN` | Personal Access Token | **Yes** | - |
| `GITLAB_ROOT_GROUP_ID` | Root group ID | Yes* | - |
| `GITLAB_ROOT_GROUP_PATH` | Root group path | Yes* | - |
| `GITLAB_OUTPUT_DIR` | Output directory | No | `./terraform` |
| `GITLAB_TIMEOUT` | API timeout (s) | No | `60` |
| `GITLAB_VERIFY_SSL` | SSL verification | No | `true` |
| `GITLAB_INCLUDE_ARCHIVED` | Include archived | No | `false` |
| `GITLAB_MAX_DEPTH` | Max depth | No | `None` |
| `GITLAB_TERRAFORM_BINARY` | Terraform binary (terraform/tofu) | No | `terraform` |
| `GITLAB_OUTPUT_FORMAT` | Output format (hcl/json) | No | `hcl` |

\* Either `GITLAB_ROOT_GROUP_ID` **or** `GITLAB_ROOT_GROUP_PATH` is required

## 🧪 Testing

The project includes comprehensive test suite with 120+ tests:

```bash
# Run all tests
poetry run pytest tests/ -v

# Run with coverage
poetry run pytest tests/ --cov=src/gitlab_terraform_importer --cov-report=html

# Run specific test file
poetry run pytest tests/domain/entities/test_group.py -v

# With Taskfile
task test
task test-cov
```

### Test Coverage:

- **Domain Layer**: 45+ tests (entities, validation, serialization)
- **Application Layer**: 20+ tests (use cases, business logic)
- **Infrastructure Layer**: 26+ tests (GitLab/Terraform clients)
- **Interface Layer**: 12+ tests (CLI commands)

## 🔄 CI/CD

The project includes automated CI/CD pipelines for both **GitHub Actions** and **GitLab CI/CD**.

### GitHub Actions

Workflow file: `.github/workflows/tests.yml`

**Pipeline stages:**
1. **Lint** - Code quality checks (Black, Ruff)
2. **Test** - Run tests on Python 3.13 and 3.14
3. **Type Check** - Static type checking with MyPy
4. **Security** - Dependency security scan with Safety
5. **Build** - Build Python package
6. **Test Summary** - Aggregate test results

**Features:**
- ✅ Multi-version Python testing (3.13, 3.14)
- ✅ Coverage reports uploaded to Codecov
- ✅ HTML coverage reports as artifacts
- ✅ Poetry dependency caching
- ✅ Automatic on push to main/develop and PRs

### GitLab CI/CD

Configuration file: `.gitlab-ci.yml`

**Pipeline stages:**
1. **lint** - Code formatting (Black, Ruff) and type checking (MyPy)
2. **test** - Run tests on multiple Python versions
3. **security** - Security scanning (Safety, Bandit)
4. **build** - Build package for distribution
5. **report** - Generate and publish coverage reports
6. **pages** - Publish coverage to GitLab Pages

**Features:**
- ✅ Multi-version Python testing (3.13, 3.14)
- ✅ Coverage visualization in merge requests
- ✅ GitLab Pages for coverage reports
- ✅ Poetry dependency caching
- ✅ Security scanning with Bandit
- ✅ Artifact retention (30 days)
- ✅ Manual PyPI release job for tags

**View CI/CD Results:**
- GitHub: Check the "Actions" tab
- GitLab: Check "CI/CD > Pipelines" and "CI/CD > Jobs"
- Coverage: Available in GitLab Pages (main branch only)

### Running Linters Locally

```bash
# Format code with Black
poetry run black src/ tests/

# Check formatting
poetry run black --check src/ tests/

# Lint with Ruff
poetry run ruff check src/ tests/

# Auto-fix Ruff issues
poetry run ruff check --fix src/ tests/

# Type check with MyPy
poetry run mypy src/gitlab_terraform_importer --ignore-missing-imports

# With Taskfile
task lint
task format
```

## 🏗️ Development

### Project Structure

```
src/gitlab_terraform_importer/
├── domain/
│   ├── entities/
│   │   ├── group.py
│   │   ├── project.py
│   │   └── terraform_resource.py
│   └── repositories/
│       ├── gitlab_repository.py
│       └── terraform_repository.py
├── application/
│   └── use_cases/
│       ├── import_gitlab_structure.py
│       ├── analyze_terraform_modules.py
│       └── generate_terraform_imports.py
├── infrastructure/
│   ├── gitlab/
│   │   └── gitlab_client.py
│   └── terraform/
│       ├── terraform_parser.py
│       ├── module_analyzer.py
│       ├── import_generator.py
│       └── terraform_client.py
└── interfaces/
    └── cli/
        └── commands.py
```

### Adding New Features

1. **New entity**: `domain/entities/`
2. **New use case**: `application/use_cases/`
3. **New implementation**: `infrastructure/`
4. **New CLI command**: `interfaces/cli/commands.py`

## 🐛 Troubleshooting

### Import Timeout

```bash
GITLAB_TIMEOUT=120 gitlab-importer import-structure
```

### SSL Certificate Errors

```bash
GITLAB_VERIFY_SSL=false gitlab-importer import-structure
```

### Module Parsing Errors

Ensure modules use HCL2 syntax and are properly formatted:

```bash
terraform fmt -recursive ./modules
```

## 📝 TODO / Roadmap

- [ ] Terraform State support for comparisons
- [ ] Import group members and permissions
- [ ] Support for CI/CD variables
- [ ] Export to other formats (Pulumi, CDK)
- [ ] Web UI for visualization
- [ ] Diff between GitLab and Terraform state

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

[Specify license]

## 👤 Author

Aleksander Cynarski <aleksander@cynarski.pl>

## 🙏 Acknowledgments

- GitLab SDK Team
- Terraform Provider GitLab Team
- Clean Architecture by Robert C. Martin
