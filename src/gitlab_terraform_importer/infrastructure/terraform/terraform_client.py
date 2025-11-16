"""Terraform client implementation (adapter)."""

from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from ...domain.entities import (
    TerraformModule,
    TerraformResource,
    TerraformPlan,
    TerraformState,
    Group,
    Project,
)
from ...domain.repositories import TerraformRepository
from .terraform_parser import TerraformParser
from .module_analyzer import ModuleAnalyzer
from .import_generator import ImportGenerator

logger = logging.getLogger(__name__)


class TerraformClient(TerraformRepository):
    """Terraform repository implementation."""

    def __init__(self, terraform_binary: str = "terraform"):
        """Initialize Terraform client.

        Args:
            terraform_binary: Terraform binary to use (terraform or tofu)
        """
        self.terraform_binary = terraform_binary
        self.parser = TerraformParser()
        self.analyzer = ModuleAnalyzer()
        self.generator = ImportGenerator(terraform_binary=terraform_binary)

    def parse_module(self, module_path: Path) -> TerraformModule:
        """Parse a Terraform module from filesystem.

        Args:
            module_path: Path to the module directory

        Returns:
            Parsed TerraformModule
        """
        return self.parser.parse_module_directory(module_path)

    def parse_plan(self, plan_file: Path) -> TerraformPlan:
        """Parse a Terraform plan file.

        Args:
            plan_file: Path to plan JSON file

        Returns:
            Parsed TerraformPlan
        """
        plan_data = self.parser.parse_json_plan(plan_file)

        return TerraformPlan(
            format_version=plan_data.get('format_version', ''),
            terraform_version=plan_data.get('terraform_version', ''),
            planned_values=plan_data.get('planned_values', {}),
            resource_changes=plan_data.get('resource_changes', []),
            configuration=plan_data.get('configuration', {}),
        )

    def parse_state(self, state_file: Path) -> TerraformState:
        """Parse a Terraform state file.

        Args:
            state_file: Path to state JSON file

        Returns:
            Parsed TerraformState
        """
        state_data = self.parser.parse_json_state(state_file)

        return TerraformState(
            version=state_data.get('version', 0),
            terraform_version=state_data.get('terraform_version', ''),
            resources=state_data.get('resources', []),
        )

    def analyze_module_variables(self, module: TerraformModule) -> Dict[str, Any]:
        """Analyze variables in a module and extract metadata.

        Args:
            module: Terraform module to analyze

        Returns:
            Dictionary with variable analysis
        """
        return self.analyzer.analyze_variables(module)

    def generate_import_commands(
        self,
        resources: List[TerraformResource],
        output_file: Optional[Path] = None
    ) -> List[str]:
        """Generate Terraform import commands for resources.

        Args:
            resources: List of resources to import
            output_file: Optional file to write commands to

        Returns:
            List of import commands
        """
        return self.generator.generate_import_commands(resources, output_file)

    def generate_resource_configs(
        self,
        groups: List[Group],
        projects: List[Project],
        output_dir: Path
    ) -> List[Path]:
        """Generate Terraform resource configuration files.

        Args:
            groups: List of groups to generate configs for
            projects: List of projects to generate configs for
            output_dir: Directory to write configs to

        Returns:
            List of generated file paths
        """
        return self.generator.generate_resource_files(groups, projects, output_dir)

    def map_module_to_gitlab_resources(
        self,
        group_module: TerraformModule,
        project_module: TerraformModule,
        gitlab_data: Group
    ) -> List[TerraformResource]:
        """Map GitLab data to Terraform resources based on module definitions.

        Args:
            group_module: Module defining group resources
            project_module: Module defining project resources
            gitlab_data: GitLab group hierarchy

        Returns:
            List of Terraform resources ready for import
        """
        # Collect all groups and projects from the hierarchy
        groups = self._collect_all_groups(gitlab_data)
        projects = self._collect_all_projects(gitlab_data)

        # Map to Terraform resources
        resources = self.generator.map_gitlab_to_terraform_resources(groups, projects)

        logger.info(
            f"Mapped {len(groups)} groups and {len(projects)} projects "
            f"to {len(resources)} Terraform resources"
        )

        return resources

    def validate_module_compatibility(
        self,
        module: TerraformModule,
        resource_type: str
    ) -> bool:
        """Validate if a module is compatible with a resource type.

        Args:
            module: Terraform module to check
            resource_type: Expected resource type (e.g., 'gitlab_group')

        Returns:
            True if compatible
        """
        return self.analyzer.validate_module_for_resource_type(module, resource_type)

    def _collect_all_groups(self, root_group: Group) -> List[Group]:
        """Recursively collect all groups.

        Args:
            root_group: Root group to start from

        Returns:
            List of all groups
        """
        groups = [root_group]
        for subgroup in root_group.subgroups:
            groups.extend(self._collect_all_groups(subgroup))
        return groups

    def _collect_all_projects(self, root_group: Group) -> List[Project]:
        """Recursively collect all projects.

        Args:
            root_group: Root group to start from

        Returns:
            List of all projects
        """
        projects = list(root_group.projects)
        for subgroup in root_group.subgroups:
            projects.extend(self._collect_all_projects(subgroup))
        return projects
