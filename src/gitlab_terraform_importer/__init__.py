"""GitLab Terraform Importer - Clean Architecture Edition.

Import GitLab structure to Terraform configuration with support for
custom modules and advanced analysis.
"""

__version__ = "0.2.0"

# Configuration
# Use cases
from .application.use_cases import (
    AnalyzeTerraformModulesUseCase,
    GenerateTerraformImportsUseCase,
    ImportGitLabStructureUseCase,
)
from .config import GitLabConfig, load_config

# Domain entities
from .domain.entities import (
    Group,
    Project,
    TerraformModule,
    TerraformPlan,
    TerraformResource,
    TerraformState,
    TerraformVariable,
)

# Repository interfaces
from .domain.repositories import (
    GitLabRepository,
    TerraformRepository,
)

# Infrastructure implementations
from .infrastructure.gitlab import GitLabClient
from .infrastructure.terraform import TerraformClient

# CLI
from .interfaces.cli import cli, main

__all__ = [
    # Configuration
    "GitLabConfig",
    "load_config",
    # Entities
    "Group",
    "Project",
    "TerraformResource",
    "TerraformModule",
    "TerraformVariable",
    "TerraformPlan",
    "TerraformState",
    # Repositories
    "GitLabRepository",
    "TerraformRepository",
    # Use cases
    "ImportGitLabStructureUseCase",
    "AnalyzeTerraformModulesUseCase",
    "GenerateTerraformImportsUseCase",
    # Infrastructure
    "GitLabClient",
    "TerraformClient",
    # CLI
    "cli",
    "main",
]
