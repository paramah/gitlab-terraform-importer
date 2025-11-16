"""Use case for analyzing Terraform modules."""

from pathlib import Path
from typing import Dict, Any, List
import logging

from ...domain.entities import TerraformModule
from ...domain.repositories import TerraformRepository

logger = logging.getLogger(__name__)


class AnalyzeTerraformModulesUseCase:
    """Use case for analyzing Terraform modules."""

    def __init__(self, terraform_repository: TerraformRepository):
        """Initialize use case.

        Args:
            terraform_repository: Terraform repository implementation
        """
        self.terraform_repository = terraform_repository

    def execute(
        self,
        group_module_path: Path,
        project_module_path: Path
    ) -> Dict[str, Any]:
        """Execute the module analysis use case.

        Args:
            group_module_path: Path to group module directory
            project_module_path: Path to project module directory

        Returns:
            Dictionary with analysis results

        Raises:
            FileNotFoundError: If modules not found
            ParseError: If modules cannot be parsed
        """
        logger.info(f"Analyzing group module: {group_module_path}")
        group_module = self.terraform_repository.parse_module(group_module_path)

        logger.info(f"Analyzing project module: {project_module_path}")
        project_module = self.terraform_repository.parse_module(project_module_path)

        # Validate modules
        group_valid = self.terraform_repository.validate_module_compatibility(
            group_module, "gitlab_group"
        )
        project_valid = self.terraform_repository.validate_module_compatibility(
            project_module, "gitlab_project"
        )

        if not group_valid:
            logger.warning("Group module may not be compatible with gitlab_group resources")

        if not project_valid:
            logger.warning("Project module may not be compatible with gitlab_project resources")

        # Analyze variables
        group_vars = self.terraform_repository.analyze_module_variables(group_module)
        project_vars = self.terraform_repository.analyze_module_variables(project_module)

        analysis = {
            "group_module": {
                "path": str(group_module_path),
                "name": group_module.name,
                "source": group_module.source,
                "version": group_module.version,
                "variables": group_vars,
                "required_variables": [
                    var.name for var in group_module.get_required_variables()
                ],
                "outputs": list(group_module.outputs.keys()),
                "resource_count": len(group_module.resources),
                "compatible": group_valid,
            },
            "project_module": {
                "path": str(project_module_path),
                "name": project_module.name,
                "source": project_module.source,
                "version": project_module.version,
                "variables": project_vars,
                "required_variables": [
                    var.name for var in project_module.get_required_variables()
                ],
                "outputs": list(project_module.outputs.keys()),
                "resource_count": len(project_module.resources),
                "compatible": project_valid,
            },
        }

        logger.info("Module analysis complete")
        logger.info(f"Group module: {len(group_module.variables)} variables, "
                   f"{len(group_module.resources)} resources")
        logger.info(f"Project module: {len(project_module.variables)} variables, "
                   f"{len(project_module.resources)} resources")

        return analysis

    def get_modules(
        self,
        group_module_path: Path,
        project_module_path: Path
    ) -> tuple[TerraformModule, TerraformModule]:
        """Parse and return both modules.

        Args:
            group_module_path: Path to group module
            project_module_path: Path to project module

        Returns:
            Tuple of (group_module, project_module)
        """
        group_module = self.terraform_repository.parse_module(group_module_path)
        project_module = self.terraform_repository.parse_module(project_module_path)
        return group_module, project_module
