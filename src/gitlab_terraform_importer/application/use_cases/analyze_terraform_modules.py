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
        module_paths: List[Path] = None,
        group_module_path: Path = None,
        project_module_path: Path = None
    ) -> Dict[str, Any]:
        """Execute the module analysis use case.

        Args:
            module_paths: List of module paths to analyze (generic mode)
            group_module_path: Path to group module directory (legacy mode)
            project_module_path: Path to project module directory (legacy mode)

        Returns:
            Dictionary with analysis results

        Raises:
            FileNotFoundError: If modules not found
            ParseError: If modules cannot be parsed
        """
        # Support both old API (group/project specific) and new API (generic list)
        if module_paths is not None:
            return self._execute_generic(module_paths)
        elif group_module_path and project_module_path:
            return self._execute_legacy(group_module_path, project_module_path)
        else:
            raise ValueError("Either module_paths or both group_module_path and project_module_path must be provided")

    def _execute_generic(self, module_paths: List[Path]) -> Dict[str, Any]:
        """Execute generic module analysis for a list of modules.

        Args:
            module_paths: List of module paths to analyze

        Returns:
            Dictionary with analysis results
        """
        modules_analysis = []

        for module_path in module_paths:
            logger.info(f"Analyzing module: {module_path}")
            module = self.terraform_repository.parse_module(module_path)

            # Analyze variables
            var_analysis = self.terraform_repository.analyze_module_variables(module)

            # Check compatibility with GitLab resources
            compatible_with_gitlab = (
                module.is_compatible_with_resource_type("gitlab_group") or
                module.is_compatible_with_resource_type("gitlab_project")
            )

            module_info = {
                "path": module_path,
                "module": module,
                "analysis": var_analysis,
                "compatible_with_gitlab": compatible_with_gitlab,
            }
            modules_analysis.append(module_info)

        summary = {
            "total_modules": len(modules_analysis),
        }

        return {
            "modules": modules_analysis,
            "summary": summary,
        }

    def _execute_legacy(self, group_module_path: Path, project_module_path: Path) -> Dict[str, Any]:
        """Execute legacy module analysis for group and project modules.

        Args:
            group_module_path: Path to group module directory
            project_module_path: Path to project module directory

        Returns:
            Dictionary with analysis results
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
