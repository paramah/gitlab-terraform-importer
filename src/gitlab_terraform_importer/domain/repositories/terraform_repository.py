"""Terraform repository interface (port)."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from ..entities import (
    Group,
    Project,
    TerraformModule,
    TerraformPlan,
    TerraformResource,
    TerraformState,
)


class TerraformRepository(ABC):
    """Abstract repository for Terraform operations."""

    @abstractmethod
    def parse_module(self, module_source: str | Path, subdirectory: Optional[str] = None) -> TerraformModule:
        """Parse a Terraform module from filesystem, HTTP URL, or Git repository.

        Args:
            module_source: Path to module directory, HTTP URL to archive, or Git repository URL
            subdirectory: Optional subdirectory within the module source

        Returns:
            Parsed TerraformModule

        Raises:
            FileNotFoundError: If module not found
            ParseError: If module cannot be parsed
            ValueError: If module source is invalid
            RuntimeError: If download or parsing fails
        """
        pass

    @abstractmethod
    def parse_plan(self, plan_file: Path) -> TerraformPlan:
        """Parse a Terraform plan file.

        Args:
            plan_file: Path to plan JSON file

        Returns:
            Parsed TerraformPlan

        Raises:
            FileNotFoundError: If plan file not found
            ParseError: If plan cannot be parsed
        """
        pass

    @abstractmethod
    def parse_state(self, state_file: Path) -> TerraformState:
        """Parse a Terraform state file.

        Args:
            state_file: Path to state JSON file

        Returns:
            Parsed TerraformState

        Raises:
            FileNotFoundError: If state file not found
            ParseError: If state cannot be parsed
        """
        pass

    @abstractmethod
    def analyze_module_variables(self, module: TerraformModule) -> dict[str, Any]:
        """Analyze variables in a module and extract metadata.

        Args:
            module: Terraform module to analyze

        Returns:
            Dictionary with variable analysis
        """
        pass

    @abstractmethod
    def generate_import_commands(
        self, resources: list[TerraformResource], output_file: Path | None = None
    ) -> list[str]:
        """Generate Terraform import commands for resources.

        Args:
            resources: List of resources to import
            output_file: Optional file to write commands to

        Returns:
            List of import commands
        """
        pass

    @abstractmethod
    def generate_resource_configs(
        self, groups: list[Group], projects: list[Project], output_dir: Path
    ) -> list[Path]:
        """Generate Terraform resource configuration files.

        Args:
            groups: List of groups to generate configs for
            projects: List of projects to generate configs for
            output_dir: Directory to write configs to

        Returns:
            List of generated file paths
        """
        pass

    @abstractmethod
    def map_module_to_gitlab_resources(
        self, group_module: TerraformModule, project_module: TerraformModule, gitlab_data: Group
    ) -> list[TerraformResource]:
        """Map GitLab data to Terraform resources based on module definitions.

        Args:
            group_module: Module defining group resources
            project_module: Module defining project resources
            gitlab_data: GitLab group hierarchy

        Returns:
            List of Terraform resources ready for import
        """
        pass

    @abstractmethod
    def validate_module_compatibility(self, module: TerraformModule, resource_type: str) -> bool:
        """Validate if a module is compatible with a resource type.

        Args:
            module: Terraform module to check
            resource_type: Expected resource type (e.g., 'gitlab_group')

        Returns:
            True if compatible
        """
        pass
