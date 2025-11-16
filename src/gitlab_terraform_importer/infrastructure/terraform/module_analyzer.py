"""Terraform module analyzer."""

from typing import Dict, Any, List
import logging

from ...domain.entities import TerraformModule, TerraformVariable

logger = logging.getLogger(__name__)


class ModuleAnalyzer:
    """Analyzer for Terraform modules."""

    def analyze_variables(self, module: TerraformModule) -> Dict[str, Any]:
        """Analyze variables in a module.

        Args:
            module: Terraform module

        Returns:
            Dictionary with variable analysis
        """
        analysis = {
            "total_count": len(module.variables),
            "required_count": len(module.get_required_variables()),
            "optional_count": len([v for v in module.variables.values() if not v.required or v.default is not None]),
            "sensitive_count": len([v for v in module.variables.values() if v.sensitive]),
            "by_type": self._count_by_type(module.variables),
            "variables": {},
        }

        for var_name, var in module.variables.items():
            analysis["variables"][var_name] = {
                "type": var.type,
                "required": var.required,
                "has_default": var.default is not None,
                "sensitive": var.sensitive,
                "description": var.description,
            }

        return analysis

    def validate_module_for_resource_type(
        self,
        module: TerraformModule,
        expected_resource_type: str
    ) -> bool:
        """Validate if module is compatible with a resource type.

        Args:
            module: Terraform module
            expected_resource_type: Expected resource type (e.g., 'gitlab_group')

        Returns:
            True if compatible
        """
        # Check if module contains the expected resource type
        for resource in module.resources:
            if resource.resource_type == expected_resource_type:
                return True

        logger.warning(
            f"Module {module.name} does not contain {expected_resource_type} resources"
        )
        return False

    def get_module_resource_types(self, module: TerraformModule) -> List[str]:
        """Get all resource types used in a module.

        Args:
            module: Terraform module

        Returns:
            List of resource types
        """
        return list(set(resource.resource_type for resource in module.resources))

    def _count_by_type(self, variables: Dict[str, TerraformVariable]) -> Dict[str, int]:
        """Count variables by type.

        Args:
            variables: Dictionary of variables

        Returns:
            Count by type
        """
        counts: Dict[str, int] = {}
        for var in variables.values():
            var_type = var.type
            counts[var_type] = counts.get(var_type, 0) + 1
        return counts

    def extract_module_schema(self, module: TerraformModule) -> Dict[str, Any]:
        """Extract schema information from a module.

        Args:
            module: Terraform module

        Returns:
            Module schema
        """
        return {
            "name": module.name,
            "source": module.source,
            "version": module.version,
            "inputs": {
                name: {
                    "type": var.type,
                    "required": var.required,
                    "description": var.description,
                    "sensitive": var.sensitive,
                }
                for name, var in module.variables.items()
            },
            "outputs": {
                name: {
                    "description": output.description,
                    "sensitive": output.sensitive,
                }
                for name, output in module.outputs.items()
            },
            "resources": [
                {
                    "type": res.resource_type,
                    "name": res.resource_name,
                }
                for res in module.resources
            ],
        }
