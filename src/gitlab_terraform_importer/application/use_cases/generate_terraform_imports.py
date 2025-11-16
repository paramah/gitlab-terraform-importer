"""Use case for generating Terraform import configuration."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from ...domain.entities import Group, Project, TerraformModule, TerraformResource
from ...domain.repositories import TerraformRepository

logger = logging.getLogger(__name__)


class GenerateTerraformImportsUseCase:
    """Use case for generating Terraform imports from GitLab data."""

    def __init__(self, terraform_repository: TerraformRepository):
        """Initialize use case.

        Args:
            terraform_repository: Terraform repository implementation
        """
        self.terraform_repository = terraform_repository

    def execute(
        self,
        gitlab_structure: Group,
        group_module: TerraformModule,
        project_module: TerraformModule,
        output_dir: Path,
        generate_import_script: bool = True
    ) -> Dict[str, Any]:
        """Execute the Terraform import generation use case.

        Args:
            gitlab_structure: GitLab group hierarchy
            group_module: Terraform module for groups
            project_module: Terraform module for projects
            output_dir: Output directory for generated files
            generate_import_script: Whether to generate import script

        Returns:
            Dictionary with generation results

        Raises:
            ValueError: If modules are incompatible
        """
        logger.info("Starting Terraform import generation")

        # Map GitLab data to Terraform resources based on modules
        resources = self.terraform_repository.map_module_to_gitlab_resources(
            group_module=group_module,
            project_module=project_module,
            gitlab_data=gitlab_structure
        )

        logger.info(f"Mapped {len(resources)} resources from GitLab data")

        # Extract groups and projects from the structure
        groups = self._collect_all_groups(gitlab_structure)
        projects = self._collect_all_projects(gitlab_structure)

        # Generate Terraform configuration files
        generated_files = self.terraform_repository.generate_resource_configs(
            groups=groups,
            projects=projects,
            output_dir=output_dir
        )

        logger.info(f"Generated {len(generated_files)} Terraform configuration files")

        # Generate import commands
        import_commands = []
        import_script_path = None

        if generate_import_script:
            import_script_path = output_dir / "import.sh"
            import_commands = self.terraform_repository.generate_import_commands(
                resources=resources,
                output_file=import_script_path
            )
            logger.info(f"Generated import script: {import_script_path}")

        result = {
            "resources_count": len(resources),
            "groups_count": len(groups),
            "projects_count": len(projects),
            "generated_files": [str(f) for f in generated_files],
            "import_commands_count": len(import_commands),
            "import_script": str(import_script_path) if import_script_path else None,
            "output_dir": str(output_dir),
        }

        logger.info("Terraform import generation complete")
        return result

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
